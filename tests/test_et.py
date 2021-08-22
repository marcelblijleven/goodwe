import asyncio
import os
from unittest import TestCase

from goodwe.et import ET
from goodwe.protocol import ProtocolCommand

root_dir = os.path.dirname(os.path.abspath(__file__))

class Testee(ET):

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

    def test_runtime_data(self):

        et = Testee("localhost", 8899)

        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(et.read_runtime_data())
        loop.close()

        #for (sensor, _, _, unit, name, _) in ET.sensors():
        #   print(f"self.assertEqual({data[sensor]}, data['{sensor}'])")

        self.assertEqual(5.1, data['ipv1'])
        self.assertEqual(1695, data['ppv1'])
        self.assertEqual(332.6, data['vpv2'])
        self.assertEqual(5.3, data['ipv2'])
        self.assertEqual(1761, data['ppv2'])
        self.assertEqual(3456, data['ppv'])
        self.assertEqual(0, data['xx38'])
        self.assertEqual(514, data['xx40'])
        self.assertEqual(239.3, data['vgrid'])
        self.assertEqual(1.5, data['igrid'])
        self.assertEqual(49.99, data['fgrid'])
        self.assertEqual(336, data['pgrid'])
        self.assertEqual(241.5, data['vgrid2'])
        self.assertEqual(1.3, data['igrid2'])
        self.assertEqual(49.99, data['fgrid2'])
        self.assertEqual(287, data['pgrid2'])
        self.assertEqual(241.1, data['vgrid3'])
        self.assertEqual(1.1, data['igrid3'])
        self.assertEqual(49.99, data['fgrid3'])
        self.assertEqual(206, data['pgrid3'])
        self.assertEqual(1, data['xx72'])
        self.assertEqual(831, data['total_inverter_power'])
        self.assertEqual(-3, data['active_power'])
        self.assertEqual(0, data['grid_in_out'])
        self.assertEqual('Idle', data['grid_in_out_label'])
        self.assertEqual(0, data['xx82'])
        self.assertEqual(0, data['xx84'])
        self.assertEqual(0, data['xx86'])
        self.assertEqual(239.0, data['backup_v1'])
        self.assertEqual(0.6, data['backup_i1'])
        self.assertEqual(49.98, data['backup_f1'])
        self.assertEqual(1, data['xx96'])
        self.assertEqual(107, data['backup_p1'])
        self.assertEqual(241.3, data['backup_v2'])
        self.assertEqual(0.9, data['backup_i2'])
        self.assertEqual(50.0, data['backup_f2'])
        self.assertEqual(1, data['xx108'])
        self.assertEqual(189, data['backup_p2'])
        self.assertEqual(241.2, data['backup_v3'])
        self.assertEqual(0.2, data['backup_i3'])
        self.assertEqual(49.99, data['backup_f3'])
        self.assertEqual(1, data['xx120'])
        self.assertEqual(0, data['backup_p3'])
        self.assertEqual(224, data['load_p1'])
        self.assertEqual(80, data['load_p2'])
        self.assertEqual(233, data['load_p3'])
        self.assertEqual(537, data['load_ptotal'])
        self.assertEqual(312, data['backup_ptotal'])
        self.assertEqual(522, data['pload'])
        self.assertEqual(4, data['xx146'])
        self.assertEqual(51.0, data['temperature2'])
        self.assertEqual(0, data['xx150'])
        self.assertEqual(58.7, data['temperature'])
        self.assertEqual(0, data['xx154'])
        self.assertEqual(8036, data['xx156'])
        self.assertEqual(4018, data['xx158'])
        self.assertEqual(254.2, data['vbattery1'])
        self.assertEqual(-9.8, data['ibattery1'])
        self.assertEqual(-2491, data['pbattery1'])
        self.assertEqual(3, data['battery_mode'])
        self.assertEqual('Charge', data['battery_mode_label'])
        self.assertEqual(0, data['xx170'])
        self.assertEqual(32, data['safety_country'])
        self.assertEqual('50Hz Grid Default', data['safety_country_label'])
        self.assertEqual(1, data['work_mode'])
        self.assertEqual('Normal (On-Grid)', data['work_mode_label'])
        self.assertEqual(0, data['xx176'])
        self.assertEqual(0, data['error_codes'])
        self.assertEqual(6085.3, data['e_total'])
        self.assertEqual(12.5, data['e_day'])
        self.assertEqual(0, data['xx190'])
        self.assertEqual(-1835.0, data['s_total'])
        self.assertEqual(9246, data['h_total'])
        self.assertEqual(98, data['xx198'])
        self.assertEqual(0.0, data['s_day'])
        self.assertEqual(117442560, data['diagnose_result'])
        self.assertEqual(968, data['house_consumption'])
        self.assertEqual(255, data['battery_bms'])
        self.assertEqual(256, data['battery_index'])
        self.assertEqual(37.0, data['battery_temperature'])
        self.assertEqual(10, data['battery_charge_limit'])
        self.assertEqual(25, data['battery_discharge_limit'])
        self.assertEqual(0, data['battery_status'])
        self.assertEqual(91, data['battery_soc'])
        self.assertEqual(99, data['battery_soh'])
        self.assertEqual(0, data['battery_warning'])
        self.assertEqual(1, data['xxx0'])
        self.assertEqual(37, data['xxx2'])
        self.assertEqual(10, data['xxx4'])
        self.assertEqual(0, data['xxx6'])
        self.assertEqual(1, data['xxx8'])
        self.assertEqual(-8, data['xxx10'])
        self.assertEqual(18, data['xxx12'])
        self.assertEqual(-24, data['xxx14'])
        self.assertEqual(-13, data['xxx16'])
        self.assertEqual(991, data['xxx18'])
        self.assertEqual(17, data['xxx20'])
        self.assertEqual(89, data['xxx22'])
        self.assertEqual(-61, data['xxx24'])
        self.assertEqual(-4, data['xxx26'])
        self.assertEqual(4998, data['xxx28'])
        self.assertEqual(17953, data['xxx30'])
        self.assertEqual(26304, data['xxx32'])

