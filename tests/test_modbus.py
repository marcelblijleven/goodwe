from unittest import TestCase, mock

from goodwe.modbus import create_modbus_request, validate_modbus_response


class TestModbus(TestCase):

    def assert_response_ok(self, response: str, cmd: int, value: int):
        self.assertTrue(validate_modbus_response(bytes.fromhex(response), cmd, 0, value))

    def assert_response_fail(self, response: str, cmd: int, value: int):
        self.assertFalse(validate_modbus_response(bytes.fromhex(response), cmd, 0, value))

    def test_create_modbus_request(self):
        request = create_modbus_request(0xf7, 0x3, 0x88b8, 0x0021)
        self.assertEqual(bytes.fromhex('f70388b800213ac1'), request)

    def test_validate_modbus_read_response(self):
        self.assert_response_ok('aa55f7030401020304cd33', 0x03, 2)
        # some garbage after response end
        self.assert_response_ok('aa55f7030401020304cd33ffffff', 0x03, 2)
        # length too short
        self.assert_response_fail('aa55f7030401020304', 0x03, 2)
        # wrong checksum
        self.assert_response_fail('aa55f70304010203043346', 0x03, 2)
        # failure code
        self.assert_response_fail('aa55f783040102030405b35e', 0x03, 2)
        # unexpected message length
        self.assert_response_fail('aa55f70306010203040506b417', 0x03, 2)

    def test_validate_modbus_write_response(self):
        self.assert_response_ok('aa55f706b12c00147ba6', 0x06, 0)
        # some garbage after response end
        self.assert_response_ok('aa55f706b12c00147ba6ffffff', 0x06, 0)
        # length too short
        self.assert_response_fail('aa55f7066b12', 0x06, 0)
        # wrong checksum
        self.assert_response_fail('aa55f706b12c00147ba7', 0x06, 0)
