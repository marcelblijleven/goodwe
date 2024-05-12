import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe import DISCOVERY_COMMAND
from goodwe.es import ES
from goodwe.exceptions import RequestFailedException
from goodwe.inverter import OperationMode
from goodwe.protocol import Aa55ReadCommand, ProtocolCommand, ProtocolResponse


class EsMock(TestCase, ES):

    def __init__(self, methodName='runTest'):
        TestCase.__init__(self, methodName)
        ES.__init__(self, "localhost", 8899)
        self.sensor_map = {s.id_: s.unit for s in self.sensors()}
        self._mock_responses = {}

    def mock_response(self, command: ProtocolCommand, filename: str):
        self._mock_responses[command] = filename

    async def _read_from_socket(self, command: ProtocolCommand) -> ProtocolResponse:
        """Mock UDP communication"""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        filename = self._mock_responses.get(command)
        if filename is not None:
            if filename.startswith('aa55'):
                return ProtocolResponse(bytes.fromhex(filename), command)
            with open(root_dir + '/sample/es/' + filename, 'r') as f:
                response = bytes.fromhex(f.read())
                if not command.validator(response):
                    raise RequestFailedException
                return ProtocolResponse(response, command)
        else:
            self.request = command.request
            return ProtocolResponse(bytes.fromhex("010203040506070809"), command)

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensor_map.get(sensor))
        self.sensor_map.pop(sensor)

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()


class GW5048D_ES_Test(EsMock):

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW5048D-ES_device_info.hex')
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5048D-ES_running_data.hex')
        self.mock_response(self._READ_DEVICE_SETTINGS_DATA, 'GW5048D-ES_settings_data.hex')
        self.mock_response(Aa55ReadCommand(1793, 1), 'aa557fc0019a08000000000000007f0360')
        self.mock_response(Aa55ReadCommand(1800, 1), 'aa557fc0019a02007f035a')

    def test_GW5048D_ES_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW5048D-ES', self.model_name)
        self.assertEqual('95048ESU227W0000', self.serial_number)
        self.assertEqual('2323G', self.firmware)
        self.assertEqual(23, self.dsp1_version)
        self.assertEqual(23, self.dsp2_version)
        self.assertEqual(16, self.arm_version)

    def test_GW5048D_ES_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(57, len(data))

        self.assertSensor('vpv1', 0.0, 'V', data)
        self.assertSensor('ipv1', 0.1, 'A', data)
        self.assertSensor('ppv1', 0, 'W', data)
        self.assertSensor('pv1_mode', 0, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('vpv2', 0.0, 'V', data)
        self.assertSensor('ipv2', 0.0, 'A', data)
        self.assertSensor('ppv2', 0, 'W', data)
        self.assertSensor('pv2_mode', 0, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('ppv', 0, 'W', data)
        self.assertSensor('vbattery1', 49.4, 'V', data)
        self.assertSensor('battery_temperature', 24.6, 'C', data)
        self.assertSensor('ibattery1', 9.5, 'A', data)
        self.assertSensor('pbattery1', 469, 'W', data)
        self.assertSensor('battery_charge_limit', 74, 'A', data)
        self.assertSensor('battery_discharge_limit', 74, 'A', data)
        self.assertSensor('battery_status', 80, '', data)
        self.assertSensor('battery_error', 0, '', data)
        self.assertSensor('battery_soc', 60, '%', data)
        self.assertSensor('battery_soh', 98, '%', data)
        self.assertSensor('battery_mode', 2, '', data)
        self.assertSensor('battery_mode_label', 'Discharge', '', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('meter_status', 1, '', data)
        self.assertSensor('vgrid', 228.3, 'V', data)
        self.assertSensor('igrid', 2.3, 'A', data)
        self.assertSensor('pgrid', 2, 'W', data)
        self.assertSensor('fgrid', 49.83, 'Hz', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Inverter On', '', data)
        self.assertSensor('vload', 228.3, 'V', data)
        self.assertSensor('iload', 2.6, 'A', data)
        self.assertSensor('pload', 156, 'W', data)
        self.assertSensor('fload', 49.83, 'Hz', data)
        self.assertSensor('load_mode', 1, '', data)
        self.assertSensor('load_mode_label', 'The inverter is connected to a load', '', data)
        self.assertSensor('work_mode', 2, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('temperature', 22.9, 'C', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 22963.2, 'kWh', data)
        self.assertSensor('h_total', 46332, 'h', data)
        self.assertSensor('e_day', 12.3, 'kWh', data)
        self.assertSensor('e_load_day', 13.7, 'kWh', data)
        self.assertSensor('e_load_total', 31348.0, 'kWh', data)
        self.assertSensor('total_power', 393, 'W', data)
        self.assertSensor('effective_work_mode', 1, '', data)
        self.assertSensor('effective_relay_control', 48, '', data)
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 535, 'W', data)
        self.assertSensor('plant_power', 691, 'W', data)
        self.assertSensor('meter_power_factor', 0.001, '', data)
        self.assertSensor('diagnose_result', 117440576, '', data)
        self.assertSensor('diagnose_result_label',
                          'Discharge Driver On, Export power limit set, PF value set, Real power limit set', '', data)
        # self.assertSensor('e_total_exp', 0, 'kWh', data)
        # self.assertSensor('e_total_imp', 0, 'kWh', data)
        # self.assertSensor('vgrid_uo', 0, 'V', data)
        # self.assertSensor('igrid_uo', 0, 'A', data)
        # self.assertSensor('vgrid_wo', 0, 'V', data)
        # self.assertSensor('igrid_wo', 0, 'A', data)
        # self.assertSensor('e_bat_charge_total', 0, 'kWh', data)
        # self.assertSensor('e_bat_discharge_total', 0, 'kWh', data)
        self.assertSensor('house_consumption', 467, 'W', data)

        self.assertFalse(self.sensor_map, f"Some sensors were not tested {self.sensor_map}")

    def test_get_operation_modes(self):
        self.assertEqual((OperationMode.GENERAL, OperationMode.OFF_GRID, OperationMode.BACKUP, OperationMode.ECO),
                         self.loop.run_until_complete(self.get_operation_modes(False)))
        self.assertEqual((OperationMode.GENERAL, OperationMode.OFF_GRID, OperationMode.BACKUP, OperationMode.ECO,
                          OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE),
                         self.loop.run_until_complete(self.get_operation_modes(True)))

    def test_settings(self):
        self.assertEqual(27, len(self.settings()))
        settings = {s.id_: s for s in self.settings()}
        self.assertEqual('EcoModeV1', type(settings.get("eco_mode_1")).__name__)

    def test_read_setting(self):
        data = self.loop.run_until_complete(self.read_setting('capacity'))
        self.assertEqual(74, data)
        data = self.loop.run_until_complete(self.read_setting('charge_v'))
        self.assertEqual(53.2, data)
        data = self.loop.run_until_complete(self.read_setting('charge_i'))
        self.assertEqual(98, data)
        data = self.loop.run_until_complete(self.read_setting('discharge_i'))
        self.assertEqual(46, data)
        data = self.loop.run_until_complete(self.read_setting('discharge_v'))
        self.assertEqual(44.5, data)
        data = self.loop.run_until_complete(self.read_setting('dod'))
        self.assertEqual(0, data)
        data = self.loop.run_until_complete(self.read_setting('grid_export_limit'))
        self.assertEqual(10000, data)

        data = self.loop.run_until_complete(self.read_setting('eco_mode_1'))
        self.assertEqual(
            "EcoModeV1(id_='eco_mode_1', offset=1793, name='Eco Mode Group 1', size_=8, unit='', kind=<SensorKind.BAT: 4>)",
            repr(data))
        data = self.loop.run_until_complete(self.read_setting('eco_mode_2_switch'))
        self.assertEqual(0, data)

    def test_write_setting(self):
        self.loop.run_until_complete(self.write_setting('eco_mode_2_switch', 0))


class GW5048_EM_Test(EsMock):

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5048-EM_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW5048-EM_device_info.hex')

    def test_GW5048_EM_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW5048-EM', self.model_name)
        self.assertEqual('00000EMU00AW0000', self.serial_number)
        self.assertEqual('1010B', self.firmware)
        self.assertEqual(10, self.dsp1_version)
        self.assertEqual(10, self.dsp2_version)
        self.assertEqual(11, self.arm_version)

        self.assertFalse(self._supports_eco_mode_v2())

    def test_GW5048_EM_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(57, len(data))

        self.assertSensor('vpv1', 130.8, 'V', data)
        self.assertSensor('ipv1', 0.3, 'A', data)
        self.assertSensor('ppv1', 39, 'W', data)
        self.assertSensor('pv1_mode', 0, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('vpv2', 340.9, 'V', data)
        self.assertSensor('ipv2', 0.3, 'A', data)
        self.assertSensor('ppv2', 102, 'W', data)
        self.assertSensor('pv2_mode', 2, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('ppv', 141, 'W', data)
        self.assertSensor('vbattery1', 52.9, 'V', data)
        self.assertSensor('battery_temperature', 29.0, 'C', data)
        self.assertSensor('ibattery1', 18.5, 'A', data)
        self.assertSensor('pbattery1', 979, 'W', data)
        self.assertSensor('battery_charge_limit', 99, 'A', data)
        self.assertSensor('battery_discharge_limit', 99, 'A', data)
        self.assertSensor('battery_status', 82, '', data)
        self.assertSensor('battery_error', 0, '', data)
        self.assertSensor('battery_soc', 97, '%', data)
        self.assertSensor('battery_soh', 0, '%', data)
        self.assertSensor('battery_mode', 2, '', data)
        self.assertSensor('battery_mode_label', 'Discharge', '', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('meter_status', 1, '', data)
        self.assertSensor('vgrid', 241.5, 'V', data)
        self.assertSensor('igrid', 4.3, 'A', data)
        self.assertSensor('pgrid', 2, 'W', data)
        self.assertSensor('fgrid', 49.87, 'Hz', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Inverter On', '', data)
        self.assertSensor('vload', 241.5, 'V', data)
        self.assertSensor('iload', 3.6, 'A', data)
        self.assertSensor('pload', 209, 'W', data)
        self.assertSensor('fload', 49.87, 'Hz', data)
        self.assertSensor('load_mode', 1, '', data)
        self.assertSensor('load_mode_label', 'The inverter is connected to a load', '', data)
        self.assertSensor('work_mode', 2, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('temperature', 34.8, 'C', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 957.8, 'kWh', data)
        self.assertSensor('h_total', 1343, 'h', data)
        self.assertSensor('e_day', 8.8, 'kWh', data)
        self.assertSensor('e_load_day', 17.6, 'kWh', data)
        self.assertSensor('e_load_total', 1803.7, 'kWh', data)
        self.assertSensor('total_power', 1032, 'W', data)
        self.assertSensor('effective_work_mode', 1, '', data)
        self.assertSensor('effective_relay_control', 48, '', data)
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 847, 'W', data)
        self.assertSensor('plant_power', 1056, 'W', data)
        self.assertSensor('meter_power_factor', 0.001, '', data)
        self.assertSensor('diagnose_result', 64, '', data)
        self.assertSensor('diagnose_result_label', 'Discharge Driver On', '', data)
        # self.assertSensor('e_total_exp', 512.9, 'kWh', data)
        # self.assertSensor('e_total_imp', 33653839.0, 'kWh', data)
        # self.assertSensor('vgrid_uo', 0, 'V', data)
        # self.assertSensor('igrid_uo', 0, 'A', data)
        # self.assertSensor('vgrid_wo', 0, 'V', data)
        # self.assertSensor('igrid_wo', 0, 'A', data)
        # self.assertSensor('e_bat_charge_total', 0, 'kWh', data)
        # self.assertSensor('e_bat_discharge_total', 0, 'kWh', data)
        self.assertSensor('house_consumption', 1118, 'W', data)

        self.assertFalse(self.sensor_map, f"Some sensors were not tested {self.sensor_map}")


class GW5048_EM_No_Batt_Test(EsMock):

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5048-EM-no-bat_running_data.hex')

    def test_GW5048_EM_no_batt_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(57, len(data))

        self.assertSensor('vpv1', 334.3, 'V', data)
        self.assertSensor('ipv1', 0.4, 'A', data)
        self.assertSensor('ppv1', 134, 'W', data)
        self.assertSensor('pv1_mode', 2, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('vpv2', 214.0, 'V', data)
        self.assertSensor('ipv2', 0.5, 'A', data)
        self.assertSensor('ppv2', 107, 'W', data)
        self.assertSensor('pv2_mode', 2, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels connected, producing power', '', data)
        self.assertSensor('ppv', 241, 'W', data)
        self.assertSensor('vbattery1', 0.0, 'V', data)
        self.assertSensor('battery_temperature', 0.0, 'C', data)
        self.assertSensor('ibattery1', 0.0, 'A', data)
        self.assertSensor('pbattery1', 0, 'W', data)
        self.assertSensor('battery_charge_limit', 0, 'A', data)
        self.assertSensor('battery_discharge_limit', 0, 'A', data)
        self.assertSensor('battery_status', 0, '', data)
        self.assertSensor('battery_error', 256, '', data)
        self.assertSensor('battery_soc', 0, '%', data)
        self.assertSensor('battery_soh', 0, '%', data)
        self.assertSensor('battery_mode', 0, '', data)
        self.assertSensor('battery_mode_label', 'No battery', '', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('meter_status', 1, '', data)
        self.assertSensor('vgrid', 240.8, 'V', data)
        self.assertSensor('igrid', 1.0, 'A', data)
        self.assertSensor('pgrid', 7, 'W', data)
        self.assertSensor('fgrid', 49.91, 'Hz', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Inverter On', '', data)
        self.assertSensor('vload', 0.0, 'V', data)
        self.assertSensor('iload', 0.0, 'A', data)
        self.assertSensor('pload', 249, 'W', data)
        self.assertSensor('fload', 0.0, 'Hz', data)
        self.assertSensor('load_mode', 0, '', data)
        self.assertSensor('load_mode_label', 'Inverter and the load is disconnected', '', data)
        self.assertSensor('work_mode', 2, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('temperature', 29.9, 'C', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 587.7, 'kWh', data)
        self.assertSensor('h_total', 299, 'h', data)
        self.assertSensor('e_day', 23.3, 'kWh', data)
        self.assertSensor('e_load_day', 20.5, 'kWh', data)
        self.assertSensor('e_load_total', 550.4, 'kWh', data)
        self.assertSensor('total_power', 212, 'W', data)
        self.assertSensor('effective_work_mode', 1, '', data)
        self.assertSensor('effective_relay_control', 32, '', data)
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 0, 'W', data)
        self.assertSensor('plant_power', 249, 'W', data)
        self.assertSensor('meter_power_factor', 0.001, '', data)
        self.assertSensor('diagnose_result', 18501, '', data)
        self.assertSensor('diagnose_result_label',
                          'Battery voltage low, Battery SOC in back, Discharge Driver On, Self-use load light, Battery Disconnected',
                          '', data)
        # self.assertSensor('e_total_exp', 512.9, 'kWh', data)
        # self.assertSensor('e_total_imp', 33653889.9, 'kWh', data)
        # self.assertSensor('vgrid_uo', 0, 'V', data)
        # self.assertSensor('igrid_uo', 0, 'A', data)
        # self.assertSensor('vgrid_wo', 0, 'V', data)
        # self.assertSensor('igrid_wo', 0, 'A', data)
        # self.assertSensor('e_bat_charge_total', 0, 'kWh', data)
        # self.assertSensor('e_bat_discharge_total', 0, 'kWh', data)
        self.assertSensor('house_consumption', 234, 'W', data)


class GW5000S_BP_Test(EsMock):

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5000S-BP_running_data.hex')

    def test_GW5000S_BP_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(57, len(data))

        self.assertSensor('vpv1', 374.9, 'V', data)
        self.assertSensor('ipv1', 2.2, 'A', data)
        self.assertSensor('ppv1', 825, 'W', data)
        self.assertSensor('pv1_mode', 0, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('vpv2', 0.0, 'V', data)
        self.assertSensor('ipv2', 0.2, 'A', data)
        self.assertSensor('ppv2', 0, 'W', data)
        self.assertSensor('pv2_mode', 0, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('ppv', 825, 'W', data)
        self.assertSensor('vbattery1', 50.3, 'V', data)
        self.assertSensor('battery_temperature', 15.0, 'C', data)
        self.assertSensor('ibattery1', -9.9, 'A', data)
        self.assertSensor('pbattery1', -498, 'W', data)
        self.assertSensor('battery_charge_limit', 99, 'A', data)
        self.assertSensor('battery_discharge_limit', 98, 'A', data)
        self.assertSensor('battery_status', 82, '', data)
        self.assertSensor('battery_error', 0, '', data)
        self.assertSensor('battery_soc', 72, '%', data)
        self.assertSensor('battery_soh', 0, '%', data)
        self.assertSensor('battery_mode', 3, '', data)
        self.assertSensor('battery_mode_label', 'Charge', '', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('meter_status', 1, '', data)
        self.assertSensor('vgrid', 240.1, 'V', data)
        self.assertSensor('igrid', 1.9, 'A', data)
        self.assertSensor('pgrid', 184, 'W', data)
        self.assertSensor('fgrid', 49.95, 'Hz', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Inverter On', '', data)
        self.assertSensor('vload', 240.1, 'V', data)
        self.assertSensor('iload', 0.1, 'A', data)
        self.assertSensor('pload', 1285, 'W', data)
        self.assertSensor('fload', 49.95, 'Hz', data)
        self.assertSensor('load_mode', 1, '', data)
        self.assertSensor('load_mode_label', 'The inverter is connected to a load', '', data)
        self.assertSensor('work_mode', 2, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('temperature', 19.5, 'C', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 49.4, 'kWh', data)
        self.assertSensor('h_total', 211, 'h', data)
        self.assertSensor('e_day', 0.2, 'kWh', data)
        self.assertSensor('e_load_day', 2.7, 'kWh', data)
        self.assertSensor('e_load_total', 194.9, 'kWh', data)
        self.assertSensor('total_power', -650, 'W', data)
        self.assertSensor('effective_work_mode', 1, '', data)
        self.assertSensor('effective_relay_control', 48, '', data)
        self.assertSensor('grid_in_out', 1, '', data)
        self.assertSensor('grid_in_out_label', 'Exporting', '', data)
        self.assertSensor('pback_up', 0, 'W', data)
        self.assertSensor('plant_power', 1285, 'W', data)
        self.assertSensor('meter_power_factor', 0.001, '', data)
        self.assertSensor('diagnose_result', 524320, '', data)
        self.assertSensor('diagnose_result_label', 'Charge time on, Self-use off', '', data)
        # self.assertSensor('e_total_exp', 538.4, 'kWh', data)
        # self.assertSensor('e_total_imp', 48713267.2, 'kWh', data)
        # self.assertSensor('vgrid_uo', 0, 'V', data)
        # self.assertSensor('igrid_uo', 0, 'A', data)
        # self.assertSensor('vgrid_wo', 0, 'V', data)
        # self.assertSensor('igrid_wo', 0, 'A', data)
        # self.assertSensor('e_bat_charge_total', 0, 'kWh', data)
        # self.assertSensor('e_bat_discharge_total', 0, 'kWh', data)
        self.assertSensor('house_consumption', 143, 'W', data)

    def test_get_grid_export_limit(self):
        self.loop.run_until_complete(self.get_grid_export_limit())
        self.assertEqual('aa55c07f0109000248', self.request.hex())

    def test_set_grid_export_limit(self):
        self.loop.run_until_complete(self.set_grid_export_limit(100))
        self.assertEqual('aa55c07f033502006402dc', self.request.hex())

    def test_get_operation_modes(self):
        self.assertEqual((OperationMode.GENERAL, OperationMode.OFF_GRID, OperationMode.BACKUP, OperationMode.ECO),
                         self.loop.run_until_complete(self.get_operation_modes(False)))
        self.assertEqual((OperationMode.GENERAL, OperationMode.OFF_GRID, OperationMode.BACKUP, OperationMode.ECO,
                          OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE),
                         self.loop.run_until_complete(self.get_operation_modes(True)))

    def test_get_operation_mode(self):
        self.loop.run_until_complete(self.get_operation_mode())
        self.assertEqual('aa55c07f0109000248', self.request.hex())

    #    def test_set_operation_mode(self):
    #        self.loop.run_until_complete(self.set_operation_mode(1))
    #        self.assertEqual('aa55c07f03590101029c', self.request.hex())

    def test_get_ongrid_battery_dod(self):
        self.loop.run_until_complete(self.get_ongrid_battery_dod())
        self.assertEqual('aa55c07f0109000248', self.request.hex())

    def test_set_ongrid_battery_dod(self):
        self.loop.run_until_complete(self.set_ongrid_battery_dod(80))
        self.assertEqual('aa55c07f023905056001001402f8', self.request.hex())

    def test_write_setting(self):
        self.loop.run_until_complete(self.write_setting('time', datetime(2022, 1, 4, 18, 30, 25)))
        self.assertEqual('aa55c07f030206160104121e1902ad', self.request.hex())


class GW5048_ESA_Test(EsMock):

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(DISCOVERY_COMMAND, 'GW5048-ESA_discovery.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW5048-ESA_device_info.hex')
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5048-ESA_running_data.hex')

    def test_GW5048_ESA_discovery(self):
        response = self.loop.run_until_complete(self._read_from_socket(DISCOVERY_COMMAND))
        raw_data = response.raw_data
        self.assertEqual(86, len(raw_data))
        self.assertEqual('GW5048-ESA', raw_data[12:22].decode("ascii").rstrip())
        self.assertEqual('95048ESA223W0000', raw_data[38:54].decode("ascii"))

    def test_GW5048_ESA_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW5048-ESA', self.model_name)
        self.assertEqual('95048ESA223W0000', self.serial_number)
        self.assertEqual('1717A', self.firmware)
        self.assertEqual(17, self.dsp1_version)
        self.assertEqual(17, self.dsp2_version)
        self.assertEqual(10, self.arm_version)

    def test_GW5048_ESA_runtime_data(self):
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(57, len(data))

        self.assertSensor('vpv1', 111.9, 'V', data)
        self.assertSensor('ipv1', 0.0, 'A', data)
        self.assertSensor('ppv1', 0, 'W', data)
        self.assertSensor('pv1_mode', 0, '', data)
        self.assertSensor('pv1_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('vpv2', 79.9, 'V', data)
        self.assertSensor('ipv2', 0.1, 'A', data)
        self.assertSensor('ppv2', 8, 'W', data)
        self.assertSensor('pv2_mode', 0, '', data)
        self.assertSensor('pv2_mode_label', 'PV panels not connected', '', data)
        self.assertSensor('ppv', 8, 'W', data)
        self.assertSensor('vbattery1', 53.6, 'V', data)
        self.assertSensor('battery_status', 80, '', data)
        self.assertSensor('battery_temperature', 25.0, 'C', data)
        self.assertSensor('ibattery1', 0.2, 'A', data)
        self.assertSensor('pbattery1', 11, 'W', data)
        self.assertSensor('battery_charge_limit', 0, 'A', data)
        self.assertSensor('battery_discharge_limit', 100, 'A', data)
        self.assertSensor('battery_error', 0, '', data)
        self.assertSensor('battery_soc', 100, '%', data)
        self.assertSensor('battery_soh', 100, '%', data)
        self.assertSensor('battery_mode', 2, '', data)
        self.assertSensor('battery_mode_label', 'Discharge', '', data)
        self.assertSensor('battery_warning', 0, '', data)
        self.assertSensor('meter_status', 1, '', data)
        self.assertSensor('vgrid', 231.2, 'V', data)
        self.assertSensor('igrid', 0.6, 'A', data)
        self.assertSensor('pgrid', 807, 'W', data)
        self.assertSensor('fgrid', 50.0, 'Hz', data)
        self.assertSensor('grid_mode', 1, '', data)
        self.assertSensor('grid_mode_label', 'Inverter On', '', data)
        self.assertSensor('vload', 231.2, 'V', data)
        self.assertSensor('iload', 0.3, 'A', data)
        self.assertSensor('pload', 916, 'W', data)
        self.assertSensor('fload', 50.0, 'Hz', data)
        self.assertSensor('load_mode', 1, '', data)
        self.assertSensor('load_mode_label', 'The inverter is connected to a load', '', data)
        self.assertSensor('work_mode', 2, '', data)
        self.assertSensor('work_mode_label', 'Normal (On-Grid)', '', data)
        self.assertSensor('temperature', 25.1, 'C', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('e_total', 0.2, 'kWh', data)
        self.assertSensor('h_total', 3, 'h', data)
        self.assertSensor('e_day', 0.2, 'kWh', data)
        self.assertSensor('e_load_day', 15.0, 'kWh', data)
        self.assertSensor('e_load_total', 15.0, 'kWh', data)
        self.assertSensor('total_power', -109, 'W', data)
        self.assertSensor('effective_work_mode', 1, '', data)
        self.assertSensor('effective_relay_control', 32, '', data)
        self.assertSensor('grid_in_out', 1, '', data)
        self.assertSensor('grid_in_out_label', 'Exporting', '', data)
        self.assertSensor('pback_up', 0, 'W', data)
        self.assertSensor('plant_power', 916, 'W', data)
        self.assertSensor('meter_power_factor', 0.001, '', data)
        self.assertSensor('diagnose_result', 16780352, '', data)
        self.assertSensor('diagnose_result_label',
                          'Discharge Driver On, Meter connection reversed, Self-use load light, Export power limit set',
                          '', data)
        self.assertSensor('house_consumption', -788, 'W', data)

        self.assertFalse(self.sensor_map, f"Some sensors were not tested {self.sensor_map}")


class GW6000_ES_20_Test(EsMock):
    """This is Gen 2 ES inverter, actually a modbus (ET) talking inverter, not ES"""

    def __init__(self, methodName='runTest'):
        EsMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW6000-ES-20_device_info.hex')

    def test_GW6000_ES_20_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('', self.model_name)
        self.assertEqual('56000ESN00AW0000', self.serial_number)
        self.assertEqual('0002000205', self.firmware)
        self.assertEqual(0, self.dsp1_version)
        self.assertEqual(2, self.dsp2_version)
        self.assertEqual(0, self.arm_version)
