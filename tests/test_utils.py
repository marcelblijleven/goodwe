import io
from unittest import TestCase

from goodwe.utils import read_byte, read_bytes2, read_voltage


class TestUtils(TestCase):

    def test_read_byte(self):
        data = bytes()
        data += (21).to_bytes(1, 'big')
        data += (5).to_bytes(1, 'big')
        buffer = io.BytesIO(data)

        self.assertEqual(read_byte(buffer, 0), 21)
        self.assertEqual(read_byte(buffer, 1), 5)

    def test_read_bytes2(self):
        data = bytes()
        data += (21).to_bytes(1, 'big')
        data += (1337).to_bytes(2, 'big')
        buffer = io.BytesIO(data)

        self.assertEqual(read_bytes2(buffer, 1), 1337)

    def test_read_voltage(self):
        data = bytes()
        data += (21).to_bytes(1, 'big')
        data += (1337).to_bytes(2, 'big')
        buffer = io.BytesIO(data)

        self.assertEqual(read_voltage(buffer, 1), 133.7)
