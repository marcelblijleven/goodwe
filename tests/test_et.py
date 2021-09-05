import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe.et import ET
from goodwe.exceptions import RequestFailedException
from goodwe.protocol import ProtocolCommand


class EtMock(TestCase, ET):

    def __init__(self, methodName='runTest'):
        TestCase.__init__(self, methodName)
        ET.__init__(self, "localhost")
        self.sensor_map = {s.id_: s.unit for s in self.sensors()}
        self._mock_responses = {}

    def mock_response(self, command: ProtocolCommand, filename: str):
        self._mock_responses[command] = filename

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        filename = self._mock_responses.get(command)
        if filename is not None:
            with open(root_dir + '/sample/et/' + filename, 'r') as f:
                response = bytes.fromhex(f.read())
                if not command.validator(response):
                    raise RequestFailedException
                return response
        else:
            self.request = command.request
            return bytes.fromhex("010203040506070809")

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensor_map.get(sensor))

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()


class GW10K_ET_Test(EtMock):

    def __init__(self, methodName='runTest'):
        EtMock.__init__(self, methodName)
        self.mock_response(self._READ_RUNNING_DATA, 'GW10K-ET_running_data.hex')
        self.mock_response(self._READ_METER_DATA, 'GW10K-ET_meter_data.hex')
        self.mock_response(self._READ_BATTERY_INFO, 'GW10K-ET_battery_info.hex')

    def test_GW10K_ET_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(145, len(data))

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
        self.assertSensor('pv1_mode', 2, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('pv2_mode', 2, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels connected, producing power', '', data)
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
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Connected to grid', '', data)
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
        self.assertSensor('errors', '', '', data)
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
        self.assertSensor('battery_temperature', 35.0, 'C', data)
        self.assertSensor('battery_charge_limit', 25, 'A', data)
        self.assertSensor('battery_discharge_limit', 25, 'A', data)
        self.assertSensor("battery_error_l", 0, "", data),
        self.assertSensor('battery_soc', 68, '%', data)
        self.assertSensor('battery_soh', 99, '%', data)
        self.assertSensor("battery_modules", 5, "", data)
        self.assertSensor("battery_warning_l", 0, "", data)
        self.assertSensor("battery_protocol", 257, "", data)
        self.assertSensor("battery_error_h", 0, "", data)
        self.assertSensor("battery_error", "", "", data)
        self.assertSensor("battery_warning_h", 0, "", data)
        self.assertSensor("battery_warning", "", "", data)
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
        self.assertSensor('rssi', 35, '', data)
        self.assertSensor('manufacture_code', 10, '', data)
        self.assertSensor('meter_test_status', 0, '', data)
        self.assertSensor('meter_comm_status', 1, '', data)
        self.assertSensor('active_power1', -57, 'W', data)
        self.assertSensor('active_power2', -46, 'W', data)
        self.assertSensor('active_power3', -6, 'W', data)
        self.assertSensor('active_power_total', -110, 'W', data)
        self.assertSensor('reactive_power_total', 1336, 'W', data)
        self.assertSensor('meter_power_factor1', -1.45, '', data)
        self.assertSensor('meter_power_factor2', -1.24, '', data)
        self.assertSensor('meter_power_factor3', -0.14, '', data)
        self.assertSensor('meter_power_factor', -0.8, '', data)
        self.assertSensor('meter_freq', 50.05, 'Hz', data)
        self.assertSensor('meter_e_total_exp', 10.514, 'kWh', data)
        self.assertSensor('meter_e_total_imp', 3254.462, 'kWh', data)

    def test_GW10K_ET_read_setting(self):
        self.loop.run_until_complete(self.read_settings('work_mode'))
        self.assertEqual('f703b798000136c7', self.request.hex())

        self.loop.run_until_complete(self.read_settings('grid_export_limit'))
        self.assertEqual('f703b996000155ec', self.request.hex())

    def test_GW10K_ET_write_setting(self):
        self.loop.run_until_complete(self.write_settings('grid_export_limit', 100))
        self.assertEqual('f706b996006459c7', self.request.hex())

    def test_set_grid_export_limit(self):
        self.loop.run_until_complete(self.set_grid_export_limit(100))
        self.assertEqual('f706b996006459c7', self.request.hex())

    def test_set_work_mode(self):
        self.loop.run_until_complete(self.set_work_mode(1))
        self.assertEqual('f706b7980001fac7', self.request.hex())

    def test_set_ongrid_battery_dod(self):
        self.loop.run_until_complete(self.set_ongrid_battery_dod(80))
        self.assertEqual('f706b12c00147ba6', self.request.hex())


class GW6000_EH_Test(EtMock):

    def __init__(self, methodName='runTest'):
        EtMock.__init__(self, methodName)
        self.mock_response(self._READ_RUNNING_DATA, 'GW6000_EH_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW6000_EH_device_info.hex')

    def test_GW6000_EH_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW6000-EH', self.model_name)
        self.assertEqual('00000EHU00000000', self.serial_number)
        self.assertEqual(6000, self.rated_power)
        self.assertEqual('02041-16-S00', self.arm_version)

    def test_GW6000_EH_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(99, len(data))

        self.assertSensor('vpv1', 330.3, 'V', data)
        self.assertSensor('ipv1', 2.6, 'A', data)
        self.assertSensor('ppv1', 857, 'W', data)
        self.assertSensor('vpv2', 329.6, 'V', data)
        self.assertSensor('ipv2', 2.1, 'A', data)
        self.assertSensor('ppv2', 691, 'W', data)
        self.assertSensor('ppv', 1548, 'W', data)
        self.assertSensor('pv1_mode', 2, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('pv2_mode', 2, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('vgrid', 236.6, 'V', data)
        self.assertSensor('igrid', 6.6, 'A', data)
        self.assertSensor('fgrid', 49.97, 'Hz', data)
        self.assertSensor('pgrid', 1561, 'W', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Connected to grid', '', data)
        self.assertSensor('total_inverter_power', 1561, 'W', data)
        self.assertSensor('active_power', -163, 'W', data)
        self.assertSensor('grid_in_out', 2, '', data)
        self.assertSensor('grid_in_out_label', 'Importing', '', data)
        self.assertSensor('reactive_power', 2147418112, 'W', data)
        self.assertSensor('apparent_power', -1, 'W', data)
        self.assertSensor('backup_v1', 0.0, 'V', data)
        self.assertSensor('backup_i1', 0.0, 'A', data)
        self.assertSensor('backup_f1', 0.0, 'Hz', data)
        self.assertSensor('load_mode1', 0, '', data)
        self.assertSensor('backup_p1', 0, 'W', data)
        self.assertSensor('load_p1', 1724, 'W', data)
        self.assertSensor('load_ptotal', 4294837948, 'W', data)  # TODO fix 3f calculation
        self.assertSensor('backup_ptotal', 0, 'W', data)
        self.assertSensor('pload', 1725, 'W', data)
        self.assertSensor('ups_load', 0, '%', data)
        self.assertSensor('temperature_air', 60.4, 'C', data)
        self.assertSensor('temperature_module', 3276.7, 'C', data)
        self.assertSensor('temperature', 38.6, 'C', data)
        self.assertSensor('xx154', 256, '', data)
        self.assertSensor('bus_voltage', 380.6, 'V', data)
        self.assertSensor('nbus_voltage', -0.1, 'V', data)
        self.assertSensor('vbattery1', 0.0, 'V', data)
        self.assertSensor('ibattery1', 0.1, 'A', data)
        self.assertSensor('pbattery1', 0, 'W', data)
        self.assertSensor('battery_mode', 0, '', data)
        self.assertSensor('battery_mode_label', 'No battery', '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('safety_country', 3, '', data)
        self.assertSensor('safety_country_label', 'Spain', '', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('operation_mode', -1, '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('errors', '', '', data)
        self.assertSensor("e_total", 59.4, 'kWh', data)
        self.assertSensor("e_day", 22.0, 'kWh', data)
        self.assertSensor("e_total_exp", 58.6, 'kWh', data)
        self.assertSensor('h_total', 33, 'h', data)
        self.assertSensor("e_day_exp", 21.6, 'kWh', data)
        self.assertSensor("e_total_imp", 0.0, 'kWh', data)
        self.assertSensor("e_day_imp", 0.0, 'kWh', data)
        self.assertSensor("e_load_total", 70.1, 'kWh', data)
        self.assertSensor("e_load_day", 27.1, 'kWh', data)
        self.assertSensor("e_bat_charge_total", 0.0, 'kWh', data)
        self.assertSensor("e_bat_charge_day", 0.0, 'kWh', data)
        self.assertSensor("e_bat_discharge_total", 0.0, 'kWh', data)
        self.assertSensor("e_bat_discharge_day", 0.0, 'kWh', data)
        self.assertSensor('diagnose_result', 117983303, '', data)
        self.assertSensor('house_consumption', 1711, 'W', data)
