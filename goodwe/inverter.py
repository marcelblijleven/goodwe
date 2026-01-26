"""Generic inverter API module."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Callable, Optional

from .const import GOODWE_UDP_PORT
from .exceptions import MaxRetriesException, RequestFailedException
from .protocol import (
    InverterProtocol,
    ProtocolCommand,
    ProtocolResponse,
    TcpInverterProtocol,
    UdpInverterProtocol,
)

logger = logging.getLogger(__name__)


class SensorKind(Enum):
    """
    Enumeration of sensor kinds.

    Possible values are:
    PV - inverter photo-voltaic (e.g. dc voltage of pv panels)
    AC - inverter grid output (e.g. ac voltage of grid connected output)
    UPS - inverter ups/eps/backup output (e.g. ac voltage of backup/off-grid connected output)
    BAT - battery (e.g. dc voltage of connected battery pack)
    GRID - power grid/smart meter (e.g. active power exported to grid)
    BMS - BMS direct data (e.g. dc voltage of)
    """

    PV = 1
    AC = 2
    UPS = 3
    BAT = 4
    GRID = 5
    BMS = 6


@dataclass
class Sensor:
    """Definition of inverter sensor and its attributes"""

    id_: str
    offset: int
    name: str
    size_: int
    unit: str
    kind: Optional[SensorKind]

    def read_value(self, data: ProtocolResponse) -> Any:
        """Read the sensor value from data at current position"""
        raise NotImplementedError()

    def read(self, data: ProtocolResponse) -> Any:
        """Read the sensor value from data (at sensor offset)"""
        data.seek(self.offset)
        return self.read_value(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        """Encode the (setting mostly) value to (usually) 2 bytes raw register value"""
        raise NotImplementedError()


class OperationMode(IntEnum):
    """
    Enumeration of operation modes.

    Possible values are:
    GENERAL - General mode
    OFF_GRID - Off grid mode
    BACKUP - Backup mode
    ECO - Eco mode
    PEAK_SHAVING - Peak shaving mode
    ECO_CHARGE - Eco mode with a single "Charge" group valid all the time (from 00:00-23:59, Mon-Sun)
    ECO_DISCHARGE - Eco mode with a single "Discharge" group valid all the time (from 00:00-23:59, Mon-Sun)
    """

    GENERAL = 0
    OFF_GRID = 1
    BACKUP = 2
    ECO = 3
    PEAK_SHAVING = 4
    SELF_USE = 5
    ECO_CHARGE = 98
    ECO_DISCHARGE = 99


class EMSMode(IntEnum):
    """
    Enumeration of EMS modes.

    AUTO - Auto
    CHARGE_PV - Charge PV
    IMPORT_AC - Import AC
    EXPORT_AC- Export AC
    CONSERVE - Conserve
    OFF_GRID- Off-Grid
    BATTERY_STANDBY - Battery Standby
    BUY_POWER- Buy Power
    SELL_POWER - Sell Power
    CHARGE_BATTERY - Charge Battery
    DISCHARGE_BATTERY - Discharge Battery
    """

    # Scenario: Self-use.
    #
    # PBattery = PInv - Pmeter - Ppv (Discharge/Charge)
    #
    # The battery power is controlled by the meter power when the meter communication is normal.
    AUTO = 1

    # Scenario: Control the battery to keep charging.
    #
    # PBattery = Xmax + PV (Charge)
    # Xmax is to allow the power to be taken from the grid, and PV power is preferred.
    # When set to 0, only PV power is used. Charging power will be limited by charging current limit.
    #
    # Interpretation: Charge Battery from PV (high priority) or Grid (low priority).
    # EmsPowerSet = negative ESS ActivePower (if possible because of PV).
    CHARGE_PV = 2

    # Scenario: Control the battery to keep discharging.
    #
    # PBattery = Xmax (Discharge)
    #
    # Xmax is the allowable discharge power of the battery. When the power fed into the grid is limited, PV power will be used first.
    #
    # Interpretation: ESS ActivePower = PV power + EmsPowerSet (i.e. battery* discharge); useful for surplus feed-to-grid.
    DISCHARGE_PV = 3

    # Scenario: The inverter is used as a unit for power grid energy scheduling.
    #
    # PBattery = Xset + PV (Charge)
    #
    # Xset refers to the power purchased from the power grid. The power purchased from the grid is preferred.
    # If the PV power is too large, the MPPT power will be limited. (grid side load is not considered)
    #
    # Interpretation: Charge Battery from Grid (high priority) or PV (low priority)
    # EmsPowerSet = negative ESS ActivePower; as long as BMS_CHARGE_MAX_CURRENT is > 0, no AC-Power is exported
    # when BMS_CHARGE_MAX_CURRENT == 0, PV surplus feed in starts!
    IMPORT_AC = 4

    # Scenario: The inverter is used as a unit for power grid energy scheduling.
    #
    # PBattery = Xset (Discharge)
    #
    # Xset is to sell power to the grid. PV power is preferred. When PV energy is insufficient, the battery will discharge.
    # PV power will be limited by x. (grid side load is not considered)
    #
    # Interpretation: EmsPowerSet = positive ESS ActivePower. But PV will be limited, i.e. remaining power is not used to charge battery.
    EXPORT_AC = 5

    # Scenario: Off-grid reservation mode.
    #
    # PBattery = PV (Charge)
    #
    # In on-grid mode, the battery is continuously charged, and only PV power (AC Couple model takes 10% of the rated power of the power grid) is used.
    # The battery can only discharge in off-grid mode.
    CONSERVE = 6

    # Scenario: Off-Grid Mode.
    #
    # PBattery = Pbackup - Ppv (Charge/Discharge)
    #
    # Forced off-grid operation.
    OFF_GRID = 7

    # Scenario: The inverter is used as a unit for power grid energy scheduling.
    #
    # PBattery = 0 (Standby)
    #
    # The battery does not charge and discharge
    BATTERY_STANDBY = 8

    # Scenario: Regional energy management.
    #
    # PBattery = PInv - (Pmeter + Xset) - Ppv (Charge/Discharge)
    #
    # When the meter communication is normal, the power purchased from the power grid is controlled as Xset.
    # When the PV power is too large, the MPPT power will be limited. When the load is too large, the battery will discharge.
    #
    # Interpretation: Control power at the point of common coupling.
    BUY_POWER = 9

    # Scenario: Regional energy management.
    #
    # PBattery = PInv - (Pmeter - Xset) - Ppv (Charge/Discharge)
    #
    # When the communication of electricity meter is normal, the power sold from the power grid is controlled as Xset, PV power is preferred,
    # and the battery discharges when PV energy is insufficient.PV power will be limited by Xset.
    #
    # Interpretation: Control power at the point of common coupling.
    SELL_POWER = 10

    # Scenario: Force the battery to work at set power value.
    #
    # PBattery = Xset (Charge)
    #
    # Xset is the charging power of the battery. PV power is preferred. When PV * power is insufficient, it will buy power from the power grid.
    # The charging power is also affected by the charging current limit.
    #
    # Interpretation: Charge Battery from PV (high priority) or Grid (low priority); priorities are inverted compared to IMPORT_AC.
    CHARGE_BATTERY = 11

    # Scenario: Force the battery to work at set power value.
    #
    # PBattery = Xset (Discharge)
    #
    # Xset is the discharge power of the battery, and the battery discharge has priority.
    # If the PV power is too large, MPPT will be limited. Discharge power is also affected by discharge current limit.
    #
    # Interpretation: ???
    DISCHARGE_BATTERY = 12


class Inverter(ABC):
    """
    Common superclass for various inverter models implementations.
    Represents the inverter state and its basic behavior
    """

    def __init__(
        self,
        host: str,
        port: int,
        comm_addr: int = 0,
        timeout: int = 1,
        retries: int = 3,
    ):
        self._protocol: InverterProtocol = self._create_protocol(
            host, port, comm_addr, timeout, retries
        )
        self._consecutive_failures_count: int = 0

        self.model_name: str | None = None
        self.serial_number: str | None = None
        self.rated_power: int = 0
        self.ac_output_type: int | None = None
        self.firmware: str | None = None
        self.arm_firmware: str | None = None
        self.modbus_version: int | None = None
        self.dsp1_version: int = 0
        self.dsp2_version: int = 0
        self.dsp_svn_version: int | None = None
        self.arm_version: int = 0
        self.arm_svn_version: int | None = None

    def _read_command(self, offset: int, count: int) -> ProtocolCommand:
        """Create read protocol command."""
        return self._protocol.read_command(offset, count)

    def _write_command(self, register: int, value: int) -> ProtocolCommand:
        """Create write protocol command."""
        return self._protocol.write_command(register, value)

    def _write_multi_command(self, offset: int, values: bytes) -> ProtocolCommand:
        """Create write multiple protocol command."""
        return self._protocol.write_multi_command(offset, values)

    async def _read_from_socket(self, command: ProtocolCommand) -> ProtocolResponse:
        try:
            result = await command.execute(self._protocol)
            self._consecutive_failures_count = 0
            return result
        except MaxRetriesException:
            self._consecutive_failures_count += 1
            raise RequestFailedException(
                f"No valid response received even after {self._protocol.retries} retries",
                self._consecutive_failures_count,
            ) from None
        except RequestFailedException as ex:
            self._consecutive_failures_count += 1
            raise RequestFailedException(
                ex.message, self._consecutive_failures_count
            ) from None

    def set_keep_alive(self, keep_alive: bool) -> None:
        self._protocol.keep_alive = keep_alive

    @abstractmethod
    async def read_device_info(self):
        """
        Request the device information from the inverter.
        The inverter instance variables will be loaded with relevant data.
        """
        raise NotImplementedError()

    @abstractmethod
    async def read_runtime_data(self) -> dict[str, Any]:
        """
        Request the runtime data from the inverter.
        Answer dictionary of individual sensors and their values.
        List of supported sensors (and their definitions) is provided by sensors() method.
        """
        raise NotImplementedError()

    @abstractmethod
    async def read_sensor(self, sensor_id: str) -> Any:
        """
        Read the value of specific inverter sensor.
        Sensor must be in list provided by sensors() method, otherwise ValueError is raised.
        """
        raise NotImplementedError()

    @abstractmethod
    async def read_setting(self, setting_id: str) -> Any:
        """
        Read the value of specific inverter setting/configuration parameter.
        Setting must be in list provided by settings() method, otherwise ValueError is raised.
        """
        raise NotImplementedError()

    @abstractmethod
    async def write_setting(self, setting_id: str, value: Any):
        """
        Set the value of specific inverter settings/configuration parameter.
        Setting must be in list provided by settings() method, otherwise ValueError is raised.

        BEWARE !!!
        This method modifies inverter operational parameter (usually accessible to installers only).
        Use with caution and at your own risk !
        """
        raise NotImplementedError()

    @abstractmethod
    async def read_settings_data(self) -> dict[str, Any]:
        """
        Request the settings data from the inverter.
        Answer dictionary of individual settings and their values.
        List of supported settings (and their definitions) is provided by settings() method.
        """
        raise NotImplementedError()

    async def send_command(
        self, command: bytes, validator: Callable[[bytes], bool] = lambda x: True
    ) -> ProtocolResponse:
        """
        Send low level command (as bytes).
        Answer ProtocolResponse with command's raw response data.
        """
        return await self._read_from_socket(ProtocolCommand(command, validator))

    @abstractmethod
    async def get_grid_export_limit(self) -> int:
        """
        Get the current grid export limit in W
        """
        raise NotImplementedError()

    @abstractmethod
    async def set_grid_export_limit(self, export_limit: int) -> None:
        """
        BEWARE !!!
        This method modifies inverter operational parameter accessible to installers only.
        Use with caution and at your own risk !

        Set the grid export limit in W
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_operation_modes(
        self, include_emulated: bool
    ) -> tuple[OperationMode, ...]:
        """
        Answer list of supported inverter operation modes
        """
        return ()

    @abstractmethod
    async def get_operation_mode(self) -> OperationMode:
        """
        Get the inverter operation mode
        """
        raise NotImplementedError()

    @abstractmethod
    async def set_operation_mode(
        self,
        operation_mode: OperationMode,
        eco_mode_power: int = 100,
        eco_mode_soc: int = 100,
    ) -> None:
        """
        BEWARE !!!
        This method modifies inverter operational parameter.
        Use with caution and at your own risk !

        Set the inverter operation mode

        The modes ECO_CHARGE and ECO_DISCHARGE are not real inverter operation modes, but a convenience
        shortcuts to enter Eco Mode with a single group valid all the time (from 00:00-23:59, Mon-Sun)
        charging or discharging with optional charging power and SoC (%) parameters.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_ems_mode(self) -> EMSMode:
        """Get the inverter EMS mode."""
        raise NotImplementedError()

    @abstractmethod
    async def set_ems_mode(
        self, ems_mode: EMSMode, ems_power_limit: int | None = None
    ) -> None:
        """
        Set the inverter EMS mode.

        BEWARE !!!
        This method modifies inverter operational parameter.
        Use with caution and at your own risk !
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_ongrid_battery_dod(self) -> int:
        """
        Get the On-Grid Battery DoD
        0% - 89%
        """
        raise NotImplementedError()

    @abstractmethod
    async def set_ongrid_battery_dod(self, dod: int) -> None:
        """
        BEWARE !!!
        This method modifies On-Grid Battery DoD parameter.
        Use with caution and at your own risk !

        Set the On-Grid Battery DoD
        0% - 89%
        """
        raise NotImplementedError()

    @abstractmethod
    def sensors(self) -> tuple[Sensor, ...]:
        """
        Return tuple of sensor definitions
        """
        raise NotImplementedError()

    @abstractmethod
    def settings(self) -> tuple[Sensor, ...]:
        """
        Return tuple of settings definitions
        """
        raise NotImplementedError()

    @staticmethod
    def _create_protocol(
        host: str, port: int, comm_addr: int, timeout: int, retries: int
    ) -> InverterProtocol:
        if port == GOODWE_UDP_PORT:
            return UdpInverterProtocol(host, port, comm_addr, timeout, retries)
        return TcpInverterProtocol(host, port, comm_addr, timeout, retries)

    @staticmethod
    def _map_response(
        response: ProtocolResponse, sensors: tuple[Sensor, ...]
    ) -> dict[str, Any]:
        """Process the response data and return dictionary with runtime values"""
        result = {}
        for sensor in sensors:
            try:
                result[sensor.id_] = sensor.read(response)
            except ValueError:
                logger.exception("Error reading sensor %s.", sensor.id_)
                result[sensor.id_] = None
        return result

    @staticmethod
    def _decode(data: bytes) -> str:
        """Decode the bytes to ascii string"""
        try:
            if any(x < 32 for x in data):
                return data.decode("utf-16be").rstrip().replace("\x00", "")
            return data.decode("ascii").rstrip()
        except ValueError:
            return data.hex()
