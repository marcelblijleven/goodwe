from typing import Any, Tuple

from goodwe.inverter import Inverter, Sensor, SensorKind
from goodwe.protocol import ProtocolCommand, ModbusProtocolCommand
from goodwe.utils import *


class ET(Inverter):
    """Class representing inverter of ET family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusProtocolCommand("F70388b80021", 73)
    _READ_DEVICE_RUNNING_DATA1: ProtocolCommand = ModbusProtocolCommand("F703891c007d", 257)
    _READ_DEVICE_RUNNING_DATA2: ProtocolCommand = ModbusProtocolCommand("F7038ca00011", 41)
    _READ_BATTERY_INFO: ProtocolCommand = ModbusProtocolCommand("F7039088000b", 29)
    _GET_WORK_MODE: ProtocolCommand = ModbusProtocolCommand("F703b7980001", 9)

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 6, read_voltage, "V", "PV1 Voltage", SensorKind.pv),
        Sensor("ipv1", 8, read_current, "A", "PV1 Current", SensorKind.pv),
        Sensor("ppv1", 10, read_power, "W", "PV1 Power", SensorKind.pv),
        Sensor("vpv2", 14, read_voltage, "V", "PV2 Voltage", SensorKind.pv),
        Sensor("ipv2", 16, read_current, "A", "PV2 Current", SensorKind.pv),
        Sensor("ppv2", 18, read_power, "W", "PV2 Power", SensorKind.pv),
        # Sensor("vpv3", 22, read_voltage, "V", "PV3 Voltage", SensorKind.pv),
        # Sensor("ipv3", 24, read_current, "A", "PV3 Current", SensorKind.pv),
        # Sensor("ppv3", 26, read_power, "W", "PV3 Power", SensorKind.pv),
        # Sensor("vpv4", 30, read_voltage, "V", "PV4 Voltage", SensorKind.pv),
        # Sensor("ipv4", 32, read_current, "A", "PV4 Current", SensorKind.pv),
        # Sensor("ppv4", 34, read_power, "W", "PV4 Power", SensorKind.pv),
        # ppv1 + ppv2 + ppv3 + ppv4
        Sensor(
            "ppv",
            0,
            lambda data, _: read_power(data, 10) + read_power(data, 18),
            "W",
            "PV Power",
            SensorKind.pv,
        ),
        Sensor("xx38", 38, read_bytes2, "", "Unknown sensor@38", None),
        Sensor("xx40", 40, read_bytes2, "", "Unknown sensor@40", None),
        Sensor("vgrid", 42, read_voltage, "V", "On-grid L1 Voltage", SensorKind.ac),
        Sensor("igrid", 44, read_current, "A", "On-grid L1 Current", SensorKind.ac),
        Sensor("fgrid", 46, read_freq, "Hz", "On-grid L1 Frequency", SensorKind.ac),
        Sensor("pgrid", 48, read_power, "W", "On-grid L1 Power", SensorKind.ac),
        Sensor("vgrid2", 52, read_voltage, "V", "On-grid L2 Voltage", SensorKind.ac),
        Sensor("igrid2", 54, read_current, "A", "On-grid L2 Current", SensorKind.ac),
        Sensor("fgrid2", 56, read_freq, "Hz", "On-grid L2 Frequency", SensorKind.ac),
        Sensor("pgrid2", 58, read_power, "W", "On-grid L2 Power", SensorKind.ac),
        Sensor("vgrid3", 62, read_voltage, "V", "On-grid L3 Voltage", SensorKind.ac),
        Sensor("igrid3", 64, read_current, "A", "On-grid L3 Current", SensorKind.ac),
        Sensor("fgrid3", 66, read_freq, "Hz", "On-grid L3 Frequency", SensorKind.ac),
        Sensor("pgrid3", 68, read_power, "W", "On-grid L3 Power", SensorKind.ac),
        Sensor("xx72", 72, read_bytes2, "", "Unknown sensor@72", None),
        Sensor(
            "total_inverter_power", 74, read_power, "W", "Total Power", SensorKind.ac
        ),
        Sensor("active_power", 78, read_power, "W", "Active Power", SensorKind.ac),
        Sensor(
            "grid_in_out", 78, read_grid_mode, "", "On-grid Mode code", SensorKind.ac
        ),
        Sensor(
            "grid_in_out_label",
            0,
            lambda data, _: GRID_MODES.get(read_grid_mode(data, 78)),
            "",
            "On-grid Mode",
            SensorKind.ac,
        ),
        Sensor("xx82", 82, read_bytes2, "", "Unknown sensor@82", None),
        Sensor("xx84", 84, read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, read_bytes2, "", "Unknown sensor@86", None),
        Sensor(
            "backup_v1", 90, read_voltage, "V", "Back-up L1 Voltage", SensorKind.ups
        ),
        Sensor(
            "backup_i1", 92, read_current, "A", "Back-up L1 Current", SensorKind.ups
        ),
        Sensor(
            "backup_f1", 94, read_freq, "Hz", "Back-up L1 Frequency", SensorKind.ups
        ),
        Sensor("xx96", 96, read_bytes2, "", "Unknown sensor@96", None),
        Sensor("backup_p1", 98, read_power, "W", "Back-up L1 Power", SensorKind.ups),
        Sensor(
            "backup_v2", 102, read_voltage, "V", "Back-up L2 Voltage", SensorKind.ups
        ),
        Sensor(
            "backup_i2", 104, read_current, "A", "Back-up L2 Current", SensorKind.ups
        ),
        Sensor(
            "backup_f2", 106, read_freq, "Hz", "Back-up L2 Frequency", SensorKind.ups
        ),
        Sensor("xx108", 108, read_bytes2, "", "Unknown sensor@108", None),
        Sensor("backup_p2", 110, read_power, "W", "Back-up L2 Power", SensorKind.ups),
        Sensor(
            "backup_v3", 114, read_voltage, "V", "Back-up L3 Voltage", SensorKind.ups
        ),
        Sensor(
            "backup_i3", 116, read_current, "A", "Back-up L3 Current", SensorKind.ups
        ),
        Sensor(
            "backup_f3", 118, read_freq, "Hz", "Back-up L3 Frequency", SensorKind.ups
        ),
        Sensor("xx120", 120, read_bytes2, "", "Unknown sensor@120", None),
        Sensor("backup_p3", 122, read_power, "W", "Back-up L3 Power", SensorKind.ups),
        Sensor("load_p1", 126, read_power, "W", "Load L1", SensorKind.ac),
        Sensor("load_p2", 130, read_power, "W", "Load L2", SensorKind.ac),
        Sensor("load_p3", 134, read_power, "W", "Load L3", SensorKind.ac),
        # load_p1 + load_p2 + load_p3
        Sensor(
            "load_ptotal",
            0,
            lambda data, _: read_power(data, 126) + read_power(data, 130) + read_power(data, 134),
            "W",
            "Load Total",
            SensorKind.ac,
        ),
        Sensor("backup_ptotal", 138, read_power, "W", "Back-up Power", SensorKind.ups),
        Sensor("pload", 142, read_power, "W", "Load", SensorKind.ac),
        Sensor("xx146", 146, read_bytes2, "", "Unknown sensor@146", None),
        Sensor(
            "temperature2",
            148,
            read_temp,
            "C",
            "Inverter Temperature 2",
            SensorKind.ac,
        ),
        Sensor("xx150", 150, read_bytes2, "", "Unknown sensor@150", None),
        Sensor(
            "temperature", 152, read_temp, "C", "Inverter Temperature", SensorKind.ac
        ),
        Sensor("xx154", 154, read_bytes2, "", "Unknown sensor@154", None),
        Sensor("xx156", 156, read_bytes2, "", "Unknown sensor@156", None),
        Sensor("xx158", 158, read_bytes2, "", "Unknown sensor@158", None),
        Sensor("vbattery1", 160, read_voltage, "V", "Battery Voltage", SensorKind.bat),
        Sensor("ibattery1", 162, read_current, "A", "Battery Current", SensorKind.bat),
        # round(vbattery1 * ibattery1),
        Sensor(
            "pbattery1",
            0,
            lambda data, _: round(read_voltage(data, 160) * read_current(data, 162)),
            "W",
            "Battery Power",
            SensorKind.bat,
        ),
        Sensor(
            "battery_mode", 168, read_bytes2, "", "Battery Mode code", SensorKind.bat
        ),
        Sensor(
            "battery_mode_label",
            168,
            read_battery_mode,
            "",
            "Battery Mode",
            SensorKind.bat,
        ),
        Sensor("xx170", 170, read_bytes2, "", "Unknown sensor@170", None),
        Sensor(
            "safety_country",
            172,
            read_bytes2,
            "",
            "Safety Country code",
            SensorKind.ac,
        ),
        Sensor(
            "safety_country_label",
            172,
            read_safety_country,
            "",
            "Safety Country",
            SensorKind.ac,
        ),
        Sensor("work_mode", 174, read_bytes2, "", "Work Mode code", None),
        Sensor("work_mode_label", 174, read_work_mode_et, "", "Work Mode", None),
        Sensor("xx176", 176, read_bytes2, "", "Unknown sensor@176", None),
        Sensor("error_codes", 178, read_bytes4, "", "Error Codes", None),
        Sensor(
            "e_total", 182, read_power_k, "kWh", "Total PV Generation", SensorKind.pv
        ),
        Sensor(
            "e_day", 186, read_power_k, "kWh", "Today's PV Generation", SensorKind.pv
        ),
        Sensor("xx190", 190, read_bytes2, "", "Unknown sensor@190", None),
        Sensor(
            "s_total",
            192,
            read_power_k2,
            "kWh",
            "Total Electricity Sold",
            SensorKind.ac,
        ),
        Sensor("h_total", 194, read_bytes4, "", "Hours Total", SensorKind.pv),
        Sensor("xx198", 198, read_bytes2, "", "Unknown sensor@198", None),
        Sensor(
            "s_day", 200, read_power_k2, "kWh", "Today Electricity Sold", SensorKind.ac
        ),
        Sensor("diagnose_result", 240, read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - active_power
        Sensor(
            "house_consumption",
            0,
            lambda data, _: read_power(data, 10) + read_power(data, 18) + round(
                read_voltage(data, 160) * read_current(data, 162)) - read_power(data, 78),
            "W",
            "House Comsumption",
            SensorKind.ac,
        ),
    )

    __sensors_battery: Tuple[Sensor, ...] = (
        Sensor("battery_bms", 0, read_bytes2, "", "Battery BMS", SensorKind.bat),
        Sensor("battery_index", 2, read_bytes2, "", "Battery Index", SensorKind.bat),
        Sensor(
            "battery_temperature",
            6,
            read_temp,
            "C",
            "Battery Temperature",
            SensorKind.bat,
        ),
        Sensor(
            "battery_charge_limit",
            8,
            read_bytes2,
            "A",
            "Battery Charge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_discharge_limit",
            10,
            read_bytes2,
            "A",
            "Battery Discharge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_status", 12, read_bytes2, "", "Battery Status", SensorKind.bat
        ),
        Sensor(
            "battery_soc",
            14,
            read_bytes2,
            "%",
            "Battery State of Charge",
            SensorKind.bat,
        ),
        Sensor(
            "battery_soh",
            16,
            read_bytes2,
            "%",
            "Battery State of Health",
            SensorKind.bat,
        ),
        Sensor(
            "battery_warning", 20, read_bytes2, "", "Battery Warning", SensorKind.bat
        ),
    )

    __sensors2: Tuple[Sensor, ...] = (
        Sensor("xxx0", 0, read_bytes2, "", "Unknown sensor2@0", None),
        Sensor("xxx2", 2, read_bytes2, "", "Unknown sensor2@2", None),
        Sensor("xxx4", 4, read_bytes2, "", "Unknown sensor2@4", None),
        Sensor("xxx6", 6, read_bytes2, "", "Unknown sensor2@6", None),
        Sensor("xxx8", 8, read_bytes2, "", "Unknown sensor2@8", None),
        Sensor("xxx10", 10, read_bytes2, "", "Unknown sensor2@10", None),
        Sensor("xxx12", 12, read_bytes2, "", "Unknown sensor2@12", None),
        Sensor("xxx14", 14, read_bytes2, "", "Unknown sensor2@14", None),
        Sensor("xxx16", 16, read_bytes2, "", "Unknown sensor2@16", None),
        Sensor("xxx18", 18, read_bytes2, "", "Unknown sensor2@18", None),
        Sensor("xxx20", 20, read_bytes2, "", "Unknown sensor2@20", None),
        Sensor("xxx22", 22, read_bytes2, "", "Unknown sensor2@22", None),
        Sensor("xxx24", 24, read_bytes2, "", "Unknown sensor2@24", None),
        Sensor("xxx26", 26, read_bytes2, "", "Unknown sensor2@26", None),
        Sensor("xxx28", 28, read_bytes2, "", "Unknown sensor2@28", None),
        Sensor("xxx30", 30, read_bytes2, "", "Unknown sensor2@30", None),
        Sensor("xxx32", 32, read_bytes2, "", "Unknown sensor2@32", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.software_version = response[54:66].decode("ascii")

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA1)
        data = self._map_response(raw_data[5:-2], self.__sensors, include_unknown_sensors)
        raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
        data.update(self._map_response(raw_data[5:-2], self.__sensors_battery, include_unknown_sensors))
        if include_unknown_sensors: # all sensors in RUNNING_DATA2 request are not yet know at the moment
            raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA2)
            data.update(self._map_response(raw_data[5:-2], self.__sensors2, include_unknown_sensors))
        return data

    async def set_work_mode(self, work_mode: int):
        if work_mode in (0, 1, 2):
            await self._read_from_socket(
                ModbusProtocolCommand("F706b798" + "{:04x}".format(work_mode))
            )

    async def set_ongrid_battery_dod(self, dod: int):
        if 0 <= dod <= 89:
            await self._read_from_socket(
                ModbusProtocolCommand("F706b12c" + "{:04x}".format(100 - dod), 10)
            )

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors + cls.__sensors_battery + cls.__sensors2
