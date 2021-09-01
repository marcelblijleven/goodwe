import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe.et import ET
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))


class GW10K_ET(ET):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == self._READ_RUNNING_DATA:
            with open(root_dir + '/sample/et/GW10K-ET_running_data1.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == self._READ_METER_DATA:
            with open(root_dir + '/sample/et/GW10K-ET_running_data2.hex', 'r') as f:
                return bytes.fromhex(f.read())
        elif command == self._READ_BATTERY_INFO:
            with open(root_dir + '/sample/et/GW10K-ET_battery_info.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            self.request = command.request
            return bytes.fromhex("010203040506070809")


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
        self.assertEqual(125, len(data))

        # for sensor in ET.sensors():
        #   print(f"self.assertSensor('{sensor.id_}', {data[sensor.id_]}, '{self.sensors.get(sensor.id_)}', data)")

        self.assertSensor('timestamp', datetime.strptime('2021-08-22 11:11:12', '%Y-%m-%d %H:%M:%S'), '', data)
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
        self.assertSensor('reactive_power', 0, 'W', data)
        self.assertSensor('apparent_power', 0, 'W', data)
        self.assertSensor('backup_v1', 239.0, 'V', data)
        self.assertSensor('backup_i1', 0.6, 'A', data)
        self.assertSensor('backup_f1', 49.98, 'Hz', data)
        self.assertSensor('load_mode1', 1, '', data)
        self.assertSensor('backup_p1', 107, 'W', data)
        self.assertSensor('backup_v2', 241.3, 'V', data)
        self.assertSensor('backup_i2', 0.9, 'A', data)
        self.assertSensor('backup_f2', 50.0, 'Hz', data)
        self.assertSensor('load_mode2', 1, '', data)
        self.assertSensor('backup_p2', 189, 'W', data)
        self.assertSensor('backup_v3', 241.2, 'V', data)
        self.assertSensor('backup_i3', 0.2, 'A', data)
        self.assertSensor('backup_f3', 49.99, 'Hz', data)
        self.assertSensor('load_mode3', 1, '', data)
        self.assertSensor('backup_p3', 0, 'W', data)
        self.assertSensor('load_p1', 224, 'W', data)
        self.assertSensor('load_p2', 80, 'W', data)
        self.assertSensor('load_p3', 233, 'W', data)
        self.assertSensor('load_ptotal', 537, 'W', data)
        self.assertSensor('backup_ptotal', 312, 'W', data)
        self.assertSensor('pload', 522, 'W', data)
        self.assertSensor('ups_load', 4, '%', data)
        self.assertSensor('temperature_air', 51.0, 'C', data)
        self.assertSensor('temperature_module', 0, 'C', data)
        self.assertSensor('temperature', 58.7, 'C', data)
        self.assertSensor('xx154', 0, '', data)
        self.assertSensor('bus_voltage', 803.6, 'V', data)
        self.assertSensor('nbus_voltage', 401.8, 'V', data)
        self.assertSensor('vbattery1', 254.2, 'V', data)
        self.assertSensor('ibattery1', -9.8, 'A', data)
        self.assertSensor('pbattery1', -2491, 'W', data)
        self.assertSensor('battery_mode', 3, '', data)
        self.assertSensor('battery_mode_label', 'Charge', '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz Grid Default', '', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('operation_mode', 0, '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor("e_total", 6085.3, 'kWh', data)
        self.assertSensor("e_day", 12.5, 'kWh', data)
        self.assertSensor("e_total_exp", 4718.6, 'kWh', data)
        self.assertSensor('h_total', 9246, 'h', data)
        self.assertSensor("e_day_exp", 9.8, 'kWh', data)
        self.assertSensor("e_total_imp", 58.0, 'kWh', data)
        self.assertSensor("e_day_imp", 0.0, 'kWh', data)
        self.assertSensor("e_load_total", 8820.2, 'kWh', data)
        self.assertSensor("e_load_day", 11.6, 'kWh', data)
        self.assertSensor("e_bat_charge_total", 2758.1, 'kWh', data)
        self.assertSensor("e_bat_charge_day", 5.3, 'kWh', data)
        self.assertSensor("e_bat_discharge_total", 2442.1, 'kWh', data)
        self.assertSensor("e_bat_discharge_day", 2.9, 'kWh', data)
        self.assertSensor('diagnose_result', 117442560, '', data)
        self.assertSensor('house_consumption', 968, 'W', data)
        self.assertSensor('battery_bms', 255, '', data)
        self.assertSensor('battery_index', 256, '', data)
        self.assertSensor('battery_status', 1, '', data)
        self.assertSensor('battery_temperature', 37.0, 'C', data)
        self.assertSensor('battery_charge_limit', 10, 'A', data)
        self.assertSensor('battery_discharge_limit', 25, 'A', data)
        self.assertSensor("battery_error_l", 0, "", data),
        self.assertSensor('battery_soc', 91, '%', data)
        self.assertSensor('battery_soh', 99, '%', data)
        self.assertSensor("battery_modules", 5, "", data)
        self.assertSensor("battery_warning_l", 0, "", data)
        self.assertSensor("battery_protocol", 0, "", data)
        self.assertSensor("battery_error_h", 0, "", data)
        self.assertSensor("battery_warning_h", 0, "", data)
        self.assertSensor("battery_sw_version", 0, "", data)
        self.assertSensor("battery_hw_version", 0, "", data)
        self.assertSensor("battery_max_cell_temp_id", 0, "", data)
        self.assertSensor("battery_min_cell_temp_id", 0, "", data)
        self.assertSensor("battery_max_cell_voltage_id", 0, "", data)
        self.assertSensor("battery_min_cell_voltage_id", 0, "", data)
        self.assertSensor("battery_max_cell_temp", 0, "C", data)
        self.assertSensor("battery_min_cell_temp", 0, "C", data)
        self.assertSensor("battery_max_cell_voltage", 0, "V", data)
        self.assertSensor("battery_min_cell_voltage", 0, "V", data)
        self.assertSensor('commode', 1, '', data)
        self.assertSensor('rssi', 37, '', data)
        self.assertSensor('manufacture_code', 10, '', data)
        self.assertSensor('meter_test_status', 0, '', data)
        self.assertSensor('meter_comm_status', 1, '', data)
        self.assertSensor('active_power1', -8, 'W', data)
        self.assertSensor('active_power2', 18, 'W', data)
        self.assertSensor('active_power3', -24, 'W', data)
        self.assertSensor('active_power_total', -13, '', data)
        self.assertSensor('reactive_power_total', 991, '', data)
        self.assertSensor('meter_power_factor1', 0.17, '', data)
        self.assertSensor('meter_power_factor2', 0.89, '', data)
        self.assertSensor('meter_power_factor3', -0.61, '', data)
        self.assertSensor('meter_power_factor', -0.04, '', data)
        self.assertSensor('meter_freq', 49.98, 'Hz', data)
        self.assertSensor('meter_e_total_exp', 1795.3, 'kWh', data)
        self.assertSensor('meter_e_total_imp', 2630.4, 'kWh', data)

    def test_GW10K_ET_read_setting(self):
        testee = GW10K_ET("localhost", 8899)
        self.loop.run_until_complete(testee.read_settings('work_mode'))
        self.assertEqual('f703b798000136c7', testee.request.hex())

        self.loop.run_until_complete(testee.read_settings('grid_export_limit'))
        self.assertEqual('f703b996000155ec', testee.request.hex())

    def test_GW10K_ET_write_setting(self):
        testee = GW10K_ET("localhost", 8899)
        self.loop.run_until_complete(testee.write_settings('grid_export_limit', 100))
        self.assertEqual('f706b996006459c7', testee.request.hex())

    def test_set_grid_export_limit(self):
        testee = GW10K_ET("localhost", 8899)
        self.loop.run_until_complete(testee.set_grid_export_limit(100))
        self.assertEqual('f706b996006459c7', testee.request.hex())

    def test_set_work_mode(self):
        testee = GW10K_ET("localhost", 8899)
        self.loop.run_until_complete(testee.set_work_mode(1))
        self.assertEqual('f706b7980001fac7', testee.request.hex())

    def test_set_ongrid_battery_dod(self):
        testee = GW10K_ET("localhost", 8899)
        self.loop.run_until_complete(testee.set_ongrid_battery_dod(80))
        self.assertEqual('f706b12c00147ba6', testee.request.hex())
