from unittest import TestCase

from goodwe.sensor import *


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
        data = bytes.fromhex("0cfe")
        buffer = io.BytesIO(data)
        self.assertEqual(read_voltage(buffer), 332.6)
        self.assertEqual("0cfe", encode_voltage(332.6).hex())

        data = bytes.fromhex("1f64")
        buffer = io.BytesIO(data)
        self.assertEqual(read_voltage(buffer), 803.6)
        self.assertEqual("1f64", encode_voltage(803.6).hex())

    def test_read_current(self):
        data = bytes.fromhex("0031")
        buffer = io.BytesIO(data)
        self.assertEqual(read_current(buffer), 4.9)
        self.assertEqual("0031", encode_current(4.9).hex())

        data = bytes.fromhex("ff9e")
        buffer = io.BytesIO(data)
        self.assertEqual(read_current(buffer), -9.8)
        self.assertEqual("ff9e", encode_current(-9.8).hex())

    def test_read_power(self):
        data = bytes.fromhex("0000069f")
        buffer = io.BytesIO(data)
        self.assertEqual(read_power(buffer), 1695)

        data = bytes.fromhex("fffffffd")
        buffer = io.BytesIO(data)
        self.assertEqual(read_power(buffer), -3)

    def test_read_power_k2(self):
        data = bytes.fromhex("0972")
        buffer = io.BytesIO(data)
        self.assertEqual(read_power_k2(buffer), 241.8)

    def test_read_power_k(self):
        data = bytes.fromhex("00020972")
        buffer = io.BytesIO(data)
        self.assertEqual(read_power_k(buffer), 13349.0)
