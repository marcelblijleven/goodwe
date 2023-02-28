from unittest import TestCase

from goodwe.exceptions import RequestRejectedException
from goodwe.modbus import create_modbus_request, create_modbus_multi_request, validate_modbus_response


class TestModbus(TestCase):

    def assert_response_ok(self, response: str, cmd: int, offset: int, value: int):
        self.assertTrue(validate_modbus_response(bytes.fromhex(response), cmd, offset, value))

    def assert_response_fail(self, response: str, cmd: int, offset: int, value: int):
        self.assertFalse(validate_modbus_response(bytes.fromhex(response), cmd, offset, value))

    def assert_response_rejected(self, response: str, cmd: int, offset: int, value: int):
        self.assertRaises(RequestRejectedException,
                          lambda: validate_modbus_response(bytes.fromhex(response), cmd, offset, value))

    def test_create_modbus_request(self):
        request = create_modbus_request(0xf7, 0x3, 0x88b8, 0x0021)
        self.assertEqual('f70388b800213ac1', request.hex())

        request = create_modbus_request(0xf7, 0x6, 0x88b8, 0x00FF)
        self.assertEqual('f70688b800ff7699', request.hex())
        request = create_modbus_request(0xf7, 0x6, 0x88b8, -1)
        self.assertEqual('f70688b8ffff3769', request.hex())

    def test_create_modbus_multi_request(self):
        request = create_modbus_multi_request(0xf7, 0x10, 0x88b8, b'\x01\x02\x03\x04\x05\x06')
        self.assertEqual('f71088b8000306010203040506102e', request.hex())

    def test_validate_modbus_read_response(self):
        self.assert_response_ok('aa55f7030401020304cd33', 0x03, 0x0401, 2)
        # some garbage after response end
        self.assert_response_ok('aa55f7030401020304cd33ffffff', 0x03, 0x0401, 2)
        # length too short
        self.assert_response_fail('aa55f7030401020304', 0x03, 0x0401, 2)
        # wrong checksum
        self.assert_response_fail('aa55f70304010203043346', 0x03, 0x0401, 2)
        # failure code
        self.assert_response_rejected('aa55f783040102030405b35e', 0x03, 0x0401, 2)
        # unexpected message length
        self.assert_response_fail('aa55f70306010203040506b417', 0x03, 0x0401, 2)

    def test_validate_modbus_write_response(self):
        self.assert_response_ok('aa55f706b12c00147ba6', 0x06, 0xb12c, 0x14)
        self.assert_response_ok('aa55f706b12cffff7a19', 0x06, 0xb12c, -1)
        # some garbage after response end
        self.assert_response_ok('aa55f706b12c00147ba6ffffff', 0x06, 0xb12c, 0x14)
        # length too short
        self.assert_response_fail('aa55f7066b12', 0x06, 0xb12c, 0x14)
        # wrong checksum
        self.assert_response_fail('aa55f706b12c00147ba7', 0x06, 0xb12c, 0x14)
        # wrong value written
        self.assert_response_fail('aa55f706b12c0012fba4', 0x06, 0xb12c, 0x14)

    def test_validate_modbus_write_multi_response(self):
        self.assert_response_ok('aa55f71088b800033f1b', 0x10, 0x88b8, 0x03)
        # some garbage after response end
        self.assert_response_ok('aa55f71088b800033f1bffffff', 0x10, 0x88b8, 0x03)
        # length too short
        self.assert_response_fail('aa55f71088b8', 0x10, 0x88b8, 0x03)
        # wrong checksum
        self.assert_response_fail('aa55f71088b800033f1c', 0x10, 0x88b8, 0x03)
        # wrong value written
        self.assert_response_fail('aa55f71088b80001beda', 0x10, 0x88b8, 0x03)
