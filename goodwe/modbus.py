import logging
from typing import Union

from .exceptions import PartialResponseException, RequestRejectedException

logger = logging.getLogger(__name__)

MODBUS_READ_CMD: int = 0x3
MODBUS_WRITE_CMD: int = 0x6
MODBUS_WRITE_MULTI_CMD: int = 0x10

ILLEGAL_DATA_ADDRESS: str = 'ILLEGAL DATA ADDRESS'

FAILURE_CODES = {
    1: "ILLEGAL FUNCTION",
    2: ILLEGAL_DATA_ADDRESS,
    3: "ILLEGAL DATA VALUE",
    4: "SLAVE DEVICE FAILURE",
    5: "ACKNOWLEDGE",
    6: "SLAVE DEVICE BUSY",
    7: "NEGATIVE ACKNOWLEDGEMENT",
    8: "MEMORY PARITY ERROR",
    10: "GATEWAY PATH UNAVAILABLE",
    11: "GATEWAY TARGET DEVICE FAILED TO RESPOND",
}


def _create_crc16_table() -> tuple:
    """Construct (modbus) CRC-16 table"""
    table = []
    for i in range(256):
        buffer = i << 1
        crc = 0
        for _ in range(8, 0, -1):
            buffer >>= 1
            if (buffer ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
        table.append(crc)
    return tuple(table)


_CRC_16_TABLE = _create_crc16_table()


def _modbus_checksum(data: Union[bytearray, bytes]) -> int:
    """
    Calculate modbus crc-16 checksum
    """
    crc = 0xFFFF
    for ch in data:
        crc = (crc >> 8) ^ _CRC_16_TABLE[(crc ^ ch) & 0xFF]
    return crc


def create_modbus_rtu_request(comm_addr: int, cmd: int, offset: int, value: int) -> bytes:
    """
    Create modbus RTU request.
    data[0] is inverter address
    data[1] is modbus command
    data[2:3] is command offset parameter
    data[4:5] is command value parameter
    data[6:7] is crc-16 checksum
    """
    data: bytearray = bytearray(6)
    data[0] = comm_addr
    data[1] = cmd
    data[2] = (offset >> 8) & 0xFF
    data[3] = offset & 0xFF
    data[4] = (value >> 8) & 0xFF
    data[5] = value & 0xFF
    checksum = _modbus_checksum(data)
    data.append(checksum & 0xFF)
    data.append((checksum >> 8) & 0xFF)
    return bytes(data)


def create_modbus_tcp_request(comm_addr: int, cmd: int, offset: int, value: int) -> bytes:
    """
    Create modbus TCP request.
    data[0:1] is transaction identifier
    data[2:3] is protocol identifier (0)
    data[4:5] message length
    data[6] is inverter address
    data[7] is modbus command
    data[8:9] is command offset parameter
    data[10:11] is command value parameter
    """
    data: bytearray = bytearray(12)
    data[0] = 0
    data[1] = 1  # Not transaction ID support yet
    data[2] = 0
    data[3] = 0
    data[4] = 0
    data[5] = 6
    data[6] = comm_addr
    data[7] = cmd
    data[8] = (offset >> 8) & 0xFF
    data[9] = offset & 0xFF
    data[10] = (value >> 8) & 0xFF
    data[11] = value & 0xFF
    return bytes(data)


def create_modbus_rtu_multi_request(comm_addr: int, cmd: int, offset: int, values: bytes) -> bytes:
    """
    Create modbus RTU (multi value) request.
    data[0] is inverter address
    data[1] is modbus command
    data[2:3] is command offset parameter
    data[4:5] is number of registers
    data[6] is number of bytes
    data[7-n] is data payload
    data[n+1:n+2] is crc-16 checksum
    """
    data: bytearray = bytearray(7)
    data[0] = comm_addr
    data[1] = cmd
    data[2] = (offset >> 8) & 0xFF
    data[3] = offset & 0xFF
    data[4] = 0
    data[5] = len(values) // 2
    data[6] = len(values)
    data.extend(values)
    checksum = _modbus_checksum(data)
    data.append(checksum & 0xFF)
    data.append((checksum >> 8) & 0xFF)
    return bytes(data)


def create_modbus_tcp_multi_request(comm_addr: int, cmd: int, offset: int, values: bytes) -> bytes:
    """
    Create modbus TCP (multi value) request.
    data[0:1] is transaction identifier
    data[2:3] is protocol identifier (0)
    data[4:5] message length
    data[6] is inverter address
    data[7] is modbus command
    data[8:9] is command offset parameter
    data[10:11] is number of registers
    data[12] is number of bytes
    data[13-n] is data payload
    """
    data: bytearray = bytearray(13)
    data[0] = 0
    data[1] = 1  # Not transaction ID support yet
    data[2] = 0
    data[3] = 0
    data[4] = 0
    data[5] = 7 + len(values)
    data[6] = comm_addr
    data[7] = cmd
    data[8] = (offset >> 8) & 0xFF
    data[9] = offset & 0xFF
    data[10] = 0
    data[11] = len(values) // 2
    data[12] = len(values)
    data.extend(values)
    return bytes(data)


def validate_modbus_rtu_response(data: bytes, cmd: int, offset: int, value: int) -> bool:
    """
    Validate the modbus RTU response.
    data[0:1] is header
    data[2] is source address
    data[3] is command return type
    data[4] is response payload length (for read commands)
    data[-2:] is crc-16 checksum
    """
    if len(data) <= 4:
        logger.debug("Response is too short.")
        return False
    if data[3] == MODBUS_READ_CMD:
        if data[4] != value * 2:
            logger.debug("Response has unexpected length: %d, expected %d.", data[4], value * 2)
            return False
        expected_length = data[4] + 7
        if len(data) < expected_length:
            raise PartialResponseException(len(data), expected_length)
    elif data[3] in (MODBUS_WRITE_CMD, MODBUS_WRITE_MULTI_CMD):
        if len(data) < 10:
            logger.debug("Response has unexpected length: %d, expected %d.", len(data), 10)
            return False
        expected_length = 10
        response_offset = int.from_bytes(data[4:6], byteorder='big', signed=False)
        if response_offset != offset:
            logger.debug("Response has wrong offset: %X, expected %X.", response_offset, offset)
            return False
        response_value = int.from_bytes(data[6:8], byteorder='big', signed=True)
        if response_value != value:
            logger.debug("Response has wrong value: %X, expected %X.", response_value, value)
            return False
    else:
        expected_length = len(data)

    checksum_offset = expected_length - 2
    if _modbus_checksum(data[2:checksum_offset]) != ((data[checksum_offset + 1] << 8) + data[checksum_offset]):
        logger.debug("Response CRC-16 checksum does not match.")
        return False

    if data[3] != cmd:
        failure_code = FAILURE_CODES.get(data[4], "UNKNOWN")
        logger.debug("Response is command failure: %s.", FAILURE_CODES.get(data[4], "UNKNOWN"))
        raise RequestRejectedException(failure_code)

    return True


def validate_modbus_tcp_response(data: bytes, cmd: int, offset: int, value: int) -> bool:
    """
    Validate the modbus TCP response.
    data[0:1] is transaction identifier
    data[2:3] is protocol identifier (0)
    data[4:5] message length
    data[6] is source address
    data[7] is command return type
    data[8] is response payload length (for read commands)
    """
    if len(data) <= 8:
        logger.debug("Response is too short.")
        return False
    expected_length = int.from_bytes(data[4:6], byteorder='big', signed=False) + 6
    # The weird expected_length != 12 is work around Goodwe bug answering wrong (hardcoded 6) length.
    if len(data) < expected_length and expected_length != 12:
        raise PartialResponseException(len(data), expected_length)

    if data[7] == MODBUS_READ_CMD:
        expected_length = data[8] + 9
        if len(data) < expected_length:
            raise PartialResponseException(len(data), expected_length)
        if data[8] != value * 2:
            logger.debug("Response has unexpected length: %d, expected %d.", data[8], value * 2)
            return False
    elif data[7] in (MODBUS_WRITE_CMD, MODBUS_WRITE_MULTI_CMD):
        if len(data) < 12:
            logger.debug("Response has unexpected length: %d, expected %d.", len(data), 14)
            raise PartialResponseException(len(data), expected_length)
        response_offset = int.from_bytes(data[8:10], byteorder='big', signed=False)
        if response_offset != offset:
            logger.debug("Response has wrong offset: %X, expected %X.", response_offset, offset)
            return False
        response_value = int.from_bytes(data[10:12], byteorder='big', signed=True)
        if response_value != value:
            logger.debug("Response has wrong value: %X, expected %X.", response_value, value)
            return False

    if data[7] != cmd:
        failure_code = FAILURE_CODES.get(data[8], "UNKNOWN")
        logger.debug("Response is command failure: %s.", FAILURE_CODES.get(data[8], "UNKNOWN"))
        raise RequestRejectedException(failure_code)

    return True
