from unittest import TestCase

from goodwe.sensor import *


class TestUtils(TestCase):

    def test_byte(self):
        testee = Byte("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0c"))
        self.assertEqual(12, testee.read(data))
        self.assertEqual("0c", testee.encode_value(12).hex())

        data = io.BytesIO(bytes.fromhex("f0"))
        self.assertEqual(-16, testee.read(data))
        self.assertEqual("f0", testee.encode_value(-16).hex())

    def test_integer(self):
        testee = Integer("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0031"))
        self.assertEqual(49, testee.read(data))
        self.assertEqual("0031", testee.encode_value(49).hex())

        data = io.BytesIO(bytes.fromhex("ff9e"))
        self.assertEqual(-98, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-98).hex())

    def test_decimal(self):
        testee = Decimal("", 0, 10, "", None)

        data = io.BytesIO(bytes.fromhex("0031"))
        self.assertEqual(4.9, testee.read(data))
        self.assertEqual("0031", testee.encode_value(4.9).hex())

        data = io.BytesIO(bytes.fromhex("ff9e"))
        self.assertEqual(-9.8, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-9.8).hex())

    def test_voltage(self):
        testee = Voltage("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0cfe"))
        self.assertEqual(332.6, testee.read(data))
        self.assertEqual("0cfe", testee.encode_value(332.6).hex())

        data = io.BytesIO(bytes.fromhex("1f64"))
        self.assertEqual(803.6, testee.read(data))
        self.assertEqual("1f64", testee.encode_value(803.6).hex())

    def test_current(self):
        testee = Current("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0031"))
        self.assertEqual(4.9, testee.read(data))
        self.assertEqual("0031", testee.encode_value(4.9).hex())

        data = io.BytesIO(bytes.fromhex("ff9e"))
        self.assertEqual(-9.8, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-9.8).hex())

    def test_power4(self):
        testee = Power4("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0000069f"))
        self.assertEqual(1695, testee.read(data))

        data = io.BytesIO(bytes.fromhex("fffffffd"))
        self.assertEqual(-3, testee.read(data))

    def test_power_k(self):
        testee = PowerK("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0972"))
        self.assertEqual(241.8, testee.read(data))

    def test_power_k4(self):
        testee = PowerK4("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("00020972"))
        self.assertEqual(13349.0, testee.read(data))

    def test_decode_bitmap(self):
        self.assertEqual('', decode_bitmap(0, ERROR_CODES))
        self.assertEqual('Utility Loss', decode_bitmap(512, ERROR_CODES))
        self.assertEqual(', Utility Loss', decode_bitmap(516, ERROR_CODES))
        self.assertEqual('Utility Loss, Vac Failure', decode_bitmap(131584, ERROR_CODES))
