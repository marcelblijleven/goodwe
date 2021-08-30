from unittest import TestCase, mock

from goodwe.modbus import create_modbus_request, validate_modbus_response


class TestModbus(TestCase):

    def test_create_modbus_request(self):
        request = create_modbus_request(0xf7, 0x3, 0x88b8, 0x0021)
        self.assertEqual(bytes.fromhex('f70388b800213ac1'), request)

    def test_validate_modbus_response(self):
        self.assertTrue(validate_modbus_response(bytes.fromhex('aa55f7030501020304053347')))
        # some garbage after response end
        self.assertTrue(validate_modbus_response(bytes.fromhex('aa55f7030501020304053347ffffff')))
        # length too short
        self.assertFalse(validate_modbus_response(bytes.fromhex('aa55f7030501020304')))
        # wrong checksum
        self.assertFalse(validate_modbus_response(bytes.fromhex('aa55f7030501020304053346')))
