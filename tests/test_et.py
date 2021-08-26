import asyncio
import os
from unittest import TestCase

from goodwe.et import ET
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))


class GW10K_ET(ET):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == ET._READ_DEVICE_RUNNING_DATA1:
            with open(root_dir + '/sample/et/GW10K-ET_running_data1.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == ET._READ_DEVICE_RUNNING_DATA2:
            with open(root_dir + '/sample/et/GW10K-ET_running_data2.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == ET._READ_BATTERY_INFO:
            with open(root_dir + '/sample/et/GW10K-ET_battery_info.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class EtProtocolTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.sensors = {s.id_: s.unit for s in ET.sensors()}

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensors.get(sensor))

    def test_GW10K_ET_runtime_data(self):
        testee = GW10K_ET("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

        # for sensor in ET.sensors():
        #   print(f"self.assertSensor('{sensor.id}', {data[sensor.id]}, '{self.sensors.get(sensor.id)}', data)")

        self.assertSensor('vpv1', 332.6, 'V', data)
        self.assertSensor('ipv1', 5.1, 'A', data)
        self.assertSensor('ppv1', 1695, 'W', data)
        self.assertSensor('vpv2', 332.6, 'V', data)
        self.assertSensor('ipv2', 5.3, 'A', data)
        self.assertSensor('ppv2', 1761, 'W', data)
        self.assertSensor('ppv', 3456, 'W', data)
        self.assertSensor('xx38', 0, '', data)
        self.assertSensor('xx40', 514, '', data)
        self.assertSensor('vgrid', 239.3, 'V', data)
        self.assertSensor('igrid', 1.5, 'A', data)
        self.assertSensor('fgrid', 49.99, 'Hz', data)
        self.assertSensor('pgrid', 336, 'W', data)
        self.assertSensor('vgrid2', 241.5, 'V', data)
        self.assertSensor('igrid2', 1.3, 'A', data)
        self.assertSensor('fgrid2', 49.99, 'Hz', data)
        self.assertSensor('pgrid2', 287, 'W', data)
        self.assertSensor('vgrid3', 241.1, 'V', data)
        self.assertSensor('igrid3', 1.1, 'A', data)
        self.assertSensor('fgrid3', 49.99, 'Hz', data)
        self.assertSensor('pgrid3', 206, 'W', data)
        self.assertSensor('xx72', 1, '', data)
        self.assertSensor('total_inverter_power', 831, 'W', data)
        self.assertSensor('active_power', -3, 'W', data)
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('xx82', 0, '', data)
        self.assertSensor('xx84', 0, '', data)
        self.assertSensor('xx86', 0, '', data)
        self.assertSensor('backup_v1', 239.0, 'V', data)
        self.assertSensor('backup_i1', 0.6, 'A', data)
        self.assertSensor('backup_f1', 49.98, 'Hz', data)
        self.assertSensor('xx96', 1, '', data)
        self.assertSensor('backup_p1', 107, 'W', data)
        self.assertSensor('backup_v2', 241.3, 'V', data)
        self.assertSensor('backup_i2', 0.9, 'A', data)
        self.assertSensor('backup_f2', 50.0, 'Hz', data)
        self.assertSensor('xx108', 1, '', data)
        self.assertSensor('backup_p2', 189, 'W', data)
        self.assertSensor('backup_v3', 241.2, 'V', data)
        self.assertSensor('backup_i3', 0.2, 'A', data)
        self.assertSensor('backup_f3', 49.99, 'Hz', data)
        self.assertSensor('xx120', 1, '', data)
        self.assertSensor('backup_p3', 0, 'W', data)
        self.assertSensor('load_p1', 224, 'W', data)
        self.assertSensor('load_p2', 80, 'W', data)
        self.assertSensor('load_p3', 233, 'W', data)
        self.assertSensor('load_ptotal', 537, 'W', data)
        self.assertSensor('backup_ptotal', 312, 'W', data)
        self.assertSensor('pload', 522, 'W', data)
        self.assertSensor('xx146', 4, '', data)
        self.assertSensor('temperature2', 51.0, 'C', data)
        self.assertSensor('xx150', 0, '', data)
        self.assertSensor('temperature', 58.7, 'C', data)
        self.assertSensor('xx154', 0, '', data)
        self.assertSensor('xx156', 8036, '', data)
        self.assertSensor('xx158', 4018, '', data)
        self.assertSensor('vbattery1', 254.2, 'V', data)
        self.assertSensor('ibattery1', -9.8, 'A', data)
        self.assertSensor('pbattery1', -2491, 'W', data)
        self.assertSensor('battery_mode', 3, '', data)
        self.assertSensor('battery_mode_label', 'Charge', '', data)
        self.assertSensor('xx170', 0, '', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz Grid Default', '', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('xx176', 0, '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 6085.3, 'kWh', data)
        self.assertSensor('e_day', 12.5, 'kWh', data)
        self.assertSensor('xx190', 0, '', data)
        self.assertSensor('s_total', -1835.0, 'kWh', data)
        self.assertSensor('h_total', 9246, 'h', data)
        self.assertSensor('xx198', 98, '', data)
        self.assertSensor('s_day', 0.0, 'kWh', data)
        self.assertSensor('diagnose_result', 117442560, '', data)
        self.assertSensor('house_consumption', 968, 'W', data)
        self.assertSensor('battery_bms', 255, '', data)
        self.assertSensor('battery_index', 256, '', data)
        self.assertSensor('battery_temperature', 37.0, 'C', data)
        self.assertSensor('battery_charge_limit', 10, 'A', data)
        self.assertSensor('battery_discharge_limit', 25, 'A', data)
        self.assertSensor('battery_status', 0, '', data)
        self.assertSensor('battery_soc', 91, '%', data)
        self.assertSensor('battery_soh', 99, '%', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('xxx0', 1, '', data)
        self.assertSensor('xxx2', 37, '', data)
        self.assertSensor('xxx4', 10, '', data)
        self.assertSensor('xxx6', 0, '', data)
        self.assertSensor('xxx8', 1, '', data)
        self.assertSensor('xxx10', -8, '', data)
        self.assertSensor('xxx12', 18, '', data)
        self.assertSensor('xxx14', -24, '', data)
        self.assertSensor('xxx16', -13, '', data)
        self.assertSensor('xxx18', 991, '', data)
        self.assertSensor('xxx20', 17, '', data)
        self.assertSensor('xxx22', 89, '', data)
        self.assertSensor('xxx24', -61, '', data)
        self.assertSensor('xxx26', -4, '', data)
        self.assertSensor('xxx28', 4998, '', data)
        self.assertSensor('xxx30', 17953, '', data)
        self.assertSensor('xxx32', 26304, '', data)
