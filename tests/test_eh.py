import asyncio
import os
from unittest import TestCase

from goodwe.eh import EH
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))


class GW6000_EH(EH):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == EH._READ_DEVICE_RUNNING_DATA1:
            with open(root_dir + '/sample/eh/GW6000_EH_running_data1.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == EH._READ_DEVICE_VERSION_INFO:
            with open(root_dir + '/sample/eh/GW6000_EH_device_info.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class EhProtocolTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.sensors = {s.id_: s.unit for s in EH.sensors()}

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensors.get(sensor))

    def test_GW6000_EH_runtime_data(self):
        testee = GW6000_EH("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

        self.assertSensor('vpv1', 330.3, 'V', data)
        self.assertSensor('ipv1', 2.6, 'A', data)
        self.assertSensor('ppv1', 857, 'W', data)
        self.assertSensor('vpv2', 329.6, 'V', data)
        self.assertSensor('ipv2', 2.1, 'A', data)
        self.assertSensor('ppv2', 691, 'W', data)
        self.assertSensor('ppv', 1548, 'W', data)
        self.assertSensor('xx38', 0, '', data)
        self.assertSensor('xx40', 514, '', data)
        self.assertSensor('vgrid', 236.6, 'V', data)
        self.assertSensor('igrid', 6.6, 'A', data)
        self.assertSensor('fgrid', 49.97, 'Hz', data)
        self.assertSensor('pgrid', 1561, 'W', data)
        self.assertSensor('xx72', 1, '', data)
        self.assertSensor('total_inverter_power', 1561, 'W', data)
        self.assertSensor('active_power', -163, 'W', data)
        self.assertSensor('grid_in_out', 2, '', data)
        self.assertSensor('grid_in_out_label', 'Importing', '', data)
        self.assertSensor('xx82', 32767, '', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('backup_v1', 0.0, 'V', data)
        self.assertSensor('backup_i1', 0.0, 'A', data)
        self.assertSensor('backup_f1', 0.0, 'Hz', data)
        self.assertSensor('xx96', 0, '', data)
        self.assertSensor('backup_p1', 0, 'W', data)
        self.assertSensor('load_p1', 1724, 'W', data)
        self.assertSensor('load_ptotal', 1724, 'W', data)
        self.assertSensor('backup_ptotal', 0, 'W', data)
        self.assertSensor('pload', 1725, 'W', data)
        self.assertSensor('xx146', 0, '', data)
        self.assertSensor('temperature2', 60.4, 'C', data)
        self.assertSensor('xx150', 32767, '', data)
        self.assertSensor('temperature', 38.6, 'C', data)
        self.assertSensor('xx154', 256, '', data)
        self.assertSensor('xx156', 3806, '', data)
        self.assertSensor('xx158', -1, '', data)
        self.assertSensor('vbattery1', 0.0, 'V', data)
        self.assertSensor('ibattery1', 0.1, 'A', data)
        self.assertSensor('pbattery1', 0, 'W', data)
        self.assertSensor('battery_mode', 0, '', data)
        self.assertSensor('battery_mode_label', 'No battery', '', data)
        self.assertSensor('xx170', 0, '', data)
        self.assertSensor('safety_country', 3, '', data)
        self.assertSensor('safety_country_label', 'Spain', '', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('xx176', -1, '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 59.4, 'kWh', data)
        self.assertSensor('e_day', 22.0, 'kWh', data)
        self.assertSensor('xx190', 0, '', data)
        self.assertSensor('s_total', 58.6, 'kWh', data)
        self.assertSensor('h_total', 33, 'h', data)
        self.assertSensor('xx198', 216, '', data)
        self.assertSensor('s_day', 0.0, 'kWh', data)
        self.assertSensor('diagnose_result', 117983303, '', data)
        self.assertSensor('house_consumption', 1711, 'W', data)
