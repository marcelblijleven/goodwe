import io

from unittest import TestCase

from goodwe.utils import get_float_from_buffer, get_int_from_buffer


class TestUtils(TestCase):


    def test_get_float_from_buffer(self):
        data = bytes()
        data += (21).to_bytes(1, 'big')
        data += (1337).to_bytes(2, 'big')
        buffer = io.BytesIO(data)

        value_one = get_float_from_buffer(buffer, 0, 1, 'big', 0.1, 1)
        value_two = get_float_from_buffer(buffer, 1, 2, 'big', 0.1, 0)

        self.assertEqual(value_one, 2.1)
        self.assertEqual(value_two, 134)

    def test_get_int_from_buffer(self):
        data = bytes()
        data += (21).to_bytes(1, 'big')
        data += (1337).to_bytes(2, 'big')
        buffer = io.BytesIO(data)

        value_one = get_int_from_buffer(buffer, 0, 1, 'big')
        value_two = get_int_from_buffer(buffer, 1, 2, 'big')

        self.assertEqual(value_one, 21)
        self.assertEqual(value_two, 1337)
