from __future__ import annotations

import logging
from typing import Tuple

from .exceptions import RequestFailedException, RequestRejectedException
from .inverter import Inverter
from .inverter import OperationMode
from .inverter import SensorKind as Kind
from .modbus import ILLEGAL_DATA_ADDRESS
from .model import is_2_battery, is_4_mppt, is_745_platform, is_single_phase
from .protocol import ProtocolCommand
from .sensor import *

logger = logging.getLogger(__name__)


class ET(Inverter):
    """Class representing inverter of ET/EH/BT/BH or GE's GEH families AKA platform 205 or 745"""

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __all_sensors: Tuple[Sensor, ...] = (
        Timestamp("timestamp", 35100, "Timestamp"),
        Voltage("vpv1", 35103, "PV1 Voltage", Kind.PV),
        Current("ipv1", 35104, "PV1 Current", Kind.PV),
        Power4("ppv1", 35105, "PV1 Power", Kind.PV),
        Voltage("vpv2", 35107, "PV2 Voltage", Kind.PV),
        Current("ipv2", 35108, "PV2 Current", Kind.PV),
        Power4("ppv2", 35109, "PV2 Power", Kind.PV),
        Voltage("vpv3", 35111, "PV3 Voltage", Kind.PV),
        Current("ipv3", 35112, "PV3 Current", Kind.PV),
        Power4("ppv3", 35113, "PV3 Power", Kind.PV),
        Voltage("vpv4", 35115, "PV4 Voltage", Kind.PV),
        Current("ipv4", 35116, "PV4 Current", Kind.PV),
        Power4("ppv4", 35117, "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv",
                   lambda data:
                   max(0, read_bytes4(data, 35105, 0)) +
                   max(0, read_bytes4(data, 35109, 0)) +
                   max(0, read_bytes4(data, 35113, 0)) +
                   max(0, read_bytes4(data, 35117, 0)),
                   "PV Power", "W", Kind.PV),
        ByteH("pv4_mode", 35119, "PV4 Mode code", "", Kind.PV),
        EnumH("pv4_mode_label", 35119, PV_MODES, "PV4 Mode", Kind.PV),
        ByteL("pv3_mode", 35119, "PV3 Mode code", "", Kind.PV),
        EnumL("pv3_mode_label", 35119, PV_MODES, "PV3 Mode", Kind.PV),
        ByteH("pv2_mode", 35120, "PV2 Mode code", "", Kind.PV),
        EnumH("pv2_mode_label", 35120, PV_MODES, "PV2 Mode", Kind.PV),
        ByteL("pv1_mode", 35120, "PV1 Mode code", "", Kind.PV),
        EnumL("pv1_mode_label", 35120, PV_MODES, "PV1 Mode", Kind.PV),
        Voltage("vgrid", 35121, "On-grid L1 Voltage", Kind.AC),
        Current("igrid", 35122, "On-grid L1 Current", Kind.AC),
        Frequency("fgrid", 35123, "On-grid L1 Frequency", Kind.AC),
        # 35124 reserved
        PowerS("pgrid", 35125, "On-grid L1 Power", Kind.AC),
        Voltage("vgrid2", 35126, "On-grid L2 Voltage", Kind.AC),
        Current("igrid2", 35127, "On-grid L2 Current", Kind.AC),
        Frequency("fgrid2", 35128, "On-grid L2 Frequency", Kind.AC),
        # 35129 reserved
        PowerS("pgrid2", 35130, "On-grid L2 Power", Kind.AC),
        Voltage("vgrid3", 35131, "On-grid L3 Voltage", Kind.AC),
        Current("igrid3", 35132, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid3", 35133, "On-grid L3 Frequency", Kind.AC),
        # 35134 reserved
        PowerS("pgrid3", 35135, "On-grid L3 Power", Kind.AC),
        Integer("grid_mode", 35136, "Grid Mode code", "", Kind.PV),
        Enum2("grid_mode_label", 35136, GRID_MODES, "Grid Mode", Kind.PV),
        # 35137 reserved
        PowerS("total_inverter_power", 35138, "Total Power", Kind.AC),
        # 35139 reserved
        PowerS("active_power", 35140, "Active Power", Kind.GRID),
        Calculated("grid_in_out",
                   lambda data: read_grid_mode(data, 35140),
                   "On-grid Mode code", "", Kind.GRID),
        EnumCalculated("grid_in_out_label",
                       lambda data: read_grid_mode(data, 35140), GRID_IN_OUT_MODES,
                       "On-grid Mode", Kind.GRID),
        # 35141 reserved
        Reactive("reactive_power", 35142, "Reactive Power", Kind.GRID),
        # 35143 reserved
        Apparent("apparent_power", 35144, "Apparent Power", Kind.GRID),
        Voltage("backup_v1", 35145, "Back-up L1 Voltage", Kind.UPS),
        Current("backup_i1", 35146, "Back-up L1 Current", Kind.UPS),
        Frequency("backup_f1", 35147, "Back-up L1 Frequency", Kind.UPS),
        Integer("load_mode1", 35148, "Load Mode L1"),
        # 35149 reserved
        PowerS("backup_p1", 35150, "Back-up L1 Power", Kind.UPS),
        Voltage("backup_v2", 35151, "Back-up L2 Voltage", Kind.UPS),
        Current("backup_i2", 35152, "Back-up L2 Current", Kind.UPS),
        Frequency("backup_f2", 35153, "Back-up L2 Frequency", Kind.UPS),
        Integer("load_mode2", 35154, "Load Mode L2"),
        # 35155 reserved
        PowerS("backup_p2", 35156, "Back-up L2 Power", Kind.UPS),
        Voltage("backup_v3", 35157, "Back-up L3 Voltage", Kind.UPS),
        Current("backup_i3", 35158, "Back-up L3 Current", Kind.UPS),
        Frequency("backup_f3", 35159, "Back-up L3 Frequency", Kind.UPS),
        Integer("load_mode3", 35160, "Load Mode L3"),
        # 35161 reserved
        PowerS("backup_p3", 35162, "Back-up L3 Power", Kind.UPS),
        # 35163 reserved
        PowerS("load_p1", 35164, "Load L1", Kind.AC),
        # 35165 reserved
        PowerS("load_p2", 35166, "Load L2", Kind.AC),
        # 35167 reserved
        PowerS("load_p3", 35168, "Load L3", Kind.AC),
        # 35169 reserved
        PowerS("backup_ptotal", 35170, "Back-up Load", Kind.UPS),
        # 35171 reserved
        PowerS("load_ptotal", 35172, "Load", Kind.AC),
        Integer("ups_load", 35173, "Ups Load", "%", Kind.UPS),
        Temp("temperature_air", 35174, "Inverter Temperature (Air)", Kind.AC),
        Temp("temperature_module", 35175, "Inverter Temperature (Module)"),
        Temp("temperature", 35176, "Inverter Temperature (Radiator)", Kind.AC),
        Integer("function_bit", 35177, "Function Bit"),
        Voltage("bus_voltage", 35178, "Bus Voltage", None),
        Voltage("nbus_voltage", 35179, "NBus Voltage", None),
        Voltage("vbattery1", 35180, "Battery Voltage", Kind.BAT),
        CurrentS("ibattery1", 35181, "Battery Current", Kind.BAT),
        Power4S("pbattery1", 35182, "Battery Power", Kind.BAT),
        Integer("battery_mode", 35184, "Battery Mode code", "", Kind.BAT),
        Enum2("battery_mode_label", 35184, BATTERY_MODES, "Battery Mode", Kind.BAT),
        Integer("warning_code", 35185, "Warning code"),
        Integer("safety_country", 35186, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 35186, SAFETY_COUNTRIES, "Safety Country", Kind.AC),
        Integer("work_mode", 35187, "Work Mode code"),
        Enum2("work_mode_label", 35187, WORK_MODES_ET, "Work Mode"),
        Integer("operation_mode", 35188, "Operation Mode code"),
        Long("error_codes", 35189, "Error Codes"),
        EnumBitmap4("errors", 35189, ERROR_CODES, "Errors"),
        Energy4("e_total", 35191, "Total PV Generation", Kind.PV),
        Energy4("e_day", 35193, "Today's PV Generation", Kind.PV),
        Energy4("e_total_exp", 35195, "Total Energy (export)", Kind.AC),
        Long("h_total", 35197, "Hours Total", "h", Kind.PV),
        Energy("e_day_exp", 35199, "Today Energy (export)", Kind.AC),
        Energy4("e_total_imp", 35200, "Total Energy (import)", Kind.AC),
        Energy("e_day_imp", 35202, "Today Energy (import)", Kind.AC),
        Energy4("e_load_total", 35203, "Total Load", Kind.AC),
        Energy("e_load_day", 35205, "Today Load", Kind.AC),
        Energy4("e_bat_charge_total", 35206, "Total Battery Charge", Kind.BAT),
        Energy("e_bat_charge_day", 35208, "Today Battery Charge", Kind.BAT),
        Energy4("e_bat_discharge_total", 35209, "Total Battery Discharge", Kind.BAT),
        Energy("e_bat_discharge_day", 35211, "Today Battery Discharge", Kind.BAT),
        Long("diagnose_result", 35220, "Diag Status Code"),
        EnumBitmap4("diagnose_result_label", 35220, DIAG_STATUS_CODES, "Diag Status"),
        # ppv1 + ppv2 + ppv3 + ppv4 + pbattery1 - active_power
        Calculated("house_consumption",
                   lambda data:
                   read_bytes4(data, 35105, 0) +
                   read_bytes4(data, 35109, 0) +
                   read_bytes4(data, 35113, 0) +
                   read_bytes4(data, 35117, 0) +
                   read_bytes4_signed(data, 35182) -
                   read_bytes2_signed(data, 35140),
                   "House Consumption", "W", Kind.AC),

        # Power4S("pbattery2", 35264, "Battery2 Power", Kind.BAT),
        # Integer("battery2_mode", 35266, "Battery2 Mode code", "", Kind.BAT),
        # Enum2("battery2_mode_label", 35184, BATTERY_MODES, "Battery2 Mode", Kind.BAT),
    )

    # Modbus registers from offset 0x9088 (37000)
    __all_sensors_battery: Tuple[Sensor, ...] = (
        Integer("battery_bms", 37000, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 37001, "Battery Index", "", Kind.BAT),
        Integer("battery_status", 37002, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 37003, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 37004, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 37005, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_error_l", 37006, "Battery Error L", "", Kind.BAT),
        Integer("battery_soc", 37007, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 37008, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_modules", 37009, "Battery Modules", "", Kind.BAT),
        Integer("battery_warning_l", 37010, "Battery Warning L", "", Kind.BAT),
        Integer("battery_protocol", 37011, "Battery Protocol", "", Kind.BAT),
        Integer("battery_error_h", 37012, "Battery Error H", "", Kind.BAT),
        EnumBitmap22("battery_error", 37012, 37006, BMS_ALARM_CODES, "Battery Error", Kind.BAT),
        Integer("battery_warning_h", 37013, "Battery Warning H", "", Kind.BAT),
        EnumBitmap22("battery_warning", 37013, 37010, BMS_WARNING_CODES, "Battery Warning", Kind.BAT),
        Integer("battery_sw_version", 37014, "Battery Software Version", "", Kind.BAT),
        Integer("battery_hw_version", 37015, "Battery Hardware Version", "", Kind.BAT),
        Integer("battery_max_cell_temp_id", 37016, "Battery Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery_min_cell_temp_id", 37017, "Battery Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery_max_cell_voltage_id", 37018, "Battery Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery_min_cell_voltage_id", 37019, "Battery Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery_max_cell_temp", 37020, "Battery Max Cell Temperature", Kind.BAT),
        Temp("battery_min_cell_temp", 37021, "Battery Min Cell Temperature", Kind.BAT),
        CellVoltage("battery_max_cell_voltage", 37022, "Battery Max Cell Voltage", Kind.BAT),
        CellVoltage("battery_min_cell_voltage", 37023, "Battery Min Cell Voltage", Kind.BAT),
        # Energy4("battery_total_charge", 37056, "Total Battery 1 Charge", Kind.BAT),
        # Energy4("battery_total_discharge", 37058, "Total Battery 1 Discharge", Kind.BAT),
        # String8("battery_sn", 37060, "Battery S/N", Kind.BAT),
    )

    # Modbus registers from offset 0x9858 (39000)
    __all_sensors_battery2: Tuple[Sensor, ...] = (
        Integer("battery2_status", 39000, "Battery 2 Status", "", Kind.BAT),
        Temp("battery2_temperature", 39001, "Battery 2 Temperature", Kind.BAT),
        Integer("battery2_charge_limit", 39002, "Battery 2 Charge Limit", "A", Kind.BAT),
        Integer("battery2_discharge_limit", 39003, "Battery 2 Discharge Limit", "A", Kind.BAT),
        Integer("battery2_error_l", 39004, "Battery 2 rror L", "", Kind.BAT),
        Integer("battery2_soc", 39005, "Battery 2 State of Charge", "%", Kind.BAT),
        Integer("battery2_soh", 39006, "Battery 2 State of Health", "%", Kind.BAT),
        Integer("battery2_modules", 39007, "Battery 2 Modules", "", Kind.BAT),
        Integer("battery2_warning_l", 39008, "Battery 2 Warning L", "", Kind.BAT),
        Integer("battery2_protocol", 39009, "Battery 2 Protocol", "", Kind.BAT),
        Integer("battery2_error_h", 39010, "Battery 2 Error H", "", Kind.BAT),
        EnumBitmap22("battery2_error", 39010, 39004, BMS_ALARM_CODES, "Battery 2 Error", Kind.BAT),
        Integer("battery2_warning_h", 39011, "Battery 2 Warning H", "", Kind.BAT),
        EnumBitmap22("battery2_warning", 39011, 39008, BMS_WARNING_CODES, "Battery 2 Warning", Kind.BAT),
        Integer("battery2_sw_version", 39012, "Battery 2 Software Version", "", Kind.BAT),
        Integer("battery2_hw_version", 39013, "Battery 2 Hardware Version", "", Kind.BAT),
        Integer("battery2_max_cell_temp_id", 39014, "Battery 2 Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery2_min_cell_temp_id", 39015, "Battery 2 Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery2_max_cell_voltage_id", 39016, "Battery 2 Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery2_min_cell_voltage_id", 39017, "Battery 2 Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery2_max_cell_temp", 39018, "Battery 2 Max Cell Temperature", Kind.BAT),
        Temp("battery2_min_cell_temp", 39019, "Battery 2 Min Cell Temperature", Kind.BAT),
        CellVoltage("battery2_max_cell_voltage", 39020, "Battery 2 Max Cell Voltage", Kind.BAT),
        CellVoltage("battery2_min_cell_voltage", 39021, "Battery 2 Min Cell Voltage", Kind.BAT),
        # Energy4("battery2_total_charge", 39054, "Total Battery 2 Charge", Kind.BAT),
        # Energy4("battery2_total_discharge", 39056, "Total Battery 2 Discharge", Kind.BAT),
        # String8("battery2_sn", 39058, "Battery 2 S/N", Kind.BAT),
    )

    # Inverter's meter data
    # Modbus registers from offset 0x8ca0 (36000)
    __all_sensors_meter: Tuple[Sensor, ...] = (
        Integer("commode", 36000, "Commode"),
        Integer("rssi", 36001, "RSSI"),
        Integer("manufacture_code", 36002, "Manufacture Code"),
        Integer("meter_test_status", 36003, "Meter Test Status"),  # 1: correct，2: reverse，3: incorrect，0: not checked
        Integer("meter_comm_status", 36004, "Meter Communication Status"),  # 1 OK, 0 NotOK
        PowerS("active_power1", 36005, "Active Power L1", Kind.GRID),
        PowerS("active_power2", 36006, "Active Power L2", Kind.GRID),
        PowerS("active_power3", 36007, "Active Power L3", Kind.GRID),
        PowerS("active_power_total", 36008, "Active Power Total", Kind.GRID),
        Reactive("reactive_power_total", 36009, "Reactive Power Total", Kind.GRID),
        Decimal("meter_power_factor1", 36010, 1000, "Meter Power Factor L1", "", Kind.GRID),
        Decimal("meter_power_factor2", 36011, 1000, "Meter Power Factor L2", "", Kind.GRID),
        Decimal("meter_power_factor3", 36012, 1000, "Meter Power Factor L3", "", Kind.GRID),
        Decimal("meter_power_factor", 36013, 1000, "Meter Power Factor", "", Kind.GRID),
        Frequency("meter_freq", 36014, "Meter Frequency", Kind.GRID),
        Float("meter_e_total_exp", 36015, 1000, "Meter Total Energy (export)", "kWh", Kind.GRID),
        Float("meter_e_total_imp", 36017, 1000, "Meter Total Energy (import)", "kWh", Kind.GRID),
        Power4S("meter_active_power1", 36019, "Meter Active Power L1", Kind.GRID),
        Power4S("meter_active_power2", 36021, "Meter Active Power L2", Kind.GRID),
        Power4S("meter_active_power3", 36023, "Meter Active Power L3", Kind.GRID),
        Power4S("meter_active_power_total", 36025, "Meter Active Power Total", Kind.GRID),
        Reactive4("meter_reactive_power1", 36027, "Meter Reactive Power L1", Kind.GRID),
        Reactive4("meter_reactive_power2", 36029, "Meter Reactive Power L2", Kind.GRID),
        Reactive4("meter_reactive_power3", 36031, "Meter Reactive Power L2", Kind.GRID),
        Reactive4("meter_reactive_power_total", 36033, "Meter Reactive Power Total", Kind.GRID),
        Apparent4("meter_apparent_power1", 36035, "Meter Apparent Power L1", Kind.GRID),
        Apparent4("meter_apparent_power2", 36037, "Meter Apparent Power L2", Kind.GRID),
        Apparent4("meter_apparent_power3", 36039, "Meter Apparent Power L3", Kind.GRID),
        Apparent4("meter_apparent_power_total", 36041, "Meter Apparent Power Total", Kind.GRID),
        Integer("meter_type", 36043, "Meter Type", "", Kind.GRID),  # (0: Single phase, 1: 3P3W, 2: 3P4W, 3: HomeKit)
        Integer("meter_sw_version", 36044, "Meter Software Version", "", Kind.GRID),
        # Sensors added in some ARM fw update, read when flag _has_meter_extended is on
        Power4S("meter2_active_power", 36045, "Meter 2 Active Power", Kind.GRID),
        Float("meter2_e_total_exp", 36047, 1000, "Meter 2 Total Energy (export)", "kWh", Kind.GRID),
        Float("meter2_e_total_imp", 36049, 1000, "Meter 2 Total Energy (import)", "kWh", Kind.GRID),
        Integer("meter2_comm_status", 36051, "Meter 2 Communication Status"),
        Voltage("meter_voltage1", 36052, "Meter L1 Voltage", Kind.GRID),
        Voltage("meter_voltage2", 36053, "Meter L2 Voltage", Kind.GRID),
        Voltage("meter_voltage3", 36054, "Meter L3 Voltage", Kind.GRID),
        Current("meter_current1", 36055, "Meter L1 Current", Kind.GRID),
        Current("meter_current2", 36056, "Meter L2 Current", Kind.GRID),
        Current("meter_current3", 36057, "Meter L3 Current", Kind.GRID),
    )

    # Inverter's MPPT data
    # Modbus registers from offset 0x89e5 (35301)
    __all_sensors_mppt: Tuple[Sensor, ...] = (
        Power4("ppv_total", 35301, "PV Power Total", Kind.PV),
        Integer("pv_channel", 35303, "PV Channel", "", Kind.PV),
        Voltage("vpv5", 35304, "PV5 Voltage", Kind.PV),
        Current("ipv5", 35305, "PV5 Current", Kind.PV),
        Voltage("vpv6", 35306, "PV6 Voltage", Kind.PV),
        Current("ipv6", 35307, "PV6 Current", Kind.PV),
        Voltage("vpv7", 35308, "PV7 Voltage", Kind.PV),
        Current("ipv7", 35309, "PV7 Current", Kind.PV),
        Voltage("vpv8", 35310, "PV8 Voltage", Kind.PV),
        Current("ipv8", 35311, "PV8 Current", Kind.PV),
        Voltage("vpv9", 35312, "PV9 Voltage", Kind.PV),
        Current("ipv9", 35313, "PV9 Current", Kind.PV),
        Voltage("vpv10", 35314, "PV10 Voltage", Kind.PV),
        Current("ipv10", 35315, "PV10 Current", Kind.PV),
        Voltage("vpv11", 35316, "PV11 Voltage", Kind.PV),
        Current("ipv11", 35317, "PV11 Current", Kind.PV),
        Voltage("vpv12", 35318, "PV12 Voltage", Kind.PV),
        Current("ipv12", 35319, "PV12 Current", Kind.PV),
        Voltage("vpv13", 35320, "PV13 Voltage", Kind.PV),
        Current("ipv13", 35321, "PV13 Current", Kind.PV),
        Voltage("vpv14", 35322, "PV14 Voltage", Kind.PV),
        Current("ipv14", 35323, "PV14 Current", Kind.PV),
        Voltage("vpv15", 35324, "PV15 Voltage", Kind.PV),
        Current("ipv15", 35325, "PV15 Current", Kind.PV),
        Voltage("vpv16", 35326, "PV16 Voltage", Kind.PV),
        Current("ipv16", 35327, "PV16 Current", Kind.PV),
        # 35328 Warning Message
        # 35330 Grid10minAvgVoltR
        # 35331 Grid10minAvgVoltS
        # 35332 Grid10minAvgVoltT
        # 35333 Error Message Extend
        # 35335 Warning Message Extend
        Power("pmppt1", 35337, "MPPT1 Power", Kind.PV),
        Power("pmppt2", 35338, "MPPT2 Power", Kind.PV),
        Power("pmppt3", 35339, "MPPT3 Power", Kind.PV),
        Power("pmppt4", 35340, "MPPT4 Power", Kind.PV),
        Power("pmppt5", 35341, "MPPT5 Power", Kind.PV),
        Power("pmppt6", 35342, "MPPT6 Power", Kind.PV),
        Power("pmppt7", 35343, "MPPT7 Power", Kind.PV),
        Power("pmppt8", 35344, "MPPT8 Power", Kind.PV),
        Current("imppt1", 35345, "MPPT1 Current", Kind.PV),
        Current("imppt2", 35346, "MPPT2 Current", Kind.PV),
        Current("imppt3", 35347, "MPPT3 Current", Kind.PV),
        Current("imppt4", 35348, "MPPT4 Current", Kind.PV),
        Current("imppt5", 35349, "MPPT5 Current", Kind.PV),
        Current("imppt6", 35350, "MPPT6 Current", Kind.PV),
        Current("imppt7", 35351, "MPPT7 Current", Kind.PV),
        Current("imppt8", 35352, "MPPT8 Current", Kind.PV),
        Reactive4("reactive_power1", 35353, "Reactive Power L1", Kind.GRID),
        Reactive4("reactive_power2", 35355, "Reactive Power L2", Kind.GRID),
        Reactive4("reactive_power3", 35357, "Reactive Power L3", Kind.GRID),
        Apparent4("apparent_power1", 35359, "Apparent Power L1", Kind.GRID),
        Apparent4("apparent_power2", 35361, "Apparent Power L2", Kind.GRID),
        Apparent4("apparent_power3", 35363, "Apparent Power L3", Kind.GRID),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: Tuple[Sensor, ...] = (
        Integer("comm_address", 45127, "Communication Address", ""),
        Integer("modbus_baud_rate", 45132, "Modbus Baud rate", ""),
        Timestamp("time", 45200, "Inverter time"),

        Integer("sensitivity_check", 45246, "Sensitivity Check Mode", "", Kind.AC),
        Integer("cold_start", 45248, "Cold Start", "", Kind.AC),
        Integer("shadow_scan", 45251, "Shadow Scan", "", Kind.PV),
        Integer("backup_supply", 45252, "Backup Supply", "", Kind.UPS),
        Integer("unbalanced_output", 45264, "Unbalanced Output", "", Kind.AC),
        Integer("pen_relay", 45288, "PE-N Relay", "", Kind.AC),

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
        Integer("dred", 47010, "DRED/Remote Shutdown", "", Kind.AC),

        Integer("battery_soc_protection", 47500, "Battery SoC Protection", "", Kind.BAT),

        Integer("grid_export", 47509, "Grid Export Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 47510, "Grid Export Limit", "W", Kind.GRID),

        Integer("battery_protocol_code", 47514, "Battery Protocol Code", "", Kind.BAT),

        EcoModeV1("eco_mode_1", 47515, "Eco Mode Group 1"),
        ByteH("eco_mode_1_switch", 47518, "Eco Mode Group 1 Switch"),
        EcoModeV1("eco_mode_2", 47519, "Eco Mode Group 2"),
        ByteH("eco_mode_2_switch", 47522, "Eco Mode Group 2 Switch"),
        EcoModeV1("eco_mode_3", 47523, "Eco Mode Group 3"),
        ByteH("eco_mode_3_switch", 47526, "Eco Mode Group 3 Switch"),
        EcoModeV1("eco_mode_4", 47527, "Eco Mode Group 4"),
        ByteH("eco_mode_4_switch", 47530, "Eco Mode Group 4 Switch"),

        # Direct BMS communication for EMS Control
        Integer("bms_version", 47900, "BMS Version"),
        Integer("bms_bat_modules", 47901, "BMS Battery Modules"),
        # Real time read from BMS
        Voltage("bms_bat_charge_v_max", 47902, "BMS Battery Charge Voltage (max)", Kind.BMS),
        Current("bms_bat_charge_i_max", 47903, "BMS Battery Charge Current (max)", Kind.BMS),
        Voltage("bms_bat_discharge_v_min", 47904, "BMS min. Battery Discharge Voltage (min)", Kind.BMS),
        Current("bms_bat_discharge_i_max", 47905, "BMS max. Battery Discharge Current (max)", Kind.BMS),
        Voltage("bms_bat_voltage", 47906, "BMS Battery Voltage", Kind.BMS),
        Current("bms_bat_current", 47907, "BMS Battery Current", Kind.BMS),
        #
        Integer("bms_bat_soc", 47908, "BMS Battery State of Charge", "%", Kind.BMS),
        Integer("bms_bat_soh", 47909, "BMS Battery State of Health", "%", Kind.BMS),
        Temp("bms_bat_temperature", 47910, "BMS Battery Temperature", Kind.BMS),
        Long("bms_bat_warning-code", 47911, "BMS Battery Warning Code"),
        # Reserved
        Long("bms_bat_alarm-code", 47913, "BMS Battery Alarm Code"),
        Integer("bms_status", 47915, "BMS Status"),
        Integer("bms_comm_loss_disable", 47916, "BMS Communication Loss Disable"),
        # RW settings of BMS voltage rate
        Integer("bms_battery_string_rate_v", 47917, "BMS Battery String Rate Voltage"),

        # Direct BMS communication for EMS Control
        Integer("bms2_version", 47918, "BMS2 Version"),
        Integer("bms2_bat_modules", 47919, "BMS2 Battery Modules"),
        # Real time read from BMS
        Voltage("bms2_bat_charge_v_max", 47920, "BMS2 Battery Charge Voltage (max)", Kind.BMS),
        Current("bms2_bat_charge_i_max", 47921, "BMS2 Battery Charge Current (max)", Kind.BMS),
        Voltage("bms2_bat_discharge_v_min", 47922, "BMS2 min. Battery Discharge Voltage (min)", Kind.BMS),
        Current("bms2_bat_discharge_i_max", 47923, "BMS2 max. Battery Discharge Current (max)", Kind.BMS),
        Voltage("bms2_bat_voltage", 47924, "BMS2 Battery Voltage", Kind.BMS),
        Current("bms2_bat_current", 47925, "BMS2 Battery Current", Kind.BMS),
        #
        Integer("bms2_bat_soc", 47926, "BMS2 Battery State of Charge", "%", Kind.BMS),
        Integer("bms2_bat_soh", 47927, "BMS2 Battery State of Health", "%", Kind.BMS),
        Temp("bms2_bat_temperature", 47928, "BMS2 Battery Temperature", Kind.BMS),
        Long("bms2_bat_warning-code", 47929, "BMS2 Battery Warning Code"),
        # Reserved
        Long("bms2_bat_alarm-code", 47931, "BMS2 Battery Alarm Code"),
        Integer("bms2_status", 47933, "BMS2 Status"),
        Integer("bms2_comm_loss_disable", 47934, "BMS2 Communication Loss Disable"),
        # RW settings of BMS voltage rate
        Integer("bms2_battery_string_rate_v", 47935, "BMS2 Battery String Rate Voltage"),

    )

    # Settings added in ARM firmware 19
    __settings_arm_fw_19: Tuple[Sensor, ...] = (
        Integer("fast_charging", 47545, "Fast Charging Enabled", "", Kind.BAT),
        Integer("fast_charging_soc", 47546, "Fast Charging SoC", "%", Kind.BAT),
        EcoModeV2("eco_mode_1", 47547, "Eco Mode Group 1"),
        ByteH("eco_mode_1_switch", 47549, "Eco Mode Group 1 Switch"),
        EcoModeV2("eco_mode_2", 47553, "Eco Mode Group 2"),
        ByteH("eco_mode_2_switch", 47555, "Eco Mode Group 2 Switch"),
        EcoModeV2("eco_mode_3", 47559, "Eco Mode Group 3"),
        ByteH("eco_mode_3_switch", 47561, "Eco Mode Group 3 Switch"),
        EcoModeV2("eco_mode_4", 47565, "Eco Mode Group 4"),
        ByteH("eco_mode_4_switch", 47567, "Eco Mode Group 4 Switch"),

        Integer("load_control_mode", 47595, "Load Control Mode", "", Kind.AC),
        Integer("load_control_switch", 47596, "Load Control Switch", "", Kind.AC),
        Integer("load_control_soc", 47597, "Load Control SoC", "", Kind.AC),
        Integer("hardware_feed_power", 47599, "Hardware Feed Power"),

        Integer("fast_charging_power", 47603, "Fast Charging Power", "%", Kind.BAT),
    )

    # Settings added in ARM firmware 22
    __settings_arm_fw_22: Tuple[Sensor, ...] = (
        Long("peak_shaving_power_limit", 47542, "Peak Shaving Power Limit"),
        Integer("peak_shaving_soc", 47544, "Peak Shaving SoC"),
        # EcoModeV2("eco_modeV2_5", 47571, "Eco Mode Version 2 Power Group 5"),
        # EcoModeV2("eco_modeV2_6", 47577, "Eco Mode Version 2 Power Group 6"),
        # EcoModeV2("eco_modeV2_7", 47583, "Eco Mode Version 2 Power Group 7"),
        PeakShavingMode("peak_shaving_mode", 47589, "Peak Shaving Mode"),

        Integer("dod_holding", 47602, "DoD Holding", "", Kind.BAT),
        Integer("backup_mode_enable", 47605, "Backup Mode Switch"),
        Integer("max_charge_power", 47606, "Max Charge Power"),
        Integer("smart_charging_enable", 47609, "Smart Charging Mode Switch"),
        Integer("eco_mode_enable", 47612, "Eco Mode Switch"),
    )

    def __init__(self, host: str, port: int, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr if comm_addr else 0xf7, timeout, retries)
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = self._read_command(0x88b8, 0x0021)
        self._READ_RUNNING_DATA: ProtocolCommand = self._read_command(0x891c, 0x007d)
        self._READ_METER_DATA: ProtocolCommand = self._read_command(0x8ca0, 0x2d)
        self._READ_METER_DATA_EXTENDED: ProtocolCommand = self._read_command(0x8ca0, 0x3a)
        self._READ_BATTERY_INFO: ProtocolCommand = self._read_command(0x9088, 0x0018)
        self._READ_BATTERY2_INFO: ProtocolCommand = self._read_command(0x9858, 0x0016)
        self._READ_MPPT_DATA: ProtocolCommand = self._read_command(0x89e5, 0x3d)
        self._has_eco_mode_v2: bool = True
        self._has_peak_shaving: bool = True
        self._has_battery: bool = True
        self._has_battery2: bool = False
        self._has_meter_extended: bool = False
        self._has_mppt: bool = False
        self._sensors = self.__all_sensors
        self._sensors_battery = self.__all_sensors_battery
        self._sensors_battery2 = self.__all_sensors_battery2
        self._sensors_meter = self.__all_sensors_meter
        self._sensors_mppt = self.__all_sensors_mppt
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

    @staticmethod
    def _single_phase_only(s: Sensor) -> bool:
        """Filter to exclude phase2/3 sensors on single phase inverters"""
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    @staticmethod
    def _not_extended_meter(s: Sensor) -> bool:
        """Filter to exclude extended meter sensors"""
        return s.offset < 36045

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response.response_data()
        # Modbus registers from 35000 - 35032
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)  # 0: 1-phase, 1: 3-phase (4 wire), 2: 3-phase (3 wire)
        self.serial_number = self._decode(response[6:22])  # 35003 - 350010
        self.model_name = self._decode(response[22:32])  # 35011 - 35015
        self.dsp1_version = read_unsigned_int(response, 32)  # 35016
        self.dsp2_version = read_unsigned_int(response, 34)  # 35017
        self.dsp_svn_version = read_unsigned_int(response, 36)  # 35018
        self.arm_version = read_unsigned_int(response, 38)  # 35019
        self.arm_svn_version = read_unsigned_int(response, 40)  # 35020
        self.firmware = self._decode(response[42:54])  # 35021 - 35027
        self.arm_firmware = self._decode(response[54:66])  # 35027 - 35032

        if not is_4_mppt(self) and self.rated_power < 15000:
            # This inverter does not have 4 MPPTs or PV strings
            self._sensors = tuple(filter(lambda s: not ('pv4' in s.id_), self._sensors))
            self._sensors = tuple(filter(lambda s: not ('pv3' in s.id_), self._sensors))

        if is_single_phase(self):
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._single_phase_only, self._sensors))
            self._sensors_meter = tuple(filter(self._single_phase_only, self._sensors_meter))

        if is_2_battery(self) or self.rated_power >= 25000:
            self._has_battery2 = True

        if self.rated_power >= 15000:
            self._has_mppt = True
            self._has_meter_extended = True
        else:
            self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))

        # Check and add EcoModeV2 settings added in (ETU fw 19)
        try:
            await self._read_from_socket(self._read_command(47547, 6))
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_19})
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("EcoModeV2 settings not supported, switching to EcoModeV1.")
                self._has_eco_mode_v2 = False
        except RequestFailedException:
            logger.debug("Cannot read EcoModeV2 settings, switching to EcoModeV1.")
            self._has_eco_mode_v2 = False

        # Check and add Peak Shaving settings added in (ETU fw 22)
        try:
            await self._read_from_socket(self._read_command(47589, 6))
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_22})
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("PeakShaving setting not supported, disabling it.")
                self._has_peak_shaving = False
        except RequestFailedException:
            logger.debug("Cannot read _has_peak_shaving settings, disabling it.")
            self._has_peak_shaving = False

    async def read_runtime_data(self) -> Dict[str, Any]:
        response = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(response, self._sensors)

        self._has_battery = data.get('battery_mode', 0) != 0
        if self._has_battery:
            try:
                response = await self._read_from_socket(self._READ_BATTERY_INFO)
                data.update(self._map_response(response, self._sensors_battery))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Battery values not supported, disabling further attempts.")
                    self._has_battery = False
                else:
                    raise ex
        if self._has_battery2:
            try:
                response = await self._read_from_socket(self._READ_BATTERY2_INFO)
                data.update(
                    self._map_response(response, self._sensors_battery2))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Battery 2 values not supported, disabling further attempts.")
                    self._has_battery2 = False
                else:
                    raise ex

        if self._has_meter_extended:
            try:
                response = await self._read_from_socket(self._READ_METER_DATA_EXTENDED)
                data.update(self._map_response(response, self._sensors_meter))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Extended meter values not supported, disabling further attempts.")
                    self._has_meter_extended = False
                    self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))
                    response = await self._read_from_socket(self._READ_METER_DATA)
                    data.update(
                        self._map_response(response, self._sensors_meter))
                else:
                    raise ex
        else:
            response = await self._read_from_socket(self._READ_METER_DATA)
            data.update(self._map_response(response, self._sensors_meter))

        if self._has_mppt:
            try:
                response = await self._read_from_socket(self._READ_MPPT_DATA)
                data.update(self._map_response(response, self._sensors_mppt))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("MPPT values not supported, disabling further attempts.")
                    self._has_mppt = False
                else:
                    raise ex

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
            try:
                value = await self.read_setting(setting.id_)
                data[setting.id_] = value
            except (ValueError, RequestFailedException):
                logger.exception("Error reading setting %s.", setting.id_)
                data[setting.id_] = None
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_export_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0:
            await self.write_setting('grid_export_limit', export_limit)

    async def get_operation_modes(self, include_emulated: bool) -> Tuple[OperationMode, ...]:
        result = [e for e in OperationMode]
        if not self._has_peak_shaving:
            result.remove(OperationMode.PEAK_SHAVING)
        if not is_745_platform(self):
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
            await self.write_setting('work_mode', 0)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.OFF_GRID:
            await self.write_setting('work_mode', 1)
            await self._set_offline(True)
            await self.write_setting('backup_supply', 1)
            await self.write_setting('cold_start', 4)
            await self._clear_battery_mode_param()
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
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.SELF_USE:
            await self.write_setting('work_mode', 5)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode in (OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE):
            if eco_mode_power < 0 or eco_mode_power > 100:
                raise ValueError()
            if eco_mode_soc < 0 or eco_mode_soc > 100:
                raise ValueError()

            eco_mode: EcoMode | Sensor = self._settings.get('eco_mode_1')
            # Load the current values to try to detect schedule type
            try:
                await self._read_setting(eco_mode)
            except ValueError:
                pass
            eco_mode.set_schedule_type(ScheduleType.ECO_MODE, is_745_platform(self))
            if operation_mode == OperationMode.ECO_CHARGE:
                await self.write_setting('eco_mode_1', eco_mode.encode_charge(eco_mode_power, eco_mode_soc))
            else:
                await self.write_setting('eco_mode_1', eco_mode.encode_discharge(eco_mode_power))
            await self.write_setting('eco_mode_2_switch', 0)
            await self.write_setting('eco_mode_3_switch', 0)
            await self.write_setting('eco_mode_4_switch', 0)
            await self.write_setting('work_mode', 3)
            await self._set_offline(False)

    async def get_ongrid_battery_dod(self) -> int:
        return 100 - await self.read_setting('battery_discharge_depth')

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        if 0 <= dod <= 100:
            await self.write_setting('battery_discharge_depth', 100 - dod)

    def sensors(self) -> Tuple[Sensor, ...]:
        result = self._sensors + self._sensors_meter
        if self._has_battery:
            result = result + self._sensors_battery
        if self._has_battery2:
            result = result + self._sensors_battery2
        if self._has_mppt:
            result = result + self._sensors_mppt
        return result

    def settings(self) -> Tuple[Sensor, ...]:
        return tuple(self._settings.values())

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(self._write_command(0xb9ad, 1))

    async def _set_offline(self, mode: bool) -> None:
        value = bytes.fromhex('00070000') if mode else bytes.fromhex('00010000')
        await self._read_from_socket(self._write_multi_command(0xb997, value))
