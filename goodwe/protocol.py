from __future__ import annotations

import asyncio
import io
import logging
import platform
import socket
from asyncio.futures import Future
from typing import Tuple, Optional, Callable

from .exceptions import MaxRetriesException, PartialResponseException, RequestFailedException, RequestRejectedException
from .modbus import create_modbus_rtu_request, create_modbus_rtu_multi_request, create_modbus_tcp_request, \
    create_modbus_tcp_multi_request, validate_modbus_rtu_response, validate_modbus_tcp_response, MODBUS_READ_CMD, \
    MODBUS_WRITE_CMD, MODBUS_WRITE_MULTI_CMD

logger = logging.getLogger(__name__)

_modbus_tcp_tx = 0


def _next_tx() -> bytes:
    global _modbus_tcp_tx
    _modbus_tcp_tx += 1
    if _modbus_tcp_tx == 0xFFFF:
        _modbus_tcp_tx = 1
    return int.to_bytes(_modbus_tcp_tx, length=2, byteorder="big", signed=False)


class InverterProtocol:

    def __init__(self, host: str, port: int, comm_addr: int, timeout: int, retries: int):
        self._host: str = host
        self._port: int = port
        self._comm_addr: int = comm_addr
        self._running_loop: asyncio.AbstractEventLoop | None = None
        self._lock: asyncio.Lock | None = None
        self._timer: asyncio.TimerHandle | None = None
        self.timeout: int = timeout
        self.retries: int = retries
        self.keep_alive: bool = True
        self.protocol: asyncio.Protocol | None = None
        self.response_future: Future | None = None
        self.command: ProtocolCommand | None = None
        self._partial_data: bytes | None = None

    def _ensure_lock(self) -> asyncio.Lock:
        """Validate (or create) asyncio Lock.

           The asyncio.Lock must always be created from within's asyncio loop,
           so it cannot be eagerly created in constructor.
           Additionally, since asyncio.run() creates and closes its own loop,
           the lock's scope (its creating loop) mus be verified to support proper
           behavior in subsequent asyncio.run() invocations.
        """
        if self._lock and self._running_loop == asyncio.get_event_loop():
            return self._lock
        else:
            logger.debug("Creating lock instance for current event loop.")
            self._lock = asyncio.Lock()
            self._running_loop = asyncio.get_event_loop()
            self._close_transport()
            return self._lock

    async def close(self) -> None:
        """Close the underlying transport/connection."""
        raise NotImplementedError()

    async def send_request(self, command: ProtocolCommand) -> Future:
        """Convert command to request and send it to inverter."""
        raise NotImplementedError()

    def read_command(self, offset: int, count: int) -> ProtocolCommand:
        """Create read protocol command."""
        raise NotImplementedError()

    def write_command(self, register: int, value: int) -> ProtocolCommand:
        """Create write protocol command."""
        raise NotImplementedError()

    def write_multi_command(self, offset: int, values: bytes) -> ProtocolCommand:
        """Create write multiple protocol command."""
        raise NotImplementedError()


class UdpInverterProtocol(InverterProtocol, asyncio.DatagramProtocol):
    def __init__(self, host: str, port: int, comm_addr: int, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr, timeout, retries)
        self._transport: asyncio.transports.DatagramTransport | None = None
        self._retry: int = 0

    def read_command(self, offset: int, count: int) -> ProtocolCommand:
        """Create read protocol command."""
        return ModbusRtuReadCommand(self._comm_addr, offset, count)

    def write_command(self, register: int, value: int) -> ProtocolCommand:
        """Create write protocol command."""
        return ModbusRtuWriteCommand(self._comm_addr, register, value)

    def write_multi_command(self, offset: int, values: bytes) -> ProtocolCommand:
        """Create write multiple protocol command."""
        return ModbusRtuWriteMultiCommand(self._comm_addr, offset, values)

    async def _connect(self) -> None:
        if not self._transport or self._transport.is_closing():
            self._transport, self.protocol = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: self,
                remote_addr=(self._host, self._port),
            )

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """On connection made"""
        self._transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """On connection lost"""
        if exc:
            logger.debug("Socket closed with error: %s.", exc)
        else:
            logger.debug("Socket closed.")
        self._close_transport()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """On datagram received"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        try:
            if self._partial_data:
                logger.debug("Received another response fragment: %s.", data.hex())
                data = self._partial_data + data
            if self.command.validator(data):
                if self._partial_data:
                    logger.debug("Composed fragmented response: %s", data.hex())
                else:
                    logger.debug("Received: %s", data.hex())
                self._partial_data = None
                self.response_future.set_result(data)
            else:
                logger.debug("Received invalid response: %s", data.hex())
                asyncio.get_running_loop().call_soon(self._retry_mechanism)
        except PartialResponseException:
            logger.debug("Received response fragment: %s", data.hex())
            self._partial_data = data
            return
        except asyncio.InvalidStateError:
            logger.debug("Response already handled: %s", data.hex())
        except RequestRejectedException as ex:
            logger.debug("Received exception response: %s", data.hex())
            self.response_future.set_exception(ex)
            self._close_transport()

    def error_received(self, exc: Exception) -> None:
        """On error received"""
        logger.debug("Received error: %s", exc)
        self.response_future.set_exception(exc)
        self._close_transport()

    async def send_request(self, command: ProtocolCommand) -> Future:
        """Send message via transport"""
        async with self._ensure_lock():
            await self._connect()
            response_future = asyncio.get_running_loop().create_future()
            self._retry = 0
            self._send_request(command, response_future)
            await response_future
            return response_future

    def _send_request(self, command: ProtocolCommand, response_future: Future) -> None:
        """Send message via transport"""
        self.command = command
        self.response_future = response_future
        payload = command.request_bytes()
        if self._retry > 0:
            logger.debug("Sending: %s - retry #%s/%s", self.command, self._retry, self.retries)
        else:
            logger.debug("Sending: %s", self.command)
        self._transport.sendto(payload)
        self._timer = asyncio.get_running_loop().call_later(self.timeout, self._retry_mechanism)

    def _retry_mechanism(self) -> None:
        """Retry mechanism to prevent hanging transport"""
        if self.response_future.done():
            logger.debug("Response already received.")
        elif self._retry < self.retries:
            if self._timer:
                logger.debug("Failed to receive response to %s in time (%ds).", self.command, self.timeout)
            self._retry += 1
            self._send_request(self.command, self.response_future)
        else:
            logger.debug("Max number of retries (%d) reached, request %s failed.", self.retries, self.command)
            self.response_future.set_exception(MaxRetriesException)
            self._close_transport()

    def _close_transport(self) -> None:
        if self._transport:
            try:
                self._transport.close()
            except RuntimeError:
                logger.debug("Failed to close transport.")
            self._transport = None
        # Cancel Future on connection close
        if self.response_future and not self.response_future.done():
            self.response_future.cancel()

    async def close(self):
        self._close_transport()


class TcpInverterProtocol(InverterProtocol, asyncio.Protocol):
    def __init__(self, host: str, port: int, comm_addr: int, timeout: int = 1, retries: int = 0):
        super().__init__(host, port, comm_addr, timeout, retries)
        self._transport: asyncio.transports.Transport | None = None
        self._retry: int = 0

    def read_command(self, offset: int, count: int) -> ProtocolCommand:
        """Create read protocol command."""
        return ModbusTcpReadCommand(self._comm_addr, offset, count)

    def write_command(self, register: int, value: int) -> ProtocolCommand:
        """Create write protocol command."""
        return ModbusTcpWriteCommand(self._comm_addr, register, value)

    def write_multi_command(self, offset: int, values: bytes) -> ProtocolCommand:
        """Create write multiple protocol command."""
        return ModbusTcpWriteMultiCommand(self._comm_addr, offset, values)

    async def _connect(self) -> None:
        if not self._transport or self._transport.is_closing():
            logger.debug("Opening connection.")
            self._transport, self.protocol = await asyncio.get_running_loop().create_connection(
                lambda: self,
                host=self._host, port=self._port,
            )
            if self.keep_alive:
                try:
                    sock = self._transport.get_extra_info('socket')
                    if sock is not None:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
                        if platform.system() == 'Windows':
                            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 10000))
                except AttributeError as ex:
                    logger.debug("Failed to apply KEEPALIVE: %s", ex)

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """On connection made"""
        logger.debug("Connection opened.")
        pass

    def eof_received(self) -> None:
        logger.debug("EOF received.")
        self._close_transport()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """On connection lost"""
        if exc:
            logger.debug("Connection closed with error: %s.", exc)
        else:
            logger.debug("Connection closed.")
        self._close_transport()

    def data_received(self, data: bytes) -> None:
        """On data received"""
        if self._timer:
            self._timer.cancel()
        try:
            if self._partial_data:
                logger.debug("Received another response fragment: %s.", data.hex())
                data = self._partial_data + data
            if self.command.validator(data):
                if self._partial_data:
                    logger.debug("Composed fragmented response: %s", data.hex())
                else:
                    logger.debug("Received: %s", data.hex())
                self._retry = 0
                self._partial_data = None
                self.response_future.set_result(data)
            else:
                logger.debug("Received invalid response: %s", data.hex())
                self.response_future.set_exception(RequestRejectedException())
                self._close_transport()
        except PartialResponseException:
            logger.debug("Received response fragment: %s", data.hex())
            self._partial_data = data
            return
        except asyncio.InvalidStateError:
            logger.debug("Response already handled: %s", data.hex())
        except RequestRejectedException as ex:
            logger.debug("Received exception response: %s", data.hex())
            self.response_future.set_exception(ex)
            # self._close_transport()

    def error_received(self, exc: Exception) -> None:
        """On error received"""
        logger.debug("Received error: %s", exc)
        self.response_future.set_exception(exc)
        self._close_transport()

    async def send_request(self, command: ProtocolCommand) -> Future:
        """Send message via transport"""
        await self._ensure_lock().acquire()
        try:
            await asyncio.wait_for(self._connect(), timeout=5)
            response_future = asyncio.get_running_loop().create_future()
            self._send_request(command, response_future)
            await response_future
            return response_future
        except asyncio.CancelledError:
            if self._retry < self.retries:
                if self._timer:
                    logger.debug("Connection broken error.")
                self._retry += 1
                if self._lock and self._lock.locked():
                    self._lock.release()
                self._close_transport()
                return await self.send_request(command)
            else:
                return self._max_retries_reached()
        except (ConnectionRefusedError, TimeoutError, OSError, asyncio.TimeoutError):
            if self._retry < self.retries:
                logger.debug("Connection refused error.")
                self._retry += 1
                if self._lock and self._lock.locked():
                    self._lock.release()
                return await self.send_request(command)
            else:
                return self._max_retries_reached()
        finally:
            if self._lock and self._lock.locked():
                self._lock.release()

    def _send_request(self, command: ProtocolCommand, response_future: Future) -> None:
        """Send message via transport"""
        self.command = command
        self.response_future = response_future
        payload = command.request_bytes()
        if self._retry > 0:
            logger.debug("Sending: %s - retry #%s/%s", self.command, self._retry, self.retries)
        else:
            logger.debug("Sending: %s", self.command)
        self._transport.write(payload)
        self._timer = asyncio.get_running_loop().call_later(self.timeout, self._timeout_mechanism)

    def _timeout_mechanism(self) -> None:
        """Retry mechanism to prevent hanging transport"""
        if self.response_future.done():
            self._retry = 0
        else:
            if self._timer:
                logger.debug("Failed to receive response to %s in time (%ds).", self.command, self.timeout)
                self._timer = None
            self._close_transport()

    def _max_retries_reached(self) -> Future:
        logger.debug("Max number of retries (%d) reached, request %s failed.", self.retries, self.command)
        self._close_transport()
        self.response_future = asyncio.get_running_loop().create_future()
        self.response_future.set_exception(MaxRetriesException)
        return self.response_future

    def _close_transport(self) -> None:
        if self._transport:
            try:
                self._transport.close()
            except RuntimeError:
                logger.debug("Failed to close transport.")
            self._transport = None
        # Cancel Future on connection lost
        if self.response_future and not self.response_future.done():
            self.response_future.cancel()

    async def close(self):
        await self._ensure_lock().acquire()
        try:
            self._close_transport()
        finally:
            if self._lock and self._lock.locked():
                self._lock.release()


class ProtocolResponse:
    """Definition of response to protocol command"""

    def __init__(self, raw_data: bytes, command: Optional[ProtocolCommand]):
        self.raw_data: bytes = raw_data
        self.command: ProtocolCommand = command
        self._bytes: io.BytesIO = io.BytesIO(self.response_data())

    def __repr__(self):
        return self.raw_data.hex()

    def response_data(self) -> bytes:
        if self.command is not None:
            return self.command.trim_response(self.raw_data)
        else:
            return self.raw_data

    def seek(self, address: int) -> None:
        if self.command is not None:
            self._bytes.seek(self.command.get_offset(address))
        else:
            self._bytes.seek(address)

    def read(self, size: int) -> bytes:
        return self._bytes.read(size)


class ProtocolCommand:
    """Definition of inverter protocol command"""

    def __init__(self, request: bytes, validator: Callable[[bytes], bool]):
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator

    def __eq__(self, other):
        if not isinstance(other, ProtocolCommand):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.request == other.request

    def __hash__(self):
        return hash(self.request)

    def __repr__(self):
        return self.request.hex()

    def request_bytes(self) -> bytes:
        """Return raw bytes payload, optionally pre-processed"""
        return self.request

    def trim_response(self, raw_response: bytes):
        """Trim raw response from header and checksum data"""
        return raw_response

    def get_offset(self, address: int):
        """Calculate relative offset to start of the response bytes"""
        return address

    async def execute(self, protocol: InverterProtocol) -> ProtocolResponse:
        """
        Execute the protocol command on the specified connection.

        Return ProtocolResponse with raw response data
        """
        try:
            response_future = await protocol.send_request(self)
            result = response_future.result()
            if result is not None:
                return ProtocolResponse(result, self)
            else:
                raise RequestFailedException(
                    "No response received to '" + self.request.hex() + "' request."
                )
        except (asyncio.CancelledError, ConnectionRefusedError):
            raise RequestFailedException(
                "No valid response received to '" + self.request.hex() + "' request."
            ) from None
        finally:
            if not protocol.keep_alive:
                await protocol.close()


class Aa55ProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol seen mostly on older generations of inverters.
    Quite probably it is some variation of the protocol used on RS-485 serial link,
    extended/adapted to UDP transport layer.

    Each request starts with header of 0xAA, 0x55, then 0xC0, 0x7F (probably some sort of address/command)
    followed by actual payload data.
    It is suffixed with 2 bytes of plain checksum of header+payload.

    Response starts again with 0xAA, 0x55, then 0x7F, 0xC0.
    5-6th bytes are some response type, byte 7 is length of the response payload.
    The last 2 bytes are again plain checksum of header+payload.
    """

    def __init__(self, payload: str, response_type: str):
        super().__init__(
            bytes.fromhex(
                "AA55C07F"
                + payload
                + self._checksum(bytes.fromhex("AA55C07F" + payload)).hex()
            ),
            lambda x: self._validate_response(x, response_type),
        )

    @staticmethod
    def _checksum(data: bytes) -> bytes:
        checksum = 0
        for each in data:
            checksum += each
        return checksum.to_bytes(2, byteorder="big", signed=False)

    @staticmethod
    def _validate_response(data: bytes, response_type: str) -> bool:
        """
        Validate the response.
        data[0:3] is header
        data[4:5] is response type
        data[6] is response payload length
        data[-2:] is checksum (plain sum of response data incl. header)
        """
        if len(data) <= 8 or len(data) != data[6] + 9:
            raise PartialResponseException(len(data), data[6] + 9)
        elif response_type:
            data_rt_int = int.from_bytes(data[4:6], byteorder="big", signed=True)
            if int(response_type, 16) != data_rt_int:
                logger.debug("Response type unexpected: %04x, expected %s.", data_rt_int, response_type)
                return False
        checksum = 0
        for each in data[:-2]:
            checksum += each
        if checksum != int.from_bytes(data[-2:], byteorder="big", signed=True):
            logger.debug("Response checksum does not match.")
            return False
        return True

    def trim_response(self, raw_response: bytes):
        """Trim raw response from header and checksum data"""
        return raw_response[7:-2]


class Aa55ReadCommand(Aa55ProtocolCommand):
    """
    Inverter modbus READ command for retrieving <count> modbus registers starting at register # <offset>
    """

    def __init__(self, offset: int, count: int):
        super().__init__("011A03" + "{:04x}".format(offset) + "{:02x}".format(count), "019A")


class Aa55WriteCommand(Aa55ProtocolCommand):
    """
    Inverter aa55 WRITE command setting single register # <register> value <value>
    """

    def __init__(self, register: int, value: int):
        super().__init__("023905" + "{:04x}".format(register) + "01" + "{:04x}".format(value), "02B9")


class Aa55WriteMultiCommand(Aa55ProtocolCommand):
    """
    Inverter aa55 WRITE command setting multiple register # <register> value <value>
    """

    def __init__(self, offset: int, values: bytes):
        super().__init__("02390B" + "{:04x}".format(offset) + "{:02x}".format(len(values)) + values.hex(),
                         "02B9")


class ModbusRtuProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol seen on newer generation of inverters, based on Modbus
    protocol over UDP transport layer.
    The modbus communication is rather simple, there are "registers" at specified addresses/offsets,
    each represented by 2 bytes. The protocol may query/update individual or range of these registers.
    Each register represents some measured value or operational settings.
    It's inverter implementation specific which register means what.
    Some values may span more registers (i.e. 4bytes measurement value over 2 registers).

    Every request usually starts with communication address (usually 0xF7, but can be changed).
    Second byte is the modbus command - 0x03 read multiple, 0x06 write single, 0x10 write multiple.
    Bytes 3-4 represent the register address (or start of range)
    Bytes 5-6 represent the command parameter (range size or actual value for write).
    Last 2 bytes of request is the CRC-16 (modbus flavor) of the request.

    Responses seem to always start with 0xAA, 0x55, then the comm_addr and modbus command.
    (If the command fails, the highest bit of command is set to 1 ?)
    For read requests, next byte is response payload length, then the actual payload.
    Last 2 bytes of response is again the CRC-16 of the response.
    """

    def __init__(self, request: bytes, cmd: int, offset: int, value: int):
        super().__init__(
            request,
            lambda x: validate_modbus_rtu_response(x, cmd, offset, value),
        )
        self.first_address: int = offset
        self.value = value

    def trim_response(self, raw_response: bytes):
        """Trim raw response from header and checksum data"""
        return raw_response[5:-2]

    def get_offset(self, address: int):
        """Calculate relative offset to start of the response bytes"""
        return (address - self.first_address) * 2


class ModbusRtuReadCommand(ModbusRtuProtocolCommand):
    """
    Inverter Modbus/RTU READ command for retrieving <count> modbus registers starting at register # <offset>
    """

    def __init__(self, comm_addr: int, offset: int, count: int):
        super().__init__(
            create_modbus_rtu_request(comm_addr, MODBUS_READ_CMD, offset, count),
            MODBUS_READ_CMD, offset, count)

    def __repr__(self):
        if self.value > 1:
            return f'READ {self.value} registers from {self.first_address} ({self.request.hex()})'
        else:
            return f'READ register {self.first_address} ({self.request.hex()})'


class ModbusRtuWriteCommand(ModbusRtuProtocolCommand):
    """
    Inverter Modbus/RTU WRITE command setting single modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, register: int, value: int):
        super().__init__(
            create_modbus_rtu_request(comm_addr, MODBUS_WRITE_CMD, register, value),
            MODBUS_WRITE_CMD, register, value)

    def __repr__(self):
        return f'WRITE {self.value} to register {self.first_address} ({self.request.hex()})'


class ModbusRtuWriteMultiCommand(ModbusRtuProtocolCommand):
    """
    Inverter Modbus/RTU WRITE command setting multiple modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, offset: int, values: bytes):
        super().__init__(
            create_modbus_rtu_multi_request(comm_addr, MODBUS_WRITE_MULTI_CMD, offset, values),
            MODBUS_WRITE_MULTI_CMD, offset, len(values) // 2)


class ModbusTcpProtocolCommand(ProtocolCommand):
    """
    Modbus/TCP inverter communication protocol.
    """

    def __init__(self, request: bytes, cmd: int, offset: int, value: int):
        super().__init__(
            request,
            lambda x: validate_modbus_tcp_response(x, cmd, offset, value),
        )
        self.first_address: int = offset
        self.value = value

    def request_bytes(self) -> bytes:
        """Return raw bytes payload, optionally pre-processed"""
        # Apply sequential Modbus/TCP transaction identifier
        self.request = _next_tx() + self.request[2:]
        return self.request

    def trim_response(self, raw_response: bytes):
        """Trim raw response from header and checksum data"""
        return raw_response[9:]

    def get_offset(self, address: int):
        """Calculate relative offset to start of the response bytes"""
        return (address - self.first_address) * 2


class ModbusTcpReadCommand(ModbusTcpProtocolCommand):
    """
    Inverter Modbus/TCP READ command for retrieving <count> modbus registers starting at register # <offset>
    """

    def __init__(self, comm_addr: int, offset: int, count: int):
        super().__init__(
            create_modbus_tcp_request(comm_addr, MODBUS_READ_CMD, offset, count),
            MODBUS_READ_CMD, offset, count)

    def __repr__(self):
        if self.value > 1:
            return f'READ {self.value} registers from {self.first_address} ({self.request.hex()})'
        else:
            return f'READ register {self.first_address} ({self.request.hex()})'


class ModbusTcpWriteCommand(ModbusTcpProtocolCommand):
    """
    Inverter Modbus/TCP WRITE command setting single modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, register: int, value: int):
        super().__init__(
            create_modbus_tcp_request(comm_addr, MODBUS_WRITE_CMD, register, value),
            MODBUS_WRITE_CMD, register, value)

    def __repr__(self):
        return f'WRITE {self.value} to register {self.first_address} ({self.request.hex()})'


class ModbusTcpWriteMultiCommand(ModbusTcpProtocolCommand):
    """
    Inverter Modbus/TCP WRITE command setting multiple modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, offset: int, values: bytes):
        super().__init__(
            create_modbus_tcp_multi_request(comm_addr, MODBUS_WRITE_MULTI_CMD, offset, values),
            MODBUS_WRITE_MULTI_CMD, offset, len(values) // 2)
