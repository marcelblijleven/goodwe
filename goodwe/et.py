from __future__ import annotations

import logging
from typing import Tuple, cast

from .exceptions import RequestRejectedException
from .inverter import Inverter
from .inverter import OperationMode
from .inverter import SensorKind as Kind
from .model import is_2_battery, is_3_mptt, is_4_mptt, is_single_phase
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand, ModbusWriteMultiCommand
from .sensor import *

logger = logging.getLogger(__name__)


class ET(Inverter):
    """Class representing inverter of ET/EH/BT/BH or GE's GEH families"""

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __all_sensors: Tuple[Sensor, ...] = (
        Timestamp("timestamp", 0, "Timestamp"),  # 35100
        Voltage("vpv1", 6, "PV1 Voltage", Kind.PV),  # 35103
        Current("ipv1", 8, "PV1 Current", Kind.PV),  # 35104
        Power4("ppv1", 10, "PV1 Power", Kind.PV),  # 35105
        Voltage("vpv2", 14, "PV2 Voltage", Kind.PV),  # 35107
        Current("ipv2", 16, "PV2 Current", Kind.PV),  # 35108
        Power4("ppv2", 18, "PV2 Power", Kind.PV),  # 35109
        Voltage("vpv3", 22, "PV3 Voltage", Kind.PV),  # 35111
        Current("ipv3", 24, "PV3 Current", Kind.PV),  # 35112
        Power4("ppv3", 26, "PV3 Power", Kind.PV),  # 35113
        Voltage("vpv4", 30, "PV4 Voltage", Kind.PV),  # 35115
        Current("ipv4", 32, "PV4 Current", Kind.PV),  # 35116
        Power4("ppv4", 34, "PV4 Power", Kind.PV),  # 35117
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv",
                   lambda data:
                   max(0, read_bytes4(data, 10)) +
                   max(0, read_bytes4(data, 18)) +
                   max(0, read_bytes4(data, 26)) +
                   max(0, read_bytes4(data, 34)),
                   "PV Power", "W", Kind.PV),  # 35119
        Byte("pv4_mode", 38, "PV4 Mode code", "", Kind.PV),  # 35120 l
        Enum("pv4_mode_label", 38, PV_MODES, "PV4 Mode", Kind.PV),
        Byte("pv3_mode", 39, "PV3 Mode code", "", Kind.PV),  # 35120 h
        Enum("pv3_mode_label", 39, PV_MODES, "PV3 Mode", Kind.PV),
        Byte("pv2_mode", 40, "PV2 Mode code", "", Kind.PV),  # 35119 l
        Enum("pv2_mode_label", 40, PV_MODES, "PV2 Mode", Kind.PV),
        Byte("pv1_mode", 41, "PV1 Mode code", "", Kind.PV),  # 35119 h
        Enum("pv1_mode_label", 41, PV_MODES, "PV1 Mode", Kind.PV),
        Voltage("vgrid", 42, "On-grid L1 Voltage", Kind.AC),  # 35121
        Current("igrid", 44, "On-grid L1 Current", Kind.AC),  # 35122
        Frequency("fgrid", 46, "On-grid L1 Frequency", Kind.AC),  # 35123
        # 48 reserved
        Power("pgrid", 50, "On-grid L1 Power", Kind.AC),  # 35125
        Voltage("vgrid2", 52, "On-grid L2 Voltage", Kind.AC),  # 35126
        Current("igrid2", 54, "On-grid L2 Current", Kind.AC),  # 35127
        Frequency("fgrid2", 56, "On-grid L2 Frequency", Kind.AC),  # 35128
        # 58 reserved
        Power("pgrid2", 60, "On-grid L2 Power", Kind.AC),  # 35130
        Voltage("vgrid3", 62, "On-grid L3 Voltage", Kind.AC),  # 35131
        Current("igrid3", 64, "On-grid L3 Current", Kind.AC),  # 35132
        Frequency("fgrid3", 66, "On-grid L3 Frequency", Kind.AC),  # 35133
        # 68 reserved
        Power("pgrid3", 70, "On-grid L3 Power", Kind.AC),  # 35135
        Integer("grid_mode", 72, "Grid Mode code", "", Kind.PV),  # 35136
        Enum2("grid_mode_label", 72, GRID_MODES, "Grid Mode", Kind.PV),
        # 74 reserved
        Power("total_inverter_power", 76, "Total Power", Kind.AC),  # 35138
        # 78 reserved
        Power("active_power", 80, "Active Power", Kind.GRID),  # 35140
        Calculated("grid_in_out",
                   lambda data: read_grid_mode(data, 80),
                   "On-grid Mode code", "", Kind.GRID),
        EnumCalculated("grid_in_out_label",
                       lambda data: read_grid_mode(data, 80), GRID_IN_OUT_MODES,
                       "On-grid Mode", Kind.GRID),
        # 82 reserved
        Reactive("reactive_power", 84, "Reactive Power", Kind.GRID),  # 35142
        # 86 reserved
        Apparent("apparent_power", 88, "Apparent Power", Kind.GRID),  # 35144
        Voltage("backup_v1", 90, "Back-up L1 Voltage", Kind.UPS),  # 35145
        Current("backup_i1", 92, "Back-up L1 Current", Kind.UPS),  # 35146
        Frequency("backup_f1", 94, "Back-up L1 Frequency", Kind.UPS),  # 35147
        Integer("load_mode1", 96, "Load Mode L1"),  # 35148
        # 98 reserved
        Power("backup_p1", 100, "Back-up L1 Power", Kind.UPS),  # 35150
        Voltage("backup_v2", 102, "Back-up L2 Voltage", Kind.UPS),  # 35151
        Current("backup_i2", 104, "Back-up L2 Current", Kind.UPS),  # 35152
        Frequency("backup_f2", 106, "Back-up L2 Frequency", Kind.UPS),  # 35153
        Integer("load_mode2", 108, "Load Mode L2"),  # 35154
        # 110 reserved
        Power("backup_p2", 112, "Back-up L2 Power", Kind.UPS),  # 35156
        Voltage("backup_v3", 114, "Back-up L3 Voltage", Kind.UPS),  # 35157
        Current("backup_i3", 116, "Back-up L3 Current", Kind.UPS),  # 35158
        Frequency("backup_f3", 118, "Back-up L3 Frequency", Kind.UPS),  # 35159
        Integer("load_mode3", 120, "Load Mode L3"),  # 35160
        # 122 reserved
        Power("backup_p3", 124, "Back-up L3 Power", Kind.UPS),  # 35162
        # 126 reserved
        Power("load_p1", 128, "Load L1", Kind.AC),  # 35164
        # 130 reserved
        Power("load_p2", 132, "Load L2", Kind.AC),  # 35166
        # 134 reserved
        Power("load_p3", 136, "Load L3", Kind.AC),  # 35168
        # 138 reserved
        Power("backup_ptotal", 140, "Back-up Load", Kind.UPS),  # 35170
        # 142 reserved
        Power("load_ptotal", 144, "Load", Kind.AC),  # 35172
        Integer("ups_load", 146, "Ups Load", "%", Kind.UPS),  # 35173
        Temp("temperature_air", 148, "Inverter Temperature (Air)", Kind.AC),  # 35174
        Temp("temperature_module", 150, "Inverter Temperature (Module)"),  # 35175
        Temp("temperature", 152, "Inverter Temperature (Radiator)", Kind.AC),  # 35176
        Integer("function_bit", 154, "Function Bit"),  # 35177
        Voltage("bus_voltage", 156, "Bus Voltage", None),  # 35178
        Voltage("nbus_voltage", 158, "NBus Voltage", None),  # 35179
        Voltage("vbattery1", 160, "Battery Voltage", Kind.BAT),  # 35180
        Current("ibattery1", 162, "Battery Current", Kind.BAT),  # 35181
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1",
                   lambda data: round(read_voltage(data, 160) * read_current(data, 162)),
                   "Battery Power", "W", Kind.BAT),  # 35182+35183 ?
        Integer("battery_mode", 168, "Battery Mode code", "", Kind.BAT),  # 35184
        Enum2("battery_mode_label", 168, BATTERY_MODES, "Battery Mode", Kind.BAT),
        Integer("warning_code", 170, "Warning code"),  # 35185
        Integer("safety_country", 172, "Safety Country code", "", Kind.AC),  # 35186
        Enum2("safety_country_label", 172, SAFETY_COUNTRIES, "Safety Country", Kind.AC),
        Integer("work_mode", 174, "Work Mode code"),  # 35187
        Enum2("work_mode_label", 174, WORK_MODES_ET, "Work Mode"),
        Integer("operation_mode", 176, "Operation Mode code"),  # 35188 ?
        Long("error_codes", 178, "Error Codes"),
        EnumBitmap4("errors", 178, ERROR_CODES, "Errors"),  # 35189
        Energy4("e_total", 182, "Total PV Generation", Kind.PV),  # 35190/91
        Energy4("e_day", 186, "Today's PV Generation", Kind.PV),  # 35192/93
        Energy4("e_total_exp", 190, "Total Energy (export)", Kind.AC),  # 35194/95
        Long("h_total", 194, "Hours Total", "h", Kind.PV),  # 35196/97
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
        Integer("battery_bms", 0, "Battery BMS", "", Kind.BAT),  # 37000
        Integer("battery_index", 2, "Battery Index", "", Kind.BAT),  # 37001
        Integer("battery_status", 4, "Battery Status", "", Kind.BAT),  # 37002
        Temp("battery_temperature", 6, "Battery Temperature", Kind.BAT),  # 37003
        Integer("battery_charge_limit", 8, "Battery Charge Limit", "A", Kind.BAT),  # 37004
        Integer("battery_discharge_limit", 10, "Battery Discharge Limit", "A", Kind.BAT),  # 37005
        Integer("battery_error_l", 12, "Battery Error L", "", Kind.BAT),  # 37006
        Integer("battery_soc", 14, "Battery State of Charge", "%", Kind.BAT),  # 37007
        Integer("battery_soh", 16, "Battery State of Health", "%", Kind.BAT),  # 37008
        Integer("battery_modules", 18, "Battery Modules", "", Kind.BAT),  # 37009
        Integer("battery_warning_l", 20, "Battery Warning L", "", Kind.BAT),  # 37010
        Integer("battery_protocol", 22, "Battery Protocol", "", Kind.BAT),  # 37011
        Integer("battery_error_h", 24, "Battery Error H", "", Kind.BAT),  # 37012
        EnumBitmap22("battery_error", 24, 12, BMS_ALARM_CODES, "Battery Error", Kind.BAT),
        Integer("battery_warning_h", 26, "Battery Warning H", "", Kind.BAT),  # 37013
        EnumBitmap22("battery_warning", 26, 20, BMS_WARNING_CODES, "Battery Warning", Kind.BAT),
        Integer("battery_sw_version", 28, "Battery Software Version", "", Kind.BAT),  # 37014
        Integer("battery_hw_version", 30, "Battery Hardware Version", "", Kind.BAT),  # 37015
        Integer("battery_max_cell_temp_id", 32, "Battery Max Cell Temperature ID", "", Kind.BAT),  # 37016
        Integer("battery_min_cell_temp_id", 34, "Battery Min Cell Temperature ID", "", Kind.BAT),  # 37017
        Integer("battery_max_cell_voltage_id", 36, "Battery Max Cell Voltage ID", "", Kind.BAT),  # 37018
        Integer("battery_min_cell_voltage_id", 38, "Battery Min Cell Voltage ID", "", Kind.BAT),  # 37019
        Temp("battery_max_cell_temp", 40, "Battery Max Cell Temperature", Kind.BAT),  # 37020
        Temp("battery_min_cell_temp", 42, "Battery Min Cell Temperature", Kind.BAT),  # 37021
        Voltage("battery_max_cell_voltage", 44, "Battery Max Cell Voltage", Kind.BAT),  # 37022
        Voltage("battery_min_cell_voltage", 46, "Battery Min Cell Voltage", Kind.BAT),  # 37023
        # Energy4("battery_total_charge", 112, "Total Battery 1 Charge", Kind.BAT),  #37056
        # Energy4("battery_total_discharge", 116, "Total Battery 1 Discharge", Kind.BAT),  # 37058
        # String8("battery_sn", 120, "Battery S/N", Kind.BAT),  # 37060-67
    )

    # Modbus registers from offset 0x9858 (39000)
    __all_sensors_battery2: Tuple[Sensor, ...] = (
        Integer("battery2_status", 0, "Battery 2 Status", "", Kind.BAT),  # 39000
        Temp("battery2_temperature", 2, "Battery 2 Temperature", Kind.BAT),  # 39001
        Integer("battery2_charge_limit", 4, "Battery 2 Charge Limit", "A", Kind.BAT),  # 39002
        Integer("battery2_discharge_limit", 6, "Battery 2 Discharge Limit", "A", Kind.BAT),  # 39003
        Integer("battery2_error_l", 8, "Battery 2 rror L", "", Kind.BAT),  # 39004
        Integer("battery2_soc", 10, "Battery 2 State of Charge", "%", Kind.BAT),  # 39005
        Integer("battery2_soh", 12, "Battery 2 State of Health", "%", Kind.BAT),  # 39006
        Integer("battery2_modules", 14, "Battery 2 Modules", "", Kind.BAT),  # 39007
        Integer("battery2_warning_l", 16, "Battery 2 Warning L", "", Kind.BAT),  # 39008
        Integer("battery2_protocol", 18, "Battery 2 Protocol", "", Kind.BAT),  # 39009
        Integer("battery2_error_h", 20, "Battery 2 Error H", "", Kind.BAT),  # 39010
        EnumBitmap22("battery2_error", 20, 8, BMS_ALARM_CODES, "Battery 2 Error", Kind.BAT),
        Integer("battery2_warning_h", 22, "Battery 2 Warning H", "", Kind.BAT),  # 39011
        EnumBitmap22("battery2_warning", 22, 16, BMS_WARNING_CODES, "Battery 2 Warning", Kind.BAT),
        Integer("battery2_sw_version", 24, "Battery 2 Software Version", "", Kind.BAT),  # 39012
        Integer("battery2_hw_version", 26, "Battery 2 Hardware Version", "", Kind.BAT),  # 39013
        Integer("battery2_max_cell_temp_id", 28, "Battery 2 Max Cell Temperature ID", "", Kind.BAT),  # 39014
        Integer("battery2_min_cell_temp_id", 30, "Battery 2 Min Cell Temperature ID", "", Kind.BAT),  # 39015
        Integer("battery2_max_cell_voltage_id", 32, "Battery 2 Max Cell Voltage ID", "", Kind.BAT),  # 39016
        Integer("battery2_min_cell_voltage_id", 34, "Battery 2 Min Cell Voltage ID", "", Kind.BAT),  # 39017
        Temp("battery2_max_cell_temp", 36, "Battery 2 Max Cell Temperature", Kind.BAT),  # 39018
        Temp("battery2_min_cell_temp", 38, "Battery 2 Min Cell Temperature", Kind.BAT),  # 39019
        Voltage("battery2_max_cell_voltage", 40, "Battery 2 Max Cell Voltage", Kind.BAT),  # 39020
        Voltage("battery2_min_cell_voltage", 42, "Battery 2 Min Cell Voltage", Kind.BAT),  # 39021
        # Energy4("battery2_total_charge", 108, "Total Battery 2 Charge", Kind.BAT),  #39054
        # Energy4("battery2_total_discharge", 112, "Total Battery 2 Discharge", Kind.BAT),  # 39056
        # String8("battery2_sn", 120, "Battery 2 S/N", Kind.BAT),  # 39058-65
    )

    # Inverter's meter data
    # Modbus registers from offset 0x8ca0 (36000)
    __all_sensors_meter: Tuple[Sensor, ...] = (
        Integer("commode", 0, "Commode"),  # 36000
        Integer("rssi", 2, "RSSI"),  # 36001
        Integer("manufacture_code", 4, "Manufacture Code"),  # 36002
        Integer("meter_test_status", 6, "Meter Test Status"),  # 1: correct，2: reverse，3: incorrect，0: not checked
        Integer("meter_comm_status", 8, "Meter Communication Status"),  # 36004 # 1 OK, 0 NotOK
        Power("active_power1", 10, "Active Power L1", Kind.GRID),  # 36005
        Power("active_power2", 12, "Active Power L2", Kind.GRID),  # 36006
        Power("active_power3", 14, "Active Power L3", Kind.GRID),  # 36007
        Power("active_power_total", 16, "Active Power Total", Kind.GRID),  # 36008
        Reactive("reactive_power_total", 18, "Reactive Power Total", Kind.GRID),  # 36009
        Decimal("meter_power_factor1", 20, 1000, "Meter Power Factor L1", "", Kind.GRID),  # 36010
        Decimal("meter_power_factor2", 22, 1000, "Meter Power Factor L2", "", Kind.GRID),  # 36011
        Decimal("meter_power_factor3", 24, 1000, "Meter Power Factor L3", "", Kind.GRID),  # 36012
        Decimal("meter_power_factor", 26, 1000, "Meter Power Factor", "", Kind.GRID),  # 36013
        Frequency("meter_freq", 28, "Meter Frequency", Kind.GRID),  # 36014
        Float("meter_e_total_exp", 30, 1000, "Meter Total Energy (export)", "kWh", Kind.GRID),  # 36015/16
        Float("meter_e_total_imp", 34, 1000, "Meter Total Energy (import)", "kWh", Kind.GRID),  # 36017/18
        Power4("meter_active_power1", 38, "Meter Active Power L1", Kind.GRID),  # 36019/20
        Power4("meter_active_power2", 42, "Meter Active Power L2", Kind.GRID),  # 36021/22
        Power4("meter_active_power3", 46, "Meter Active Power L3", Kind.GRID),  # 36023/24
        Power4("meter_active_power_total", 50, "Meter Active Power Total", Kind.GRID),  # 36025/26
        Reactive4("meter_reactive_power1", 54, "Meter Reactive Power L1", Kind.GRID),  # 36027/28
        Reactive4("meter_reactive_power2", 58, "Meter Reactive Power L2", Kind.GRID),  # 36029/30
        Reactive4("meter_reactive_power3", 62, "Meter Reactive Power L2", Kind.GRID),  # 36031/32
        Reactive4("meter_reactive_power_total", 66, "Meter Reactive Power Total", Kind.GRID),  # 36033/34
        Apparent4("meter_apparent_power1", 70, "Meter Apparent Power L1", Kind.GRID),  # 36035/36
        Apparent4("meter_apparent_power2", 74, "Meter Apparent Power L2", Kind.GRID),  # 36037/38
        Apparent4("meter_apparent_power3", 78, "Meter Apparent Power L3", Kind.GRID),  # 36039/40
        Apparent4("meter_apparent_power_total", 82, "Meter Apparent Power Total", Kind.GRID),  # 36041/42
        Integer("meter_type", 86, "Meter Type", "", Kind.GRID),  # 36043 (0: Single phase, 1: 3P3W, 2: 3P4W, 3: HomeKit)
        Integer("meter_sw_version", 88, "Meter Software Version", "", Kind.GRID),  # 36044
        # Sensors added in some ARM fw update
        Power4("meter2_active_power", 90, "Meter 2 Active Power", Kind.GRID),  # 36045/46
        Float("meter2_e_total_exp", 94, 1000, "Meter 2 Total Energy (export)", "kWh", Kind.GRID),  # 36047/48
        Float("meter2_e_total_imp", 98, 1000, "Meter 2 Total Energy (import)", "kWh", Kind.GRID),  # 36049/50
        Integer("meter2_comm_status", 102, "Meter 2 Communication Status"),  # 36051
        Voltage("meter_voltage1", 104, "Meter L1 Voltage", Kind.GRID),  # 36052
        Voltage("meter_voltage2", 106, "Meter L2 Voltage", Kind.GRID),  # 36053
        Voltage("meter_voltage3", 108, "Meter L3 Voltage", Kind.GRID),  # 36054
        Current("meter_current1", 110, "Meter L1 Current", Kind.GRID),  # 36055
        Current("meter_current2", 112, "Meter L2 Current", Kind.GRID),  # 36056
        Current("meter_current3", 114, "Meter L3 Current", Kind.GRID),  # 36057
    )

    # Inverter's MPPT data
    # Modbus registers from offset 0x89e5 (35301)
    __all_sensors_mptt: Tuple[Sensor, ...] = (
        Power4("ppv_total", 0, "PV Power Total", Kind.PV),  # 35301
        # 35303 PV channel RO U16 1 1 PV channel
        Voltage("vpv5", 6, "PV5 Voltage", Kind.PV),  # 35304
        Current("ipv5", 8, "PV5 Current", Kind.PV),  # 35305
        Voltage("vpv6", 10, "PV6 Voltage", Kind.PV),  # 35306
        Current("ipv6", 12, "PV6 Current", Kind.PV),  # 35307
        Voltage("vpv7", 14, "PV7 Voltage", Kind.PV),  # 35308
        Current("ipv7", 16, "PV7 Current", Kind.PV),  # 35309
        Voltage("vpv8", 18, "PV8 Voltage", Kind.PV),  # 35310
        Current("ipv8", 20, "PV8 Current", Kind.PV),  # 35311
        Voltage("vpv9", 22, "PV9 Voltage", Kind.PV),  # 35312
        Current("ipv9", 24, "PV9 Current", Kind.PV),  # 35313
        Voltage("vpv10", 26, "PV10 Voltage", Kind.PV),  # 35314
        Current("ipv10", 28, "PV10 Current", Kind.PV),  # 35315
        Voltage("vpv11", 30, "PV11 Voltage", Kind.PV),  # 35316
        Current("ipv11", 32, "PV11 Current", Kind.PV),  # 35317
        Voltage("vpv12", 34, "PV12 Voltage", Kind.PV),  # 35318
        Current("ipv12", 36, "PV12 Current", Kind.PV),  # 35319
        Voltage("vpv13", 38, "PV13 Voltage", Kind.PV),  # 35320
        Current("ipv13", 40, "PV13 Current", Kind.PV),  # 35321
        Voltage("vpv14", 42, "PV14 Voltage", Kind.PV),  # 35322
        Current("ipv14", 44, "PV14 Current", Kind.PV),  # 35323
        Voltage("vpv15", 46, "PV15 Voltage", Kind.PV),  # 35324
        Current("ipv15", 48, "PV15 Current", Kind.PV),  # 35325
        Voltage("vpv16", 50, "PV16 Voltage", Kind.PV),  # 35326
        Current("ipv16", 52, "PV16 Current", Kind.PV),  # 35327
        # 35328 Warning Message
        # 35330 Grid10minAvgVoltR
        # 35331 Grid10minAvgVoltS
        # 35332 Grid10minAvgVoltT
        # 35333 Error Message Extend
        # 35335 Warning Message Extend
        Power("pmppt1", 72, "MPPT1 Power", Kind.PV),  # 35337
        Power("pmppt2", 74, "MPPT2 Power", Kind.PV),  # 35338
        Power("pmppt3", 76, "MPPT3 Power", Kind.PV),  # 35339
        Power("pmppt4", 78, "MPPT4 Power", Kind.PV),  # 35340
        Power("pmppt5", 80, "MPPT5 Power", Kind.PV),  # 35341
        Power("pmppt6", 82, "MPPT6 Power", Kind.PV),  # 35342
        Power("pmppt7", 84, "MPPT7 Power", Kind.PV),  # 35343
        Power("pmppt8", 86, "MPPT8 Power", Kind.PV),  # 35344
        Power("imppt1", 88, "MPPT1 Current", Kind.PV),  # 35345
        Power("imppt2", 90, "MPPT2 Current", Kind.PV),  # 35346
        Power("imppt3", 92, "MPPT3 Current", Kind.PV),  # 35347
        Power("imppt4", 94, "MPPT4 Current", Kind.PV),  # 35348
        Power("imppt5", 96, "MPPT5 Current", Kind.PV),  # 35349
        Power("imppt6", 98, "MPPT6 Current", Kind.PV),  # 35350
        Power("imppt7", 100, "MPPT7 Current", Kind.PV),  # 35351
        Power("imppt8", 102, "MPPT8 Current", Kind.PV),  # 35352
        Reactive4("reactive_power1", 104, "Reactive Power L1", Kind.GRID),  # 36353/54
        Reactive4("reactive_power2", 108, "Reactive Power L2", Kind.GRID),  # 36355/56
        Reactive4("reactive_power3", 112, "Reactive Power L2", Kind.GRID),  # 36357/58
        Apparent4("apparent_power1", 116, "Apparent Power L1", Kind.GRID),  # 36359/60
        Apparent4("apparent_power2", 120, "Apparent Power L2", Kind.GRID),  # 36361/62
        Apparent4("apparent_power3", 124, "Apparent Power L3", Kind.GRID),  # 36363/64
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
        Integer("load_control_soc", 47596, "Load Control SoC", "", Kind.AC),

        Integer("fast_charging_power", 47603, "Fast Charging Power", "%", Kind.BAT),
    )

    # Settings added in ARM firmware 22
    __settings_arm_fw_22: Tuple[Sensor, ...] = (
        # EcoModeV2("eco_modeV2_5", 47571, "Eco Mode Version 2 Power Group 5"),
        # EcoModeV2("eco_modeV2_6", 47577, "Eco Mode Version 2 Power Group 6"),
        # EcoModeV2("eco_modeV2_7", 47583, "Eco Mode Version 2 Power Group 7"),
        PeakShavingMode("peak_shaving_mode", 47589, "Peak Shaving Mode"),

        Integer("dod_holding", 47602, "DoD Holding", "", Kind.BAT),
    )

    def __init__(self, host: str, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, comm_addr, timeout, retries)
        if not self.comm_addr:
            # Set the default inverter address
            self.comm_addr = 0xf7
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x88b8, 0x0021)
        self._READ_RUNNING_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x891c, 0x007d)
        self._READ_METER_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x8ca0, 0x2d)
        self._READ_METER_DATA_EXTENDED: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x8ca0, 0x3a)
        self._READ_BATTERY_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x9088, 0x0018)
        self._READ_BATTERY2_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x9858, 0x0016)
        self._READ_MPTT_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x89e5, 0x3d)
        self._has_battery: bool = True
        self._has_battery2: bool = False
        self._has_meter_extended: bool = False
        self._has_mptt: bool = False
        self._sensors = self.__all_sensors
        self._sensors_battery = self.__all_sensors_battery
        self._sensors_battery2 = self.__all_sensors_battery2
        self._sensors_meter = self.__all_sensors_meter
        self._sensors_mptt = self.__all_sensors_mptt
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

    def _supports_eco_mode_v2(self) -> bool:
        return self.arm_version >= 19

    def _supports_peak_shaving(self) -> bool:
        return self.arm_version >= 22

    @staticmethod
    def _single_phase_only(s: Sensor) -> bool:
        """Filter to exclude phase2/3 sensors on single phase inverters"""
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    @staticmethod
    def _not_extended_meter(s: Sensor) -> bool:
        """Filter to exclude extended meter sensors"""
        return s.offset < 90

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        # Modbus registers from offset (35000)
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)  # 0: 1-phase, 1: 3-phase (4 wire), 2: 3-phase (3 wire)
        self.serial_number = response[6:22].decode("ascii")
        self.model_name = self._decode(response[22:32])
        self.dsp1_version = read_unsigned_int(response, 32)
        self.dsp2_version = read_unsigned_int(response, 34)
        self.dsp_svn_version = read_unsigned_int(response, 36)
        self.arm_version = read_unsigned_int(response, 38)
        self.arm_svn_version = read_unsigned_int(response, 40)
        self.firmware = self._decode(response[42:54])
        self.arm_firmware = self._decode(response[54:66])

        if not is_4_mptt(self):
            # This inverter does not have 4th MPPTs
            self._sensors = tuple(filter(lambda s: not ('pv4' in s.id_), self._sensors))
            if not is_3_mptt(self):
                # This inverter neither has 3rd MPPTs
                self._sensors = tuple(filter(lambda s: not ('pv3' in s.id_), self._sensors))

        if is_single_phase(self):
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._single_phase_only, self._sensors))
            self._sensors_meter = tuple(filter(self._single_phase_only, self._sensors_meter))

        if is_2_battery(self) or self.rated_power >= 25000:
            self._has_battery2 = True

        if self.rated_power >= 15000:
            self._has_mptt = True
            self._has_meter_extended = True
        else:
            self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))

        if self.arm_version >= 19 or self.rated_power >= 15000:
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_19})
        if self.arm_version >= 22 or self.rated_power >= 15000:
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_22})

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self._sensors, include_unknown_sensors)

        self._has_battery = data.get('battery_mode', 0) != 0
        if self._has_battery:
            try:
                raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
                data.update(self._map_response(raw_data[5:-2], self._sensors_battery, include_unknown_sensors))
            except RequestRejectedException as ex:
                if ex.message == 'ILLEGAL DATA ADDRESS':
                    logger.warning("Cannot read battery values, disabling further attempts.")
                    self._has_battery = False
                else:
                    raise ex
        if self._has_battery2:
            try:
                raw_data = await self._read_from_socket(self._READ_BATTERY2_INFO)
                data.update(self._map_response(raw_data[5:-2], self._sensors_battery2, include_unknown_sensors))
            except RequestRejectedException as ex:
                if ex.message == 'ILLEGAL DATA ADDRESS':
                    logger.warning("Cannot read battery 2 values, disabling further attempts.")
                    self._has_battery2 = False
                else:
                    raise ex

        if self._has_meter_extended:
            try:
                raw_data = await self._read_from_socket(self._READ_METER_DATA_EXTENDED)
                data.update(self._map_response(raw_data[5:-2], self._sensors_meter, include_unknown_sensors))
            except RequestRejectedException as ex:
                if ex.message == 'ILLEGAL DATA ADDRESS':
                    logger.warning("Cannot read extended meter values, disabling further attempts.")
                    self._has_meter_extended = False
                    self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))
                    raw_data = await self._read_from_socket(self._READ_METER_DATA)
                    data.update(self._map_response(raw_data[5:-2], self._sensors_meter, include_unknown_sensors))
                else:
                    raise ex
        else:
            raw_data = await self._read_from_socket(self._READ_METER_DATA)
            data.update(self._map_response(raw_data[5:-2], self._sensors_meter, include_unknown_sensors))

        if self._has_mptt:
            try:
                raw_data = await self._read_from_socket(self._READ_MPTT_DATA)
                data.update(self._map_response(raw_data[5:-2], self._sensors_mptt, include_unknown_sensors))
            except RequestRejectedException as ex:
                if ex.message == 'ILLEGAL DATA ADDRESS':
                    logger.warning("Cannot read MPPT values, disabling further attempts.")
                    self._has_mptt = False
                else:
                    raise ex

        return data

    async def read_setting(self, setting_id: str) -> Any:
        setting = self._settings.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        count = (setting.size_ + (setting.size_ % 2)) // 2
        raw_data = await self._read_from_socket(ModbusReadCommand(self.comm_addr, setting.offset, count))
        with io.BytesIO(raw_data[5:-2]) as buffer:
            return setting.read_value(buffer)

    async def write_setting(self, setting_id: str, value: Any):
        setting = self._settings.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        if setting.size_ == 1:
            # modbus can address/store only 16 bit values, read the other 8 bytes
            register_data = await self._read_from_socket(ModbusReadCommand(self.comm_addr, setting.offset, 1))
            raw_value = setting.encode_value(value, register_data[5:7])
        else:
            raw_value = setting.encode_value(value)
        if len(raw_value) <= 2:
            value = int.from_bytes(raw_value, byteorder="big", signed=True)
            await self._read_from_socket(ModbusWriteCommand(self.comm_addr, setting.offset, value))
        else:
            await self._read_from_socket(ModbusWriteMultiCommand(self.comm_addr, setting.offset, raw_value))

    async def read_settings_data(self) -> Dict[str, Any]:
        data = {}
        for setting in self.settings():
            try:
                value = await self.read_setting(setting.id_)
                data[setting.id_] = value
            except ValueError:
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
        if not self._supports_peak_shaving():
            result.remove(OperationMode.PEAK_SHAVING)
        if not include_emulated:
            result.remove(OperationMode.ECO_CHARGE)
            result.remove(OperationMode.ECO_DISCHARGE)
        return tuple(result)

    async def get_operation_mode(self) -> OperationMode:
        mode = OperationMode(await self.read_setting('work_mode'))
        if OperationMode.ECO != mode:
            return mode
        ecomode = await self.read_setting('eco_mode_1')
        if ecomode.is_eco_charge_mode():
            return OperationMode.ECO_CHARGE
        elif ecomode.is_eco_discharge_mode():
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
            if eco_mode_soc < 0 or eco_mode_soc > 100:
                raise ValueError()
            eco_mode: EcoMode = self._convert_eco_mode(EcoModeV2("", 0, ""))
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
        if 0 <= dod <= 90:
            await self.write_setting('battery_discharge_depth', 100 - dod)

    def sensors(self) -> Tuple[Sensor, ...]:
        result = self._sensors + self._sensors_meter
        if self._has_battery:
            result = result + self._sensors_battery
        if self._has_battery2:
            result = result + self._sensors_battery2
        if self._has_mptt:
            result = result + self._sensors_mptt
        return result

    def settings(self) -> Tuple[Sensor, ...]:
        return tuple(self._settings.values())

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(ModbusWriteCommand(self.comm_addr, 0xb9ad, 1))

    async def _set_offline(self, mode: bool) -> None:
        value = bytes.fromhex('00070000') if mode else bytes.fromhex('00010000')
        await self._read_from_socket(ModbusWriteMultiCommand(self.comm_addr, 0xb997, value))

    def _convert_eco_mode(self, sensor: Sensor) -> Sensor | EcoMode:
        if EcoModeV1 == type(sensor) and self._supports_eco_mode_v2():
            return cast(EcoModeV1, sensor).as_eco_mode_v2()
        elif EcoModeV2 == type(sensor) and not self._supports_eco_mode_v2():
            return cast(EcoModeV2, sensor).as_eco_mode_v1()
        else:
            return sensor
