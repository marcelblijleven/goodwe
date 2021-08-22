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

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def test_GW5048_EM_runtime_data(self):
        testee = GW5048_EM("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data())

        self.assertEqual(0.3, data['ipv1'])
        self.assertEqual(39, data['ppv1'])
        self.assertEqual(0, data['pv1_mode'])
        self.assertEqual('PV panels not connected', data['pv1_mode_label'])
        self.assertEqual(340.9, data['vpv2'])
        self.assertEqual(0.3, data['ipv2'])
        self.assertEqual(102, data['ppv2'])
        self.assertEqual(2, data['pv2_mode'])
        self.assertEqual('PV panels connected, producing power', data['pv2_mode_label'])
        self.assertEqual(141, data['ppv'])
        self.assertEqual(52.9, data['vbattery1'])
        self.assertEqual(29.0, data['battery_temperature'])
        self.assertEqual(18.5, data['ibattery1'])
        self.assertEqual(979, data['pbattery1'])
        self.assertEqual(99, data['battery_charge_limit'])
        self.assertEqual(99, data['battery_discharge_limit'])
        self.assertEqual(0, data['battery_status'])
        self.assertEqual(97, data['battery_soc'])
        self.assertEqual(0, data['battery_soh'])
        self.assertEqual(2, data['battery_mode'])
        self.assertEqual('Discharge', data['battery_mode_label'])
        self.assertEqual(0, data['battery_warning'])
        self.assertEqual(1, data['meter_status'])
        self.assertEqual(241.5, data['vgrid'])
        self.assertEqual(4.3, data['igrid'])
        self.assertEqual(2, data['pgrid'])
        self.assertEqual(49.87, data['fgrid'])
        self.assertEqual(1, data['grid_mode'])
        self.assertEqual('Inverter On', data['grid_mode_label'])
        self.assertEqual(241.5, data['vload'])
        self.assertEqual(3.6, data['iload'])
        self.assertEqual(209, data['pload'])
        self.assertEqual(49.87, data['fload'])
        self.assertEqual(1, data['load_mode'])
        self.assertEqual('The inverter is connected to a load', data['load_mode_label'])
        self.assertEqual(2, data['work_mode'])
        self.assertEqual('Normal (On-Grid)', data['work_mode_label'])
        self.assertEqual(34.8, data['temperature'])
        self.assertEqual(0, data['error_codes'])
        self.assertEqual(957.8, data['e_total'])
        self.assertEqual(1343, data['h_total'])
        self.assertEqual(8.8, data['e_day'])
        self.assertEqual(17.6, data['e_load_day'])
        self.assertEqual(1803.7, data['e_load_total'])
        self.assertEqual(1032, data['total_power'])
        self.assertEqual(1, data['effective_work_mode'])
        self.assertEqual(0, data['grid_in_out'])
        self.assertEqual('Idle', data['grid_in_out_label'])
        self.assertEqual(847, data['pback_up'])
        self.assertEqual(1056, data['plant_power'])
        self.assertEqual(64, data['diagnose_result'])
        self.assertEqual(1118, data['house_consumption'])

    def test_GW5048_EM_no_batt_runtime_data(self):
        testee = GW5048_EM_No_Batt("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data())

        self.assertEqual(334.3, data['vpv1'])
        self.assertEqual(0.4, data['ipv1'])
        self.assertEqual(134, data['ppv1'])
        self.assertEqual(2, data['pv1_mode'])
        self.assertEqual('PV panels connected, producing power', data['pv1_mode_label'])
        self.assertEqual(214.0, data['vpv2'])
        self.assertEqual(0.5, data['ipv2'])
        self.assertEqual(107, data['ppv2'])
        self.assertEqual(2, data['pv2_mode'])
        self.assertEqual('PV panels connected, producing power', data['pv2_mode_label'])
        self.assertEqual(241, data['ppv'])
        self.assertEqual(0.0, data['vbattery1'])
        self.assertEqual(0.0, data['battery_temperature'])
        self.assertEqual(0.0, data['ibattery1'])
        self.assertEqual(0, data['pbattery1'])
        self.assertEqual(0, data['battery_charge_limit'])
        self.assertEqual(0, data['battery_discharge_limit'])
        self.assertEqual(256, data['battery_status'])
        self.assertEqual(0, data['battery_soc'])
        self.assertEqual(0, data['battery_soh'])
        self.assertEqual(0, data['battery_mode'])
        self.assertEqual('No battery', data['battery_mode_label'])
        self.assertEqual(0, data['battery_warning'])
        self.assertEqual(1, data['meter_status'])
        self.assertEqual(240.8, data['vgrid'])
        self.assertEqual(1.0, data['igrid'])
        self.assertEqual(7, data['pgrid'])
        self.assertEqual(49.91, data['fgrid'])
        self.assertEqual(1, data['grid_mode'])
        self.assertEqual('Inverter On', data['grid_mode_label'])
        self.assertEqual(0.0, data['vload'])
        self.assertEqual(0.0, data['iload'])
        self.assertEqual(249, data['pload'])
        self.assertEqual(0.0, data['fload'])
        self.assertEqual(0, data['load_mode'])
        self.assertEqual('Inverter and the load is disconnected', data['load_mode_label'])
        self.assertEqual(2, data['work_mode'])
        self.assertEqual('Normal (On-Grid)', data['work_mode_label'])
        self.assertEqual(29.9, data['temperature'])
        self.assertEqual(0, data['error_codes'])
        self.assertEqual(587.7, data['e_total'])
        self.assertEqual(299, data['h_total'])
        self.assertEqual(23.3, data['e_day'])
        self.assertEqual(20.5, data['e_load_day'])
        self.assertEqual(550.4, data['e_load_total'])
        self.assertEqual(212, data['total_power'])
        self.assertEqual(1, data['effective_work_mode'])
        self.assertEqual(0, data['grid_in_out'])
        self.assertEqual('Idle', data['grid_in_out_label'])
        self.assertEqual(0, data['pback_up'])
        self.assertEqual(249, data['plant_power'])
        self.assertEqual(18501, data['diagnose_result'])
        self.assertEqual(234, data['house_consumption'])

    def test_GW5048D_ES_runtime_data(self):
        testee = GW5048D_ES("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data())

        self.assertEqual(0.0, data['vpv1'])
        self.assertEqual(0.1, data['ipv1'])
        self.assertEqual(0, data['ppv1'])
        self.assertEqual(0, data['pv1_mode'])
        self.assertEqual('PV panels not connected', data['pv1_mode_label'])
        self.assertEqual(0.0, data['vpv2'])
        self.assertEqual(0.0, data['ipv2'])
        self.assertEqual(0, data['ppv2'])
        self.assertEqual(0, data['pv2_mode'])
        self.assertEqual('PV panels not connected', data['pv2_mode_label'])
        self.assertEqual(0, data['ppv'])
        self.assertEqual(49.4, data['vbattery1'])
        self.assertEqual(24.6, data['battery_temperature'])
        self.assertEqual(9.5, data['ibattery1'])
        self.assertEqual(469, data['pbattery1'])
        self.assertEqual(74, data['battery_charge_limit'])
        self.assertEqual(74, data['battery_discharge_limit'])
        self.assertEqual(0, data['battery_status'])
        self.assertEqual(60, data['battery_soc'])
        self.assertEqual(98, data['battery_soh'])
        self.assertEqual(2, data['battery_mode'])
        self.assertEqual('Discharge', data['battery_mode_label'])
        self.assertEqual(0, data['battery_warning'])
        self.assertEqual(1, data['meter_status'])
        self.assertEqual(228.3, data['vgrid'])
        self.assertEqual(2.3, data['igrid'])
        self.assertEqual(2, data['pgrid'])
        self.assertEqual(49.83, data['fgrid'])
        self.assertEqual(1, data['grid_mode'])
        self.assertEqual('Inverter On', data['grid_mode_label'])
        self.assertEqual(228.3, data['vload'])
        self.assertEqual(2.6, data['iload'])
        self.assertEqual(156, data['pload'])
        self.assertEqual(49.83, data['fload'])
        self.assertEqual(1, data['load_mode'])
        self.assertEqual('The inverter is connected to a load', data['load_mode_label'])
        self.assertEqual(2, data['work_mode'])
        self.assertEqual('Normal (On-Grid)', data['work_mode_label'])
        self.assertEqual(22.9, data['temperature'])
        self.assertEqual(0, data['error_codes'])
        self.assertEqual(22963.2, data['e_total'])
        self.assertEqual(46332, data['h_total'])
        self.assertEqual(12.3, data['e_day'])
        self.assertEqual(13.7, data['e_load_day'])
        self.assertEqual(31348.0, data['e_load_total'])
        self.assertEqual(393, data['total_power'])
        self.assertEqual(1, data['effective_work_mode'])
        self.assertEqual(0, data['grid_in_out'])
        self.assertEqual('Idle', data['grid_in_out_label'])
        self.assertEqual(535, data['pback_up'])
        self.assertEqual(691, data['plant_power'])
        self.assertEqual(117440576, data['diagnose_result'])
        self.assertEqual(467, data['house_consumption'])
