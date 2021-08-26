import asyncio
import os
from unittest import TestCase

from goodwe.es import ES
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))


class GW5048_EM(ES):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == ES._READ_DEVICE_RUNNING_DATA:
            with open(root_dir + '/sample/es/GW5048-EM_running_data.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class GW5048_EM_No_Batt(ES):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == ES._READ_DEVICE_RUNNING_DATA:
            with open(root_dir + '/sample/es/GW5048-EM-no-bat_running_data.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class GW5048D_ES(ES):

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        if command == ES._READ_DEVICE_RUNNING_DATA:
            with open(root_dir + '/sample/es/GW5048D-ES_running_data.hex', 'r') as f:
                return bytes.fromhex(f.read())
        else:
            raise ValueError


class EsProtocolTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.sensors = {s.id_: s.unit for s in ES.sensors()}

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensors.get(sensor))

    def test_GW5048_EM_runtime_data(self):
        testee = GW5048_EM("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

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
        self.assertSensor('battery_status', 0, '', data)
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
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 847, 'W', data)
        self.assertSensor('plant_power', 1056, 'W', data)
        self.assertSensor('diagnose_result', 64, '', data)
        self.assertSensor('house_consumption', 1118, 'W', data)

    def test_GW5048_EM_no_batt_runtime_data(self):
        testee = GW5048_EM_No_Batt("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

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
        self.assertSensor('battery_status', 256, '', data)
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
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 0, 'W', data)
        self.assertSensor('plant_power', 249, 'W', data)
        self.assertSensor('diagnose_result', 18501, '', data)
        self.assertSensor('house_consumption', 234, 'W', data)

    def test_GW5048D_ES_runtime_data(self):
        testee = GW5048D_ES("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

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
        self.assertSensor('battery_status', 0, '', data)
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
        self.assertSensor('grid_in_out', 0, '', data)
        self.assertSensor('grid_in_out_label', 'Idle', '', data)
        self.assertSensor('pback_up', 535, 'W', data)
        self.assertSensor('plant_power', 691, 'W', data)
        self.assertSensor('diagnose_result', 117440576, '', data)
        self.assertSensor('house_consumption', 467, 'W', data)