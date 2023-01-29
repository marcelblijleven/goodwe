from __future__ import annotations

from typing import Tuple

from .exceptions import InverterError
from .inverter import Inverter
from .inverter import OperationMode
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand, ModbusWriteMultiCommand
from .sensor import *


class ET(Inverter):
    """Class representing inverter of ET/EH/BT/BH or GE's GEH families"""

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __all_sensors: Tuple[Sensor, ...] = (
        Timestamp("timestamp", 0, "Timestamp"),
        Voltage("vpv1", 6, "PV1 Voltage", Kind.PV),
        Current("ipv1", 8, "PV1 Current", Kind.PV),
        Power4("ppv1", 10, "PV1 Power", Kind.PV),
        Voltage("vpv2", 14, "PV2 Voltage", Kind.PV),
        Current("ipv2", 16, "PV2 Current", Kind.PV),
        Power4("ppv2", 18, "PV2 Power", Kind.PV),
        Voltage("vpv3", 22, "PV3 Voltage", Kind.PV),  # modbus35111
        Current("ipv3", 24, "PV3 Current", Kind.PV),
        Power4("ppv3", 26, "PV3 Power", Kind.PV),
        Voltage("vpv4", 30, "PV4 Voltage", Kind.PV),
        Current("ipv4", 32, "PV4 Current", Kind.PV),
        Power4("ppv4", 34, "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv",
                   lambda data:
                   read_bytes4(data, 10) +
                   read_bytes4(data, 18) +
                   read_bytes4(data, 26) +
                   read_bytes4(data, 34),
                   "PV Power", "W", Kind.PV),
        Byte("pv4_mode", 38, "PV4 Mode code", "", Kind.PV),
        Enum("pv4_mode_label", 38, PV_MODES, "PV4 Mode", Kind.PV),
        Byte("pv3_mode", 39, "PV3 Mode code", "", Kind.PV),
        Enum("pv3_mode_label", 39, PV_MODES, "PV3 Mode", Kind.PV),
        Byte("pv2_mode", 40, "PV2 Mode code", "", Kind.PV),
        Enum("pv2_mode_label", 40, PV_MODES, "PV2 Mode", Kind.PV),
        Byte("pv1_mode", 41, "PV1 Mode code", "", Kind.PV),
        Enum("pv1_mode_label", 41, PV_MODES, "PV1 Mode", Kind.PV),
        Voltage("vgrid", 42, "On-grid L1 Voltage", Kind.AC),  # modbus 35121
        Current("igrid", 44, "On-grid L1 Current", Kind.AC),
        Frequency("fgrid", 46, "On-grid L1 Frequency", Kind.AC),
        # 48 reserved
        Power("pgrid", 50, "On-grid L1 Power", Kind.AC),
        Voltage("vgrid2", 52, "On-grid L2 Voltage", Kind.AC),
        Current("igrid2", 54, "On-grid L2 Current", Kind.AC),
        Frequency("fgrid2", 56, "On-grid L2 Frequency", Kind.AC),
        # 58 reserved
        Power("pgrid2", 60, "On-grid L2 Power", Kind.AC),
        Voltage("vgrid3", 62, "On-grid L3 Voltage", Kind.AC),
        Current("igrid3", 64, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid3", 66, "On-grid L3 Frequency", Kind.AC),
        # 68 reserved
        Power("pgrid3", 70, "On-grid L3 Power", Kind.AC),
        Integer("grid_mode", 72, "Grid Mode code", "", Kind.PV),
        Enum2("grid_mode_label", 72, GRID_MODES, "Grid Mode", Kind.PV),
        # 74 reserved
        Power("total_inverter_power", 76, "Total Power", Kind.AC),
        # 78 reserved
        Power("active_power", 80, "Active Power", Kind.GRID),
        Calculated("grid_in_out",
                   lambda data: read_grid_mode(data, 80),
                   "On-grid Mode code", "", Kind.GRID),
        EnumCalculated("grid_in_out_label",
                       lambda data: read_grid_mode(data, 80), GRID_IN_OUT_MODES,
                       "On-grid Mode", Kind.GRID),
        # 82 reserved
        Reactive("reactive_power", 84, "Reactive Power", Kind.GRID),
        # 86 reserved
        Apparent("apparent_power", 88, "Apparent Power", Kind.GRID),
        Voltage("backup_v1", 90, "Back-up L1 Voltage", Kind.UPS),  # modbus 35145
        Current("backup_i1", 92, "Back-up L1 Current", Kind.UPS),
        Frequency("backup_f1", 94, "Back-up L1 Frequency", Kind.UPS),
        Integer("load_mode1", 96, "Load Mode L1"),
        # 98 reserved
        Power("backup_p1", 100, "Back-up L1 Power", Kind.UPS),
        Voltage("backup_v2", 102, "Back-up L2 Voltage", Kind.UPS),
        Current("backup_i2", 104, "Back-up L2 Current", Kind.UPS),
        Frequency("backup_f2", 106, "Back-up L2 Frequency", Kind.UPS),
        Integer("load_mode2", 108, "Load Mode L2"),
        # 110 reserved
        Power("backup_p2", 112, "Back-up L2 Power", Kind.UPS),
        Voltage("backup_v3", 114, "Back-up L3 Voltage", Kind.UPS),
        Current("backup_i3", 116, "Back-up L3 Current", Kind.UPS),
        Frequency("backup_f3", 118, "Back-up L3 Frequency", Kind.UPS),
        Integer("load_mode3", 120, "Load Mode L3"),
        # 122 reserved
        Power("backup_p3", 124, "Back-up L3 Power", Kind.UPS),
        # 126 reserved
        Power("load_p1", 128, "Load L1", Kind.AC),
        # 130 reserved
        Power("load_p2", 132, "Load L2", Kind.AC),
        # 134 reserved
        Power("load_p3", 136, "Load L3", Kind.AC),
        # 138 reserved
        Power("backup_ptotal", 140, "Back-up Load", Kind.UPS),
        # 142 reserved
        Power("load_ptotal", 144, "Load", Kind.AC),
        Integer("ups_load", 146, "Ups Load", "%", Kind.UPS),
        Temp("temperature_air", 148, "Inverter Temperature (Air)", Kind.AC),
        Temp("temperature_module", 150, "Inverter Temperature (Module)"),
        Temp("temperature", 152, "Inverter Temperature (Radiator)", Kind.AC),
        Integer("function_bit", 154, "Function Bit"),
        Voltage("bus_voltage", 156, "Bus Voltage", None),
        Voltage("nbus_voltage", 158, "NBus Voltage", None),
        Voltage("vbattery1", 160, "Battery Voltage", Kind.BAT),  # modbus 35180
        Current("ibattery1", 162, "Battery Current", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1",
                   lambda data: round(read_voltage(data, 160) * read_current(data, 162)),
                   "Battery Power", "W", Kind.BAT),
        Integer("battery_mode", 168, "Battery Mode code", "", Kind.BAT),
        Enum2("battery_mode_label", 168, BATTERY_MODES_ET, "Battery Mode", Kind.BAT),
        Integer("warning_code", 170, "Warning code"),
        Integer("safety_country", 172, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 172, SAFETY_COUNTRIES_ET, "Safety Country", Kind.AC),
        Integer("work_mode", 174, "Work Mode code"),
        Enum2("work_mode_label", 174, WORK_MODES_ET, "Work Mode"),
        Integer("operation_mode", 176, "Operation Mode code"),
        Long("error_codes", 178, "Error Codes"),
        EnumBitmap4("errors", 178, ERROR_CODES, "Errors"),
        Energy4("e_total", 182, "Total PV Generation", Kind.PV),
        Energy4("e_day", 186, "Today's PV Generation", Kind.PV),
        Energy4("e_total_exp", 190, "Total Energy (export)", Kind.AC),
        Long("h_total", 194, "Hours Total", "h", Kind.PV),
        Energy("e_day_exp", 198, "Today Energy (export)", Kind.AC),
        Energy4("e_total_imp", 200, "Total Energy (import)", Kind.AC),
        Energy("e_day_imp", 204, "Today Energy (import)", Kind.AC),
        Energy4("e_load_total", 206, "Total Load", Kind.AC),
        Energy("e_load_day", 210, "Today Load", Kind.AC),
        Energy4("e_bat_charge_total", 212, "Total Battery Charge", Kind.BAT),
        Energy("e_bat_charge_day", 216, "Today Battery Charge", Kind.BAT),
        Energy4("e_bat_discharge_total", 218, "Total Battery Discharge", Kind.BAT),
        Energy("e_bat_discharge_day", 222, "Today Battery Discharge", Kind.BAT),
        Long("diagnose_result", 240, "Diag Status Code"),
        EnumBitmap4("diagnose_result_label", 240, DIAG_STATUS_CODES, "Diag Status"),
        # ppv1 + ppv2 + pbattery - active_power
        Calculated("house_consumption",
                   lambda data:
                   read_bytes4(data, 10) +
                   read_bytes4(data, 18) +
                   read_bytes4(data, 26) +
                   read_bytes4(data, 34) +
                   round(read_voltage(data, 160) * read_current(data, 162)) -
                   read_bytes2(data, 80),
                   "House Consumption", "W", Kind.AC),
    )

    # Modbus registers from offset 0x9088 (37000)
    __all_sensors_battery: Tuple[Sensor, ...] = (
        Integer("battery_bms", 0, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 2, "Battery Index", "", Kind.BAT),
        Integer("battery_status", 4, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 6, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 8, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 10, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_error_l", 12, "Battery Error L", "", Kind.BAT),
        Integer("battery_soc", 14, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 16, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_modules", 18, "Battery Modules", "", Kind.BAT),  # modbus 37009
        Integer("battery_warning_l", 20, "Battery Warning L", "", Kind.BAT),
        Integer("battery_protocol", 22, "Battery Protocol", "", Kind.BAT),
        Integer("battery_error_h", 24, "Battery Error H", "", Kind.BAT),
        EnumBitmap22("battery_error", 24, 12, BMS_ALARM_CODES, "Battery Error", Kind.BAT),
        Integer("battery_warning_h", 28, "Battery Warning H", "", Kind.BAT),
        EnumBitmap22("battery_warning", 28, 20, BMS_WARNING_CODES, "Battery Warning", Kind.BAT),
        Integer("battery_sw_version", 30, "Battery Software Version", "", Kind.BAT),
        Integer("battery_hw_version", 32, "Battery Hardware Version", "", Kind.BAT),
        Integer("battery_max_cell_temp_id", 34, "Battery Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery_min_cell_temp_id", 36, "Battery Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery_max_cell_voltage_id", 38, "Battery Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery_min_cell_voltage_id", 40, "Battery Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery_max_cell_temp", 42, "Battery Max Cell Temperature", Kind.BAT),
        Temp("battery_min_cell_temp", 44, "Battery Min Cell Temperature", Kind.BAT),
        Voltage("battery_max_cell_voltage", 46, "Battery Max Cell Voltage", Kind.BAT),
        Voltage("battery_min_cell_voltage", 48, "Battery Min Cell Voltage", Kind.BAT),
    )

    # Inverter's meter data
    # Modbus registers from offset 0x8ca0 (36000)
    __all_sensors_meter: Tuple[Sensor, ...] = (
        Integer("commode", 0, "Commode"),
        Integer("rssi", 2, "RSSI"),
        Integer("manufacture_code", 4, "Manufacture Code"),
        Integer("meter_test_status", 6, "Meter Test Status"),  # 1: correct，2: reverse，3: incorrect，0: not checked
        Integer("meter_comm_status", 8, "Meter Communication Status"),  # 1 OK, 0 NotOK
        Power("active_power1", 10, "Active Power L1", Kind.GRID),  # modbus 36005
        Power("active_power2", 12, "Active Power L2", Kind.GRID),
        Power("active_power3", 14, "Active Power L3", Kind.GRID),
        Power("active_power_total", 16, "Active Power Total", Kind.GRID),
        Reactive("reactive_power_total", 18, "Reactive Power Total", Kind.GRID),
        Decimal("meter_power_factor1", 20, 1000, "Meter Power Factor L1", "", Kind.GRID),
        Decimal("meter_power_factor2", 22, 1000, "Meter Power Factor L2", "", Kind.GRID),
        Decimal("meter_power_factor3", 24, 1000, "Meter Power Factor L3", "", Kind.GRID),
        Decimal("meter_power_factor", 26, 1000, "Meter Power Factor", "", Kind.GRID),
        Frequency("meter_freq", 28, "Meter Frequency", Kind.GRID),  # modbus 36014
        Float("meter_e_total_exp", 30, 1000, "Meter Total Energy (export)", "kWh", Kind.GRID),
        Float("meter_e_total_imp", 34, 1000, "Meter Total Energy (import)", "kWh", Kind.GRID),
        Power4("meter_active_power1", 38, "Meter Active Power L1", Kind.GRID),
        Power4("meter_active_power2", 42, "Meter Active Power L2", Kind.GRID),
        Power4("meter_active_power3", 46, "Meter Active Power L3", Kind.GRID),
        Power4("meter_active_power_total", 50, "Meter Active Power Total", Kind.GRID),
        Reactive4("meter_reactive_power1", 54, "Meter Reactive Power L1", Kind.GRID),
        Reactive4("meter_reactive_power2", 58, "Meter Reactive Power L2", Kind.GRID),
        Reactive4("meter_reactive_power3", 62, "Meter Reactive Power L2", Kind.GRID),
        Reactive4("meter_reactive_power_total", 66, "Meter Reactive Power Total", Kind.GRID),
        Apparent4("meter_apparent_power1", 70, "Meter Apparent Power L1", Kind.GRID),
        Apparent4("meter_apparent_power2", 74, "Meter Apparent Power L2", Kind.GRID),
        Apparent4("meter_apparent_power3", 78, "Meter Apparent Power L3", Kind.GRID),
        Apparent4("meter_apparent_power_total", 82, "Meter Apparent Power Total", Kind.GRID),
        Integer("meter_type", 86, "Meter Type", "", Kind.GRID),
        Integer("meter_sw_version", 88, "Meter Software Version", "", Kind.GRID),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: Tuple[Sensor, ...] = (
        Integer("comm_address", 45127, "Communication Address", ""),

        Timestamp("time", 45200, "Inverter time"),

        Integer("sensitivity_check", 45246, "Sensitivity Check Mode", "", Kind.AC),
        Integer("cold_start", 45248, "Cold Start", "", Kind.AC),
        Integer("shadow_scan", 45251, "Shadow Scan", "", Kind.PV),
        Integer("backup_supply", 45252, "Backup Supply", "", Kind.UPS),
        Integer("unbalanced_output", 45264, "Unbalanced Output", "", Kind.AC),

        Integer("battery_capacity", 45350, "Battery Capacity", "Ah", Kind.BAT),
        Integer("battery_modules", 45351, "Battery Modules", "", Kind.BAT),
        Voltage("battery_charge_voltage", 45352, "Battery Charge Voltage", Kind.BAT),
        Current("battery_charge_current", 45353, "Battery Charge Current", Kind.BAT),
        Voltage("battery_discharge_voltage", 45354, "Battery Discharge Voltage", Kind.BAT),
        Current("battery_discharge_current", 45355, "Battery Discharge Current", Kind.BAT),
        Integer("battery_discharge_depth", 45356, "Battery Discharge Depth", "%", Kind.BAT),
        Voltage("battery_discharge_voltage_offline", 45357, "Battery Discharge Voltage (off-line)", Kind.BAT),
        Integer("battery_discharge_depth_offline", 45358, "Battery Discharge Depth (off-line)", "%", Kind.BAT),

        Decimal("power_factor", 45482, 100, "Power Factor"),

        Integer("work_mode", 47000, "Work Mode", "", Kind.AC),

        Integer("battery_soc_protection", 47500, "Battery SoC Protection", "", Kind.BAT),

        Integer("grid_export", 47509, "Grid Export Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 47510, "Grid Export Limit", "W", Kind.GRID),

        EcoMode("eco_mode_1", 47515, "Eco Mode Power Group 1"),
        # Byte("eco_mode_1_switch", 47518, "Eco Mode Power Group 1 Switch", "", Kind.BAT),
        EcoMode("eco_mode_2", 47519, "Eco Mode Power Group 2"),
        # Byte("eco_mode_2_switch", 47522, "Eco Mode Power Group 2 Switch", "", Kind.BAT),
        EcoMode("eco_mode_3", 47523, "Eco Mode Power Group 3"),
        # Byte("eco_mode_3_switch", 47526, "Eco Mode Power Group 3 Switch", "", Kind.BAT),
        EcoMode("eco_mode_4", 47527, "Eco Mode Power Group 4"),
        # Byte("eco_mode_4_switch", 47530, "Eco Mode Power Group 4 Switch", "", Kind.BAT),
    )

    # Extra Modbus registers for EcoMode version 2 settings, offsets are modbus register addresses
    __EcoModeV2_settings: Tuple[Sensor, ...] = (
        EcoModeV2("eco_modeV2_1", 47547, "Eco Mode Version 2 Power Group 1"),
        EcoModeV2("eco_modeV2_2", 47553, "Eco Mode Version 2 Power Group 2"),
        EcoModeV2("eco_modeV2_3", 47559, "Eco Mode Version 2 Power Group 3"),
        EcoModeV2("eco_modeV2_4", 47565, "Eco Mode Version 2 Power Group 4"),
    )

    def __init__(self, host: str, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, comm_addr, timeout, retries)
        if not self.comm_addr:
            # Set the default inverter address
            self.comm_addr = 0xf7
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x88b8, 0x0021)
        self._READ_RUNNING_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x891c, 0x007d)
        self._READ_METER_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x8ca0, 0x2d)
        self._READ_BATTERY_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x9088, 0x0018)
        self._has_battery: bool = True
        # By default, we set up only PV1 on PV2 sensors, only few inverters support PV3 and PV3
        # In case they are needed, they are added later in read_device_info
        self._sensors = tuple(filter(self._pv1_pv2_only, self.__all_sensors))
        self._sensors_battery = self.__all_sensors_battery
        self._sensors_meter = self.__all_sensors_meter
        self._settings = self.__all_settings

    def _supports_eco_mode_v2(self) -> bool:
        if not self.dsp1_sw_version:
            return False
        if self.dsp1_sw_version < 8:
            return False
        if self.dsp2_sw_version < 8:
            return False
        if self.arm_sw_version < 19:
            return False
        return True

    def _supports_peak_shawing(self) -> bool:
        return self.arm_sw_version >= 22

    @staticmethod
    def _single_phase_only(s: Sensor) -> bool:
        """Filter to exclude phase2/3 sensors on single phase inverters"""
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    @staticmethod
    def _pv1_pv2_only(s: Sensor) -> bool:
        """Filter to exclude sensors on < 4 PV inverters"""
        return not (('pv3' in s.id_) or ('pv4' in s.id_))

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        # Modbus registers from offset (35000)
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)  # 0: 1-phase, 1: 3-phase (4 wire), 2: 3-phase (3 wire)
        self.serial_number = response[6:22].decode("ascii")
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.dsp1_sw_version = read_unsigned_int(response, 32)
        self.dsp2_sw_version = read_unsigned_int(response, 34)
        self.dsp_svn_version = read_unsigned_int(response, 36)
        self.arm_sw_version = read_unsigned_int(response, 38)
        self.arm_svn_version = read_unsigned_int(response, 40)
        self.software_version = response[42:54].decode("ascii")
        self.arm_version = response[54:66].decode("ascii")

        if "EHU" in self.serial_number:
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._single_phase_only, self._sensors))
            self._sensors_meter = tuple(filter(self._single_phase_only, self._sensors_meter))

        if "HSB" in self.serial_number:
            # this is PV3/PV4 re-include all sensors
            self._sensors = tuple(filter(self._single_phase_only, self.__all_sensors))
            self._sensors_meter = tuple(filter(self._single_phase_only, self._sensors_meter))

        if self._supports_eco_mode_v2():
            # this inverter has eco mode version 2, adding EcoModeV2 to settings
            self._settings = self.__all_settings + self.__EcoModeV2_settings

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self._sensors, include_unknown_sensors)

        self._has_battery = data.get('battery_mode', 0) != 0
        if self._has_battery:
            raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
            data.update(self._map_response(raw_data[5:-2], self._sensors_battery, include_unknown_sensors))

        raw_data = await self._read_from_socket(self._READ_METER_DATA)
        data.update(self._map_response(raw_data[5:-2], self._sensors_meter, include_unknown_sensors))
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
        if export_limit >= 0 or export_limit <= 10000:
            await self.write_setting('grid_export_limit', export_limit)

    async def get_operation_modes(self, include_emulated: bool) -> Tuple[OperationMode, ...]:
        result = [e for e in OperationMode]
        if not self._supports_peak_shawing():
            result.remove(OperationMode.PEAK_SHAVING)
        if not include_emulated:
            result.remove(OperationMode.ECO_CHARGE)
            result.remove(OperationMode.ECO_DISCHARGE)
        return tuple(result)

    async def get_operation_mode(self) -> int:
        return await self.read_setting('work_mode')

    async def set_operation_mode(self, operation_mode: OperationMode, eco_mode_power: int = 100,
                                 max_charge: int = 100) -> None:
        if operation_mode == OperationMode.GENERAL:
            await self.write_setting('work_mode', 0)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.OFF_GRID:
            await self.write_setting('work_mode', 1)
            await self._set_offline(True)
            await self.write_setting('backup_supply', 1)
            await self.write_setting('cold_start', 4)
        elif operation_mode == OperationMode.BACKUP:
            await self.write_setting('work_mode', 2)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.ECO:
            await self.write_setting('work_mode', 3)
            await self._set_offline(False)
        elif operation_mode == OperationMode.PEAK_SHAVING:
            await self.write_setting('work_mode', 4)
            await self._set_offline(False)
        elif operation_mode in (OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE):
            if eco_mode_power < 0 or eco_mode_power > 100:
                raise ValueError()
            if max_charge < 0 or max_charge > 100:
                raise ValueError()
            ecoMode_class = EcoMode
            ecoMode_name = 'eco_mode_'
            if self._supports_eco_mode_v2():
                ecoMode_class = EcoModeV2
                ecoMode_name = 'eco_modeV2_'

            if operation_mode == OperationMode.ECO_CHARGE:
                if ecoMode_class == EcoModeV2:
                    await self.write_setting('eco_modeV2_1',
                                             EcoModeV2("1", 0, "").encode_charge(eco_mode_power, max_charge))
                else:
                    if max_charge != 100:
                        raise InverterError("Operation not supported")
                    await self.write_setting('eco_mode_1', EcoMode("1", 0, "").encode_charge(eco_mode_power))
            else:
                await self.write_setting(ecoMode_name + '1', ecoMode_class("1", 0, "").encode_discharge(eco_mode_power))
            await self.write_setting(ecoMode_name + '2', ecoMode_class("2", 0, "").encode_off())
            await self.write_setting(ecoMode_name + '3', ecoMode_class("3", 0, "").encode_off())
            await self.write_setting(ecoMode_name + '4', ecoMode_class("4", 0, "").encode_off())
            await self.write_setting('work_mode', 3)
            await self._set_offline(False)

    async def get_ongrid_battery_dod(self) -> int:
        return 100 - await self.read_setting('battery_discharge_depth')

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        if 0 <= dod <= 90:
            await self.write_setting('battery_discharge_depth', 100 - dod)

    def sensors(self) -> Tuple[Sensor, ...]:
        if self._has_battery:
            return self._sensors + self._sensors_battery + self._sensors_meter
        else:
            return self._sensors + self._sensors_meter

    def settings(self) -> Tuple[Sensor, ...]:
        return self._settings

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(ModbusWriteCommand(self.comm_addr, 0xb9ad, 1))

    async def _set_offline(self, mode: bool) -> None:
        value = bytes.fromhex('00070000') if mode else bytes.fromhex('00010000')
        await self._read_from_socket(ModbusWriteMultiCommand(self.comm_addr, 0xb997, value))
