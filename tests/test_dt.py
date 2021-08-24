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

    def test_GW8K_DT_runtime_data(self):
        testee = GW8K_DT("localhost", 8899)
        data = self.loop.run_until_complete(testee.read_runtime_data(True))

        self.assertEqual(datetime.strptime('2021-08-24 16:43:27', '%Y-%m-%d %H:%M:%S'), data['timestamp'])
        self.assertEqual(275.5, data['vpv1'])
        self.assertEqual(0.6, data['ipv1'])
        self.assertEqual(165, data['ppv1'])
        self.assertEqual(510.8, data['vpv2'])
        self.assertEqual(0.8, data['ipv2'])
        self.assertEqual(409, data['ppv2'])
        self.assertEqual(-1, data['xx14'])
        self.assertEqual(-1, data['xx16'])
        self.assertEqual(-1, data['xx18'])
        self.assertEqual(-1, data['xx20'])
        self.assertEqual(-1, data['xx22'])
        self.assertEqual(-1, data['xx24'])
        self.assertEqual(-1, data['xx26'])
        self.assertEqual(-1, data['xx28'])
        self.assertEqual(413.7, data['vline1'])
        self.assertEqual(413.0, data['vline2'])
        self.assertEqual(408.0, data['vline3'])
        self.assertEqual(237.2, data['vgrid1'])
        self.assertEqual(240.5, data['vgrid2'])
        self.assertEqual(235.2, data['vgrid3'])
        self.assertEqual(1.0, data['igrid1'])
        self.assertEqual(1.0, data['igrid2'])
        self.assertEqual(1.0, data['igrid3'])
        self.assertEqual(50.08, data['fgrid1'])
        self.assertEqual(50.04, data['fgrid2'])
        self.assertEqual(50.0, data['fgrid3'])
        self.assertEqual(237, data['pgrid1'])
        self.assertEqual(240, data['pgrid2'])
        self.assertEqual(235, data['pgrid3'])
        self.assertEqual(0, data['xx54'])
        self.assertEqual(643, data['ppv'])
        self.assertEqual(1, data['work_mode'])
        self.assertEqual('Normal', data['work_mode_label'])
        self.assertEqual(0, data['xx60'])
        self.assertEqual(0, data['xx62'])
        self.assertEqual(0, data['xx64'])
        self.assertEqual(0, data['xx66'])
        self.assertEqual(0, data['xx68'])
        self.assertEqual(0, data['xx70'])
        self.assertEqual(0, data['xx72'])
        self.assertEqual(0, data['xx74'])
        self.assertEqual(0, data['xx76'])
        self.assertEqual(0, data['xx78'])
        self.assertEqual(-1, data['xx80'])
        self.assertEqual(45.3, data['temperature'])
        self.assertEqual(-1, data['xx84'])
        self.assertEqual(-1, data['xx86'])
        self.assertEqual(-0.1, data['e_day'])
        self.assertEqual(-1, data['xx90'])
        self.assertEqual(-0.1, data['e_total'])
        self.assertEqual(-1, data['xx94'])
        self.assertEqual(-1, data['h_total'])
        self.assertEqual(32, data['safety_country'])
        self.assertEqual('50Hz Grid Default', data['safety_country_label'])
        self.assertEqual(0, data['xx100'])
        self.assertEqual(0, data['xx102'])
        self.assertEqual(0, data['xx104'])
        self.assertEqual(0, data['xx106'])
        self.assertEqual(-1, data['xx108'])
        self.assertEqual(-1, data['xx110'])
        self.assertEqual(-1, data['xx112'])
        self.assertEqual(-1, data['xx114'])
        self.assertEqual(-1, data['xx116'])
        self.assertEqual(-1, data['xx118'])
        self.assertEqual(-1, data['xx120'])
        self.assertEqual(-1, data['xx122'])
        self.assertEqual(512, data['funbit'])
        self.assertEqual(624.2, data['vbus'])
        self.assertEqual(316.8, data['vnbus'])
        self.assertEqual(0, data['xx130'])
        self.assertEqual(0, data['xx132'])
        self.assertEqual(0, data['xx134'])
        self.assertEqual(728, data['xx136'])
        self.assertEqual(129, data['xx138'])
        self.assertEqual(0, data['xx140'])
        self.assertEqual(-1, data['xx142'])
        self.assertEqual(84, data['xx144'])
