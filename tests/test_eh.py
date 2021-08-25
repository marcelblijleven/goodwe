import asyncio
import os
from datetime import datetime
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

    def test_GW6000_EH_runtime_data(self):
        testee = GW6000_EH("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

        self.assertEqual(330.3, data['vpv1'])
        self.assertEqual(2.6, data['ipv1'])
        self.assertEqual(857, data['ppv1'])
        self.assertEqual(329.6, data['vpv2'])
        self.assertEqual(2.1, data['ipv2'])
        self.assertEqual(691, data['ppv2'])
        self.assertEqual(1548, data['ppv'])
        self.assertEqual(0, data['xx38'])
        self.assertEqual(514, data['xx40'])
        self.assertEqual(236.6, data['vgrid'])
        self.assertEqual(6.6, data['igrid'])
        self.assertEqual(49.97, data['fgrid'])
        self.assertEqual(1561, data['pgrid'])
        self.assertEqual(1, data['xx72'])
        self.assertEqual(1561, data['total_inverter_power'])
        self.assertEqual(-163, data['active_power'])
        self.assertEqual(2, data['grid_in_out'])
        self.assertEqual('Importing', data['grid_in_out_label'])
        self.assertEqual(32767, data['xx82'])
        self.assertEqual(-1, data['xx84'])
        self.assertEqual(-1, data['xx86'])
        self.assertEqual(0.0, data['backup_v1'])
        self.assertEqual(0.0, data['backup_i1'])
        self.assertEqual(0.0, data['backup_f1'])
        self.assertEqual(0, data['xx96'])
        self.assertEqual(0, data['backup_p1'])
        self.assertEqual(1724, data['load_p1'])
        self.assertEqual(1724, data['load_ptotal'])
        self.assertEqual(0, data['backup_ptotal'])
        self.assertEqual(1725, data['pload'])
        self.assertEqual(0, data['xx146'])
        self.assertEqual(60.4, data['temperature2'])
        self.assertEqual(32767, data['xx150'])
        self.assertEqual(38.6, data['temperature'])
        self.assertEqual(256, data['xx154'])
        self.assertEqual(3806, data['xx156'])
        self.assertEqual(-1, data['xx158'])
        self.assertEqual(0.0, data['vbattery1'])
        self.assertEqual(0.1, data['ibattery1'])
        self.assertEqual(0, data['pbattery1'])
        self.assertEqual(0, data['battery_mode'])
        self.assertEqual('No battery', data['battery_mode_label'])
        self.assertEqual(0, data['xx170'])
        self.assertEqual(3, data['safety_country'])
        self.assertEqual('Spain', data['safety_country_label'])
        self.assertEqual(1, data['work_mode'])
        self.assertEqual('Normal (On-Grid)', data['work_mode_label'])
        self.assertEqual(-1, data['xx176'])
        self.assertEqual(0, data['error_codes'])
        self.assertEqual(59.4, data['e_total'])
        self.assertEqual(22.0, data['e_day'])
        self.assertEqual(0, data['xx190'])
        self.assertEqual(58.6, data['s_total'])
        self.assertEqual(33, data['h_total'])
        self.assertEqual(216, data['xx198'])
        self.assertEqual(0.0, data['s_day'])
        self.assertEqual(117983303, data['diagnose_result'])
        self.assertEqual(1711, data['house_consumption'])
