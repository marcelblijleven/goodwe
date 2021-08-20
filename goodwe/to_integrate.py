"""The GoodWe inverter data retrieval module from Home Assistant to be integrated here"""
import asyncio
import logging
from enum import Enum
from typing import Any, Callable, NamedTuple, Tuple
from goodwe.utils import *

_LOGGER = logging.getLogger(__name__)

def _read_bytes2(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset: offset + 2], byteorder="big", signed=True)

class InverterError(Exception):
    """Indicates error communicating with inverter"""


class SensorKind(Enum):
    """Enumeration of sensor kinds"""

    pv = 1
    ac = 2
    ups = 3
    bat = 4


class Sensor(NamedTuple):
    """Definition of inverter sensor and its attributes"""

    id: str
    offset: int
    getter: Callable[[io.BytesIO, int], Any]
    unit: str
    name: str
    kind: Optional[SensorKind]


class _UdpInverterProtocol(asyncio.DatagramProtocol):
    def __init__(
            self,
            request: bytes,
            validator: Callable[[bytes], bool],
            on_response_received: asyncio.futures.Future,
            timeout: int = 2,
            retries: int = 3
    ):
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator
        self.on_response_received: asyncio.futures.Future = on_response_received
        self.transport: asyncio.transports.DatagramTransport
        self.timeout: int = timeout
        self.retries: int = retries
        self.retry_nr: int = 1

    def connection_made(self, transport: asyncio.transports.DatagramTransport):
        self.transport = transport
        _LOGGER.debug("Send: '%s'", self.request.hex())
        self.transport.sendto(self.request)
        asyncio.get_event_loop().call_later(self.timeout, self._timeout_heartbeat)

    def connection_lost(self, exc: Exception):
        if exc is not None:
            _LOGGER.debug("Socket closed with error: '%s'", exc)
        if not self.on_response_received.done():
            self.on_response_received.cancel()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        _LOGGER.debug("Received: '%s'", data.hex())
        if self.validator(data):
            self.on_response_received.set_result(data)
            self.transport.close()
        else:
            _LOGGER.debug(
                "Invalid response length: %d",
                len(data),
            )
            self.retry_nr += 1
            self.connection_made(self.transport)

    def error_received(self, exc: Exception):
        _LOGGER.debug("Received error: '%s'", exc)

    def _timeout_heartbeat(self):
        if self.on_response_received.done():
            self.transport.close()
        elif self.retry_nr <= self.retries:
            _LOGGER.debug("Re-try #%d", self.retry_nr)
            self.retry_nr += 1
            self.connection_made(self.transport)
        else:
            _LOGGER.debug("Re-try #%d, closing socket", self.retry_nr)
            self.transport.close()


class ProtocolCommand:
    """Definition of inverter protocol command"""

    def __init__(self, request: bytes, validator: Callable[[bytes], bool]):
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator

    async def execute(self, host: str, port: int, timeout: int = 2, retries: int = 3) -> bytes:
        """
        Execute the udp protocol command on the specified address/port.
        Since the UDP communication is by definition unreliable, when no (valid) response is received by specified
        timeout, the command will be re-tried up to retries times.

        Return raw response data
        """
        loop = asyncio.get_running_loop()
        on_response_received = loop.create_future()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpInverterProtocol(
                self.request, self.validator, on_response_received, timeout, retries
            ),
            remote_addr=(host, port),
        )
        try:
            await on_response_received
            result = on_response_received.result()
            if result is not None:
                return result
            else:
                raise InverterError(
                    "No response received to '" + self.request.hex() + "' request"
                )
        except asyncio.CancelledError:
            raise InverterError(
                "No valid response received to '" + self.request.hex() + "' request"
            ) from None
        finally:
            transport.close()


class Aa55ProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol based on 0xAA,0x55 kinds of commands.
    Each comand starts with header of 0xAA, 0x55, 0xC0, 0x7F followed by payload data.
    It is suffixed with 2 bytes of plain checksum of header+payload.
    """

    def __init__(self, payload: str, response_type: str):
        super().__init__(
            bytes.fromhex(
                "AA55C07F"
                + payload
                + self._checksum(bytes.fromhex("AA55C07F" + payload)).hex()
            ),
            lambda x: self._validate_response(x, response_type),
        )

    @staticmethod
    def _checksum(data: bytes) -> bytes:
        checksum = 0
        for each in data:
            checksum += each
        return checksum.to_bytes(2, byteorder="big", signed=False)

    @staticmethod
    def _validate_response(data: bytes, response_type: str) -> bool:
        """
        Validate the response.
        data[0:3] is header
        data[4:5] is response type
        data[6] is response payload length
        data[-2:] is checksum (plain sum of response data incl. header)
        """
        if (
                len(data) <= 8
                or len(data) != data[6] + 9
                or (response_type and int(response_type, 16) != _read_bytes2(data[4:6], 0))
        ):
            return False
        else:
            checksum = 0
            for each in data[:-2]:
                checksum += each
            return checksum == _read_bytes2(data[-2:], 0)


class ModbusProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol, suffixes each payload with 2 bytes of Modbus-CRC16 checksum of the payload.
    """

    _CRC_16_TABLE = create_crc16_table()

    def __init__(self, payload: str, response_len: int = 0):
        super().__init__(
            bytes.fromhex(
                payload + self._checksum(bytes.fromhex(payload))
            ),
            lambda x: self._validate_response(x, response_len),
        )

    @classmethod
    def _checksum(cls, data: bytes) -> str:
        crc = 0xFFFF
        for ch in data:
            crc = (crc >> 8) ^ cls._CRC_16_TABLE[(crc ^ ch) & 0xFF]
        res = "{:04x}".format(crc)
        return res[2:] + res[:2]

    @classmethod
    def _validate_response(cls, data: bytes, response_len: int) -> bool:
        """
        Validate the response.
        data[0:1] is header
        data[2:3] is response type
        data[4] is response payload length ??
        data[-2:] is crc-16 checksum
        """
        if len(data) <= 4 or (response_len != 0 and response_len != len(data)):
            return False
        return cls._checksum(data[2:-2]) == data[-2:].hex()


class Inverter:
    """
    Common superclass for various inverter models implementations.
    Represents the inverter state and its basic behavior
    """

    def __init__(
            self,
            host: str,
            port: int,
            timeout: int = 2,
            retries: int = 3,
            model_name: str = "",
            serial_number: str = "",
            software_version: str = "",
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.model_name = model_name
        self.serial_number = serial_number
        self.software_version = software_version

    async def _read_from_socket(self, command: ProtocolCommand) -> bytes:
        return await command.execute(self.host, self.port, self.timeout, self.retries)

    async def read_device_info(self):
        """
        Request the device information from the inverter.
        The inverter instance variables will be loaded with relevant data.
        """
        raise NotImplementedError()

    async def read_runtime_data(self) -> Dict[str, Any]:
        """
        Request the runtime data from the inverter.
        Answer dictionary of individual sensors and their values.
        List of supported sensors (and their definitions) is provided by sensors() method.
        """
        raise NotImplementedError()

    async def read_settings_data(self) -> Dict[str, Any]:
        """
        Request the settings data from the inverter.
        Answer dictionary of individual settings and their values.
        List of supported settings (and their definitions) is provided by settings() method.
        """
        raise NotImplementedError()

    async def send_command(
            self, command: str, validator: Callable[[bytes], bool] = lambda x: True
    ) -> str:
        """
        Send low level udp command (in hex).
        Answer command's raw response data (in hex).
        """
        response = await self._read_from_socket(
            ProtocolCommand(bytes.fromhex(command), validator)
        )
        return response.hex()

    async def send_aa55_command(self, payload: str, response_type: str = "") -> str:
        """
        Send low level udp AA55 type command (payload in hex).
        Answer command's raw response data (in hex).
        """
        response = await self._read_from_socket(
            Aa55ProtocolCommand(payload, response_type)
        )
        return response.hex()

    async def set_work_mode(self, work_mode: int):
        """
        BEWARE !!!
        This method modifies inverter operational parameter accessible to installers only.
        Use with caution and at your own risk !

        Set the inverter work mode
        0 - General mode
        1 - Off grid mode
        2 - Backup mode
        """
        raise NotImplementedError()

    async def set_ongrid_battery_dod(self, ongrid_battery_dod: int):
        """
        BEWARE !!!
        This method modifies On-Grid Battery DoD parameter accessible to installers only.
        Use with caution and at your own risk !

        Set the On-Grid Battery DoD
        0% - 89%
        """
        raise NotImplementedError()

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        """
        Return tuple of sensor definitions
        """
        raise NotImplementedError()

    @classmethod
    def settings(cls) -> Tuple[Sensor, ...]:
        """
        Return tuple of settings definitions
        """
        raise NotImplementedError()

    @staticmethod
    def _map_response(resp_data: bytes, sensors: Tuple[Sensor, ...]) -> Dict[str, Any]:
        """Process the response data and return dictionary with runtime values"""
        with io.BytesIO(resp_data) as buffer:
            return {
                sensor_id: fn(buffer, offset)
                for (sensor_id, offset, fn, _, name, _) in sensors
            }


async def search_inverters() -> bytes:
    """Scan the network for inverters

    Raise InverterError if unable to contact any inverter
    """
    _LOGGER.debug("Searching inverters by broadcast to port 48899")
    loop = asyncio.get_running_loop()
    on_response_received = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _UdpInverterProtocol(
            "WIFIKIT-214028-READ".encode("utf-8"),
            lambda r: True,
            on_response_received,
        ),
        remote_addr=("255.255.255.255", 48899),
        allow_broadcast=True,
    )
    try:
        await on_response_received
        result = on_response_received.result()
        if result is not None:
            return result
        else:
            raise InverterError("No response received to broadcast request")
    except asyncio.CancelledError:
        raise InverterError("No valid response received to broadcast request") from None
    finally:
        transport.close()


async def discover(host: str, port: int = 8899, timeout: int = 2, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified value and answer appropriate Inverter instance

    Raise InverterError if unable to contact or recognise supported inverter
    """
    failures = []

    if ET in REGISTRY or ES in REGISTRY or EH in REGISTRY:
        # Try the common AA55C07F0102000241 command first and detect inverter type from serial_number
        try:
            _LOGGER.debug("Probing inverter at %s:%s", host, port)
            response = await Aa55ProtocolCommand("010200", "0182").execute(host, port, timeout, retries)
            model_name = response[12:22].decode("ascii").rstrip()
            serial_number = response[38:54].decode("ascii")
            if "ETU" in serial_number:
                software_version = response[71:83].decode("ascii").strip()
                _LOGGER.debug("Detected ET inverter %s, S/N:%s", model_name, serial_number)
                return ET(host, port, timeout, retries, model_name, serial_number, software_version)
            elif "ESU" in serial_number:  # TODO: check if ESU is indeed in the seriual number
                software_version = response[58:70].decode("ascii").strip()
                # arm_version = response[71:83].decode("ascii").strip()
                _LOGGER.debug("Detected ES inverter %s, S/N:%s", model_name, serial_number)
                return ES(host, port, timeout, retries, model_name, serial_number, software_version)
            elif "EHU" in serial_number:  # TODO: check if version is correct
                software_version = response[54:66].decode("ascii")
                _LOGGER.debug("Detected EH inverter %s, S/N:%s", model_name, serial_number)
                return EH(host, port, timeout, retries, model_name, serial_number, software_version)
        except InverterError as ex:
            failures.append(ex)

    # Probe inverter specific protocols
    for inverter in REGISTRY:
        i = inverter(host, port, timeout, retries)
        try:
            _LOGGER.debug("Probing %s inverter at %s:%s", inverter.__name__, host, port)
            await i.read_device_info()
            _LOGGER.debug(
                "Detected %s protocol inverter %s, S/N:%s",
                inverter.__name__,
                i.model_name,
                i.serial_number,
            )
            return i
        except InverterError as ex:
            failures.append(ex)
    raise InverterError(
        "Unable to connect to the inverter at "
        f"host={host} port={port}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )


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
            lambda data, _: read_power(data, 126)
                            + read_power(data, 130)
                            + read_power(data, 134),
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
            lambda data, _: read_power(data, 10)
                            + read_power(data, 18)
                            + round(read_voltage(data, 160) * read_current(data, 162))
                            - read_power(data, 78),
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

    async def read_runtime_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA1)
        data = self._map_response(raw_data[5:-2], self.__sensors)
        raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
        data.update(self._map_response(raw_data[5:-2], self.__sensors_battery))
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA2)
        data.update(self._map_response(raw_data[5:-2], self.__sensors2))
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


class ES(Inverter):
    """Class representing inverter of ES/EM family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = Aa55ProtocolCommand("010200", "0182")
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = Aa55ProtocolCommand("010600", "0186")
    _READ_DEVICE_SETTINGS_DATA: ProtocolCommand = Aa55ProtocolCommand("010900", "0189")

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 0, read_voltage, "V", "PV1 Voltage", SensorKind.pv),
        Sensor("ipv1", 2, read_current, "A", "PV1 Current", SensorKind.pv),
        Sensor(
            "ppv1",
            0,
            lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)),
            "W",
            "PV1 Power",
            SensorKind.pv,
        ),
        Sensor("pv1_mode", 4, read_byte, "", "PV1 Mode", SensorKind.pv),
        Sensor("pv1_mode_label", 4, read_pv_mode1, "", "PV1 Mode", SensorKind.pv),
        Sensor("vpv2", 5, read_voltage, "V", "PV2 Voltage", SensorKind.pv),
        Sensor("ipv2", 7, read_current, "A", "PV2 Current", SensorKind.pv),
        Sensor(
            "ppv2",
            0,
            lambda data, _: round(read_voltage(data, 5) * read_current(data, 7)),
            "W",
            "PV2 Power",
            SensorKind.pv,
        ),
        Sensor("pv2_mode", 9, read_byte, "", "PV2 Mode", SensorKind.pv),
        Sensor("pv2_mode_label", 9, read_pv_mode1, "", "PV2 Mode", SensorKind.pv),
        Sensor(
            "ppv",
            0,
            lambda data, _: round(read_voltage(data, 0) * read_current(data, 2))
                            + round(read_voltage(data, 5) * read_current(data, 7)),
            "W",
            "PV Power",
            SensorKind.pv,
        ),
        Sensor("vbattery1", 10, read_voltage, "V", "Battery Voltage", SensorKind.bat),
        # Sensor("vbattery2", 12, read_voltage, "V", "Battery Voltage 2", SensorKind.bat),
        # Sensor("vbattery3", 14, read_voltage, "V", "Battery Voltage 3", SensorKind.bat),
        Sensor(
            "battery_temperature",
            16,
            read_temp,
            "C",
            "Battery Temperature",
            SensorKind.bat,
        ),
        Sensor(
            "ibattery1",
            18,
            lambda data, _: abs(read_current(data, 18))
                            * (-1 if read_byte(data, 30) == 3 else 1),
            "A",
            "Battery Current",
            SensorKind.bat,
        ),
        # round(vbattery1 * ibattery1),
        Sensor(
            "pbattery1",
            0,
            lambda data, _: abs(
                round(read_voltage(data, 10) * read_current(data, 18))
            )
                            * (-1 if read_byte(data, 30) == 3 else 1),
            "W",
            "Battery Power",
            SensorKind.bat,
        ),
        Sensor(
            "battery_charge_limit",
            20,
            read_bytes2,
            "A",
            "Battery Charge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_discharge_limit",
            22,
            read_bytes2,
            "A",
            "Battery Discharge Limit",
            SensorKind.bat,
        ),
        Sensor(
            "battery_status", 24, read_bytes2, "", "Battery Status", SensorKind.bat
        ),
        Sensor(
            "battery_soc",
            26,
            read_byte,
            "%",
            "Battery State of Charge",
            SensorKind.bat,
        ),
        # Sensor("cbattery2", 27, read_byte, "%", "Battery State of Charge 2", SensorKind.bat),
        # Sensor("cbattery3", 28, read_byte, "%", "Battery State of Charge 3", SensorKind.bat),
        Sensor(
            "battery_soh",
            29,
            read_byte,
            "%",
            "Battery State of Health",
            SensorKind.bat,
        ),
        Sensor("battery_mode", 30, read_byte, "", "Battery Mode code", SensorKind.bat),
        Sensor(
            "battery_mode_label",
            30,
            read_battery_mode1,
            "",
            "Battery Mode",
            SensorKind.bat,
        ),
        Sensor(
            "battery_warning", 31, read_bytes2, "", "Battery Warning", SensorKind.bat
        ),
        Sensor("meter_status", 33, read_byte, "", "Meter Status code", SensorKind.ac),
        Sensor("vgrid", 34, read_voltage, "V", "On-grid Voltage", SensorKind.ac),
        Sensor("igrid", 36, read_current, "A", "On-grid Current", SensorKind.ac),
        Sensor(
            "pgrid",
            38,
            lambda data, _: abs(read_power2(data, 38))
                            * (-1 if read_byte(data, 80) == 2 else 1),
            "W",
            "On-grid Export Power",
            SensorKind.ac,
        ),
        Sensor("fgrid", 40, read_freq, "Hz", "On-grid Frequency", SensorKind.ac),
        Sensor("grid_mode", 42, read_byte, "", "Work Mode code", SensorKind.ac),
        Sensor("grid_mode_label", 42, read_work_mode1, "", "Work Mode", SensorKind.ac),
        Sensor("vload", 43, read_voltage, "V", "Back-up Voltage", SensorKind.ups),
        Sensor("iload", 45, read_current, "A", "Back-up Current", SensorKind.ups),
        Sensor("pload", 47, read_power2, "W", "On-grid Power", SensorKind.ac),
        Sensor("fload", 49, read_freq, "Hz", "Back-up Frequency", SensorKind.ups),
        Sensor("load_mode", 51, read_byte, "", "Load Mode code", SensorKind.ac),
        Sensor("load_mode_label", 51, read_load_mode1, "", "Load Mode", SensorKind.ac),
        Sensor("work_mode", 52, read_byte, "", "Energy Mode code", SensorKind.ac),
        Sensor(
            "work_mode_label", 52, read_energy_mode1, "", "Energy Mode", SensorKind.ac
        ),
        Sensor("temperature", 53, read_temp, "C", "Inverter Temperature", None),
        Sensor("error_codes", 55, read_bytes4, "", "Error Codes", None),
        Sensor(
            "e_total", 59, read_power_k, "kWh", "Total PV Generation", SensorKind.pv
        ),
        Sensor("h_total", 63, read_bytes4, "", "Hours Total", SensorKind.pv),
        Sensor(
            "e_day", 67, read_power_k2, "kWh", "Today's PV Generation", SensorKind.pv
        ),
        Sensor("e_load_day", 69, read_power_k2, "kWh", "Today's Load", None),
        Sensor("e_load_total", 71, read_power_k, "kWh", "Total Load", None),
        Sensor("total_power", 75, read_power2, "W", "Total Power", None),
        Sensor(
            "effective_work_mode", 77, read_byte, "", "Effective Work Mode code", None
        ),
        # Effective relay control 78-79
        Sensor("grid_in_out", 80, read_byte, "", "On-grid Mode code", SensorKind.ac),
        Sensor(
            "grid_in_out_label",
            0,
            lambda data, _: GRID_MODES.get(read_byte(data, 80)),
            "",
            "On-grid Mode",
            SensorKind.ac,
        ),
        Sensor("pback_up", 81, read_power2, "W", "Back-up Power", SensorKind.ups),
        # pload + pback_up
        Sensor(
            "plant_power",
            0,
            lambda data, _: round(read_power2(data, 47) + read_power2(data, 81)),
            "W",
            "Plant Power",
            SensorKind.ac,
        ),
        Sensor("diagnose_result", 89, read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - pgrid
        Sensor(
            "house_consumption",
            0,
            lambda data, _: round(read_voltage(data, 0) * read_current(data, 2))
                            + round(read_voltage(data, 5) * read_current(data, 7))
                            + (
                                    abs(round(read_voltage(data, 10) * read_current(data, 18)))
                                    * (-1 if read_byte(data, 30) == 3 else 1)
                            )
                            - (abs(read_power2(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1)),
            "W",
            "House Comsumption",
            SensorKind.ac,
        ),
    )

    __settings: Tuple[Sensor, ...] = (
        Sensor(
            "charge_power_limit", 4, read_bytes2, "", "Charge Power Limit Value", None
        ),
        Sensor(
            "discharge_power_limit",
            10,
            read_bytes2,
            "",
            "Disharge Power Limit Value",
            None,
        ),
        Sensor("relay_control", 13, read_byte, "", "Relay Control", None),
        Sensor("off-grid_charge", 15, read_byte, "", "Off-grid Charge", None),
        Sensor("shadow_scan", 17, read_byte, "", "Shadow Scan", None),
        Sensor("backflow_state", 18, read_bytes2, "", "Backflow State", None),
        Sensor("capacity", 22, read_bytes2, "", "Capacity", None),
        Sensor("charge_v", 24, read_bytes2, "V", "Charge Voltage", None),
        Sensor("charge_i", 26, read_bytes2, "A", "Charge Current", None),
        Sensor("discharge_i", 28, read_bytes2, "A", "Discharge Current", None),
        Sensor("discharge_v", 30, read_bytes2, "V", "Discharge Voltage", None),
        Sensor(
            "dod",
            32,
            lambda data, _: 100 - read_bytes2(data, 32),
            "%",
            "Depth of Discharge",
            None,
        ),
        Sensor("battery_activated", 34, read_bytes2, "", "Battery Activated", None),
        Sensor("bp_off_grid_charge", 36, read_bytes2, "", "BP Off-grid Charge", None),
        Sensor("bp_pv_discharge", 38, read_bytes2, "", "BP PV Discharge", None),
        Sensor("bp_bms_protocol", 40, read_bytes2, "", "BP BMS Protocol", None),
        Sensor("power_factor", 42, read_bytes2, "", "Power Factor", None),
        Sensor("grid_up_limit", 52, read_bytes2, "", "Grid Up Limit", None),
        Sensor("soc_protect", 56, read_bytes2, "", "SoC Protect", None),
        Sensor("work_mode", 66, read_bytes2, "", "Work Mode", None),
        Sensor("grid_quality_check", 68, read_bytes2, "", "Grid Quality Check", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        self.model_name = response[12:22].decode("ascii").rstrip()
        self.serial_number = response[38:54].decode("ascii")
        self.software_version = response[58:70].decode("ascii")

    async def read_runtime_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[7:-2], self.__sensors)
        return data

    async def read_settings_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_SETTINGS_DATA)
        data = self._map_response(raw_data[7:-2], self.__settings)
        return data

    async def set_work_mode(self, work_mode: int):
        if work_mode in (0, 1, 2):
            await self._read_from_socket(
                Aa55ProtocolCommand("035901" + "{:02x}".format(work_mode), "03D9")
            )

    async def set_ongrid_battery_dod(self, dod: int):
        if 0 <= dod <= 89:
            await self._read_from_socket(
                Aa55ProtocolCommand("023905056001" + "{:04x}".format(100 - dod), "02b9")
            )

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors

    @classmethod
    def settings(cls) -> Tuple[Sensor, ...]:
        return cls.__settings


class DT(Inverter):
    """Class representing inverter of DT family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusProtocolCommand("7F0375310028", 87)
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = ModbusProtocolCommand("7F0375940049", 153)

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 6, read_voltage, "V", "PV1 Voltage", SensorKind.pv),
        Sensor("ipv1", 8, read_current, "A", "PV1 Current", SensorKind.pv),
        Sensor(
            "ppv1",
            0,
            lambda data, _: round(read_voltage(data, 6) * read_current(data, 8)),
            "W",
            "PV1 Power",
            SensorKind.pv,
        ),
        Sensor("vpv2", 10, read_voltage, "V", "PV2 Voltage", SensorKind.pv),
        Sensor("ipv2", 12, read_current, "A", "PV2 Current", SensorKind.pv),
        Sensor(
            "ppv2",
            0,
            lambda data, _: round(read_voltage(data, 10) * read_current(data, 12)),
            "W",
            "PV2 Power",
            SensorKind.pv,
        ),
        Sensor("xx14", 14, read_bytes2, "", "Unknown sensor@14", None),
        Sensor("xx16", 16, read_bytes2, "", "Unknown sensor@16", None),
        Sensor("xx18", 18, read_bytes2, "", "Unknown sensor@18", None),
        Sensor("xx20", 20, read_bytes2, "", "Unknown sensor@20", None),
        Sensor("xx22", 22, read_bytes2, "", "Unknown sensor@22", None),
        Sensor("xx24", 24, read_bytes2, "", "Unknown sensor@24", None),
        Sensor("xx26", 26, read_bytes2, "", "Unknown sensor@26", None),
        Sensor("xx28", 28, read_bytes2, "", "Unknown sensor@28", None),
        Sensor("vline1", 30, read_voltage, "V", "On-grid L1-L2 Voltage", SensorKind.ac),
        Sensor("vline2", 32, read_voltage, "V", "On-grid L2-L3 Voltage", SensorKind.ac),
        Sensor("vline3", 34, read_voltage, "V", "On-grid L3-L1 Voltage", SensorKind.ac),
        Sensor("vgrid1", 36, read_voltage, "V", "On-grid L1 Voltage", SensorKind.ac),
        Sensor("vgrid2", 38, read_voltage, "V", "On-grid L2 Voltage", SensorKind.ac),
        Sensor("vgrid3", 40, read_voltage, "V", "On-grid L3 Voltage", SensorKind.ac),
        Sensor("igrid1", 42, read_current, "A", "On-grid L1 Current", SensorKind.ac),
        Sensor("igrid2", 44, read_current, "A", "On-grid L2 Current", SensorKind.ac),
        Sensor("igrid3", 46, read_current, "A", "On-grid L3 Current", SensorKind.ac),
        Sensor("fgrid1", 48, read_freq, "Hz", "On-grid L1 Frequency", SensorKind.ac),
        Sensor("fgrid2", 50, read_freq, "Hz", "On-grid L2 Frequency", SensorKind.ac),
        Sensor("fgrid3", 52, read_freq, "Hz", "On-grid L3 Frequency", SensorKind.ac),
        Sensor(
            "pgrid1",
            0,
            lambda data, _: round(read_voltage(data, 36) * read_current(data, 42)),
            "W",
            "On-grid L1 Power",
            SensorKind.ac,
        ),
        Sensor(
            "pgrid2",
            0,
            lambda data, _: round(read_voltage(data, 38) * read_current(data, 44)),
            "W",
            "On-grid L2 Power",
            SensorKind.ac,
        ),
        Sensor(
            "pgrid3",
            0,
            lambda data, _: round(read_voltage(data, 40) * read_current(data, 46)),
            "W",
            "On-grid L3 Power",
            SensorKind.ac,
        ),
        Sensor("xx54", 54, read_bytes2, "", "Unknown sensor@54", None),
        Sensor("ppv", 56, read_power2, "W", "PV Power", SensorKind.pv),
        Sensor("work_mode", 58, read_bytes2, "", "Work Mode code", None),
        Sensor("work_mode_label", 58, read_work_mode_dt, "", "Work Mode", None),
        Sensor("xx60", 60, read_bytes2, "", "Unknown sensor@60", None),
        Sensor("xx62", 62, read_bytes2, "", "Unknown sensor@62", None),
        Sensor("xx64", 64, read_bytes2, "", "Unknown sensor@64", None),
        Sensor("xx66", 66, read_bytes2, "", "Unknown sensor@66", None),
        Sensor("xx68", 68, read_bytes2, "", "Unknown sensor@68", None),
        Sensor("xx70", 70, read_bytes2, "", "Unknown sensor@70", None),
        Sensor("xx72", 72, read_bytes2, "", "Unknown sensor@72", None),
        Sensor("xx74", 74, read_bytes2, "", "Unknown sensor@74", None),
        Sensor("xx76", 76, read_bytes2, "", "Unknown sensor@76", None),
        Sensor("xx78", 78, read_bytes2, "", "Unknown sensor@78", None),
        Sensor("xx80", 80, read_bytes2, "", "Unknown sensor@80", None),
        Sensor("temperature", 82, read_temp, "C", "Inverter Temperature", SensorKind.ac),
        Sensor("xx84", 84, read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, read_bytes2, "", "Unknown sensor@86", None),
        Sensor("e_day", 88, read_power_k2, "kWh", "Today's PV Generation", SensorKind.pv),
        Sensor("xx90", 90, read_bytes2, "", "Unknown sensor@90", None),
        Sensor("e_total", 92, read_power_k2, "kWh", "Total PV Generation", SensorKind.pv),
        Sensor("xx94", 94, read_bytes2, "", "Unknown sensor@94", None),
        Sensor("h_total", 96, read_bytes2, "", "Hours Total", SensorKind.pv),
        Sensor(
            "safety_country",
            98,
            read_bytes2,
            "",
            "Safety Country code",
            SensorKind.ac,
        ),
        Sensor(
            "safety_country_label",
            98,
            read_safety_country,
            "",
            "Safety Country",
            SensorKind.ac,
        ),
        Sensor("xx100", 100, read_bytes2, "", "Unknown sensor@100", None),
        Sensor("xx102", 102, read_bytes2, "", "Unknown sensor@102", None),
        Sensor("xx104", 104, read_bytes2, "", "Unknown sensor@104", None),
        Sensor("xx106", 106, read_bytes2, "", "Unknown sensor@106", None),
        Sensor("xx108", 108, read_bytes2, "", "Unknown sensor@108", None),
        Sensor("xx110", 110, read_bytes2, "", "Unknown sensor@110", None),
        Sensor("xx112", 112, read_bytes2, "", "Unknown sensor@112", None),
        Sensor("xx114", 114, read_bytes2, "", "Unknown sensor@114", None),
        Sensor("xx116", 116, read_bytes2, "", "Unknown sensor@116", None),
        Sensor("xx118", 118, read_bytes2, "", "Unknown sensor@118", None),
        Sensor("xx120", 120, read_bytes2, "", "Unknown sensor@120", None),
        Sensor("xx122", 122, read_bytes2, "", "Unknown sensor@122", None),
        Sensor("funbit", 124, read_bytes2, "", "FunBit", SensorKind.pv),
        Sensor("vbus", 126, read_voltage, "V", "Bus Voltage", SensorKind.pv),
        Sensor("vnbus", 128, read_voltage, "V", "NBus Voltage", SensorKind.pv),
        Sensor("xx130", 130, read_bytes2, "", "Unknown sensor@130", None),
        Sensor("xx132", 132, read_bytes2, "", "Unknown sensor@132", None),
        Sensor("xx134", 134, read_bytes2, "", "Unknown sensor@134", None),
        Sensor("xx136", 136, read_bytes2, "", "Unknown sensor@136", None),
        Sensor("xx138", 138, read_bytes2, "", "Unknown sensor@138", None),
        Sensor("xx140", 140, read_bytes2, "", "Unknown sensor@140", None),
        Sensor("xx142", 142, read_bytes2, "", "Unknown sensor@142", None),
        Sensor("xx144", 144, read_bytes2, "", "Unknown sensor@144", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.software_version = "{}.{}.{:02x}".format(
            int.from_bytes(response[66:68], byteorder='big'),
            int.from_bytes(response[68:70], byteorder='big'),
            int.from_bytes(response[70:72], byteorder='big'),
        )

    async def read_runtime_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self.__sensors)

        return data

    async def set_ongrid_battery_dod(self, dod: int):
        pass

    async def set_work_mode(self, work_mode: int):
        if work_mode == 0:
            await self._read_from_socket(
                ModbusProtocolCommand("7F069D8B0000")
            )
        elif work_mode == 3:
            await self._read_from_socket(
                ModbusProtocolCommand("7F069D8A0000")
            )

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors


class EH(Inverter):
    """Class representing inverter of EH family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusProtocolCommand("F70388b800213AC1", 146)
    _READ_DEVICE_RUNNING_DATA1: ProtocolCommand = ModbusProtocolCommand("F703891c007d7ae7", 257)
    _READ_DEVICE_RUNNING_DATA2: ProtocolCommand = ModbusProtocolCommand("F7038ca0001b3be5", 61)
    _READ_BATTERY_INFO: ProtocolCommand = ModbusProtocolCommand("F7039088000bbdb1", 29)
    _GET_WORK_MODE: ProtocolCommand = ModbusProtocolCommand("F703b798000136c7", 9)

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
        Sensor("ppv", 0, lambda data, _: read_power(data, 10) + read_power(data, 18), "W", "PV Power",
               SensorKind.pv, ),
        Sensor("xx38", 38, read_bytes2, "", "Unknown sensor@38", None),
        Sensor("xx40", 40, read_bytes2, "", "Unknown sensor@40", None),
        Sensor("vgrid", 42, read_voltage, "V", "On-grid L1 Voltage", SensorKind.ac),
        Sensor("igrid", 44, read_current, "A", "On-grid L1 Current", SensorKind.ac),
        Sensor("fgrid", 46, read_freq, "Hz", "On-grid L1 Frequency", SensorKind.ac),
        Sensor("pgrid", 48, read_power, "W", "On-grid L1 Power", SensorKind.ac),
        # Sensor("vgrid2", 52, read_voltage, "V", "On-grid L2 Voltage", SensorKind.ac),
        # Sensor("igrid2", 54, read_current, "A", "On-grid L2 Current", SensorKind.ac),
        # Sensor("fgrid2", 56, read_freq, "Hz", "On-grid L2 Frequency", SensorKind.ac),
        # Sensor("pgrid2", 58, read_power, "W", "On-grid L2 Power", SensorKind.ac),
        # Sensor("vgrid3", 62, read_voltage, "V", "On-grid L3 Voltage", SensorKind.ac),
        # Sensor("igrid3", 64, read_current, "A", "On-grid L3 Current", SensorKind.ac),
        # Sensor("fgrid3", 66, read_freq, "Hz", "On-grid L3 Frequency", SensorKind.ac),
        # Sensor("pgrid3", 68, read_power, "W", "On-grid L3 Power", SensorKind.ac),
        Sensor("xx72", 72, read_bytes2, "", "Unknown sensor@72", None),
        Sensor("total_inverter_power", 74, read_power, "W", "Total Power", SensorKind.ac),
        Sensor("active_power", 78, read_power, "W", "Active Power", SensorKind.ac),
        Sensor("grid_in_out", 78, read_grid_mode, "", "On-grid Mode code", SensorKind.ac),
        Sensor("grid_in_out_label", 0, lambda data, _: GRID_MODES.get(read_grid_mode(data, 78)), "", "On-grid Mode",
               SensorKind.ac, ),
        Sensor("xx82", 82, read_bytes2, "", "Unknown sensor@82", None),
        Sensor("xx84", 84, read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, read_bytes2, "", "Unknown sensor@86", None),
        Sensor("backup_v1", 90, read_voltage, "V", "Back-up L1 Voltage", SensorKind.ups),
        Sensor("backup_i1", 92, read_current, "A", "Back-up L1 Current", SensorKind.ups),
        Sensor("backup_f1", 94, read_freq, "Hz", "Back-up L1 Frequency", SensorKind.ups),
        Sensor("xx96", 96, read_bytes2, "", "Unknown sensor@96", None),
        Sensor("backup_p1", 98, read_power, "W", "Back-up L1 Power", SensorKind.ups),
        # Sensor("backup_v2", 102, read_voltage, "V", "Back-up L2 Voltage", SensorKind.ups),
        # Sensor("backup_i2", 104, read_current, "A", "Back-up L2 Current", SensorKind.ups),
        # Sensor("backup_f2", 106, read_freq, "Hz", "Back-up L2 Frequency", SensorKind.ups),
        # Sensor("xx108", 108, read_bytes2, "", "Unknown sensor@108", None),
        # Sensor("backup_p2", 110, read_power, "W", "Back-up L2 Power", SensorKind.ups),
        # Sensor("backup_v3", 114, read_voltage, "V", "Back-up L3 Voltage", SensorKind.ups),
        # Sensor("backup_i3", 116, read_current, "A", "Back-up L3 Current", SensorKind.ups),
        # Sensor("backup_f3", 118, read_freq, "Hz", "Back-up L3 Frequency", SensorKind.ups),
        # Sensor("xx120", 120, read_bytes2, "", "Unknown sensor@120", None),
        # Sensor("backup_p3", 122, read_power, "W", "Back-up L3 Power", SensorKind.ups),
        Sensor("load_p1", 126, read_power, "W", "Load L1", SensorKind.ac),
        # Sensor("load_p2", 130, read_power, "W", "Load L2", SensorKind.ac),
        # Sensor("load_p3", 134, read_power, "W", "Load L3", SensorKind.ac),
        # load_ptotal = load_p1
        Sensor("load_ptotal", 0, lambda data, _: read_power(data, 126), "W", "Load Total", SensorKind.ac, ),
        Sensor("backup_ptotal", 138, read_power, "W", "Back-up Power", SensorKind.ups),
        Sensor("pload", 142, read_power, "W", "Load", SensorKind.ac),
        Sensor("xx146", 146, read_bytes2, "", "Unknown sensor@146", None),
        Sensor("temperature2", 148, read_temp, "C", "Inverter Temperature 2", SensorKind.ac, ),
        Sensor("xx150", 150, read_bytes2, "", "Unknown sensor@150", None),
        Sensor("temperature", 152, read_temp, "C", "Inverter Temperature", SensorKind.ac),
        Sensor("xx154", 154, read_bytes2, "", "Unknown sensor@154", None),
        Sensor("xx156", 156, read_bytes2, "", "Unknown sensor@156", None),
        Sensor("xx158", 158, read_bytes2, "", "Unknown sensor@158", None),
        Sensor("vbattery1", 160, read_voltage, "V", "Battery Voltage", SensorKind.bat),
        Sensor("ibattery1", 162, read_current, "A", "Battery Current", SensorKind.bat),
        # round(vbattery1 * ibattery1),
        Sensor("pbattery1", 0, lambda data, _: round(read_voltage(data, 160) * read_current(data, 162)), "W",
               "Battery Power", SensorKind.bat, ),
        Sensor("battery_mode", 168, read_bytes2, "", "Battery Mode code", SensorKind.bat),
        Sensor("battery_mode_label", 168, read_battery_mode, "", "Battery Mode", SensorKind.bat, ),
        Sensor("xx170", 170, read_bytes2, "", "Unknown sensor@170", None),
        Sensor("safety_country", 172, read_bytes2, "", "Safety Country code", SensorKind.ac, ),
        Sensor("safety_country_label", 172, read_safety_country, "", "Safety Country", SensorKind.ac, ),
        Sensor("work_mode", 174, read_bytes2, "", "Work Mode code", None),
        Sensor("work_mode_label", 174, read_work_mode_et, "", "Work Mode", None),
        Sensor("xx176", 176, read_bytes2, "", "Unknown sensor@176", None),
        Sensor("error_codes", 178, read_bytes4, "", "Error Codes", None),
        Sensor("e_total", 182, read_power_k, "kWh", "Total PV Generation", SensorKind.pv),
        Sensor("e_day", 186, read_power_k, "kWh", "Today's PV Generation", SensorKind.pv),
        Sensor("xx190", 190, read_bytes2, "", "Unknown sensor@190", None),
        Sensor("s_total", 192, read_power_k2, "kWh", "Total Electricity Sold??", SensorKind.ac, ),
        Sensor("h_total", 194, read_bytes4, "", "Hours Total", SensorKind.pv),
        Sensor("xx198", 198, read_bytes2, "", "Unknown sensor@198", None),
        Sensor("s_day", 200, read_power_k2, "kWh", "Today Electricity Sold", SensorKind.ac),
        Sensor("diagnose_result", 240, read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - active_power
        Sensor("house_consumption", 0, lambda data, _: read_power(data, 10)
                                                       + read_power(data, 18)
                                                       + round(read_voltage(data, 160) * read_current(data, 162))
                                                       - read_power(data, 78), "W", "House Comsumption",
               SensorKind.ac, ),
    )

    __sensors_battery: Tuple[Sensor, ...] = (
        Sensor("battery_bms", 0, read_bytes2, "", "Battery BMS", SensorKind.bat),
    )

    __sensors2: Tuple[Sensor, ...] = (
        Sensor("xxx0", 0, read_bytes2, "", "Unknown sensor2@0", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.software_version = response[54:66].decode("ascii")

    async def read_runtime_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA1)
        data = self._map_response(raw_data[5:-2], self.__sensors)
        # raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
        # data.update(self._map_response(raw_data[5:-2], self.__sensors_battery))
        # raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA2)
        # data.update(self._map_response(raw_data[5:-2], self.__sensors2))
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


# registry of supported inverter models
# TODO: it breaks when EH is not first with EH inverter
REGISTRY = [EH, ET, DT, ES]
