from __future__ import annotations

import asyncio
from unittest import IsolatedAsyncioTestCase

from goodwe.exceptions import MaxRetriesException
from goodwe.protocol import ProtocolCommand, TcpInverterProtocol, UdpInverterProtocol

TIMEOUT = 0.2
REPLY_DELAY = 0.05


def _command(name: bytes) -> ProtocolCommand:
    return ProtocolCommand(name, lambda data, expected=b'response to ' + name: data == expected)


class _FakeTransport:
    """Transport stub, delivers everything to the fake network."""

    def __init__(self, network):
        self.network = network
        self.closed = False

    def is_closing(self) -> bool:
        return self.closed

    def close(self) -> None:
        self.closed = True

    def sendto(self, payload: bytes) -> None:
        self.network.send(self, payload)

    def write(self, payload: bytes) -> None:
        self.network.send(self, payload)

    def get_extra_info(self, name):
        return None


class _FakeNetwork:
    """Fake inverter answering each request with 'response to <request>'.

    The first N sends of a request can be dropped to simulate a timeout.
    It records whether a request was sent while the previous one was still awaiting its response.
    """

    def __init__(self, protocol):
        self.protocol = protocol
        self.drops: dict[bytes, int] = {}
        self.sent: list[bytes] = []
        self.overlaps = 0
        self.on_send = None
        self._in_flight = None

    def send(self, transport: _FakeTransport, payload: bytes) -> None:
        if self._in_flight is not None and not self._in_flight.done():
            self.overlaps += 1
        self._in_flight = self.protocol.response_future
        self.sent.append(payload)
        if self.on_send:
            self.on_send(payload)
        if self.drops.get(payload, 0) > 0:
            self.drops[payload] -= 1
            return
        asyncio.get_running_loop().call_later(REPLY_DELAY, self._reply, transport, payload)

    def _reply(self, transport: _FakeTransport, payload: bytes) -> None:
        if transport.closed:
            return
        data = b'response to ' + payload
        if isinstance(self.protocol, UdpInverterProtocol):
            self.protocol.datagram_received(data, ('127.0.0.1', 8899))
        else:
            self.protocol.data_received(data)


class _FakeUdpProtocol(UdpInverterProtocol):
    def __init__(self, retries: int):
        super().__init__('127.0.0.1', 8899, 0xf7, TIMEOUT, retries)
        self.network = _FakeNetwork(self)

    async def _connect(self) -> None:
        if not self._transport or self._transport.is_closing():
            self._transport = _FakeTransport(self.network)


class _FakeTcpProtocol(TcpInverterProtocol):
    def __init__(self, retries: int):
        super().__init__('127.0.0.1', 502, 0xf7, TIMEOUT, retries)
        self.network = _FakeNetwork(self)

    async def _connect(self) -> None:
        if not self._transport or self._transport.is_closing():
            self._transport = _FakeTransport(self.network)


async def _send(protocol, name: bytes) -> bytes:
    return (await protocol.send_request(_command(name))).result()


class _ConcurrencyTests:
    """Concurrent send_request() calls sharing one protocol instance."""

    def create_protocol(self, retries: int):
        raise NotImplementedError()

    async def _gather(self, *tasks):
        return await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 5)

    async def test_concurrent_requests_with_timeout(self):
        protocol = self.create_protocol(retries=3)
        network = protocol.network
        network.drops = {b'A': 1}

        results = await self._gather(*(asyncio.create_task(_send(protocol, n)) for n in (b'A', b'B', b'C')))

        self.assertEqual([b'response to A', b'response to B', b'response to C'], results)
        self.assertEqual(0, network.overlaps)
        # the retry of A is sent right after its timeout, B and C are not interleaved
        self.assertEqual([b'A', b'A', b'B', b'C'], network.sent)

    async def test_retries_are_counted_per_request(self):
        protocol = self.create_protocol(retries=2)
        network = protocol.network
        network.drops = {b'A': 3}

        results = await self._gather(*(asyncio.create_task(_send(protocol, n)) for n in (b'A', b'B')))

        self.assertIsInstance(results[0], MaxRetriesException)
        self.assertEqual(b'response to B', results[1])
        self.assertEqual(0, network.overlaps)
        # 1 attempt + 2 retries for A, 1 attempt for B
        self.assertEqual(3, network.sent.count(b'A'))
        self.assertEqual(1, network.sent.count(b'B'))

    async def test_retries_available_after_failed_request(self):
        protocol = self.create_protocol(retries=2)
        network = protocol.network
        network.drops = {b'A': 3, b'B': 1}

        with self.assertRaises(MaxRetriesException):
            await _send(protocol, b'A')
        self.assertEqual(b'response to B', await _send(protocol, b'B'))
        self.assertEqual([b'A', b'A', b'A', b'B', b'B'], network.sent)

    async def _cancel_waiting_request(self, keep_alive: bool):
        protocol = self.create_protocol(retries=3)
        protocol.keep_alive = keep_alive
        network = protocol.network
        network.drops = {b'A': 1}
        b_sent = asyncio.Event()
        network.on_send = lambda payload: b_sent.set() if payload == b'B' else None

        task_a = asyncio.create_task(_send(protocol, b'A'))
        await asyncio.sleep(0)
        task_b = asyncio.create_task(_send(protocol, b'B'))
        await b_sent.wait()
        # caller of A gives up (e.g. asyncio.timeout), while B is in flight
        task_a.cancel()
        await asyncio.sleep(0)
        task_c = asyncio.create_task(_send(protocol, b'C'))

        results = await self._gather(task_a, task_b, task_c)

        self.assertEqual(0, network.overlaps)
        self.assertEqual(b'response to B', results[1])
        self.assertEqual(b'response to C', results[2])
        # B was neither disturbed nor retried
        self.assertEqual(1, network.sent.count(b'B'))

    async def test_cancelled_request_keeps_lock_consistent(self):
        await self._cancel_waiting_request(keep_alive=False)

    async def test_cancelled_request_keeps_lock_consistent_keep_alive(self):
        await self._cancel_waiting_request(keep_alive=True)


class TestUdpConcurrency(_ConcurrencyTests, IsolatedAsyncioTestCase):
    def create_protocol(self, retries: int):
        return _FakeUdpProtocol(retries)


class TestTcpConcurrency(_ConcurrencyTests, IsolatedAsyncioTestCase):
    def create_protocol(self, retries: int):
        return _FakeTcpProtocol(retries)
