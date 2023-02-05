from unittest import TestCase

from goodwe.sensor import *


class TestUtils(TestCase):

    def test_byte(self):
        testee = Byte("", 0, "", "", None)

        data = io.BytesIO(bytes.fromhex("0c"))
        self.assertEqual(12, testee.read(data))
        self.assertEqual("0c", testee.encode_value(12).hex())

        data = io.BytesIO(bytes.fromhex("f0"))
        self.assertEqual(-16, testee.read(data))
        self.assertEqual("f0", testee.encode_value(-16).hex())

    def test_integer(self):
        testee = Integer("", 0, "", "", None)

        data = io.BytesIO(bytes.fromhex("0031"))
        self.assertEqual(49, testee.read(data))
        self.assertEqual("0031", testee.encode_value(49).hex())

        data = io.BytesIO(bytes.fromhex("ff9e"))
        self.assertEqual(-98, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-98).hex())

    def test_decimal(self):
        testee = Decimal("", 0, 10, "", "", None)

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

    def test_energy(self):
        testee = Energy("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("0972"))
        self.assertEqual(241.8, testee.read(data))

    def test_energy4(self):
        testee = Energy4("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("00020972"))
        self.assertEqual(13349.0, testee.read(data))
        data = io.BytesIO(bytes.fromhex("ffffffff"))
        self.assertIsNone(testee.read(data))

    def test_timestamp(self):
        testee = Timestamp("", 0, "", None)

        data = io.BytesIO(bytes.fromhex("160104121e19"))
        self.assertEqual(datetime(2022, 1, 4, 18, 30, 25), testee.read(data))
        self.assertEqual("160104121e19", testee.encode_value(datetime(2022, 1, 4, 18, 30, 25)).hex())
        self.assertEqual("160104121e19", testee.encode_value("2022-01-04T18:30:25").hex())

    def test_eco_mode(self):
        testee = EcoMode("", 0, "")

        data = io.BytesIO(bytes.fromhex("0d1e0e28ffc4ff1a"))
        self.assertEqual("13:30-14:40 Mon,Wed,Thu -60% On", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("0d1e0e28ffc4ff1a"), testee.encode_value(bytes.fromhex("0d1e0e28ffc4ff1a")))
        self.assertRaises(ValueError, lambda: testee.encode_value(bytes.fromhex("0d1e0e28ffc4ffff")))
        self.assertRaises(ValueError, lambda: testee.encode_value("some string"))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

        data = io.BytesIO(testee.encode_charge(-40))
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% On", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        data = io.BytesIO(testee.encode_discharge(60))
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% On", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertTrue(testee.read(data).is_eco_discharge_mode())
        data = io.BytesIO(testee.encode_off())
        self.assertEqual("48:0-48:0  100% Off", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

    def test_eco_mode_v2(self):
        testee = EcoModeV2("", 0, "")

        data = io.BytesIO(bytes.fromhex("0d1e0e28ff1affc4005a0000"))
        self.assertEqual("13:30-14:40 Mon,Wed,Thu -60% (max charge 90%) On", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("0d1e0e28ff1affc4005a0000"),
                         testee.encode_value(bytes.fromhex("0d1e0e28ff1affc4005a0000")))
        self.assertRaises(ValueError, lambda: testee.encode_value(bytes.fromhex("0d1e0e28ffffffc4005a0000")))
        self.assertRaises(ValueError, lambda: testee.encode_value("some string"))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

        data = io.BytesIO(testee.encode_charge(-40, 80))
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% (max charge 80%) On", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        data = io.BytesIO(testee.encode_discharge(60))
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% (max charge 100%) On", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertTrue(testee.read(data).is_eco_discharge_mode())
        data = io.BytesIO(testee.encode_off())
        self.assertEqual("48:0-48:0  100% (max charge 100%) Off", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

    def test_peak_shaving_mode(self):
        testee = PeakShavingMode("", 0, "")

        data = io.BytesIO(bytes.fromhex("010a020a037f00fa00370000"))
        self.assertEqual("1:10-2:10 Sun,Mon,Tue,Wed,Thu,Fri,Sat 2.5kW (soc 55%) Off", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("010a020a037f00fa00370000"),
                         testee.encode_value(bytes.fromhex("010a020a037f00fa00370000")))

    def test_eco_mode_es(self):
        testee = EcoModeEs("", 0, "")

        data = io.BytesIO(bytes.fromhex("0d1e0e280040"))
        self.assertEqual("13:30-14:40 64%", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("0d1e0e280040"), testee.encode_value(bytes.fromhex("0d1e0e280040")))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual("13:30-14:14 Sun,Mon,Tue,Wed,Thu,Fri,Sat 64% On", testee.asEcoMode(False).__str__())
        data = io.BytesIO(bytes.fromhex("0000173b64"))
        self.assertEqual("0:0-23:59 100%", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertEqual("0:0-23:23 Sun,Mon,Tue,Wed,Thu,Fri,Sat -100% On", testee.asEcoMode(True).__str__())

    def test_decode_bitmap(self):
        self.assertEqual('', decode_bitmap(0, ERROR_CODES))
        self.assertEqual('Utility Loss', decode_bitmap(512, ERROR_CODES))
        self.assertEqual(', Utility Loss', decode_bitmap(516, ERROR_CODES))
        self.assertEqual('Utility Loss, Vac Failure', decode_bitmap(131584, ERROR_CODES))
        self.assertEqual('err16', decode_bitmap(65536, BMS_WARNING_CODES))
