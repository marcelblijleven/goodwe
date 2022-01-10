from __future__ import annotations

import asyncio
import logging
from asyncio.futures import Future
from typing import Tuple, Optional, Callable

from .const import GOODWE_UDP_PORT
from .exceptions import MaxRetriesException, RequestFailedException, RequestRejectedException
from .modbus import create_modbus_request, create_modbus_multi_request, validate_modbus_response, MODBUS_READ_CMD, \
    MODBUS_WRITE_CMD, MODBUS_WRITE_MULTI_CMD

logger = logging.getLogger(__name__)


class UdpInverterProtocol(asyncio.DatagramProtocol):
    def __init__(
            self,
            response_future: Future,
            command: ProtocolCommand,
            timeout: int,
            retries: int
    ):
        super().__init__()
        self.response_future: Future = response_future
        self.command: ProtocolCommand = command
        self._transport: asyncio.transports.DatagramTransport | None = None
        self._retry_timeout: int = timeout
        self._max_retries: int = retries
        self._retries: int = 0

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """On connection made"""
        self._transport = transport
        self._send_request()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """On connection lost"""
        if exc is not None:
            logger.debug("Socket closed with error: %s.", exc)
        # Cancel Future on connection lost
        if not self.response_future.done():
            self.response_future.cancel()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """On datagram received"""
        try:
            if self.command.validator(data):
                logger.debug("Received: %s", data.hex())
                self.response_future.set_result(data)
            else:
                logger.debug("Received invalid response: %s", data.hex())
                self._retries += 1
                self._send_request()
        except RequestRejectedException as ex:
            logger.debug("Received exception response: %s", data.hex())
            self.response_future.set_exception(ex)

    def error_received(self, exc: Exception) -> None:
        """On error received"""
        logger.debug("Received error: %s", exc)
        self.response_future.set_exception(exc)

    def _send_request(self) -> None:
        """Send message via transport"""
        logger.debug("Sending: %s%s", self.command,
                     f' - retry #{self._retries}/{self._max_retries}' if self._retries > 0 else '')
        self._transport.sendto(self.command.request)
        asyncio.get_event_loop().call_later(self._retry_timeout, self._retry_mechanism)

    def _retry_mechanism(self) -> None:
        """Retry mechanism to prevent hanging transport"""
        if self.response_future.done():
            self._transport.close()
        elif self._retries < self._max_retries:
            logger.debug("Failed to receive response to %s in time (%ds).", self.command, self._retry_timeout)
            self._retries += 1
            self._send_request()
        else:
            logger.debug("Max number of retries (%d) reached, request %s failed.", self._max_retries, self.command)
            self.response_future.set_exception(MaxRetriesException)


class ProtocolCommand:
    """Definition of inverter protocol command"""

    def __init__(self, request: bytes, validator: Callable[[bytes], bool]):
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator

    def __repr__(self):
        return self.request.hex()

    async def execute(self, host: str, timeout: int, retries: int) -> bytes:
        """
        Execute the udp protocol command on the specified address/port.
        Since the UDP communication is by definition unreliable, when no (valid) response is received by specified
        timeout, the command will be re-tried up to retries times.

        Return raw response data
        """
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: UdpInverterProtocol(response_future, self, timeout, retries),
            remote_addr=(host, GOODWE_UDP_PORT),
        )
        try:
            await response_future
            result = response_future.result()
            if result is not None:
                return result
            else:
                raise RequestFailedException(
                    "No response received to '" + self.request.hex() + "' request."
                )
        except asyncio.CancelledError:
            raise RequestFailedException(
                "No valid response received to '" + self.request.hex() + "' request."
            ) from None
        finally:
            transport.close()


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
        if (
                len(data) <= 8
                or len(data) != data[6] + 9
                or (response_type and int(response_type, 16) != int.from_bytes(data[4:6], byteorder="big", signed=True))
        ):
            logger.debug("Response has unexpected length: %d, expected %d.", len(data), data[6] + 9)
            return False
        else:
            checksum = 0
            for each in data[:-2]:
                checksum += each
            if checksum != int.from_bytes(data[-2:], byteorder="big", signed=True):
                logger.debug("Response checksum does not match.")
                return False
            return True


class ModbusProtocolCommand(ProtocolCommand):
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
            lambda x: validate_modbus_response(x, cmd, offset, value),
        )


class ModbusReadCommand(ModbusProtocolCommand):
    """
    Inverter modbus READ command for retrieving <count> modbus registers starting at register # <offset>
    """

    def __init__(self, comm_addr: int, offset: int, count: int):
        super().__init__(
            create_modbus_request(comm_addr, MODBUS_READ_CMD, offset, count),
            MODBUS_READ_CMD, offset, count)


class ModbusWriteCommand(ModbusProtocolCommand):
    """
    Inverter modbus WRITE command setting single modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, register: int, value: int):
        super().__init__(
            create_modbus_request(comm_addr, MODBUS_WRITE_CMD, register, value),
            MODBUS_WRITE_CMD, register, value)


class ModbusWriteMultiCommand(ModbusProtocolCommand):
    """
    Inverter modbus WRITE command setting multiple modbus register # <register> value <value>
    """

    def __init__(self, comm_addr: int, offset: int, values: bytes):
        super().__init__(
            create_modbus_multi_request(comm_addr, MODBUS_WRITE_MULTI_CMD, offset, values),
            MODBUS_WRITE_MULTI_CMD, offset, len(values) // 2)
