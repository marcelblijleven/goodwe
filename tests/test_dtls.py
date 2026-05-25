"""Tests for the DTLS transport.

The DTLS layer itself (pyOpenSSL) is not re-tested here — these tests verify
the async wrapper, retry/lock semantics, and command-construction symmetry with
the legacy UDP path. The blocking ``_send_recv_blocking`` and ``_close_session``
methods are patched out; pyOpenSSL is exercised end-to-end against real hardware
in ``tests/manual_dtls_check.py`` (excluded from the standard test run).
"""

import asyncio
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import MagicMock, patch

from goodwe.dtls import DTLSInverterProtocol
from goodwe.exceptions import RequestFailedException
from goodwe.protocol import (
    ModbusRtuReadCommand,
    ModbusRtuWriteCommand,
    ModbusRtuWriteMultiCommand,
)


# Canned bytes representing the dongle's response to FC03 read of 1 register at 0x7594.
# Format: AA 55 [slave] [fc] [byte_count] [hi lo] [crc16_lo crc16_hi]
_VALID_FC03_RESPONSE = bytes.fromhex("aa55f70302" + "1A04" + "")  # placeholder, fixed below


def _build_fc03_response(comm_addr: int, register_count: int, data: bytes) -> bytes:
    """Build a wrapped Modbus RTU response that the existing validator accepts."""
    from goodwe.modbus import _modbus_checksum, MODBUS_READ_CMD
    body = bytearray()
    body.append(0xAA)  # AA55 wrapper byte 0
    body.append(0x55)  # AA55 wrapper byte 1
    body.append(comm_addr)
    body.append(MODBUS_READ_CMD)
    body.append(register_count * 2)  # byte count
    body.extend(data)
    crc = _modbus_checksum(bytes(body[2:]))  # CRC over slave..data
    body.append(crc & 0xFF)
    body.append((crc >> 8) & 0xFF)
    return bytes(body)


class TestDTLSCommandConstruction(TestCase):
    """The DTLS protocol class must produce the same Modbus RTU framing as
    UdpInverterProtocol — only the transport differs."""

    def setUp(self):
        self.proto = DTLSInverterProtocol("192.0.2.1", 8899, comm_addr=0xF7)

    def test_read_command_returns_modbus_rtu(self):
        cmd = self.proto.read_command(0x7594, 0x49)
        self.assertIsInstance(cmd, ModbusRtuReadCommand)

    def test_write_command_returns_modbus_rtu(self):
        cmd = self.proto.write_command(40328, 50)
        self.assertIsInstance(cmd, ModbusRtuWriteCommand)

    def test_write_multi_command_returns_modbus_rtu(self):
        cmd = self.proto.write_multi_command(40310, b"\x01\x02\x03\x04")
        self.assertIsInstance(cmd, ModbusRtuWriteMultiCommand)

    def test_keep_alive_default_is_true(self):
        # Re-handshaking per request would cost ~1s — DTLS sessions must persist.
        self.assertTrue(self.proto.keep_alive)


class TestDTLSSendRequest(IsolatedAsyncioTestCase):
    """Verify async send_request — uses the executor + retry + lock plumbing,
    with the actual DTLS I/O patched out."""

    def setUp(self):
        self.proto = DTLSInverterProtocol(
            "192.0.2.1", 8899, comm_addr=0xF7, timeout=1, retries=2
        )

    async def test_successful_round_trip(self):
        # Read 1 register at 0x7594, dongle responds with one big-endian U16 = 0x1A04.
        cmd = self.proto.read_command(0x7594, 1)
        canned = _build_fc03_response(0xF7, 1, b"\x1A\x04")

        with patch.object(self.proto, "_send_recv_blocking",
                          return_value=canned) as mocked:
            future = await self.proto.send_request(cmd)
            self.assertEqual(future.result(), canned)
            mocked.assert_called_once()
            # The dispatched payload is the request bytes built by ModbusRtuReadCommand.
            (sent_payload,), _ = mocked.call_args
            self.assertEqual(sent_payload[0], 0xF7)  # slave addr
            self.assertEqual(sent_payload[1], 0x03)  # function code FC03

    async def test_retry_on_transient_failure(self):
        cmd = self.proto.read_command(0x7594, 1)
        canned = _build_fc03_response(0xF7, 1, b"\x12\x34")

        attempts = []

        def flaky_send(payload):
            attempts.append(payload)
            if len(attempts) == 1:
                raise RequestFailedException("simulated UDP loss", 0)
            return canned

        with patch.object(self.proto, "_send_recv_blocking", side_effect=flaky_send):
            with patch.object(self.proto, "_close_session"):  # don't actually touch sockets
                future = await self.proto.send_request(cmd)
                self.assertEqual(future.result(), canned)
                self.assertEqual(len(attempts), 2)  # one fail, one success

    async def test_max_retries_exhausted(self):
        cmd = self.proto.read_command(0x7594, 1)

        with patch.object(
            self.proto, "_send_recv_blocking",
            side_effect=RequestFailedException("persistent failure", 0),
        ):
            with patch.object(self.proto, "_close_session"):
                future = await self.proto.send_request(cmd)
                with self.assertRaises(Exception):
                    future.result()

    async def test_stale_response_triggers_retry(self):
        """If the dongle returns a wrong-length response (stale from a prior
        request), the validator rejects it and we retry on the next attempt."""
        cmd = self.proto.read_command(0x7594, 1)  # asks for 1 register => 2 bytes
        stale = _build_fc03_response(0xF7, 2, b"\x00\x00\x00\x00")
        good = _build_fc03_response(0xF7, 1, b"\x12\x34")

        send_calls = []

        def respond(payload):
            send_calls.append(payload)
            return stale if len(send_calls) == 1 else good

        with patch.object(self.proto, "_send_recv_blocking", side_effect=respond):
            with patch.object(self.proto, "_close_session"):
                future = await self.proto.send_request(cmd)
                self.assertEqual(future.result(), good)
                # The same payload was sent twice — session continued, retry happened.
                self.assertEqual(len(send_calls), 2)
                self.assertEqual(send_calls[0], send_calls[1])

    async def test_io_exception_recovers_via_retry(self):
        """On a genuine I/O failure (not just a stale response), the next
        attempt still succeeds — the retry/lock plumbing handles both cases."""
        cmd = self.proto.read_command(0x7594, 1)
        good = _build_fc03_response(0xF7, 1, b"\x12\x34")

        send_calls = []

        def flaky(payload):
            send_calls.append(payload)
            if len(send_calls) == 1:
                raise OSError("simulated socket failure")
            return good

        with patch.object(self.proto, "_send_recv_blocking", side_effect=flaky):
            with patch.object(self.proto, "_close_session"):
                future = await self.proto.send_request(cmd)
                self.assertEqual(future.result(), good)
                self.assertEqual(len(send_calls), 2)


class TestDTLSCloseLifecycle(IsolatedAsyncioTestCase):
    async def test_close_calls_close_session(self):
        proto = DTLSInverterProtocol("192.0.2.1", 8899, comm_addr=0xF7)
        with patch.object(proto, "_close_session") as mocked:
            await proto.close()
            mocked.assert_called_once()
