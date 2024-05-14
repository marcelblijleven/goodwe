from __future__ import annotations

import logging
from typing import Tuple

from .exceptions import InverterError, RequestRejectedException
from .inverter import Inverter
from .inverter import OperationMode
from .inverter import SensorKind as Kind
from .modbus import ILLEGAL_DATA_ADDRESS
from .model import is_3_mppt, is_single_phase
from .protocol import ProtocolCommand
from .sensor import *

logger = logging.getLogger(__name__)


class DT(Inverter):
    """Class representing inverter of DT/MS/D-NS/XS or GE's GEP(PSB/PSC) families"""

    __all_sensors: Tuple[Sensor, ...] = (
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
        # 30127 reserved
        Power("ppv", 30128, "PV Power", Kind.PV),
        Integer("work_mode", 30129, "Work Mode code"),
        Enum2("work_mode_label", 30129, WORK_MODES, "Work Mode"),
        Long("error_codes", 30130, "Error Codes"),
        Integer("warning_code", 30132, "Warning code"),
        Apparent4("apparent_power", 30133, "Apparent Power", Kind.AC),
        Reactive4("reactive_power", 30135, "Reactive Power", Kind.AC),
        # 30137 reserved
        # 30138 reserved
        # 30139 reserved
        # 30140 reserved
        Temp("temperature", 30141, "Inverter Temperature", Kind.AC),
        # 30142 reserved
        # 30143 reserved
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
        Integer("funbit", 30162, "FunBit", "", Kind.PV),
        Voltage("vbus", 30163, "Bus Voltage", Kind.PV),
        Voltage("vnbus", 30164, "NBus Voltage", Kind.PV),
        Long("derating_mode", 30165, "Derating Mode code"),
        EnumBitmap4("derating_mode_label", 30165, DERATING_MODE_CODES, "Derating Mode"),
        # 30167 reserved
        # 30168 reserved
        # 30169 reserved
        # 30170 reserved
        # 30171 reserved
        # 30172 reserved
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: Tuple[Sensor, ...] = (
        Timestamp("time", 40313, "Inverter time"),

        Integer("shadow_scan", 40326, "Shadow Scan", "", Kind.PV),
        Integer("grid_export", 40327, "Grid Export Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 40328, "Grid Export Limit", "%", Kind.GRID),
    )

    # Settings for single phase inverters
    __settings_single_phase: Tuple[Sensor, ...] = (
        Long("grid_export_limit", 40328, "Grid Export Limit", "W", Kind.GRID),
    )

    # Settings for three phase inverters
    __settings_three_phase: Tuple[Sensor, ...] = (
        Integer("grid_export_limit", 40336, "Grid Export Limit", "%", Kind.GRID),
    )

    def __init__(self, host: str, port: int, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr if comm_addr else 0x7f, timeout, retries)
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = self._read_command(0x7531, 0x0028)
        self._READ_DEVICE_RUNNING_DATA: ProtocolCommand = self._read_command(0x7594, 0x0049)
        self._sensors = self.__all_sensors
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

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
        try:
            self.model_name = response[22:32].decode("ascii").rstrip()
        except:
            print("No model name sent from the inverter.")
        self.serial_number = self._decode(response[6:22])
        self.dsp1_version = read_unsigned_int(response, 66)
        self.dsp2_version = read_unsigned_int(response, 68)
        self.arm_version = read_unsigned_int(response, 70)
        self.firmware = "{}.{}.{:02x}".format(self.dsp1_version, self.dsp2_version, self.arm_version)

        if is_single_phase(self):
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._single_phase_only, self.__all_sensors))
            self._settings.update({s.id_: s for s in self.__settings_single_phase})
        else:
            self._settings.update({s.id_: s for s in self.__settings_three_phase})

        if is_3_mppt(self):
            # this is 3 PV strings inverter, keep all sensors
            pass
        else:
            # this is only 2 PV strings inverter
            self._sensors = tuple(filter(self._pv1_pv2_only, self._sensors))
        pass

    async def read_runtime_data(self) -> Dict[str, Any]:
        response = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(response, self._sensors)
        return data

    async def read_setting(self, setting_id: str) -> Any:
        setting = self._settings.get(setting_id)
        if setting:
            return await self._read_setting(setting)
        else:
            if setting_id.startswith("modbus"):
                response = await self._read_from_socket(self._read_command(int(setting_id[7:]), 1))
                return int.from_bytes(response.read(2), byteorder="big", signed=True)
            else:
                raise ValueError(f'Unknown setting "{setting_id}"')

    async def _read_setting(self, setting: Sensor) -> Any:
        try:
            count = (setting.size_ + (setting.size_ % 2)) // 2
            response = await self._read_from_socket(self._read_command(setting.offset, count))
            return setting.read_value(response)
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("Unsupported setting %s", setting.id_)
                self._settings.pop(setting.id_, None)
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

    async def read_settings_data(self) -> Dict[str, Any]:
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

    async def get_operation_modes(self, include_emulated: bool) -> Tuple[OperationMode, ...]:
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

    def sensors(self) -> Tuple[Sensor, ...]:
        return self._sensors

    def settings(self) -> Tuple[Sensor, ...]:
        return tuple(self._settings.values())
