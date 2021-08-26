import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe.dt import DT
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))


class GW8K_DT(DT):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == DT._READ_DEVICE_RUNNING_DATA:
            with open(root_dir + '/sample/dt/GW8K-DT_running_data.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == DT._READ_DEVICE_VERSION_INFO:
            with open(root_dir + '/sample/dt/GW8K-DT_device_info.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class DtProtocolTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.sensors = {s.id: s.unit for s in DT.sensors()}

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensors.get(sensor))

    def test_GW8K_DT_runtime_data(self):
        testee = GW8K_DT("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

        self.assertSensor('timestamp', datetime.strptime('2021-08-24 16:43:27', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 275.5, 'V', data)
        self.assertSensor('ipv1', 0.6, 'A', data)
        self.assertSensor('ppv1', 165, 'W', data)
        self.assertSensor('vpv2', 510.8, 'V', data)
        self.assertSensor('ipv2', 0.8, 'A', data)
        self.assertSensor('ppv2', 409, 'W', data)
        self.assertSensor('xx14', -1, '', data)
        self.assertSensor('xx16', -1, '', data)
        self.assertSensor('xx18', -1, '', data)
        self.assertSensor('xx20', -1, '', data)
        self.assertSensor('xx22', -1, '', data)
        self.assertSensor('xx24', -1, '', data)
        self.assertSensor('xx26', -1, '', data)
        self.assertSensor('xx28', -1, '', data)
        self.assertSensor('vline1', 413.7, 'V', data)
        self.assertSensor('vline2', 413.0, 'V', data)
        self.assertSensor('vline3', 408.0, 'V', data)
        self.assertSensor('vgrid1', 237.2, 'V', data)
        self.assertSensor('vgrid2', 240.5, 'V', data)
        self.assertSensor('vgrid3', 235.2, 'V', data)
        self.assertSensor('igrid1', 1.0, 'A', data)
        self.assertSensor('igrid2', 1.0, 'A', data)
        self.assertSensor('igrid3', 1.0, 'A', data)
        self.assertSensor('fgrid1', 50.08, 'Hz', data)
        self.assertSensor('fgrid2', 50.04, 'Hz', data)
        self.assertSensor('fgrid3', 50.0, 'Hz', data)
        self.assertSensor('pgrid1', 237, 'W', data)
        self.assertSensor('pgrid2', 240, 'W', data)
        self.assertSensor('pgrid3', 235, 'W', data)
        self.assertSensor('xx54', 0, '', data)
        self.assertSensor('ppv', 643, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('xx60', 0, '', data)
        self.assertSensor('xx62', 0, '', data)
        self.assertSensor('xx64', 0, '', data)
        self.assertSensor('xx66', 0, '', data)
        self.assertSensor('xx68', 0, '', data)
        self.assertSensor('xx70', 0, '', data)
        self.assertSensor('xx72', 0, '', data)
        self.assertSensor('xx74', 0, '', data)
        self.assertSensor('xx76', 0, '', data)
        self.assertSensor('xx78', 0, '', data)
        self.assertSensor('xx80', -1, '', data)
        self.assertSensor('temperature', 45.3, 'C', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('e_day', -0.1, 'kWh', data)
        self.assertSensor('xx90', -1, '', data)
        self.assertSensor('e_total', -0.1, 'kWh', data)
        self.assertSensor('xx94', -1, '', data)
        self.assertSensor('h_total', -1, '', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz Grid Default', '', data)
        self.assertSensor('xx100', 0, '', data)
        self.assertSensor('xx102', 0, '', data)
        self.assertSensor('xx104', 0, '', data)
        self.assertSensor('xx106', 0, '', data)
        self.assertSensor('xx108', -1, '', data)
        self.assertSensor('xx110', -1, '', data)
        self.assertSensor('xx112', -1, '', data)
        self.assertSensor('xx114', -1, '', data)
        self.assertSensor('xx116', -1, '', data)
        self.assertSensor('xx118', -1, '', data)
        self.assertSensor('xx120', -1, '', data)
        self.assertSensor('xx122', -1, '', data)
        self.assertSensor('funbit', 512, '', data)
        self.assertSensor('vbus', 624.2, 'V', data)
        self.assertSensor('vnbus', 316.8, 'V', data)
        self.assertSensor('xx130', 0, '', data)
        self.assertSensor('xx132', 0, '', data)
        self.assertSensor('xx134', 0, '', data)
        self.assertSensor('xx136', 728, '', data)
        self.assertSensor('xx138', 129, '', data)
        self.assertSensor('xx140', 0, '', data)
        self.assertSensor('xx142', -1, '', data)
        self.assertSensor('xx144', 84, '', data)
