from unittest import TestCase, mock

from goodwe.modbus import create_modbus_request


class TestModbus(TestCase):

    def test_create_modbus_request(self):
        request = create_modbus_request(0x3, 0x88b8, 0x0021)
        self.assertEqual(bytes.fromhex('f70388b800213ac1'), request)
