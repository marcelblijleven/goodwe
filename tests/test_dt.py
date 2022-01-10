import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe.dt import DT
from goodwe.exceptions import RequestFailedException
from goodwe.protocol import ProtocolCommand


class DtMock(TestCase, DT):

    def __init__(self, methodName='runTest'):
        TestCase.__init__(self, methodName)
        DT.__init__(self, "localhost")
        self.sensor_map = {s.id_: s.unit for s in self.sensors()}
        self._mock_responses = {}

    def mock_response(self, command: ProtocolCommand, filename: str):
        self._mock_responses[command] = filename

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        """Mock UDP communication"""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        filename = self._mock_responses.get(command)
        if filename is not None:
            with open(root_dir + '/sample/dt/' + filename, 'r') as f:
                response = bytes.fromhex(f.read())
                if not command.validator(response):
                    raise RequestFailedException
                return response
        else:
            self.request = command.request
            return bytes.fromhex("aa557f00010203040506070809")

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensor_map.get(sensor))

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()


class GW6000_DT_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW6000-DT_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW8K-DT_device_info.hex')

    def test_GW6000_DT_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(67, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-08-31 12:03:02', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 320.8, 'V', data)
        self.assertSensor('ipv1', 3.1, 'A', data)
        self.assertSensor('ppv1', 994, 'W', data)
        self.assertSensor('vpv2', 324.1, 'V', data)
        self.assertSensor('ipv2', 3.2, 'A', data)
        self.assertSensor('ppv2', 1037, 'W', data)
        self.assertSensor('vline1', -0.1, 'V', data)
        self.assertSensor('vline2', -0.1, 'V', data)
        self.assertSensor('vline3', -0.1, 'V', data)
        self.assertSensor('vgrid1', 225.6, 'V', data)
        self.assertSensor('vgrid2', 229.7, 'V', data)
        self.assertSensor('vgrid3', 231.0, 'V', data)
        self.assertSensor('igrid1', 2.7, 'A', data)
        self.assertSensor('igrid2', 2.6, 'A', data)
        self.assertSensor('igrid3', 2.7, 'A', data)
        self.assertSensor('fgrid1', 49.98, 'Hz', data)
        self.assertSensor('fgrid2', 49.98, 'Hz', data)
        self.assertSensor('fgrid3', 49.98, 'Hz', data)
        self.assertSensor('pgrid1', 609, 'W', data)
        self.assertSensor('pgrid2', 597, 'W', data)
        self.assertSensor('pgrid3', 624, 'W', data)
        self.assertSensor('xx54', 0, '', data)
        self.assertSensor('ppv', 1835, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('xx66', -1, '', data)
        self.assertSensor('xx68', -1, '', data)
        self.assertSensor('xx70', -1, '', data)
        self.assertSensor('xx72', -1, '', data)
        self.assertSensor('xx74', -1, '', data)
        self.assertSensor('xx76', -1, '', data)
        self.assertSensor('xx78', 0, '', data)
        self.assertSensor('xx80', -1, '', data)
        self.assertSensor('temperature', 41.3, 'C', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('e_day', 6.0, 'kWh', data)
        self.assertSensor('e_total', 13350.2, 'kWh', data)
        self.assertSensor('h_total', 8451, 'h', data)
        self.assertSensor('safety_country', 20, '', data)
        self.assertSensor('safety_country_label', 'Holland', '', data)
        self.assertSensor('xx100', 0, '', data)
        self.assertSensor('xx102', -1, '', data)
        self.assertSensor('xx104', 0, '', data)
        self.assertSensor('xx106', -1, '', data)
        self.assertSensor('xx108', 0, '', data)
        self.assertSensor('xx110', -1, '', data)
        self.assertSensor('xx112', 0, '', data)
        self.assertSensor('xx114', -1, '', data)
        self.assertSensor('xx116', -1, '', data)
        self.assertSensor('xx118', -1, '', data)
        self.assertSensor('xx120', -1, '', data)
        self.assertSensor('xx122', -1, '', data)
        self.assertSensor('funbit', 0, '', data)
        self.assertSensor('vbus', 601.2, 'V', data)
        self.assertSensor('vnbus', 305.4, 'V', data)
        self.assertSensor('xx130', -1, '', data)
        self.assertSensor('xx132', -1, '', data)
        self.assertSensor('xx134', 207, '', data)
        self.assertSensor('xx136', 355, '', data)
        self.assertSensor('xx138', 752, '', data)
        self.assertSensor('xx140', 0, '', data)
        self.assertSensor('xx142', 0, '', data)
        self.assertSensor('xx144', 100, '', data)

    def test_GW6000_DT_read_setting(self):
        self.loop.run_until_complete(self.read_setting('grid_export_limit'))
        self.assertEqual('7f039d900001a195', self.request.hex())

        self.loop.run_until_complete(self.read_setting('time'))
        self.assertEqual('7f039d790003f1a0', self.request.hex())

    def test_GW6000_DT_write_setting(self):
        self.loop.run_until_complete(self.write_setting('grid_export_limit', 100))
        self.assertEqual('7f069d900064adbe', self.request.hex())

        self.loop.run_until_complete(self.write_setting('time', datetime(2022, 1, 4, 18, 30, 25)))
        self.assertEqual('7f109d79000306160104121e190dfd', self.request.hex())

    def test_get_grid_export_limit(self):
        self.loop.run_until_complete(self.get_grid_export_limit())
        self.assertEqual('7f039d900001a195', self.request.hex())

    def test_set_grid_export_limit(self):
        self.loop.run_until_complete(self.set_grid_export_limit(100))
        self.assertEqual('7f069d900064adbe', self.request.hex())


class GW8K_DT_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW8K-DT_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW8K-DT_device_info.hex')

    def test_GW8K_DT_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW8K-DT', self.model_name)
        self.assertEqual('00000DTS00000000', self.serial_number)
        self.assertEqual('1010.1010.08', self.software_version)

    def test_GW8K_DT_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(67, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-08-24 16:43:27', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 275.5, 'V', data)
        self.assertSensor('ipv1', 0.6, 'A', data)
        self.assertSensor('ppv1', 165, 'W', data)
        self.assertSensor('vpv2', 510.8, 'V', data)
        self.assertSensor('ipv2', 0.8, 'A', data)
        self.assertSensor('ppv2', 409, 'W', data)
        self.assertSensor('vline1', 413.7, 'V', data)
        self.assertSensor('vline2', 413.0, 'V', data)
        self.assertSensor('vline3', 408.0, 'V', data)
        self.assertSensor('vgrid1', 237.2, 'V', data)
        self.assertSensor('vgrid2', 240.5, 'V', data)
        self.assertSensor('vgrid3', 235.2, 'V', data)
        self.assertSensor('igrid1', 1.0, 'A', data)
        self.assertSensor('igrid2', 1.0, 'A', data)
        self.assertSensor('igrid3', 1.0, 'A', data)
        self.assertSensor('fgrid1', 50.08, 'Hz', data)
        self.assertSensor('fgrid2', 50.04, 'Hz', data)
        self.assertSensor('fgrid3', 50.0, 'Hz', data)
        self.assertSensor('pgrid1', 237, 'W', data)
        self.assertSensor('pgrid2', 240, 'W', data)
        self.assertSensor('pgrid3', 235, 'W', data)
        self.assertSensor('xx54', 0, '', data)
        self.assertSensor('ppv', 643, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('xx66', 0, '', data)
        self.assertSensor('xx68', 0, '', data)
        self.assertSensor('xx70', 0, '', data)
        self.assertSensor('xx72', 0, '', data)
        self.assertSensor('xx74', 0, '', data)
        self.assertSensor('xx76', 0, '', data)
        self.assertSensor('xx78', 0, '', data)
        self.assertSensor('xx80', -1, '', data)
        self.assertSensor('temperature', 45.3, 'C', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('e_day', None, 'kWh', data)
        self.assertSensor('e_total', None, 'kWh', data)
        self.assertSensor('h_total', -1, 'h', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz Grid Default', '', data)
        self.assertSensor('xx100', 0, '', data)
        self.assertSensor('xx102', 0, '', data)
        self.assertSensor('xx104', 0, '', data)
        self.assertSensor('xx106', 0, '', data)
        self.assertSensor('xx108', -1, '', data)
        self.assertSensor('xx110', -1, '', data)
        self.assertSensor('xx112', -1, '', data)
        self.assertSensor('xx114', -1, '', data)
        self.assertSensor('xx116', -1, '', data)
        self.assertSensor('xx118', -1, '', data)
        self.assertSensor('xx120', -1, '', data)
        self.assertSensor('xx122', -1, '', data)
        self.assertSensor('funbit', 512, '', data)
        self.assertSensor('vbus', 624.2, 'V', data)
        self.assertSensor('vnbus', 316.8, 'V', data)
        self.assertSensor('xx130', 0, '', data)
        self.assertSensor('xx132', 0, '', data)
        self.assertSensor('xx134', 0, '', data)
        self.assertSensor('xx136', 728, '', data)
        self.assertSensor('xx138', 129, '', data)
        self.assertSensor('xx140', 0, '', data)
        self.assertSensor('xx142', -1, '', data)
        self.assertSensor('xx144', 84, '', data)


class GW5000D_NS_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5000D-NS_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'Mock_device_info.hex')

    def test_GW5000D_NS_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(57, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-09-06 06:56:01', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 224.4, 'V', data)
        self.assertSensor('ipv1', 0.0, 'A', data)
        self.assertSensor('ppv1', 0, 'W', data)
        self.assertSensor('vpv2', 291.8, 'V', data)
        self.assertSensor('ipv2', 0, 'A', data)
        self.assertSensor('ppv2', 0, 'W', data)
        self.assertSensor('vline1', -0.1, 'V', data)
        self.assertSensor('vgrid1', 240.5, 'V', data)
        self.assertSensor('igrid1', 0.0, 'A', data)
        self.assertSensor('fgrid1', 49.97, 'Hz', data)
        self.assertSensor('pgrid1', 0, 'W', data)
        self.assertSensor('xx54', 0, '', data)
        self.assertSensor('ppv', 0, 'W', data)
        self.assertSensor('work_mode', 0, '', data)
        self.assertSensor('work_mode_label', 'Wait Mode', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('xx66', -1, '', data)
        self.assertSensor('xx68', -1, '', data)
        self.assertSensor('xx70', -1, '', data)
        self.assertSensor('xx72', -1, '', data)
        self.assertSensor('xx74', -1, '', data)
        self.assertSensor('xx76', -1, '', data)
        self.assertSensor('xx78', -1, '', data)
        self.assertSensor('xx80', -1, '', data)
        self.assertSensor('temperature', 1.4, 'C', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('e_day', 0.0, 'kWh', data)
        self.assertSensor('e_total', 881.7, 'kWh', data)
        self.assertSensor('h_total', 955, 'h', data)
        self.assertSensor('safety_country', 73, '', data)
        self.assertSensor('safety_country_label', 'AU_Pwcore&CitiPW', '', data)
        self.assertSensor('xx100', 0, '', data)
        self.assertSensor('xx102', -1, '', data)
        self.assertSensor('xx104', 0, '', data)
        self.assertSensor('xx106', -1, '', data)
        self.assertSensor('xx108', 0, '', data)
        self.assertSensor('xx110', -1, '', data)
        self.assertSensor('xx112', 0, '', data)
        self.assertSensor('xx114', -1, '', data)
        self.assertSensor('xx116', -1, '', data)
        self.assertSensor('xx118', -1, '', data)
        self.assertSensor('xx120', -1, '', data)
        self.assertSensor('xx122', -1, '', data)
        self.assertSensor('funbit', 2400, '', data)
        self.assertSensor('vbus', 291.7, 'V', data)
        self.assertSensor('vnbus', -0.1, 'V', data)
        self.assertSensor('xx130', -1, '', data)
        self.assertSensor('xx132', -1, '', data)
        self.assertSensor('xx134', 400, '', data)
        self.assertSensor('xx136', -1, '', data)
        self.assertSensor('xx138', -1, '', data)
        self.assertSensor('xx140', -1, '', data)
        self.assertSensor('xx142', 404, '', data)
        self.assertSensor('xx144', 84, '', data)


class GW5000D_MS_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5000-MS_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW5000-MS_device_info.hex')

    def test_GW6000_MS_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW5000-MS', self.model_name)
        self.assertEqual('00000MSU00000000', self.serial_number)
        self.assertEqual('12.12.10', self.software_version)

    def test_GW5000D_MS_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data(True))
        self.assertEqual(60, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-10-15 09:03:12', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 319.6, 'V', data)
        self.assertSensor('ipv1', 0.2, 'A', data)
        self.assertSensor('ppv1', 64, 'W', data)
        self.assertSensor('vpv2', 148.0, 'V', data)
        self.assertSensor('ipv2', 0.3, 'A', data)
        self.assertSensor('ppv2', 44, 'W', data)
        self.assertSensor('vpv3', 143.2, 'V', data)
        self.assertSensor('ipv3', 0.4, 'A', data)
        self.assertSensor('ppv3', 57, 'W', data)
        self.assertSensor('vline1', -0.1, 'V', data)
        self.assertSensor('vgrid1', 240.1, 'V', data)
        self.assertSensor('igrid1', 0.9, 'A', data)
        self.assertSensor('fgrid1', 49.98, 'Hz', data)
        self.assertSensor('pgrid1', 216, 'W', data)
        self.assertSensor('xx54', 0, '', data)
        self.assertSensor('ppv', 295, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor('xx66', -1, '', data)
        self.assertSensor('xx68', -1, '', data)
        self.assertSensor('xx70', -1, '', data)
        self.assertSensor('xx72', -1, '', data)
        self.assertSensor('xx74', -1, '', data)
        self.assertSensor('xx76', -1, '', data)
        self.assertSensor('xx78', -1, '', data)
        self.assertSensor('xx80', -1, '', data)
        self.assertSensor('temperature', 10.7, 'C', data)
        self.assertSensor('xx84', -1, '', data)
        self.assertSensor('xx86', -1, '', data)
        self.assertSensor('e_day', 0.4, 'kWh', data)
        self.assertSensor('e_total', 6.8, 'kWh', data)
        self.assertSensor('h_total', 7, 'h', data)
        self.assertSensor('safety_country', 73, '', data)
        self.assertSensor('safety_country_label', 'AU_Pwcore&CitiPW', '', data)
        self.assertSensor('xx100', 0, '', data)
        self.assertSensor('xx102', -1, '', data)
        self.assertSensor('xx104', 0, '', data)
        self.assertSensor('xx106', -1, '', data)
        self.assertSensor('xx108', 0, '', data)
        self.assertSensor('xx110', -1, '', data)
        self.assertSensor('xx112', 0, '', data)
        self.assertSensor('xx114', -1, '', data)
        self.assertSensor('xx116', -1, '', data)
        self.assertSensor('xx118', -1, '', data)
        self.assertSensor('xx120', -1, '', data)
        self.assertSensor('xx122', -1, '', data)
        self.assertSensor('funbit', 2384, '', data)
        self.assertSensor('vbus', 393.9, 'V', data)
        self.assertSensor('vnbus', -0.1, 'V', data)
        self.assertSensor('xx130', -1, '', data)
        self.assertSensor('xx132', -1, '', data)
        self.assertSensor('xx134', 481, '', data)
        self.assertSensor('xx136', -1, '', data)
        self.assertSensor('xx138', -1, '', data)
        self.assertSensor('xx140', -1, '', data)
        self.assertSensor('xx142', 259, '', data)
        self.assertSensor('xx144', 42, '', data)
