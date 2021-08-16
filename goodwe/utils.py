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
