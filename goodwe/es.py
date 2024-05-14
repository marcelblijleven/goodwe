from __future__ import annotations

import logging
from typing import Tuple

from .exceptions import InverterError
from .inverter import Inverter
from .inverter import OperationMode
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, Aa55ProtocolCommand, Aa55ReadCommand, Aa55WriteCommand, Aa55WriteMultiCommand
from .sensor import *

logger = logging.getLogger(__name__)


class ES(Inverter):
    """Class representing inverter of ES/EM/BP family AKA platform 105"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = Aa55ProtocolCommand("010200", "0182")
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = Aa55ProtocolCommand("010600", "0186")
    _READ_DEVICE_SETTINGS_DATA: ProtocolCommand = Aa55ProtocolCommand("010900", "0189")

    __sensors: Tuple[Sensor, ...] = (
        Voltage("vpv1", 0, "PV1 Voltage", Kind.PV),  # modbus 0x500
        Current("ipv1", 2, "PV1 Current", Kind.PV),
        Calculated("ppv1",
                   lambda data: round(read_voltage(data, 0) * read_current(data, 2)),
                   "PV1 Power", "W", Kind.PV),
        Byte("pv1_mode", 4, "PV1 Mode code", "", Kind.PV),
        Enum("pv1_mode_label", 4, PV_MODES, "PV1 Mode", Kind.PV),
        Voltage("vpv2", 5, "PV2 Voltage", Kind.PV),
        Current("ipv2", 7, "PV2 Current", Kind.PV),
        Calculated("ppv2",
                   lambda data: round(read_voltage(data, 5) * read_current(data, 7)),
                   "PV2 Power", "W", Kind.PV),
        Byte("pv2_mode", 9, "PV2 Mode code", "", Kind.PV),
        Enum("pv2_mode_label", 9, PV_MODES, "PV2 Mode", Kind.PV),
        Calculated("ppv",
                   lambda data: round(read_voltage(data, 0) * read_current(data, 2)) + round(
                       read_voltage(data, 5) * read_current(data, 7)),
                   "PV Power", "W", Kind.PV),
        Voltage("vbattery1", 10, "Battery Voltage", Kind.BAT),  # modbus 0x506
        # Voltage("vbattery2", 12, "Battery Voltage 2", Kind.BAT),
        Integer("battery_status", 14, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 16, "Battery Temperature", Kind.BAT),
        Calculated("ibattery1",
                   lambda data: abs(read_current(data, 18)) * (-1 if read_byte(data, 30) == 3 else 1),
                   "Battery Current", "A", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1",
                   lambda data: abs(
                       round(read_voltage(data, 10) * read_current(data, 18))
                   ) * (-1 if read_byte(data, 30) == 3 else 1),
                   "Battery Power", "W", Kind.BAT),
        Integer("battery_charge_limit", 20, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 22, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_error", 24, "Battery Error Code", "", Kind.BAT),
        Byte("battery_soc", 26, "Battery State of Charge", "%", Kind.BAT),  # modbus 0x50E
        # Byte("cbattery2", 27, "Battery State of Charge 2", "%", Kind.BAT),
        # Byte("cbattery3", 28, "Battery State of Charge 3", "%", Kind.BAT),
        Byte("battery_soh", 29, "Battery State of Health", "%", Kind.BAT),
        Byte("battery_mode", 30, "Battery Mode code", "", Kind.BAT),
        Enum("battery_mode_label", 30, BATTERY_MODES, "Battery Mode", Kind.BAT),
        Integer("battery_warning", 31, "Battery Warning", "", Kind.BAT),
        Byte("meter_status", 33, "Meter Status code", "", Kind.AC),
        Voltage("vgrid", 34, "On-grid Voltage", Kind.AC),
        Current("igrid", 36, "On-grid Current", Kind.AC),
        Calculated("pgrid",
                   lambda data: abs(read_bytes2_signed(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1),
                   "On-grid Export Power", "W", Kind.AC),
        Frequency("fgrid", 40, "On-grid Frequency", Kind.AC),
        Byte("grid_mode", 42, "Work Mode code", "", Kind.GRID),
        Enum("grid_mode_label", 42, WORK_MODES_ES, "Work Mode", Kind.GRID),
        Voltage("vload", 43, "Back-up Voltage", Kind.UPS),  # modbus 0x51b
        Current("iload", 45, "Back-up Current", Kind.UPS),
        Power("pload", 47, "On-grid Power", Kind.AC),
        Frequency("fload", 49, "Back-up Frequency", Kind.UPS),
        Byte("load_mode", 51, "Load Mode code", "", Kind.AC),
        Enum("load_mode_label", 51, LOAD_MODES, "Load Mode", Kind.AC),
        Byte("work_mode", 52, "Energy Mode code", "", Kind.AC),
        Enum("work_mode_label", 52, ENERGY_MODES, "Energy Mode", Kind.AC),
        Temp("temperature", 53, "Inverter Temperature"),
        Long("error_codes", 55, "Error Codes"),
        Energy4("e_total", 59, "Total PV Generation", Kind.PV),
        Long("h_total", 63, "Hours Total", "h", Kind.PV),
        Energy("e_day", 67, "Today's PV Generation", Kind.PV),
        Energy("e_load_day", 69, "Today's Load", Kind.AC),
        Energy4("e_load_total", 71, "Total Load", Kind.AC),
        PowerS("total_power", 75, "Total Power", Kind.AC),  # modbus 0x52c
        Byte("effective_work_mode", 77, "Effective Work Mode code"),
        Integer("effective_relay_control", 78, "Effective Relay Control", "", None),
        Byte("grid_in_out", 80, "On-grid Mode code", "", Kind.GRID),
        Enum("grid_in_out_label", 80, GRID_IN_OUT_MODES, "On-grid Mode", Kind.GRID),
        Power("pback_up", 81, "Back-up Power", Kind.UPS),
        # pload + pback_up
        Calculated("plant_power",
                   lambda data: round(read_bytes2(data, 47, 0) + read_bytes2(data, 81, 0)),
                   "Plant Power", "W", Kind.AC),
        Decimal("meter_power_factor", 83, 1000, "Meter Power Factor", "", Kind.GRID),  # modbus 0x531
        # Integer("xx85", 85, "Unknown sensor@85"),
        # Integer("xx87", 87, "Unknown sensor@87"),
        Long("diagnose_result", 89, "Diag Status Code"),
        EnumBitmap4("diagnose_result_label", 89, DIAG_STATUS_CODES, "Diag Status"),
        # Energy4("e_total_exp", 93, "Total Energy (export)", Kind.GRID),
        # Energy4("e_total_imp", 97, "Total Energy (import)", Kind.GRID),
        # Voltage("vpv3", 101, "PV3 Voltage", Kind.PV),  # modbus 0x500
        # Current("ipv3", 103, "PV3 Current", Kind.PV),
        # Byte("pv3_mode", 104, "PV1 Mode", "", Kind.PV),
        # Voltage("vgrid_uo", 105, "On-grid Uo Voltage", Kind.AC),
        # Current("igrid_uo", 107, "On-grid Uo Current", Kind.AC),
        # Voltage("vgrid_wo", 109, "On-grid Wo Voltage", Kind.AC),
        # Current("igrid_wo", 111, "On-grid Wo Current", Kind.AC),
        # Energy4("e_bat_charge_total", 113, "Total Battery Charge", Kind.BAT),
        # Energy4("e_bat_discharge_total", 117, "Total Battery Discharge", Kind.BAT),

        # ppv1 + ppv2 + pbattery - pgrid
        Calculated("house_consumption",
                   lambda data:
                   round(read_voltage(data, 0) * read_current(data, 2)) +
                   round(read_voltage(data, 5) * read_current(data, 7)) +
                   (abs(round(read_voltage(data, 10) * read_current(data, 18))) *
                    (-1 if read_byte(data, 30) == 3 else 1)) -
                   (abs(read_bytes2_signed(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1)),
                   "House Consumption", "W", Kind.AC),
    )

    __all_settings: Tuple[Sensor, ...] = (
        Integer("backup_supply", 12, "Backup Supply"),
        Integer("off-grid_charge", 14, "Off-grid Charge"),
        Integer("shadow_scan", 16, "Shadow Scan", "", Kind.PV),
        Integer("grid_export", 18, "Export Limit Enabled", "", Kind.GRID),
        Integer("capacity", 22, "Capacity"),
        Decimal("charge_v", 24, 10, "Charge Voltage", "V"),
        Integer("charge_i", 26, "Charge Current", "A", ),
        Integer("discharge_i", 28, "Discharge Current", "A", ),
        Decimal("discharge_v", 30, 10, "Discharge Voltage", "V"),
        Calculated("dod", lambda data: 100 - read_bytes2(data, 32, 0), "Depth of Discharge", "%"),
        Integer("battery_activated", 34, "Battery Activated"),
        Integer("bp_off_grid_charge", 36, "BP Off-grid Charge"),
        Integer("bp_pv_discharge", 38, "BP PV Discharge"),
        Integer("bp_bms_protocol", 40, "BP BMS Protocol"),
        Integer("power_factor", 42, "Power Factor"),
        Integer("grid_export_limit", 52, "Grid Export Limit", "W", Kind.GRID),
        Integer("battery_soc_protection", 56, "Battery SoC Protection", "", Kind.BAT),
        Integer("work_mode", 66, "Work Mode"),
        Integer("grid_quality_check", 68, "Grid Quality Check"),

        EcoModeV1("eco_mode_1", 1793, "Eco Mode Group 1"),  # 0x701
        ByteH("eco_mode_1_switch", 1796, "Eco Mode Group 1 Switch", "", Kind.BAT),
        EcoModeV1("eco_mode_2", 1797, "Eco Mode Group 2"),
        ByteH("eco_mode_2_switch", 1800, "Eco Mode Group 2 Switch", "", Kind.BAT),
        EcoModeV1("eco_mode_3", 1801, "Eco Mode Group 3"),
        ByteH("eco_mode_3_switch", 1804, "Eco Mode Group 3 Switch", "", Kind.BAT),
        EcoModeV1("eco_mode_4", 1805, "Eco Mode Group 4"),
        ByteH("eco_mode_4_switch", 1808, "Eco Mode Group 4 Switch", "", Kind.BAT),
    )

    # Settings added in ARM firmware 14
    __settings_arm_fw_14: Tuple[Sensor, ...] = (
        EcoModeV2("eco_mode_1", 47547, "Eco Mode Group 1"),
        ByteH("eco_mode_1_switch", 47549, "Eco Mode Group 1 Switch"),
        EcoModeV2("eco_mode_2", 47553, "Eco Mode Group 2"),
        ByteH("eco_mode_2_switch", 47555, "Eco Mode Group 2 Switch"),
        EcoModeV2("eco_mode_3", 47559, "Eco Mode Group 3"),
        ByteH("eco_mode_3_switch", 47561, "Eco Mode Group 3 Switch"),
        EcoModeV2("eco_mode_4", 47565, "Eco Mode Group 4"),
        ByteH("eco_mode_4_switch", 47567, "Eco Mode Group 4 Switch"),
    )

    def __init__(self, host: str, port: int, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr if comm_addr else 0xf7, timeout, retries)
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

    def _supports_eco_mode_v2(self) -> bool:
        if self.arm_version < 14:
            return False
        if "EMU" in self.serial_number:
            return self.dsp1_version >= 11
        if "ESU" in self.serial_number:
            return self.dsp1_version >= 22
        if "BPS" in self.serial_number:
            return self.dsp1_version >= 10
        return False

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response.response_data()
        self.firmware = self._decode(response[0:5]).rstrip()
        self.model_name = self._decode(response[5:15]).rstrip()
        self.serial_number = self._decode(response[31:47])
        self.software_version = self._decode(response[51:63])
        try:
            if len(self.firmware) >= 2:
                self.dsp1_version = int(self.firmware[0:2])
            if len(self.firmware) >= 4:
                self.dsp2_version = int(self.firmware[2:4])
            if len(self.firmware) >= 5:
                self.arm_version = int(self.firmware[4], base=36)
        except ValueError:
            logger.exception("Error decoding firmware version %s.", self.firmware)

        if self._supports_eco_mode_v2():
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_14})

    async def read_runtime_data(self) -> Dict[str, Any]:
        response = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(response, self.__sensors)
        return data

    async def read_setting(self, setting_id: str) -> Any:
        if setting_id == 'time':
            # Fake setting, just to enable write_setting to work (if checked as pair in read as in HA)
            # There does not seem to be time setting/sensor available (or is not known)
            return datetime.now()
        elif setting_id in ('eco_mode_1', 'eco_mode_2', 'eco_mode_3', 'eco_mode_4'):
            setting: Sensor | None = self._settings.get(setting_id)
            if not setting:
                raise ValueError(f'Unknown setting "{setting_id}"')
            return await self._read_setting(setting)
        elif setting_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(setting_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        else:
            all_settings = await self.read_settings_data()
            return all_settings.get(setting_id)

    async def _read_setting(self, setting: Sensor) -> Any:
        count = (setting.size_ + (setting.size_ % 2)) // 2
        if self._is_modbus_setting(setting):
            response = await self._read_from_socket(self._read_command(setting.offset, count))
            return setting.read_value(response)
        else:
            response = await self._read_from_socket(Aa55ReadCommand(setting.offset, count))
            return setting.read_value(response)

    async def write_setting(self, setting_id: str, value: Any):
        if setting_id == 'time':
            await self._read_from_socket(
                Aa55ProtocolCommand("030206" + Timestamp("time", 0, "").encode_value(value).hex(), "0382")
            )
        elif setting_id.startswith("modbus"):
            await self._read_from_socket(self._write_command(int(setting_id[7:]), int(value)))
        else:
            setting: Sensor | None = self._settings.get(setting_id)
            if not setting:
                raise ValueError(f'Unknown setting "{setting_id}"')
            await self._write_setting(setting, value)

    async def _write_setting(self, setting: Sensor, value: Any):
        if setting.size_ == 1:
            # modbus can address/store only 16 bit values, read the other 8 bytes
            if self._is_modbus_setting(setting):
                response = await self._read_from_socket(self._read_command(setting.offset, 1))
            else:
                response = await self._read_from_socket(Aa55ReadCommand(setting.offset, 1))
            raw_value = setting.encode_value(value, response.response_data()[0:2])
        else:
            raw_value = setting.encode_value(value)
        if len(raw_value) <= 2:
            value = int.from_bytes(raw_value, byteorder="big", signed=True)
            if self._is_modbus_setting(setting):
                await self._read_from_socket(self._write_command(setting.offset, value))
            else:
                await self._read_from_socket(Aa55WriteCommand(setting.offset, value))
        else:
            if self._is_modbus_setting(setting):
                await self._read_from_socket(self._write_multi_command(setting.offset, raw_value))
            else:
                await self._read_from_socket(Aa55WriteMultiCommand(setting.offset, raw_value))

    async def read_settings_data(self) -> Dict[str, Any]:
        response = await self._read_from_socket(self._READ_DEVICE_SETTINGS_DATA)
        data = self._map_response(response, self.settings())
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_export_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0:
            await self._read_from_socket(
                Aa55ProtocolCommand("033502" + "{:04x}".format(export_limit), "03b5")
            )

    async def get_operation_modes(self, include_emulated: bool) -> Tuple[OperationMode, ...]:
        result = [e for e in OperationMode]
        result.remove(OperationMode.PEAK_SHAVING)
        result.remove(OperationMode.SELF_USE)
        if not include_emulated:
            result.remove(OperationMode.ECO_CHARGE)
            result.remove(OperationMode.ECO_DISCHARGE)
        return tuple(result)

    async def get_operation_mode(self) -> OperationMode | None:
        mode_id = await self.read_setting('work_mode')
        try:
            mode = OperationMode(mode_id)
        except ValueError:
            logger.debug("Unknown work_mode value %d", mode_id)
            return None
        if OperationMode.ECO != mode:
            return mode
        eco_mode = await self.read_setting('eco_mode_1')
        if eco_mode.is_eco_charge_mode():
            return OperationMode.ECO_CHARGE
        elif eco_mode.is_eco_discharge_mode():
            return OperationMode.ECO_DISCHARGE
        else:
            return OperationMode.ECO

    async def set_operation_mode(self, operation_mode: OperationMode, eco_mode_power: int = 100,
                                 eco_mode_soc: int = 100) -> None:
        if operation_mode == OperationMode.GENERAL:
            await self._set_general_mode()
        elif operation_mode == OperationMode.OFF_GRID:
            await self._set_offgrid_mode()
        elif operation_mode == OperationMode.BACKUP:
            await self._set_backup_mode()
        elif operation_mode == OperationMode.ECO:
            await self._set_eco_mode()
        elif operation_mode == OperationMode.PEAK_SHAVING:
            raise InverterError("Operation not supported.")
        elif operation_mode in (OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE):
            if eco_mode_power < 0 or eco_mode_power > 100:
                raise ValueError()
            if eco_mode_soc < 0 or eco_mode_soc > 100:
                raise ValueError()
            eco_mode: EcoMode | Sensor = self._settings.get('eco_mode_1')
            await self._read_setting(eco_mode)
            if operation_mode == OperationMode.ECO_CHARGE:
                await self.write_setting('eco_mode_1', eco_mode.encode_charge(eco_mode_power, eco_mode_soc))
            else:
                await self.write_setting('eco_mode_1', eco_mode.encode_discharge(eco_mode_power))
            await self.write_setting('eco_mode_2_switch', 0)
            await self.write_setting('eco_mode_3_switch', 0)
            await self.write_setting('eco_mode_4_switch', 0)
            await self._set_eco_mode()

    async def get_ongrid_battery_dod(self) -> int:
        return await self.read_setting('dod')

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        if 0 <= dod <= 100:
            await self._read_from_socket(Aa55WriteCommand(0x560, 100 - dod))

    async def _reset_inverter(self) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("031d00", "039d"))

    def sensors(self) -> Tuple[Sensor, ...]:
        return self.__sensors

    def settings(self) -> Tuple[Sensor, ...]:
        return tuple(self._settings.values())

    async def _set_general_mode(self) -> None:
        if self.arm_version >= 7:
            if self._supports_eco_mode_v2():
                await self._clear_battery_mode_param()
            else:
                await self._set_limit_power_for_charge(0, 0, 0, 0, 0)
                await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
                await self._clear_battery_mode_param()
        else:
            await self._set_limit_power_for_charge(0, 0, 0, 0, 0)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(OperationMode.GENERAL)

    async def _set_offgrid_mode(self) -> None:
        if self.arm_version >= 7:
            await self._clear_battery_mode_param()
        else:
            await self._set_limit_power_for_charge(0, 0, 23, 59, 0)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(1)
        await self._set_relay_control(3)
        await self._set_store_energy_mode(0)
        await self._set_work_mode(OperationMode.OFF_GRID)

    async def _set_backup_mode(self) -> None:
        if self.arm_version >= 7:
            if self._supports_eco_mode_v2():
                await self._clear_battery_mode_param()
            else:
                await self._clear_battery_mode_param()
                await self._set_limit_power_for_charge(0, 0, 23, 59, 10)
        else:
            await self._set_limit_power_for_charge(0, 0, 23, 59, 10)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(OperationMode.BACKUP)

    async def _set_eco_mode(self) -> None:
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(OperationMode.ECO)

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(Aa55WriteCommand(0x0700, 1))

    async def _set_limit_power_for_charge(self, startH: int, startM: int, stopH: int, stopM: int, limit: int) -> None:
        if limit < 0 or limit > 100:
            raise ValueError()
        await self._read_from_socket(Aa55ProtocolCommand("032c05"
                                                         + "{:02x}".format(startH) + "{:02x}".format(startM)
                                                         + "{:02x}".format(stopH) + "{:02x}".format(stopM)
                                                         + "{:02x}".format(limit), "03AC"))

    async def _set_limit_power_for_discharge(self, startH: int, startM: int, stopH: int, stopM: int,
                                             limit: int) -> None:
        if limit < 0 or limit > 100:
            raise ValueError()
        await self._read_from_socket(Aa55ProtocolCommand("032d05"
                                                         + "{:02x}".format(startH) + "{:02x}".format(startM)
                                                         + "{:02x}".format(stopH) + "{:02x}".format(stopM)
                                                         + "{:02x}".format(limit), "03AD"))

    async def _set_offgrid_work_mode(self, mode: int) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("033601" + "{:02x}".format(mode), "03B6"))

    async def _set_relay_control(self, mode: int) -> None:
        param = 0
        if mode == 2:
            param = 16
        elif mode == 3:
            param = 48
        await self._read_from_socket(Aa55ProtocolCommand("03270200" + "{:02x}".format(param), "03B7"))

    async def _set_store_energy_mode(self, mode: int) -> None:
        param = 0
        if mode == 0:
            param = 4
        elif mode == 1:
            param = 2
        elif mode == 2:
            param = 8
        elif mode == 3:
            param = 1
        await self._read_from_socket(Aa55ProtocolCommand("032601" + "{:02x}".format(param), "03B6"))

    async def _set_work_mode(self, mode: int) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("035901" + "{:02x}".format(mode), "03D9"))

    def _is_modbus_setting(self, sensor: Sensor) -> bool:
        return sensor.offset > 30000
