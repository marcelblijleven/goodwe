from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from struct import unpack
from typing import Any, Callable, Optional

from .const import *
from .inverter import Sensor, SensorKind
from .protocol import ProtocolResponse

DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class ScheduleType(IntEnum):
    ECO_MODE = 0,
    DRY_CONTACT_LOAD = 1,
    DRY_CONTACT_SMART_LOAD = 2,
    PEAK_SHAVING = 3,
    BACKUP_MODE = 4,
    SMART_CHARGE_MODE = 5,
    ECO_MODE_745 = 6,
    NOT_SET = 85

    @classmethod
    def detect_schedule_type(cls, value: int) -> ScheduleType:
        """Detect schedule type from its on/off value"""
        if value in (0, -1):
            return ScheduleType.ECO_MODE
        elif value in (1, -2):
            return ScheduleType.DRY_CONTACT_LOAD
        elif value in (2, -3):
            return ScheduleType.DRY_CONTACT_SMART_LOAD
        elif value in (3, -4):
            return ScheduleType.PEAK_SHAVING
        elif value in (4, -5):
            return ScheduleType.BACKUP_MODE
        elif value in (5, -6):
            return ScheduleType.SMART_CHARGE_MODE
        elif value in (6, -7):
            return ScheduleType.ECO_MODE_745
        elif value == 85:
            return ScheduleType.NOT_SET
        else:
            raise ValueError(f"{value}: on_off value {value} out of range.")

    def power_unit(self):
        """Return unit of power parameter"""
        if self == ScheduleType.PEAK_SHAVING:
            return "W"
        else:
            return "%"

    def decode_power(self, value: int) -> int:
        """Decode human readable value of power parameter"""
        if self == ScheduleType.PEAK_SHAVING:
            return value * 10
        elif self == ScheduleType.ECO_MODE_745:
            return int(value / 10)
        elif self == ScheduleType.NOT_SET:
            # Prevent out of range values when changing mode
            return value if -100 <= value <= 100 else int(value / 10)
        else:
            return value

    def encode_power(self, value: int) -> int:
        """Encode human readable value of power parameter"""
        if self == ScheduleType.ECO_MODE:
            return value
        elif self == ScheduleType.PEAK_SHAVING:
            return int(value / 10)
        elif self == ScheduleType.ECO_MODE_745:
            return value * 10
        else:
            return value

    def is_in_range(self, value: int) -> bool:
        """Check if the value fits in allowed values range"""
        if self == ScheduleType.ECO_MODE:
            return -100 <= value <= 100
        elif self == ScheduleType.ECO_MODE_745:
            return -1000 <= value <= 1000
        else:
            return True


class Voltage(Sensor):
    """Sensor representing voltage [V] value encoded in 2 (unsigned) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "V", kind)

    def read_value(self, data: ProtocolResponse):
        return read_voltage(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return encode_voltage(value)


class Current(Sensor):
    """Sensor representing current [A] value encoded in 2 (unsigned) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "A", kind)

    def read_value(self, data: ProtocolResponse):
        return read_current(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return encode_current(value)


class CurrentS(Sensor):
    """Sensor representing current [A] value encoded in 2 (signed) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "A", kind)

    def read_value(self, data: ProtocolResponse):
        return read_current_signed(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return encode_current_signed(value)


class Frequency(Sensor):
    """Sensor representing frequency [Hz] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "Hz", kind)

    def read_value(self, data: ProtocolResponse):
        return read_freq(data)


class Power(Sensor):
    """Sensor representing power [W] value encoded in 2 (unsigned) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "W", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2(data)


class PowerS(Sensor):
    """Sensor representing power [W] value encoded in 2 (signed) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "W", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2_signed(data)


class Power4(Sensor):
    """Sensor representing power [W] value encoded in 4 (unsigned) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 4, "W", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4(data)


class Power4S(Sensor):
    """Sensor representing power [W] value encoded in 4 (signed) bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 4, "W", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4_signed(data)


class Energy(Sensor):
    """Sensor representing energy [kWh] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "kWh", kind)

    def read_value(self, data: ProtocolResponse):
        value = read_bytes2(data)
        return float(value) / 10 if value is not None else None


class Energy4(Sensor):
    """Sensor representing energy [kWh] value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 4, "kWh", kind)

    def read_value(self, data: ProtocolResponse):
        value = read_bytes4(data)
        return float(value) / 10 if value is not None else None


class Apparent(Sensor):
    """Sensor representing apparent power [VA] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "VA", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2_signed(data)


class Apparent4(Sensor):
    """Sensor representing apparent power [VA] value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "VA", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4_signed(data)


class Reactive(Sensor):
    """Sensor representing reactive power [var] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "var", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2_signed(data)


class Reactive4(Sensor):
    """Sensor representing reactive power [var] value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "var", kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4_signed(data)


class Temp(Sensor):
    """Sensor representing temperature [C] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 2, "C", kind)

    def read_value(self, data: ProtocolResponse):
        return read_temp(data)


class CellVoltage(Sensor):
    """Sensor representing battery cell voltage [V] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, 2, "V", kind)

    def read_value(self, data: ProtocolResponse):
        return read_voltage(data) / 100


class Byte(Sensor):
    """Sensor representing signed int value encoded in 1 byte"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 1, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_byte(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        raise NotImplementedError()


class ByteH(Byte):
    """Sensor representing signed int value encoded in 1 byte (high 8 bits of 16bit register)"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_byte(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        word = bytearray(register_value)
        word[0] = int.to_bytes(int(value), length=1, byteorder="big", signed=True)[0]
        return bytes(word)


class ByteL(Byte):
    """Sensor representing signed int value encoded in 1 byte (low 8 bits of 16bit register)"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)

    def read_value(self, data: ProtocolResponse):
        read_byte(data)
        return read_byte(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        word = bytearray(register_value)
        word[1] = int.to_bytes(int(value), length=1, byteorder="big", signed=True)[0]
        return bytes(word)


class Integer(Sensor):
    """Sensor representing unsigned int value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 2, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2(data, None, 0)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return int.to_bytes(int(value), length=2, byteorder="big", signed=False)


class IntegerS(Sensor):
    """Sensor representing signed int value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 2, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes2_signed(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return int.to_bytes(int(value), length=2, byteorder="big", signed=True)


class Long(Sensor):
    """Sensor representing unsigned int value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 4, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4(data, None, 0)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return int.to_bytes(int(value), length=4, byteorder="big", signed=False)


class LongS(Sensor):
    """Sensor representing signed int value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 4, unit, kind)

    def read_value(self, data: ProtocolResponse):
        return read_bytes4_signed(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return int.to_bytes(int(value), length=4, byteorder="big", signed=True)


class Decimal(Sensor):
    """Sensor representing signed decimal value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, scale: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 2, unit, kind)
        self.scale = scale

    def read_value(self, data: ProtocolResponse):
        return read_decimal2(data, self.scale)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return int.to_bytes(int(value * self.scale), length=2, byteorder="big", signed=True)


class Float(Sensor):
    """Sensor representing signed int value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, scale: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 4, unit, kind)
        self.scale = scale

    def read_value(self, data: ProtocolResponse):
        return round(read_float4(data) / self.scale, 3)


class Timestamp(Sensor):
    """Sensor representing datetime value encoded in 6 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 6, "", kind)

    def read_value(self, data: ProtocolResponse):
        return read_datetime(data)

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        return encode_datetime(value)


class Enum(Sensor):
    """Sensor representing label from enumeration encoded in 1 bytes"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 1, "", kind)
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse):
        return self._labels.get(read_byte(data))


class EnumH(Sensor):
    """Sensor representing label from enumeration encoded in 1 (high 8 bits of 16bit register)"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 1, "", kind)
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse):
        return self._labels.get(read_byte(data))


class EnumL(Sensor):
    """Sensor representing label from enumeration encoded in 1 byte (low 8 bits of 16bit register)"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 1, "", kind)
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse):
        read_byte(data)
        return self._labels.get(read_byte(data))


class Enum2(Sensor):
    """Sensor representing label from enumeration encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 2, "", kind)
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse):
        return self._labels.get(read_bytes2(data, None, 0))


class EnumBitmap4(Sensor):
    """Sensor representing label from bitmap encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, 4, "", kind)
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse) -> Any:
        raise NotImplementedError()

    def read(self, data: ProtocolResponse):
        bits = read_bytes4_signed(data, self.offset)
        return decode_bitmap(bits if bits != -1 else 0, self._labels)


class EnumBitmap22(Sensor):
    """Sensor representing label from bitmap encoded in 2+2 bytes"""

    def __init__(self, id_: str, offsetH: int, offsetL: int, labels: Dict, name: str,
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, offsetH, name, 2, "", kind)
        self._labels: Dict = labels
        self._offsetL: int = offsetL

    def read_value(self, data: ProtocolResponse) -> Any:
        raise NotImplementedError()

    def read(self, data: ProtocolResponse):
        return decode_bitmap(read_bytes2(data, self.offset, 0) << 16 + read_bytes2(data, self._offsetL, 0),
                             self._labels)


class EnumCalculated(Sensor):
    """Sensor representing label from enumeration of calculated value"""

    def __init__(self, id_: str, getter: Callable[[ProtocolResponse], Any], labels: Dict, name: str,
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, 0, name, 0, "", kind)
        self._getter: Callable[[ProtocolResponse], Any] = getter
        self._labels: Dict = labels

    def read_value(self, data: ProtocolResponse) -> Any:
        raise NotImplementedError()

    def read(self, data: ProtocolResponse):
        return self._labels.get(self._getter(data))


class EcoMode(ABC):
    """Sensor representing Eco Mode Battery Power Group API"""

    @abstractmethod
    def encode_charge(self, eco_mode_power: int, eco_mode_soc: int = 100) -> bytes:
        """Answer bytes representing all the time enabled charging eco mode group"""

    @abstractmethod
    def encode_discharge(self, eco_mode_power: int) -> bytes:
        """Answer bytes representing all the time enabled discharging eco mode group"""

    @abstractmethod
    def encode_off(self) -> bytes:
        """Answer bytes representing empty and disabled eco mode group"""

    @abstractmethod
    def is_eco_charge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""

    @abstractmethod
    def is_eco_discharge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""

    @abstractmethod
    def get_schedule_type(self) -> ScheduleType:
        """Answer the schedule type"""

    @abstractmethod
    def set_schedule_type(self, schedule_type: ScheduleType, is745: bool):
        """Set the schedule type"""

    @abstractmethod
    def get_power(self) -> int:
        """Answer the power value"""

    @abstractmethod
    def get_power_unit(self) -> str:
        """Answer the power unit"""


class EcoModeV1(Sensor, EcoMode):
    """Sensor representing Eco Mode Battery Power Group encoded in 8 bytes"""

    def __init__(self, id_: str, offset: int, name: str):
        super().__init__(id_, offset, name, 8, "", SensorKind.BAT)
        self.start_h: int | None = None
        self.start_m: int | None = None
        self.end_h: int | None = None
        self.end_m: int | None = None
        self.power: int | None = None
        self.on_off: int | None = None
        self.day_bits: int | None = None
        self.days: str | None = None
        self.soc: int = 100  # just to keep same API with V2

    def __str__(self):
        return f"{self.start_h}:{self.start_m}-{self.end_h}:{self.end_m} {self.days} " \
               f"{self.power}% " \
               f"{'On' if self.on_off != 0 else 'Off'}"

    def read_value(self, data: ProtocolResponse):
        self.start_h = read_byte(data)
        if (self.start_h < 0 or self.start_h > 23) and self.start_h != 48:
            raise ValueError(f"{self.id_}: start_h value {self.start_h} out of range.")
        self.start_m = read_byte(data)
        if self.start_m < 0 or self.start_m > 59:
            raise ValueError(f"{self.id_}: start_m value {self.start_m} out of range.")
        self.end_h = read_byte(data)
        if (self.end_h < 0 or self.end_h > 23) and self.end_h != 48:
            raise ValueError(f"{self.id_}: end_h value {self.end_h} out of range.")
        self.end_m = read_byte(data)
        if self.end_m < 0 or self.end_m > 59:
            raise ValueError(f"{self.id_}: end_m value {self.end_m} out of range.")
        self.power = read_bytes2_signed(data)  # negative=charge, positive=discharge
        if self.power < -100 or self.power > 100:
            raise ValueError(f"{self.id_}: power value {self.power} out of range.")
        self.on_off = read_byte(data)
        if self.on_off not in (0, -1):
            raise ValueError(f"{self.id_}: on_off value {self.on_off} out of range.")
        self.day_bits = read_byte(data)
        self.days = decode_day_of_week(self.day_bits)
        return self

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        if isinstance(value, bytes) and len(value) == 8:
            # try to read_value to check if values are valid
            if self.read_value(ProtocolResponse(value, None)):
                return value
        raise ValueError

    def encode_charge(self, eco_mode_power: int, eco_mode_soc: int = 100) -> bytes:
        """Answer bytes representing all the time enabled charging eco mode group"""
        return bytes.fromhex("0000173b{:04x}ff7f".format((-1 * abs(eco_mode_power)) & (2 ** 16 - 1)))

    def encode_discharge(self, eco_mode_power: int) -> bytes:
        """Answer bytes representing all the time enabled discharging eco mode group"""
        return bytes.fromhex("0000173b{:04x}ff7f".format(abs(eco_mode_power)))

    def encode_off(self) -> bytes:
        """Answer bytes representing empty and disabled eco mode group"""
        return bytes.fromhex("3000300000640000")

    def is_eco_charge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""
        return self.start_h == 0 \
            and self.start_m == 0 \
            and self.end_h == 23 \
            and self.end_m == 59 \
            and self.on_off != 0 \
            and self.day_bits == 127 \
            and self.power < 0

    def is_eco_discharge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""
        return self.start_h == 0 \
            and self.start_m == 0 \
            and self.end_h == 23 \
            and self.end_m == 59 \
            and self.on_off != 0 \
            and self.day_bits == 127 \
            and self.power > 0

    def get_schedule_type(self) -> ScheduleType:
        """Answer the schedule type"""
        return ScheduleType.ECO_MODE

    def set_schedule_type(self, schedule_type: ScheduleType, is745: bool):
        """Set the schedule type"""
        pass

    def get_power(self) -> int:
        """Answer the power value"""
        return self.power

    def get_power_unit(self) -> str:
        """Answer the power unit"""
        return "%"

    def as_eco_mode_v2(self) -> EcoModeV2:
        """Convert V1 to V2 EcoMode"""
        result = EcoModeV2(self.id_, self.offset, self.name)
        result.start_h = self.start_h
        result.start_m = self.start_m
        result.end_h = self.end_h
        result.end_m = self.end_m
        result.power = self.power
        result.on_off = self.on_off
        result.day_bits = self.day_bits
        result.days = decode_day_of_week(self.day_bits)
        result.soc = 100
        return result


class Schedule(Sensor, EcoMode):
    """Sensor representing Schedule Group encoded in 12 bytes"""

    def __init__(self, id_: str, offset: int, name: str, schedule_type: ScheduleType = ScheduleType.ECO_MODE):
        super().__init__(id_, offset, name, 12, "", SensorKind.BAT)
        self.start_h: int | None = None
        self.start_m: int | None = None
        self.end_h: int | None = None
        self.end_m: int | None = None
        self.on_off: int | None = None
        self.day_bits: int | None = None
        self.days: str | None = None
        self.power: int | None = None
        self.soc: int | None = None
        self.month_bits: int | None = None
        self.months: str | None = None
        self.schedule_type: ScheduleType = schedule_type

    def __str__(self):
        return f"{self.start_h}:{self.start_m}-{self.end_h}:{self.end_m} {self.days} " \
               f"{self.months + ' ' if self.months else ''}" \
               f"{self.get_power()}{self.get_power_unit()} (SoC {self.soc}%) " \
               f"{'On' if -10 < self.on_off < 0 else 'Off' if 10 > self.on_off >= 0 else 'Unset'}"

    def read_value(self, data: ProtocolResponse):
        self.start_h = read_byte(data)
        if (self.start_h < 0 or self.start_h > 23) and self.start_h != 48 and self.start_h != -1:
            raise ValueError(f"{self.id_}: start_h value {self.start_h} out of range.")
        self.start_m = read_byte(data)
        if (self.start_m < 0 or self.start_m > 59) and self.start_m != -1:
            raise ValueError(f"{self.id_}: start_m value {self.start_m} out of range.")
        self.end_h = read_byte(data)
        if (self.end_h < 0 or self.end_h > 23) and self.end_h != 48 and self.end_h != -1:
            raise ValueError(f"{self.id_}: end_h value {self.end_h} out of range.")
        self.end_m = read_byte(data)
        if (self.end_m < 0 or self.end_m > 59) and self.end_m != -1:
            raise ValueError(f"{self.id_}: end_m value {self.end_m} out of range.")
        self.on_off = read_byte(data)
        self.schedule_type = ScheduleType.detect_schedule_type(self.on_off)
        self.day_bits = read_byte(data)
        self.days = decode_day_of_week(self.day_bits)
        self.power = read_bytes2_signed(data)  # negative=charge, positive=discharge
        if not self.schedule_type.is_in_range(self.power):
            raise ValueError(f"{self.id_}: power value {self.power} out of range.")
        self.soc = read_bytes2_signed(data)
        if self.soc < 0 or self.soc > 100:
            raise ValueError(f"{self.id_}: SoC value {self.soc} out of range.")
        self.month_bits = read_bytes2_signed(data)
        self.months = decode_months(self.month_bits)
        return self

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        if isinstance(value, bytes) and len(value) == 12:
            # try to read_value to check if values are valid
            if self.read_value(ProtocolResponse(value, None)):
                return value
        raise ValueError

    def encode_charge(self, eco_mode_power: int, eco_mode_soc: int = 100) -> bytes:
        """Answer bytes representing all the time enabled charging eco mode group"""
        return bytes.fromhex(
            "0000173b{:02x}7f{:04x}{:04x}{:04x}".format(
                255 - self.schedule_type,
                (-1 * abs(self.schedule_type.encode_power(eco_mode_power))) & (2 ** 16 - 1),
                eco_mode_soc,
                0 if self.schedule_type != ScheduleType.ECO_MODE_745 else 0x0fff))

    def encode_discharge(self, eco_mode_power: int) -> bytes:
        """Answer bytes representing all the time enabled discharging eco mode group"""
        return bytes.fromhex("0000173b{:02x}7f{:04x}0064{:04x}".format(
            255 - self.schedule_type,
            abs(self.schedule_type.encode_power(eco_mode_power)),
            0 if self.schedule_type != ScheduleType.ECO_MODE_745 else 0x0fff))

    def encode_off(self) -> bytes:
        """Answer bytes representing empty and disabled schedule group"""
        return bytes.fromhex("30003000{:02x}00{:04x}00640000".format(
            self.schedule_type.value,
            self.schedule_type.encode_power(100)))

    def is_eco_charge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""
        return self.start_h == 0 \
            and self.start_m == 0 \
            and self.end_h == 23 \
            and self.end_m == 59 \
            and self.on_off == (-1 - self.schedule_type) \
            and self.day_bits == 127 \
            and self.power < 0 \
            and (self.month_bits == 0 or self.month_bits == 0x0fff)

    def is_eco_discharge_mode(self) -> bool:
        """Answer if it represents the emulated 24/7 fulltime discharge mode"""
        return self.start_h == 0 \
            and self.start_m == 0 \
            and self.end_h == 23 \
            and self.end_m == 59 \
            and self.on_off == (-1 - self.schedule_type) \
            and self.day_bits == 127 \
            and self.power > 0 \
            and (self.month_bits == 0 or self.month_bits == 0x0fff)

    def get_schedule_type(self) -> ScheduleType:
        """Answer the schedule type"""
        return self.schedule_type

    def set_schedule_type(self, schedule_type: ScheduleType, is745: bool):
        """Set the schedule type"""
        if schedule_type == ScheduleType.ECO_MODE:
            # try to keep-reuse the type, use is745 only when necessary
            if self.schedule_type not in (ScheduleType.ECO_MODE, ScheduleType.ECO_MODE_745):
                self.schedule_type = ScheduleType.ECO_MODE_745 if is745 else ScheduleType.ECO_MODE
        else:
            self.schedule_type = schedule_type

    def get_power(self) -> int:
        """Answer the power value"""
        return self.schedule_type.decode_power(self.power)

    def get_power_unit(self) -> str:
        """Answer the power unit"""
        return self.schedule_type.power_unit()

    def as_eco_mode_v1(self) -> EcoModeV1:
        """Convert V2 to V1 EcoMode"""
        result = EcoModeV1(self.id_, self.offset, self.name)
        result.start_h = self.start_h
        result.start_m = self.start_m
        result.end_h = self.end_h
        result.end_m = self.end_m
        result.power = self.power
        result.on_off = -1 if self.on_off == -1 else 0
        result.day_bits = self.day_bits
        result.days = self.days
        return result


class EcoModeV2(Schedule):
    """Sensor representing Eco Mode Group encoded in 12 bytes"""

    def __init__(self, id_: str, offset: int, name: str):
        super().__init__(id_, offset, name, ScheduleType.ECO_MODE)


class PeakShavingMode(Schedule):
    """Sensor representing Peak Shaving Mode encoded in 12 bytes"""

    def __init__(self, id_: str, offset: int, name: str):
        super().__init__(id_, offset, name, ScheduleType.PEAK_SHAVING)


class Calculated(Sensor):
    """Sensor representing calculated value"""

    def __init__(self, id_: str, getter: Callable[[ProtocolResponse], Any], name: str, unit: str,
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, 0, name, 0, unit, kind)
        self._getter: Callable[[ProtocolResponse], Any] = getter

    def read_value(self, data: ProtocolResponse) -> Any:
        raise NotImplementedError()

    def read(self, data: ProtocolResponse):
        return self._getter(data)


def read_byte(buffer: ProtocolResponse, offset: int = None) -> int:
    """Retrieve single byte (signed int) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(1), byteorder="big", signed=True)


def read_bytes2(buffer: ProtocolResponse, offset: int = None, undef: int = None) -> int:
    """Retrieve 2 byte (unsigned int) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=False)
    return undef if value == 0xffff else value


def read_bytes2_signed(buffer: ProtocolResponse, offset: int = None) -> int:
    """Retrieve 2 byte (signed int) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(2), byteorder="big", signed=True)


def read_bytes4(buffer: ProtocolResponse, offset: int = None, undef: int = None) -> int:
    """Retrieve 4 byte (unsigned int) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(4), byteorder="big", signed=False)
    return undef if value == 0xffffffff else value


def read_bytes4_signed(buffer: ProtocolResponse, offset: int = None) -> int:
    """Retrieve 4 byte (signed int) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(4), byteorder="big", signed=True)


def read_decimal2(buffer: ProtocolResponse, scale: int, offset: int = None) -> float:
    """Retrieve 2 byte (signed float) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    return float(int.from_bytes(buffer.read(2), byteorder="big", signed=True)) / scale


def read_float4(buffer: ProtocolResponse, offset: int = None) -> float:
    """Retrieve 4 byte (signed float) value from buffer"""
    if offset is not None:
        buffer.seek(offset)
    data = buffer.read(4)
    if len(data) == 4:
        return unpack('>f', data)[0]
    else:
        return float(0)


def read_voltage(buffer: ProtocolResponse, offset: int = None) -> float:
    """Retrieve voltage [V] value (2 unsigned bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=False)
    return float(value) / 10 if value != 0xffff else 0


def encode_voltage(value: Any) -> bytes:
    """Encode voltage value to raw (2 unsigned bytes) payload"""
    return int.to_bytes(int(value * 10), length=2, byteorder="big", signed=False)


def read_current(buffer: ProtocolResponse, offset: int = None) -> float:
    """Retrieve current [A] value (2 unsigned bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=False)
    return float(value) / 10 if value != 0xffff else 0


def read_current_signed(buffer: ProtocolResponse, offset: int = None) -> float:
    """Retrieve current [A] value (2 signed bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def encode_current(value: Any) -> bytes:
    """Encode current value to raw (2 unsigned bytes) payload"""
    return int.to_bytes(int(value * 10), length=2, byteorder="big", signed=False)


def encode_current_signed(value: Any) -> bytes:
    """Encode current value to raw (2 signed bytes) payload"""
    return int.to_bytes(int(value * 10), length=2, byteorder="big", signed=True)


def read_freq(buffer: ProtocolResponse, offset: int = None) -> float:
    """Retrieve frequency [Hz] value (2 bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 100


def read_temp(buffer: ProtocolResponse, offset: int = None) -> float | None:
    """Retrieve temperature [C] value (2 bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    if value == -1 or value == 32767:
        return None
    else:
        return float(value) / 10


def read_datetime(buffer: ProtocolResponse, offset: int = None) -> datetime:
    """Retrieve datetime value (6 bytes) from buffer"""
    if offset is not None:
        buffer.seek(offset)
    year = 2000 + int.from_bytes(buffer.read(1), byteorder='big')
    month = int.from_bytes(buffer.read(1), byteorder='big')
    day = int.from_bytes(buffer.read(1), byteorder='big')
    hour = int.from_bytes(buffer.read(1), byteorder='big')
    minute = int.from_bytes(buffer.read(1), byteorder='big')
    second = int.from_bytes(buffer.read(1), byteorder='big')
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


def encode_datetime(value: Any) -> bytes:
    """Encode datetime value to raw (6 bytes) payload"""
    timestamp = value
    if isinstance(value, str):
        timestamp = datetime.fromisoformat(value)

    result = bytes([
        timestamp.year - 2000,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second,
    ])
    return result


def read_grid_mode(buffer: ProtocolResponse, offset: int = None) -> int:
    """Retrieve 'grid mode' sign value from buffer"""
    value = read_bytes2_signed(buffer, offset)
    if value < -90:
        return 2
    elif value >= 90:
        return 1
    else:
        return 0


def read_unsigned_int(data: bytes, offset: int) -> int:
    """Retrieve 2 byte (unsigned int) value from bytes at specified offset"""
    return int.from_bytes(data[offset:offset + 2], byteorder="big", signed=False)


def decode_bitmap(value: int, bitmap: Dict[int, str]) -> str:
    bits = value
    result = []
    for i in range(32):
        if bits & 0x1 == 1:
            if bitmap.get(i, f'err{i}'):
                result.append(bitmap.get(i, f'err{i}'))
        bits = bits >> 1
    return ", ".join(result)


def decode_day_of_week(data: int) -> str:
    if data == -1:
        return "Mon-Sun"
    elif data == 0:
        return ""
    bits = bin(data)[2:]
    daynames = list(DAY_NAMES)
    days = ""
    for each in bits[::-1]:
        if each == '1':
            if len(days) > 0:
                days += ","
            days += daynames[0]
        daynames.pop(0)
    return days


def decode_months(data: int) -> str | None:
    if data <= 0 or data == 0x0fff:
        return None
    bits = bin(data)[2:]
    monthnames = list(MONTH_NAMES)
    months = ""
    for each in bits[::-1]:
        if each == '1':
            if len(months) > 0:
                months += ","
            months += monthnames[0]
        monthnames.pop(0)
    return months
