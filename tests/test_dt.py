import asyncio
import os
from datetime import datetime
from unittest import TestCase

from goodwe.dt import DT
from goodwe.exceptions import RequestFailedException
from goodwe.protocol import ProtocolCommand, ProtocolResponse


class DtMock(TestCase, DT):

    def __init__(self, methodName='runTest'):
        TestCase.__init__(self, methodName)
        DT.__init__(self, "localhost", 8899)
        self.sensor_map = {s.id_: s.unit for s in self.sensors()}
        self._mock_responses = {}

    def mock_response(self, command: ProtocolCommand, filename: str):
        self._mock_responses[command] = filename

    async def _read_from_socket(self, command: ProtocolCommand) -> ProtocolResponse:
        """Mock UDP communication"""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        filename = self._mock_responses.get(command)
        if filename is not None:
            with open(root_dir + '/sample/dt/' + filename, 'r') as f:
                response = bytes.fromhex(f.read())
                if not command.validator(response):
                    raise RequestFailedException
                return ProtocolResponse(response, command)
        else:
            self.request = command.request
            return ProtocolResponse(bytes.fromhex("aa557f00010203040506070809"), command)

    def assertSensor(self, sensor, expected_value, expected_unit, data):
        self.assertEqual(expected_value, data.get(sensor))
        self.assertEqual(expected_unit, self.sensor_map.get(sensor))
        self.sensor_map.pop(sensor)

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()


class GW6000_DT_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW6000-DT_running_data.hex')

    def test_GW6000_DT_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(40, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-08-31 12:03:02', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 320.8, 'V', data)
        self.assertSensor('ipv1', 3.1, 'A', data)
        self.assertSensor('ppv1', 994, 'W', data)
        self.assertSensor('vpv2', 324.1, 'V', data)
        self.assertSensor('ipv2', 3.2, 'A', data)
        self.assertSensor('ppv2', 1037, 'W', data)
        self.assertSensor('vpv3', None, 'V', data)
        self.assertSensor('ipv3', None, 'A', data)
        self.assertSensor('ppv3', None, 'W', data)
        self.assertSensor('vline1', 0, 'V', data)
        self.assertSensor('vline2', 0, 'V', data)
        self.assertSensor('vline3', 0, 'V', data)
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
        self.assertSensor('ppv', 1835, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", -1, "VA", data),
        self.assertSensor("reactive_power", -1, "var", data),
        self.assertSensor('temperature', 41.3, 'C', data)
        self.assertSensor('e_day', 6.0, 'kWh', data)
        self.assertSensor('e_total', 13350.2, 'kWh', data)
        self.assertSensor('h_total', 8451, 'h', data)
        self.assertSensor('safety_country', 20, '', data)
        self.assertSensor('safety_country_label', 'NL-A', '', data)
        self.assertSensor('funbit', 0, '', data)
        self.assertSensor('vbus', 601.2, 'V', data)
        self.assertSensor('vnbus', 305.4, 'V', data)
        self.assertSensor('derating_mode', 0, '', data)
        self.assertSensor('derating_mode_label', '', '', data)

        self.assertFalse(self.sensor_map, f"Some sensors were not tested {self.sensor_map}")

    def test_GW6000_DT_setting(self):
        self.assertEqual(4, len(self.settings()))
        settings = {s.id_: s for s in self.settings()}
        self.assertEqual('Timestamp', type(settings.get("time")).__name__)
        self.assertEqual('Integer', type(settings.get("grid_export")).__name__)
        self.assertEqual('Integer', type(settings.get("grid_export_limit")).__name__)

    def test_GW6000_DT_read_setting(self):
        self.loop.run_until_complete(self.read_setting('shadow_scan'))
        self.assertEqual('7f039d8600014051', self.request.hex())

    def test_GW6000_DT_write_setting(self):
        self.loop.run_until_complete(self.write_setting('shadow_scan', 1))
        self.assertEqual('7f069d8600018c51', self.request.hex())


class GW8K_DT_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW8K-DT_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW8K-DT_device_info.hex')

    def test_GW8K_DT_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW8K-DT', self.model_name)
        self.assertEqual('00000DTS00000000', self.serial_number)
        self.assertEqual(1010, self.dsp1_version)
        self.assertEqual(1010, self.dsp2_version)
        self.assertEqual(8, self.arm_version)
        self.assertEqual('1010.1010.08', self.firmware)

    def test_GW8K_DT_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(40, len(data))

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
        self.assertSensor('ppv', 643, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", 0, "VA", data),
        self.assertSensor("reactive_power", 0, "var", data),
        self.assertSensor('temperature', 45.3, 'C', data)
        self.assertSensor('e_day', None, 'kWh', data)
        self.assertSensor('e_total', None, 'kWh', data)
        self.assertSensor('h_total', 0, 'h', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz 230Vac Default', '', data)
        self.assertSensor('funbit', 512, '', data)
        self.assertSensor('vbus', 624.2, 'V', data)
        self.assertSensor('vnbus', 316.8, 'V', data)
        self.assertSensor('derating_mode', 0, '', data)
        self.assertSensor('derating_mode_label', '', '', data)

    def test_get_grid_export_limit(self):
        self.loop.run_until_complete(self.read_device_info())
        self.loop.run_until_complete(self.get_grid_export_limit())
        self.assertEqual('7f039d900001a195', self.request.hex())

    def test_set_grid_export_limit(self):
        self.loop.run_until_complete(self.read_device_info())
        self.loop.run_until_complete(self.set_grid_export_limit(100))
        self.assertEqual('7f069d900064adbe', self.request.hex())


class GW5000D_NS_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5000D-NS_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'Mock_device_info.hex')

    def test_GW5000D_NS_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(30, len(data))

        self.assertSensor('timestamp', datetime.strptime('2021-09-06 06:56:01', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 224.4, 'V', data)
        self.assertSensor('ipv1', 0.0, 'A', data)
        self.assertSensor('ppv1', 0, 'W', data)
        self.assertSensor('vpv2', 291.8, 'V', data)
        self.assertSensor('ipv2', 0, 'A', data)
        self.assertSensor('ppv2', 0, 'W', data)
        self.assertSensor('vline1', 0, 'V', data)
        self.assertSensor('vgrid1', 240.5, 'V', data)
        self.assertSensor('igrid1', 0.0, 'A', data)
        self.assertSensor('fgrid1', 49.97, 'Hz', data)
        self.assertSensor('pgrid1', 0, 'W', data)
        self.assertSensor('ppv', 0, 'W', data)
        self.assertSensor('work_mode', 0, '', data)
        self.assertSensor('work_mode_label', 'Wait Mode', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", -1, "VA", data),
        self.assertSensor("reactive_power", -1, "var", data),
        self.assertSensor('temperature', 1.4, 'C', data)
        self.assertSensor('e_day', 0, 'kWh', data)
        self.assertSensor('e_total', 881.7, 'kWh', data)
        self.assertSensor('h_total', 955, 'h', data)
        self.assertSensor('safety_country', 73, '', data)
        self.assertSensor('safety_country_label', 'Australia Victoria', '', data)
        self.assertSensor('funbit', 2400, '', data)
        self.assertSensor('vbus', 291.7, 'V', data)
        self.assertSensor('vnbus', 0, 'V', data)
        self.assertSensor('derating_mode', 0, '', data)
        self.assertSensor('derating_mode_label', '', '', data)

    def test_get_grid_export_limit(self):
        self.loop.run_until_complete(self.read_device_info())
        self.loop.run_until_complete(self.get_grid_export_limit())
        self.assertEqual('7f039d8800026193', self.request.hex())

    def test_set_grid_export_limit(self):
        self.loop.run_until_complete(self.read_device_info())
        self.loop.run_until_complete(self.set_grid_export_limit(5000))
        self.assertEqual('7f109d88000204000013889d80', self.request.hex())


class GW5000_MS_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW5000-MS_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW5000-MS_device_info.hex')

    def test_GW6000_MS_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW5000-MS', self.model_name)
        self.assertEqual('00000MSU00000000', self.serial_number)
        self.assertEqual(12, self.dsp1_version)
        self.assertEqual(12, self.dsp2_version)
        self.assertEqual(16, self.arm_version)
        self.assertEqual('12.12.10', self.firmware)

    def test_GW5000_MS_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(33, len(data))

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
        self.assertSensor('vline1', 0, 'V', data)
        self.assertSensor('vgrid1', 240.1, 'V', data)
        self.assertSensor('igrid1', 0.9, 'A', data)
        self.assertSensor('fgrid1', 49.98, 'Hz', data)
        self.assertSensor('pgrid1', 216, 'W', data)
        self.assertSensor('ppv', 295, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", -1, "VA", data),
        self.assertSensor("reactive_power", -1, "var", data),
        self.assertSensor('temperature', 10.7, 'C', data)
        self.assertSensor('e_day', 0.4, 'kWh', data)
        self.assertSensor('e_total', 6.8, 'kWh', data)
        self.assertSensor('h_total', 7, 'h', data)
        self.assertSensor('safety_country', 73, '', data)
        self.assertSensor('safety_country_label', 'Australia Victoria', '', data)
        self.assertSensor('funbit', 2384, '', data)
        self.assertSensor('vbus', 393.9, 'V', data)
        self.assertSensor('vnbus', 0, 'V', data)
        self.assertSensor('derating_mode', 0, '', data)
        self.assertSensor('derating_mode_label', '', '', data)


class GW10K_MS_30_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW10K-MS-30_device_info.hex')
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW10K-MS-30_running_data.hex')

    def test_GW10K_MS_30_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual(None, self.model_name)
        self.assertEqual('5010KMSC000W0000', self.serial_number)
        self.assertEqual(0, self.dsp1_version)
        self.assertEqual(0, self.dsp2_version)
        self.assertEqual(2, self.arm_version)
        self.assertEqual('0.0.02', self.firmware)

    def test_GW10K_MS_30_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(33, len(data))

        self.assertSensor('timestamp', datetime.strptime('2024-01-09 22:08:20', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 0.0, 'V', data)
        self.assertSensor('ipv1', 0.0, 'A', data)
        self.assertSensor('ppv1', 0, 'W', data)
        self.assertSensor('vpv2', 0.0, 'V', data)
        self.assertSensor('ipv2', 0.0, 'A', data)
        self.assertSensor('ppv2', 0, 'W', data)
        self.assertSensor('vpv3', 0.0, 'V', data)
        self.assertSensor('ipv3', 0.0, 'A', data)
        self.assertSensor('ppv3', 0, 'W', data)
        self.assertSensor('vline1', 0.0, 'V', data)
        self.assertSensor('vgrid1', 236.2, 'V', data)
        self.assertSensor('igrid1', 0.0, 'A', data)
        self.assertSensor('fgrid1', 50.0, 'Hz', data)
        self.assertSensor('pgrid1', 0, 'W', data)
        self.assertSensor('ppv', 0, 'W', data)
        self.assertSensor('work_mode', 0, '', data)
        self.assertSensor('work_mode_label', 'Wait Mode', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", 0, "VA", data),
        self.assertSensor("reactive_power", 0, "var", data),
        self.assertSensor('temperature', 24.3, 'C', data)
        self.assertSensor('e_day', 71.8, 'kWh', data)
        self.assertSensor('e_total', 3433.4, 'kWh', data)
        self.assertSensor('h_total', 971, 'h', data)
        self.assertSensor('safety_country', 9, '', data)
        self.assertSensor('safety_country_label', 'Australia A', '', data)
        self.assertSensor('funbit', 0, '', data)
        self.assertSensor('vbus', 5.1, 'V', data)
        self.assertSensor('vnbus', 0.0, 'V', data)
        self.assertSensor('derating_mode', 0, '', data)
        self.assertSensor('derating_mode_label', '', '', data)


class GW20KAU_DT_Test(DtMock):

    def __init__(self, methodName='runTest'):
        DtMock.__init__(self, methodName)
        self.mock_response(self._READ_DEVICE_RUNNING_DATA, 'GW20KAU-DT_running_data.hex')
        self.mock_response(self._READ_DEVICE_VERSION_INFO, 'GW20KAU-DT_device_info.hex')

    def test_GW20KAU_DT_device_info(self):
        self.loop.run_until_complete(self.read_device_info())
        self.assertEqual('GW20KAU-DT', self.model_name)
        self.assertEqual('0000KDTA00000000', self.serial_number)
        self.assertEqual(15, self.dsp1_version)
        self.assertEqual(15, self.dsp2_version)
        self.assertEqual(16, self.arm_version)
        self.assertEqual('15.15.10', self.firmware)

    def test_GW20KAU_DT_runtime_data(self):
        self.loop.run_until_complete(self.read_device_info())
        data = self.loop.run_until_complete(self.read_runtime_data())
        self.assertEqual(40, len(data))

        self.assertSensor('timestamp', datetime.strptime('2022-10-21 19:23:42', '%Y-%m-%d %H:%M:%S'), '', data)
        self.assertSensor('vpv1', 390.5, 'V', data)
        self.assertSensor('ipv1', 6.8, 'A', data)
        self.assertSensor('ppv1', 2655, 'W', data)
        self.assertSensor('vpv2', 351.6, 'V', data)
        self.assertSensor('ipv2', 7.1, 'A', data)
        self.assertSensor('ppv2', 2496, 'W', data)
        self.assertSensor('vline1', 388.5, 'V', data)
        self.assertSensor('vline2', 391.7, 'V', data)
        self.assertSensor('vline3', 394.5, 'V', data)
        self.assertSensor('vgrid1', 226.1, 'V', data)
        self.assertSensor('vgrid2', 223.6, 'V', data)
        self.assertSensor('vgrid3', 228.3, 'V', data)
        self.assertSensor('igrid1', 7.2, 'A', data)
        self.assertSensor('igrid2', 7.4, 'A', data)
        self.assertSensor('igrid3', 7.1, 'A', data)
        self.assertSensor('fgrid1', 49.96, 'Hz', data)
        self.assertSensor('fgrid2', 49.96, 'Hz', data)
        self.assertSensor('fgrid3', 49.97, 'Hz', data)
        self.assertSensor('pgrid1', 1628, 'W', data)
        self.assertSensor('pgrid2', 1655, 'W', data)
        self.assertSensor('pgrid3', 1621, 'W', data)
        self.assertSensor('ppv', 4957, 'W', data)
        self.assertSensor('work_mode', 1, '', data)
        self.assertSensor('work_mode_label', 'Normal', '', data)
        self.assertSensor('error_codes', 0, '', data)
        self.assertSensor('warning_code', 0, '', data)
        self.assertSensor("apparent_power", 0, "VA", data),
        self.assertSensor("reactive_power", 205, "var", data),
        self.assertSensor('temperature', 36.4, 'C', data)
        self.assertSensor('e_day', 19.8, 'kWh', data)
        self.assertSensor('e_total', 4304.8, 'kWh', data)
        self.assertSensor('h_total', 1139, 'h', data)
        self.assertSensor('safety_country', 32, '', data)
        self.assertSensor('safety_country_label', '50Hz 230Vac Default', '', data)
        self.assertSensor('funbit', 0, '', data)
        self.assertSensor('vbus', 596.3, 'V', data)
        self.assertSensor('vnbus', 298.9, 'V', data)
        self.assertSensor('derating_mode', 4, '', data)
        self.assertSensor('derating_mode_label', 'Reactive power derating(PF/QU/FixQ)', '', data)
