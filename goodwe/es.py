from typing import Tuple

from .exceptions import InverterError
from .inverter import Inverter
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, Aa55ProtocolCommand
from .sensor import *


class ES(Inverter):
    """Class representing inverter of ES/EM/BP family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = Aa55ProtocolCommand("010200", "0182")
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = Aa55ProtocolCommand("010600", "0186")
    _READ_DEVICE_SETTINGS_DATA: ProtocolCommand = Aa55ProtocolCommand("010900", "0189")

    __sensors: Tuple[Sensor, ...] = (
        Voltage("vpv1", 0, "PV1 Voltage", Kind.PV),  # modbus 0x500
        Current("ipv1", 2, "PV1 Current", Kind.PV),
        Calculated("ppv1", 0, lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)), "PV1 Power", "W",
                   Kind.PV),
        Byte("pv1_mode", 4, "PV1 Mode code", "", Kind.PV),
        Enum("pv1_mode_label", 4, PV_MODES, "PV1 Mode", "", Kind.PV),
        Voltage("vpv2", 5, "PV2 Voltage", Kind.PV),
        Current("ipv2", 7, "PV2 Current", Kind.PV),
        Calculated("ppv2", 0, lambda data, _: round(read_voltage(data, 5) * read_current(data, 7)), "PV2 Power", "W",
                   Kind.PV),
        Byte("pv2_mode", 9, "PV2 Mode code", "", Kind.PV),
        Enum("pv2_mode_label", 9, PV_MODES, "PV2 Mode", "", Kind.PV),
        Calculated("ppv", 0,
                   lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)) + round(
                       read_voltage(data, 5) * read_current(data, 7)),
                   "PV Power", "W", Kind.PV),
        Voltage("vbattery1", 10, "Battery Voltage", Kind.BAT),  # modbus 0x506
        # Voltage("vbattery2", 12, "Battery Voltage 2", Kind.BAT),
        Integer("battery_status", 14, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 16, "Battery Temperature", Kind.BAT),
        Calculated("ibattery1", 18,
                   lambda data, _: abs(read_current(data, 18)) * (-1 if read_byte(data, 30) == 3 else 1),
                   "Battery Current", "A", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1", 0,
                   lambda data, _: abs(
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
        Enum("battery_mode_label", 30, BATTERY_MODES_ET, "Battery Mode", "", Kind.BAT),
        Integer("battery_warning", 31, "Battery Warning", "", Kind.BAT),
        Byte("meter_status", 33, "Meter Status code", "", Kind.AC),
        Voltage("vgrid", 34, "On-grid Voltage", Kind.AC),
        Current("igrid", 36, "On-grid Current", Kind.AC),
        Calculated("pgrid", 38,
                   lambda data, _: abs(read_power2(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1),
                   "On-grid Export Power", "W", Kind.AC),
        Frequency("fgrid", 40, "On-grid Frequency", Kind.AC),
        Byte("grid_mode", 42, "Work Mode code", "", Kind.GRID),
        Enum("grid_mode_label", 42, WORK_MODES_ES, "Work Mode", "", Kind.GRID),
        Voltage("vload", 43, "Back-up Voltage", Kind.UPS),  # modbus 0x51b
        Current("iload", 45, "Back-up Current", Kind.UPS),
        Power("pload", 47, "On-grid Power", Kind.AC),
        Frequency("fload", 49, "Back-up Frequency", Kind.UPS),
        Byte("load_mode", 51, "Load Mode code", "", Kind.AC),
        Enum("load_mode_label", 51, LOAD_MODES, "Load Mode", "", Kind.AC),
        Byte("work_mode", 52, "Energy Mode code", "", Kind.AC),
        Enum("work_mode_label", 52, ENERGY_MODES, "Energy Mode", "", Kind.AC),
        Temp("temperature", 53, "Inverter Temperature"),
        Long("error_codes", 55, "Error Codes"),
        Energy4("e_total", 59, "Total PV Generation", Kind.PV),
        Long("h_total", 63, "Hours Total", "h", Kind.PV),
        Energy("e_day", 67, "Today's PV Generation", Kind.PV),
        Energy("e_load_day", 69, "Today's Load", Kind.AC),
        Energy4("e_load_total", 71, "Total Load", Kind.AC),
        Power("total_power", 75, "Total Power", Kind.AC),  # modbus 0x52c
        Byte("effective_work_mode", 77, "Effective Work Mode code"),
        Integer("effective_relay_control", 78, "Effective Relay Control", "", None),
        Byte("grid_in_out", 80, "On-grid Mode code", "", Kind.GRID),
        Calculated("grid_in_out_label", 0,
                   lambda data, _: GRID_IN_OUT_MODES.get(read_byte(data, 80)),
                   "On-grid Mode", "", Kind.GRID),
        Power("pback_up", 81, "Back-up Power", Kind.UPS),
        # pload + pback_up
        Calculated("plant_power", 0,
                   lambda data, _: round(read_power2(data, 47) + read_power2(data, 81)),
                   "Plant Power", "W", Kind.AC),
        Decimal("meter_power_factor", 83, 1000, "Meter Power Factor", "", Kind.GRID),  # modbus 0x531
        Integer("xx85", 85, "Unknown sensor@85"),
        Integer("xx87", 87, "Unknown sensor@87"),
        Long("diagnose_result", 89, "Diag Status Code"),
        Calculated("diagnose_result_label", 0,
                   lambda data, _: decode_bitmap(read_bytes4(data, 89), DIAG_STATUS_CODES),
                   "Diag Status", ""),
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
        Calculated("house_consumption", 0,
                   lambda data, _:
                   round(read_voltage(data, 0) * read_current(data, 2)) +
                   round(read_voltage(data, 5) * read_current(data, 7)) +
                   (abs(round(read_voltage(data, 10) * read_current(data, 18))) *
                    (-1 if read_byte(data, 30) == 3 else 1)) -
                   (abs(read_power2(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1)),
                   "House Consumption", "W", Kind.AC),
    )

    __settings: Tuple[Sensor, ...] = (
        Integer("charge_power_limit", 4, "Charge Power Limit Value"),
        Integer("discharge_power_limit", 10, "Disharge Power Limit Value"),
        Byte("relay_control", 13, "Relay Control"),
        Byte("off-grid_charge", 15, "Off-grid Charge"),
        Byte("shadow_scan", 17, "Shadow Scan"),
        Integer("backflow_state", 18, "Backflow State"),
        Integer("capacity", 22, "Capacity"),
        Integer("charge_v", 24, "Charge Voltage", "V"),
        Integer("charge_i", 26, "Charge Current", "A", ),
        Integer("discharge_i", 28, "Discharge Current", "A", ),
        Integer("discharge_v", 30, "Discharge Voltage", "V"),
        Calculated("dod", 32, lambda data, _: 100 - read_bytes2(data, 32), "Depth of Discharge", "%"),
        Integer("battery_activated", 34, "Battery Activated"),
        Integer("bp_off_grid_charge", 36, "BP Off-grid Charge"),
        Integer("bp_pv_discharge", 38, "BP PV Discharge"),
        Integer("bp_bms_protocol", 40, "BP BMS Protocol"),
        Integer("power_factor", 42, "Power Factor"),
        Integer("grid_up_limit", 52, "Grid Up Limit"),
        Integer("soc_protect", 56, "SoC Protect"),
        Integer("work_mode", 66, "Work Mode"),
        Integer("grid_quality_check", 68, "Grid Quality Check"),

        # emulated settings
        EcoMode("eco_mode_1", 0, "Eco Mode Power Group 1"),
        EcoMode("eco_mode_2", 0, "Eco Mode Power Group 2"),
        EcoMode("eco_mode_3", 0, "Eco Mode Power Group 3"),
        EcoMode("eco_mode_4", 0, "Eco Mode Power Group 4"),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        self.arm_version = response[7:12].decode("ascii").rstrip()
        self.model_name = response[12:22].decode("ascii").rstrip()
        self.serial_number = response[38:54].decode("ascii")
        self.software_version = response[58:70].decode("ascii")
        if len(self.arm_version) >= 5:
            self.arm_sw_version = int(self.arm_version[4], base=16)

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[7:-2], self.__sensors, include_unknown_sensors)
        return data

    async def read_setting(self, setting_id: str) -> Any:
        if setting_id == 'time':
            # Fake setting, just to enable write_setting to work (if checked as pair in read as in HA)
            # There does not seem to be time setting/sensor evailable (or is not known)
            return datetime.now()
        elif setting_id == 'eco_mode_1':
            return None
        elif setting_id == 'eco_mode_2':
            return None
        elif setting_id == 'eco_mode_3':
            return None
        elif setting_id == 'eco_mode_4':
            return None
        else:
            all_settings = await self.read_settings_data()
            return all_settings.get(setting_id)

    async def write_setting(self, setting_id: str, value: Any):
        if setting_id == 'time':
            await self._read_from_socket(
                Aa55ProtocolCommand("030206" + Timestamp("time", 0, "").encode_value(value).hex(), "0382")
            )
        elif setting_id == 'eco_mode_1':
            await self._read_from_socket(Aa55ProtocolCommand("02390b070104" + value.hex(), "02b9"))
        elif setting_id == 'eco_mode_2':
            await self._read_from_socket(Aa55ProtocolCommand("02390b070504" + value.hex(), "02b9"))
        elif setting_id == 'eco_mode_3':
            await self._read_from_socket(Aa55ProtocolCommand("02390b070904" + value.hex(), "02b9"))
        elif setting_id == 'eco_mode_4':
            await self._read_from_socket(Aa55ProtocolCommand("02390b070d04" + value.hex(), "02b9"))
        else:
            raise InverterError("Operation not supported")

    async def read_settings_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_SETTINGS_DATA)
        data = self._map_response(raw_data[7:-2], self.__settings)
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_up_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0 or export_limit <= 10000:
            await self._read_from_socket(
                Aa55ProtocolCommand("033502" + "{:04x}".format(export_limit), "03b5")
            )

    async def get_operation_mode(self) -> int:
        return await self.read_setting('work_mode')

    async def set_operation_mode(self, operation_mode: int, eco_mode_power: int = 100) -> None:
        if operation_mode == 0:
            await self._set_general_mode()
            await self.reset_inverter()
        elif operation_mode == 1:
            await self._set_offgrid_mode()
            await self.reset_inverter()
        elif operation_mode == 2:
            await self._set_backup_mode()
            await self.reset_inverter()
        elif operation_mode == 3:
            await self._set_eco_mode(eco_mode_power)
            await self.reset_inverter()
        elif operation_mode in (4, 5):
            if operation_mode == 4:
                await self.write_setting('eco_mode_1', EcoMode("1", 0, "").encode_charge(eco_mode_power))
            else:
                await self.write_setting('eco_mode_1', EcoMode("1", 0, "").encode_discharge(eco_mode_power))
            await self.write_setting('eco_mode_2', EcoMode("2", 0, "").encode_off())
            await self.write_setting('eco_mode_3', EcoMode("3", 0, "").encode_off())
            await self.write_setting('eco_mode_4', EcoMode("4", 0, "").encode_off())
            await self._set_eco_mode(eco_mode_power)
            await self.reset_inverter()

    async def get_ongrid_battery_dod(self) -> int:
        return await self.read_setting('dod')

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        if 0 <= dod <= 89:
            await self._read_from_socket(
                Aa55ProtocolCommand("023905056001" + "{:04x}".format(100 - dod), "02b9")
            )

    async def reset_inverter(self) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("031d00", "039d"))

    def sensors(self) -> Tuple[Sensor, ...]:
        return self.__sensors

    def settings(self) -> Tuple[Sensor, ...]:
        return self.__settings

    async def _set_general_mode(self) -> None:
        if self.arm_sw_version >= 7:
            if self._supports_new_eco_mode():
                await self._clear_battery_mode_param()
            else:
                await self._set_limit_power_for_charge(0, 0, 0, 0, 0)
                await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
                await self._clear_battery_mode_param()
        else:
            await self._set_limit_power_for_charge(0, 0, 0, 0, 0)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(0)

    async def _set_offgrid_mode(self) -> None:
        if self.arm_sw_version >= 7:
            await self._clear_battery_mode_param()
        else:
            await self._set_limit_power_for_charge(0, 0, 23, 59, 0)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(1)
        await self._set_relay_control(3)
        await self._set_store_energy_mode(0)
        await self._set_work_mode(1)

    async def _set_backup_mode(self) -> None:
        if self.arm_sw_version >= 7:
            if self._supports_new_eco_mode():
                await self._clear_battery_mode_param()
            else:
                await self._clear_battery_mode_param()
                await self._set_limit_power_for_charge(0, 0, 23, 59, 10)
        else:
            await self._set_limit_power_for_charge(0, 0, 23, 59, 10)
            await self._set_limit_power_for_discharge(0, 0, 0, 0, 0)
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(2)

    async def _set_eco_mode(self, eco_mode_power: int) -> None:
        await self._set_limit_power_for_charge(0, 0, 23, 59, eco_mode_power)
        await self._set_limit_power_for_discharge(0, 0, 23, 59, eco_mode_power)
        await self._set_offgrid_work_mode(0)
        await self._set_work_mode(3)

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("0239050700010001", "02B9"))

    async def _set_limit_power_for_charge(self, startH: int, startM: int, stopH: int, stopM: int, limit: int) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("032c05" + "{:02x}".format(limit)
                                                         + "{:02x}".format(startH) + "{:02x}".format(startM)
                                                         + "{:02x}".format(stopH) + "{:02x}".format(stopM), "03AC"))

    async def _set_limit_power_for_discharge(self, startH: int, startM: int, stopH: int, stopM: int,
                                             limit: int) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("032d05" + "{:02x}".format(limit)
                                                         + "{:02x}".format(startH) + "{:02x}".format(startM)
                                                         + "{:02x}".format(stopH) + "{:02x}".format(stopM), "03AD"))

    async def _set_offgrid_work_mode(self, mode: int) -> None:
        await self._read_from_socket(Aa55ProtocolCommand("033601" + "{:02x}".format(mode), "03B6"))

    def _supports_new_eco_mode(self) -> bool:
        if self.arm_sw_version < 14:
            return False
        if len(self.arm_version) < 2:
            return False
        fw_version = int(self.arm_version[0:2])
        if "EMU" in self.serial_number:
            return fw_version >= 11
        if "ESU" in self.serial_number:
            return fw_version >= 22
        if "BPS" in self.serial_number:
            return fw_version >= 10
        return False

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
