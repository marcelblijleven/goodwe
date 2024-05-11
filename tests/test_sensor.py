from unittest import TestCase

from goodwe.sensor import *


class MockResponse(ProtocolResponse):

    def __init__(self, response: str):
        super().__init__(bytes.fromhex(response), None)

    def response_data(self) -> bytes:
        return self.raw_data


class TestUtils(TestCase):

    def test_byte(self):
        testee = Byte("", 0, "", "", None)

        data = MockResponse("0c")
        self.assertEqual(12, testee.read(data))

        data = MockResponse("f0")
        self.assertEqual(-16, testee.read(data))

    def test_byteH(self):
        testee = ByteH("", 0, "", "", None)

        data = MockResponse("2039")
        self.assertEqual(32, testee.read(data))

        self.assertEqual("2039", testee.encode_value(32, bytes.fromhex("3039")).hex())
        self.assertEqual("ff39", testee.encode_value(-1, bytes.fromhex("3039")).hex())
        self.assertEqual("7f39", testee.encode_value(127, bytes.fromhex("3039")).hex())
        self.assertEqual("20ff", testee.encode_value(32, bytes.fromhex("ffff")).hex())

    def test_byteL(self):
        testee = ByteL("", 0, "", "", None)

        data = MockResponse("307f")
        self.assertEqual(127, testee.read(data))

        self.assertEqual("3020", testee.encode_value(32, bytes.fromhex("3039")).hex())
        self.assertEqual("30ff", testee.encode_value(-1, bytes.fromhex("3039")).hex())
        self.assertEqual("307f", testee.encode_value(127, bytes.fromhex("3039")).hex())
        self.assertEqual("ff20", testee.encode_value(32, bytes.fromhex("ffff")).hex())

    def test_integer(self):
        testee = Integer("", 0, "", "", None)

        data = MockResponse("0031")
        self.assertEqual(49, testee.read(data))
        self.assertEqual("0031", testee.encode_value(49).hex())

        data = MockResponse("ff9e")
        self.assertEqual(65438, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(65438).hex())

    def test_integer_signed(self):
        testee = IntegerS("", 0, "", "", None)

        data = MockResponse("0031")
        self.assertEqual(49, testee.read(data))
        self.assertEqual("0031", testee.encode_value(49).hex())

        data = MockResponse("ff9e")
        self.assertEqual(-98, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-98).hex())

    def test_decimal(self):
        testee = Decimal("", 0, 10, "", "", None)

        data = MockResponse("0031")
        self.assertEqual(4.9, testee.read(data))
        self.assertEqual("0031", testee.encode_value(4.9).hex())

        data = MockResponse("ff9e")
        self.assertEqual(-9.8, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-9.8).hex())

    def test_voltage(self):
        testee = Voltage("", 0, "", None)

        data = MockResponse("0cfe")
        self.assertEqual(332.6, testee.read(data))
        self.assertEqual("0cfe", testee.encode_value(332.6).hex())

        data = MockResponse("1f64")
        self.assertEqual(803.6, testee.read(data))
        self.assertEqual("1f64", testee.encode_value(803.6).hex())

        data = MockResponse("a000")
        self.assertEqual(4096.0, testee.read(data))

        data = MockResponse("ffff")
        self.assertEqual(0, testee.read(data))

    def test_current(self):
        testee = Current("", 0, "", None)

        data = MockResponse("0031")
        self.assertEqual(4.9, testee.read(data))
        self.assertEqual("0031", testee.encode_value(4.9).hex())

        data = MockResponse("ff9e")
        self.assertEqual(6543.8, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(6543.8).hex())

        data = MockResponse("ffff")
        self.assertEqual(0, testee.read(data))

    def test_current_signed(self):
        testee = CurrentS("", 0, "", None)

        data = MockResponse("0031")
        self.assertEqual(4.9, testee.read(data))
        self.assertEqual("0031", testee.encode_value(4.9).hex())

        data = MockResponse("ff9e")
        self.assertEqual(-9.8, testee.read(data))
        self.assertEqual("ff9e", testee.encode_value(-9.8).hex())

    def test_power4(self):
        testee = Power4("", 0, "", None)

        data = MockResponse("0000069f")
        self.assertEqual(1695, testee.read(data))

        data = MockResponse("fffffffd")
        self.assertEqual(4294967293, testee.read(data))

        data = MockResponse("ffffffff")
        self.assertIsNone(testee.read(data))

    def test_power4_signed(self):
        testee = Power4S("", 0, "", None)

        data = MockResponse("0000069f")
        self.assertEqual(1695, testee.read(data))

        data = MockResponse("fffffffd")
        self.assertEqual(-3, testee.read(data))

    def test_energy(self):
        testee = Energy("", 0, "", None)

        data = MockResponse("0972")
        self.assertEqual(241.8, testee.read(data))

    def test_energy4(self):
        testee = Energy4("", 0, "", None)

        data = MockResponse("00020972")
        self.assertEqual(13349.0, testee.read(data))
        data = MockResponse("ffffffff")
        self.assertIsNone(testee.read(data))

    def test_temp(self):
        testee = Temp("", 0, "", None)

        data = MockResponse("0177")
        self.assertEqual(37.5, testee.read(data))
        data = MockResponse("ffff")
        self.assertIsNone(testee.read(data))

    def test_timestamp(self):
        testee = Timestamp("", 0, "", None)

        data = MockResponse("160104121e19")
        self.assertEqual(datetime(2022, 1, 4, 18, 30, 25), testee.read(data))
        self.assertEqual("160104121e19", testee.encode_value(datetime(2022, 1, 4, 18, 30, 25)).hex())
        self.assertEqual("160104121e19", testee.encode_value("2022-01-04T18:30:25").hex())

    def test_eco_mode_v1(self):
        testee = EcoModeV1("", 0, "")

        data = MockResponse("0d1e0e28ffc4ff1a")
        self.assertEqual("13:30-14:40 Mon,Wed,Thu -60% On", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("0d1e0e28ffc4ff1a"), testee.encode_value(bytes.fromhex("0d1e0e28ffc4ff1a")))
        self.assertRaises(ValueError, lambda: testee.encode_value("some string"))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

        data = MockResponse(testee.encode_charge(-40).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% On", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% (SoC 100%) On",
                         testee.as_eco_mode_v2().__str__())
        data = MockResponse(testee.encode_discharge(60).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% On", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertTrue(testee.read(data).is_eco_discharge_mode())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% (SoC 100%) On",
                         testee.as_eco_mode_v2().__str__())
        data = MockResponse(testee.encode_off().hex())
        self.assertEqual("48:0-48:0  100% Off", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

    def test_schedule(self):
        testee = Schedule("", 0, "")

        data = MockResponse("0d1e0e28ff1affc4005a0000")
        self.assertEqual("13:30-14:40 Mon,Wed,Thu -60% (SoC 90%) On", testee.read(data).__str__())
        self.assertEqual(ScheduleType.ECO_MODE, testee.schedule_type)
        self.assertEqual(bytes.fromhex("0d1e0e28ff1affc4005a0000"),
                         testee.encode_value(bytes.fromhex("0d1e0e28ff1affc4005a0000")))
        self.assertRaises(ValueError, lambda: testee.encode_value("some string"))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

        data = MockResponse(testee.encode_charge(-40, 80).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% (SoC 80%) On", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% On", testee.as_eco_mode_v1().__str__())
        data = MockResponse(testee.encode_discharge(60).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% (SoC 100%) On", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertTrue(testee.read(data).is_eco_discharge_mode())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% On", testee.as_eco_mode_v1().__str__())
        data = MockResponse(testee.encode_off().hex())
        self.assertEqual("48:0-48:0  100% (SoC 100%) Off", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())

        data = MockResponse("0300080006fefd12005fcfff")
        self.assertEqual("3:0-8:0 Mon -75% (SoC 95%) Off", testee.read(data).__str__())
        data = MockResponse("0000173b5500001400640000")
        self.assertEqual("0:0-23:59  20% (SoC 100%) Unset", testee.read(data).__str__())
        data = MockResponse("ffffffff557f000000010001")
        self.assertEqual("-1:-1--1:-1 Sun,Mon,Tue,Wed,Thu,Fri,Sat Jan 0% (SoC 1%) Unset", testee.read(data).__str__())
        data = MockResponse("000000005500000000000000")
        self.assertEqual("0:0-0:0  0% (SoC 0%) Unset", testee.read(data).__str__())

    def test_eco_mode_v745(self):
        testee = Schedule("", 0, "", ScheduleType.ECO_MODE_745)

        data = MockResponse("0d1e0e28f91affc4005a0000")
        self.assertEqual("13:30-14:40 Mon,Wed,Thu -6% (SoC 90%) On", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("0d1e0e28f91affc4005a0000"),
                         testee.encode_value(bytes.fromhex("0d1e0e28f91affc4005a0000")))
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)

        data = MockResponse(testee.encode_charge(-40, 80).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% (SoC 80%) On", testee.read(data).__str__())
        self.assertTrue(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse(testee.encode_discharge(60).hex())
        self.assertEqual("0:0-23:59 Sun,Mon,Tue,Wed,Thu,Fri,Sat 60% (SoC 100%) On", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertTrue(testee.read(data).is_eco_discharge_mode())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse(testee.encode_off().hex())
        self.assertEqual("48:0-48:0  100% (SoC 100%) Off", testee.read(data).__str__())
        self.assertFalse(testee.read(data).is_eco_charge_mode())
        self.assertFalse(testee.read(data).is_eco_discharge_mode())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        self.assertEqual(1000, testee.power)
        self.assertEqual(100, testee.get_power())
        self.assertEqual("%", testee.get_power_unit())

        data = MockResponse("10001600f97f00c800000fff")
        self.assertEqual("16:0-22:0 Sun,Mon,Tue,Wed,Thu,Fri,Sat 20% (SoC 0%) On", testee.read(data).__str__())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse("10001600067f00c800000fff")
        self.assertEqual("16:0-22:0 Sun,Mon,Tue,Wed,Thu,Fri,Sat 20% (SoC 0%) Off", testee.read(data).__str__())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse("10001600f97ffe70004b0fff")
        self.assertEqual("16:0-22:0 Sun,Mon,Tue,Wed,Thu,Fri,Sat -40% (SoC 75%) On", testee.read(data).__str__())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse("10001600f97fff3800320fff")
        self.assertEqual("16:0-22:0 Sun,Mon,Tue,Wed,Thu,Fri,Sat -20% (SoC 50%) On", testee.read(data).__str__())
        self.assertEqual(ScheduleType.ECO_MODE_745, testee.schedule_type)
        data = MockResponse("10001600f902ff38004b0002")
        self.assertEqual("16:0-22:0 Mon Feb -20% (SoC 75%) On", testee.read(data).__str__())
        data = MockResponse("10001600f902ff38004b0004")
        self.assertEqual("16:0-22:0 Mon Mar -20% (SoC 75%) On", testee.read(data).__str__())

    def test_peak_shaving_mode(self):
        testee = PeakShavingMode("", 0, "")

        data = MockResponse("010a020a037f00fa00370000")
        self.assertEqual("1:10-2:10 Sun,Mon,Tue,Wed,Thu,Fri,Sat 2500W (SoC 55%) Off", testee.read(data).__str__())
        self.assertEqual(bytes.fromhex("010a020a037f00fa00370000"),
                         testee.encode_value(bytes.fromhex("010a020a037f00fa00370000")))

        data = MockResponse("00000d08fc7f006400140000")
        self.assertEqual("0:0-13:8 Sun,Mon,Tue,Wed,Thu,Fri,Sat 1000W (SoC 20%) On", testee.read(data).__str__())
        self.assertEqual(ScheduleType.PEAK_SHAVING, testee.schedule_type)
        data = MockResponse("00000d08037f000000000000")
        self.assertEqual("0:0-13:8 Sun,Mon,Tue,Wed,Thu,Fri,Sat 0W (SoC 0%) Off", testee.read(data).__str__())
        self.assertEqual(ScheduleType.PEAK_SHAVING, testee.schedule_type)

    def test_decode_bitmap(self):
        self.assertEqual('', decode_bitmap(0, ERROR_CODES))
        self.assertEqual('Utility Loss', decode_bitmap(512, ERROR_CODES))
        self.assertEqual('Utility Loss', decode_bitmap(516, ERROR_CODES))
        self.assertEqual('Utility Loss, Vac Failure', decode_bitmap(131584, ERROR_CODES))
        self.assertEqual('err16', decode_bitmap(65536, BMS_WARNING_CODES))
