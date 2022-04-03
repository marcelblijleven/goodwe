from __future__ import annotations

from typing import Tuple

from .exceptions import InverterError
from .inverter import Inverter
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand, ModbusWriteMultiCommand
from .sensor import *


class DT(Inverter):
    """Class representing inverter of DT/MS/D-NS/XS families"""

    __all_sensors: Tuple[Sensor, ...] = (
        Timestamp("timestamp", 0, "Timestamp"),
        Voltage("vpv1", 6, "PV1 Voltage", Kind.PV),
        Current("ipv1", 8, "PV1 Current", Kind.PV),
        Calculated("ppv1", 0,
                   lambda data, _: round(read_voltage(data, 6) * read_current(data, 8)),
                   "PV1 Power", "W", Kind.PV),
        Voltage("vpv2", 10, "PV2 Voltage", Kind.PV),
        Current("ipv2", 12, "PV2 Current", Kind.PV),
        Calculated("ppv2", 0,
                   lambda data, _: round(read_voltage(data, 10) * read_current(data, 12)),
                   "PV2 Power", "W", Kind.PV),
        Voltage("vpv3", 14, "PV3 Voltage", Kind.PV),
        Current("ipv3", 16, "PV3 Current", Kind.PV),
        Calculated("ppv3", 0,
                   lambda data, _: round(read_voltage(data, 14) * read_current(data, 16)),
                   "PV3 Power", "W", Kind.PV),
        # Voltage("vpv4", 14, "PV4 Voltage", Kind.PV),
        # Current("ipv4", 16, "PV4 Current", Kind.PV),
        # Voltage("vpv5", 14, "PV5 Voltage", Kind.PV),
        # Current("ipv5", 16, "PV5 Current", Kind.PV),
        # Voltage("vpv6", 14, "PV6 Voltage", Kind.PV),
        # Current("ipv6", 16, "PV7 Current", Kind.PV),
        Voltage("vline1", 30, "On-grid L1-L2 Voltage", Kind.AC),
        Voltage("vline2", 32, "On-grid L2-L3 Voltage", Kind.AC),
        Voltage("vline3", 34, "On-grid L3-L1 Voltage", Kind.AC),
        Voltage("vgrid1", 36, "On-grid L1 Voltage", Kind.AC),
        Voltage("vgrid2", 38, "On-grid L2 Voltage", Kind.AC),
        Voltage("vgrid3", 40, "On-grid L3 Voltage", Kind.AC),
        Current("igrid1", 42, "On-grid L1 Current", Kind.AC),
        Current("igrid2", 44, "On-grid L2 Current", Kind.AC),
        Current("igrid3", 46, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid1", 48, "On-grid L1 Frequency", Kind.AC),
        Frequency("fgrid2", 50, "On-grid L2 Frequency", Kind.AC),
        Frequency("fgrid3", 52, "On-grid L3 Frequency", Kind.AC),
        Calculated("pgrid1", 0,
                   lambda data, _: round(read_voltage(data, 36) * read_current(data, 42)),
                   "On-grid L1 Power", "W", Kind.AC),
        Calculated("pgrid2", 0,
                   lambda data, _: round(read_voltage(data, 38) * read_current(data, 44)),
                   "On-grid L2 Power", "W", Kind.AC),
        Calculated("pgrid3", 0,
                   lambda data, _: round(read_voltage(data, 40) * read_current(data, 46)),
                   "On-grid L3 Power", "W", Kind.AC),
        Integer("xx54", 54, "Unknown sensor@54"),
        Power("ppv", 56, "PV Power", Kind.PV),
        Integer("work_mode", 58, "Work Mode code"),
        Enum2("work_mode_label", 58, WORK_MODES, "Work Mode"),
        Long("error_codes", 60, "Error Codes"),
        Integer("warning_code", 64, "Warning code"),
        Integer("xx66", 66, "Unknown sensor@66"),
        Integer("xx68", 68, "Unknown sensor@68"),
        Integer("xx70", 70, "Unknown sensor@70"),
        Integer("xx72", 72, "Unknown sensor@72"),
        Integer("xx74", 74, "Unknown sensor@74"),
        Integer("xx76", 76, "Unknown sensor@76"),
        Integer("xx78", 78, "Unknown sensor@78"),
        Integer("xx80", 80, "Unknown sensor@80"),
        Temp("temperature", 82, "Inverter Temperature", Kind.AC),
        Integer("xx84", 84, "Unknown sensor@84"),
        Integer("xx86", 86, "Unknown sensor@86"),
        Energy("e_day", 88, "Today's PV Generation", Kind.PV),
        Energy4("e_total", 90, "Total PV Generation", Kind.PV),
        Long("h_total", 94, "Hours Total", "h", Kind.PV),
        Integer("safety_country", 98, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 98, SAFETY_COUNTRIES_ET, "Safety Country", "", Kind.AC),
        Integer("xx100", 100, "Unknown sensor@100"),
        Integer("xx102", 102, "Unknown sensor@102"),
        Integer("xx104", 104, "Unknown sensor@104"),
        Integer("xx106", 106, "Unknown sensor@106"),
        Integer("xx108", 108, "Unknown sensor@108"),
        Integer("xx110", 110, "Unknown sensor@110"),
        Integer("xx112", 112, "Unknown sensor@112"),
        Integer("xx114", 114, "Unknown sensor@114"),
        Integer("xx116", 116, "Unknown sensor@116"),
        Integer("xx118", 118, "Unknown sensor@118"),
        Integer("xx120", 120, "Unknown sensor@120"),
        Integer("xx122", 122, "Unknown sensor@122"),
        Integer("funbit", 124, "FunBit", "", Kind.PV),
        Voltage("vbus", 126, "Bus Voltage", Kind.PV),
        Voltage("vnbus", 128, "NBus Voltage", Kind.PV),
        Integer("xx130", 130, "Unknown sensor@130"),
        Integer("xx132", 132, "Unknown sensor@132"),
        Integer("xx134", 134, "Unknown sensor@134"),
        Integer("xx136", 136, "Unknown sensor@136"),
        Integer("xx138", 138, "Unknown sensor@138"),
        Integer("xx140", 140, "Unknown sensor@140"),
        Integer("xx142", 142, "Unknown sensor@142"),
        Integer("xx144", 144, "Unknown sensor@144"),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: Tuple[Sensor, ...] = (
        Timestamp("time", 40313, "Inverter time"),

        Integer("shadow_scan", 40326, "Shadow Scan", "", Kind.PV),
        Integer("grid_export", 40327, "Grid Export Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 40336, "Grid Export Limit", "%", Kind.GRID),
    )

    def __init__(self, host: str, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, comm_addr, timeout, retries)
        if not self.comm_addr:
            # Set the default inverter address
            self.comm_addr = 0x7f
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x7531, 0x0028)
        self._READ_DEVICE_RUNNING_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x7594, 0x0049)
        self._sensors = self.__all_sensors
        self._settings = self.__all_settings

    @staticmethod
    def _is_not_3phase_sensor(s: Sensor) -> bool:
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_ and not s.id_.startswith('xx'))

    @staticmethod
    def _is_not_pv3_sensor(s: Sensor) -> bool:
        return not s.id_.endswith('pv3')

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.dsp1_sw_version = read_unsigned_int(response, 66)
        self.dsp2_sw_version = read_unsigned_int(response, 68)
        self.arm_sw_version = read_unsigned_int(response, 70)
        self.software_version = "{}.{}.{:02x}".format(self.dsp1_sw_version, self.dsp2_sw_version, self.arm_sw_version)

        if "DSN" in self.serial_number or "MSU" in self.serial_number:
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._is_not_3phase_sensor, self.__all_sensors))

        if "MSU" in self.serial_number:
            # this is 3 PV strings inverter, keep all sensors
            pass
        else:
            # this is only 2 PV strings inverter
            self._sensors = tuple(filter(self._is_not_pv3_sensor, self._sensors))
        pass

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self._sensors, include_unknown_sensors)
        return data

    async def read_setting(self, setting_id: str) -> Any:
        setting: Sensor | None = {s.id_: s for s in self.settings()}.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        count = (setting.size_ + (setting.size_ % 2)) // 2
        raw_data = await self._read_from_socket(ModbusReadCommand(self.comm_addr, setting.offset, count))
        with io.BytesIO(raw_data[5:-2]) as buffer:
            return setting.read_value(buffer)

    async def write_setting(self, setting_id: str, value: Any):
        setting: Sensor | None = {s.id_: s for s in self.settings()}.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        raw_value = setting.encode_value(value)
        if len(raw_value) <= 2:
            value = int.from_bytes(raw_value, byteorder="big", signed=True)
            await self._read_from_socket(ModbusWriteCommand(self.comm_addr, setting.offset, value))
        else:
            await self._read_from_socket(ModbusWriteMultiCommand(self.comm_addr, setting.offset, raw_value))

    async def read_settings_data(self) -> Dict[str, Any]:
        data = {}
        for setting in self.settings():
            value = await self.read_setting(setting.id_)
            data[setting.id_] = value
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_export_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0 or export_limit <= 100:
            return await self.write_setting('grid_export_limit', export_limit)

    async def get_operation_mode(self) -> int:
        raise InverterError("Operation not supported.")

    async def set_operation_mode(self, operation_mode: int, eco_mode_power: int = 100) -> None:
        raise InverterError("Operation not supported.")

    async def get_ongrid_battery_dod(self) -> int:
        raise InverterError("Operation not supported, inverter has no batteries.")

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        raise InverterError("Operation not supported, inverter has no batteries.")

    def sensors(self) -> Tuple[Sensor, ...]:
        return self._sensors

    def settings(self) -> Tuple[Sensor, ...]:
        return self._settings
