import os

from datetime import datetime
from unittest import TestCase, mock

from goodwe.xs import GoodWeXSProcessor

root_dir = os.path.dirname(os.path.abspath(__file__))


class TestProcessor(TestCase):
    def test_process_data(self):

        with open(root_dir + '/sample/inverter_data', 'rb') as f:
            mock_data = f.read()

        processor = GoodWeXSProcessor()
        data = processor.process_data(mock_data)

        self.assertEqual(data.date, datetime(year=2021, month=8, day=8, hour=10, minute=49, second=52))
        self.assertEqual(data.volts_dc, 99.8)
        self.assertEqual(data.current_dc, 1.8)
        self.assertEqual(data.volts_ac, 234.7)
        self.assertEqual(data.current_ac, 0.7)
        self.assertEqual(data.frequency_ac, 50.02)
        self.assertEqual(data.generation_today, 0.3),
        self.assertEqual(data.generation_total, 201.4)
        self.assertEqual(data.rssi, 70)
        self.assertEqual(data.operational_hours, 895)
        self.assertEqual(data.temperature, 30.3)
        self.assertEqual(data.power, 189)
        self.assertEqual(data.status, 'Normal')
