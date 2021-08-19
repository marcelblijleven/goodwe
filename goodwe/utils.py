import io


def get_float_from_buffer(buffer: io.BytesIO, seek_pos: int, size: int, byteorder: str, mul: float,
                          precision: int) -> float:
    """Retrieve float value from buffer at given position"""
    buffer.seek(seek_pos)
    value = int.from_bytes(buffer.read(size), byteorder=byteorder)
    return round(float(value * mul), precision)


def get_int_from_buffer(buffer: io.BytesIO, seek_pos: int, size: int, byteorder: str) -> int:
    """Retrieve int value from buffer at given position"""
    buffer.seek(seek_pos)
    return int.from_bytes(buffer.read(size), byteorder=byteorder)


def create_crc16_table() -> tuple:
    """Construct (modbus) CRC-16 table"""
    table = []
    for i in range(256):
        data = i << 1
        crc = 0
        for _ in range(8, 0, -1):
            data >>= 1
            if (data ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
        table.append(crc)
    return tuple(table)
