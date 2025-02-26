"""Grid-only inverter support - models DT/MS/D-NS/XS or GE's GEP(PSB/PSC)"""
from __future__ import annotations

import logging

from .const import *
from .exceptions import InverterError, RequestFailedException, RequestRejectedException
from .inverter import Inverter, OperationMode, SensorKind as Kind
from .modbus import ILLEGAL_DATA_ADDRESS
from .model import is_3_mppt, is_single_phase
from .protocol import ProtocolCommand
from .sensor import *

logger = logging.getLogger(__name__)


class DT(Inverter):
    """Class representing inverter of DT/MS/D-NS/XS or GE's GEP(PSB/PSC) families"""

    __all_sensors: tuple[Sensor, ...] = (
        Timestamp("timestamp", 30100, "Timestamp"),
        Voltage("vpv1", 30103, "PV1 Voltage", Kind.PV),
        Current("ipv1", 30104, "PV1 Current", Kind.PV),
        Calculated("ppv1",
                   lambda data: round(read_voltage(data, 30103) * read_current(data, 30104)),
                   "PV1 Power", "W", Kind.PV),
        Voltage("vpv2", 30105, "PV2 Voltage", Kind.PV),
        Current("ipv2", 30106, "PV2 Current", Kind.PV),
        Calculated("ppv2",
                   lambda data: round(read_voltage(data, 30105) * read_current(data, 30106)),
                   "PV2 Power", "W", Kind.PV),
        Voltage("vpv3", 30107, "PV3 Voltage", Kind.PV),
        Current("ipv3", 30108, "PV3 Current", Kind.PV),
        Calculated("ppv3",
                   lambda data: round(read_voltage(data, 30107) * read_current(data, 30108)),
                   "PV3 Power", "W", Kind.PV),
        # ppv1 + ppv2 + ppv3
        Calculated("ppv",
                   lambda data: (round(read_voltage(data, 30103) * read_current(data, 30104))) + (
                       round(read_voltage(data, 30105) * read_current(data, 30106))) + (
                                    round(read_voltage(data, 30107) * read_current(data, 30108))),
                   "PV Power", "W", Kind.PV),
        # Voltage("vpv4", 14, "PV4 Voltage", Kind.PV),
        # Current("ipv4", 16, "PV4 Current", Kind.PV),
        # Voltage("vpv5", 14, "PV5 Voltage", Kind.PV),
        # Current("ipv5", 16, "PV5 Current", Kind.PV),
        # Voltage("vpv6", 14, "PV6 Voltage", Kind.PV),
        # Current("ipv6", 16, "PV7 Current", Kind.PV),
        Voltage("vline1", 30115, "On-grid L1-L2 Voltage", Kind.AC),
        Voltage("vline2", 30116, "On-grid L2-L3 Voltage", Kind.AC),
        Voltage("vline3", 30117, "On-grid L3-L1 Voltage", Kind.AC),
        Voltage("vgrid1", 30118, "On-grid L1 Voltage", Kind.AC),
        Voltage("vgrid2", 30119, "On-grid L2 Voltage", Kind.AC),
        Voltage("vgrid3", 30120, "On-grid L3 Voltage", Kind.AC),
        Current("igrid1", 30121, "On-grid L1 Current", Kind.AC),
        Current("igrid2", 30122, "On-grid L2 Current", Kind.AC),
        Current("igrid3", 30123, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid1", 30124, "On-grid L1 Frequency", Kind.AC),
        Frequency("fgrid2", 30125, "On-grid L2 Frequency", Kind.AC),
        Frequency("fgrid3", 30126, "On-grid L3 Frequency", Kind.AC),
        Calculated("pgrid1",
                   lambda data: round(read_voltage(data, 30118) * read_current(data, 30121)),
                   "On-grid L1 Power", "W", Kind.AC),
        Calculated("pgrid2",
                   lambda data: round(read_voltage(data, 30119) * read_current(data, 30122)),
                   "On-grid L2 Power", "W", Kind.AC),
        Calculated("pgrid3",
                   lambda data: round(read_voltage(data, 30120) * read_current(data, 30123)),
                   "On-grid L3 Power", "W", Kind.AC),
        Power4("total_inverter_power", 30127, "Total Power", Kind.AC),
        Integer("work_mode", 30129, "Work Mode code"),
        Enum2("work_mode_label", 30129, WORK_MODES, "Work Mode"),
        Long("error_codes", 30130, "Error Codes"),
        Integer("warning_code", 30132, "Warning code"),
        Apparent4("apparent_power", 30133, "Apparent Power", Kind.AC),
        Reactive4("reactive_power", 30135, "Reactive Power", Kind.AC),
        # 30137 reserved
        PowerS("total_input_power", 30138, "Total Input Power", Kind.PV),
        Decimal("power_factor", 30139, 1000, "Power Factor", "", Kind.GRID),
        # 30140 inverter efficiency
        Temp("temperature", 30141, "Inverter Temperature", Kind.AC),
        Temp("temperature_heatsink", 30142, "Heatsink Temperature", Kind.AC),
        # Temp("temperature_module", 30143, "Module Temperature", Kind.AC),
        Energy("e_day", 30144, "Today's PV Generation", Kind.PV),
        Energy4("e_total", 30145, "Total PV Generation", Kind.PV),
        Long("h_total", 30147, "Hours Total", "h", Kind.PV),
        Integer("safety_country", 30149, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 30149, SAFETY_COUNTRIES, "Safety Country", Kind.AC),
        # 30150 reserved
        # 30151 reserved
        # 30152 reserved
        # 30153 reserved
        # 30154 reserved
        # 30155 reserved
        # 30156 reserved
        # 30157 reserved
        # 30158 reserved
        # 30159 reserved
        # 30160 reserved
        # 30161 reserved
        Integer("funbit", 30162, "FunctionBit", "", Kind.PV),
        Voltage("vbus", 30163, "Bus Voltage", Kind.PV),
        Voltage("vnbus", 30164, "NBus Voltage", Kind.PV),
        Long("derating_mode", 30165, "Derating Mode code"),
        EnumBitmap4("derating_mode_label", 30165, DERATING_MODE_CODES, "Derating Mode"),
        # 30167 reserved
        # 30168 reserved
        # 30169 reserved
        # 30170 reserved
        # 30171 reserved
        Integer("rssi", 30172, "RSSI"),
    )

    # Inverter's meter data
    # Modbus registers from offset 0x75f3 (30195)
    __all_sensors_meter: tuple[Sensor, ...] = (
        Power4S("meter_active_power", 30195, "Meter Active Power", Kind.GRID),
        Energy4W("meter_e_total_exp", 30197, "Meter Total Energy (export)", Kind.GRID),
        Energy4W("meter_e_total_imp", 30199, "Meter Total Energy (import)", Kind.GRID),
        Integer("meter_comm_status", 30209, "Meter Communication Status"),  # 1 OK, 0 NotOK
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: tuple[Sensor, ...] = (
        Timestamp("time", 40313, "Inverter time"),
        Integer("shadow_scan_pv1", 40326, "Shadow Scan Status PV1", "", Kind.PV),
        Integer("shadow_scan_pv2", 40352, "Shadow Scan Status PV2", "", Kind.PV),
        Integer("shadow_scan_pv3", 40362, "Shadow Scan Status PV3", "", Kind.PV),
        Integer("shadow_scan_pv1_time", 40347, "Shadow Scan PV1 Time", "", Kind.PV),
        Integer("shadow_scan_pv2_time", 40353, "Shadow Scan PV2 Time", "", Kind.PV),
        # Integer("shadow_scan_pv3_time", 40xxx, "Shadow Scan PV3 Time", "", Kind.PV),  #TBC
        Integer("grid_export", 40327, "Grid Export Limit Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 40328, "Grid Export Limit", "%", Kind.GRID),
        Integer("start", 40330, "Start / Power On", "", Kind.GRID),
        Integer("stop", 40331, "Stop / Power Off", "", Kind.GRID),
        Integer("restart", 40332, "Restart", "", Kind.GRID),
        Integer("grid_export_hw", 40345, "Grid Export Limit Enabled (HW)", "", Kind.GRID),
    )

    # Settings for single phase inverters
    __settings_single_phase: tuple[Sensor, ...] = (
        Long("grid_export_limit", 40328, "Grid Export Limit", "W", Kind.GRID),
    )

    # Settings for three phase inverters
    __settings_three_phase: tuple[Sensor, ...] = (
        Integer("grid_export_limit", 40336, "Grid Export Limit", "%", Kind.GRID),
    )

    def __init__(self, host: str, port: int, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr if comm_addr else 0x7f, timeout, retries)
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = self._read_command(0x7531, 0x0028)
        self._READ_METER_VERSION_INFO: ProtocolCommand = self._read_command(0x756f, 0x0014)
        self._READ_DEVICE_MODEL: ProtocolCommand = self._read_command(0x9CED, 0x0008)
        self._READ_RUNNING_DATA: ProtocolCommand = self._read_command(0x7594, 0x0049)
        self._READ_METER_DATA: ProtocolCommand = self._read_command(0x75f3, 0xF)
        self._sensors = self.__all_sensors
        self._sensors_meter = self.__all_sensors_meter
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}
        self._sensors_map: dict[str, Sensor] | None = None
        self._has_meter: bool = True

    @staticmethod
    def _single_phase_only(s: Sensor) -> bool:
        """Filter to exclude phase2/3 sensors on single phase inverters"""
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    @staticmethod
    def _pv1_pv2_only(s: Sensor) -> bool:
        """Filter to exclude sensors on < 3 PV inverters"""
        return not s.id_.endswith('pv3')

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response.response_data()

        # Modbus registers from 30001 - 30040
        self.serial_number = self._decode(response[6:22])  # 30004 - 30012
        self.dsp1_version = read_unsigned_int(response, 66)  # 30034
        self.dsp2_version = read_unsigned_int(response, 68)  # 30035
        self.arm_version = read_unsigned_int(response, 70)  # 30036
        self.dsp_svn_version = read_unsigned_int(response, 72)  # 35037
        self.arm_svn_version = read_unsigned_int(response, 74)  # 35038
        self.firmware = f"{self.dsp1_version}.{self.dsp2_version}.{self.arm_version:02x}"

        try:
            self.model_name = response[22:32].decode("ascii").rstrip()
        except:
            try:
                response = await self._read_from_socket(self._READ_DEVICE_MODEL)
                response = response.response_data()
                self.model_name = response[0:16].decode("ascii").rstrip('\x00').strip()
            except InverterError as e:
                logger.debug("No model name sent from the inverter.")

        if is_single_phase(self):
            self._sensors = tuple(filter(self._single_phase_only, self.__all_sensors))
            self._settings.update({s.id_: s for s in self.__settings_single_phase})
        else:
            self._settings.update({s.id_: s for s in self.__settings_three_phase})

        if is_3_mppt(self):
            pass
        else:
            self._sensors = tuple(filter(self._pv1_pv2_only, self._sensors))

        try:
            response = await self._read_from_socket(self._READ_METER_VERSION_INFO)
            response = response.response_data()
            self.meter_software_version = read_unsigned_int(response, 0)  # 30063
            self.meter_serial_number = self._decode(response[24:38])  # 30075 - 30082
        except InverterError as e:
            logger.debug("Could not read meter version info.")

    async def read_runtime_data(self) -> dict[str, Any]:
        response = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(response, self._sensors)

        if self._has_meter:
            try:
                response = await self._read_from_socket(self._READ_METER_DATA)
                data.update(self._map_response(response, self._sensors_meter))
            except (RequestRejectedException, RequestFailedException):
                logger.info("Meter values not supported, disabling further attempts.")
                self._has_meter = False

        return data

    async def read_sensor(self, sensor_id: str) -> Any:
        sensor: Sensor = self._get_sensor(sensor_id)
        if sensor:
            return await self._read_sensor(sensor)
        if sensor_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(sensor_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown sensor "{sensor_id}"')

    async def read_setting(self, setting_id: str) -> Any:
        setting = self._settings.get(setting_id)
        if setting:
            return await self._read_sensor(setting)
        if setting_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(setting_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown setting "{setting_id}"')

    async def _read_sensor(self, setting: Sensor) -> Any:
        try:
            count = (setting.size_ + (setting.size_ % 2)) // 2
            response = await self._read_from_socket(self._read_command(setting.offset, count))
            return setting.read_value(response)
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("Unsupported sensor/setting %s", setting.id_)
                self._settings.pop(setting.id_, None)
                raise ValueError(f'Unknown sensor/setting "{setting.id_}"')
            return None

    async def write_setting(self, setting_id: str, value: Any):
        setting = self._settings.get(setting_id)
        if setting:
            await self._write_setting(setting, value)
        else:
            if setting_id.startswith("modbus"):
                await self._read_from_socket(self._write_command(int(setting_id[7:]), int(value)))
            else:
                raise ValueError(f'Unknown setting "{setting_id}"')

    async def _write_setting(self, setting: Sensor, value: Any):
        if setting.size_ == 1:
            # modbus can address/store only 16 bit values, read the other 8 bytes
            response = await self._read_from_socket(self._read_command(setting.offset, 1))
            raw_value = setting.encode_value(value, response.response_data()[0:2])
        else:
            raw_value = setting.encode_value(value)
        if len(raw_value) <= 2:
            value = int.from_bytes(raw_value, byteorder="big", signed=True)
            await self._read_from_socket(self._write_command(setting.offset, value))
        else:
            await self._read_from_socket(self._write_multi_command(setting.offset, raw_value))

    async def read_settings_data(self) -> dict[str, Any]:
        data = {}
        for setting in self.settings():
            value = await self.read_setting(setting.id_)
            data[setting.id_] = value
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_export_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0:
            return await self.write_setting('grid_export_limit', export_limit)

    async def get_operation_modes(self, include_emulated: bool) -> tuple[OperationMode, ...]:
        return ()

    async def get_operation_mode(self) -> OperationMode:
        raise InverterError("Operation not supported.")

    async def set_operation_mode(self, operation_mode: OperationMode, eco_mode_power: int = 100,
                                 eco_mode_soc: int = 100) -> None:
        raise InverterError("Operation not supported.")

    async def get_ongrid_battery_dod(self) -> int:
        raise InverterError("Operation not supported, inverter has no batteries.")

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        raise InverterError("Operation not supported, inverter has no batteries.")

    def _get_sensor(self, sensor_id: str) -> Sensor | None:
        if self._sensors_map is None:
            self._sensors_map = {s.id_: s for s in self.sensors()}
        return self._sensors_map.get(sensor_id)

    def sensors(self) -> tuple[Sensor, ...]:
        result = self._sensors
        if self._has_meter:
            result = result + self._sensors_meter
        return result

    def settings(self) -> tuple[Sensor, ...]:
        return tuple(self._settings.values())
