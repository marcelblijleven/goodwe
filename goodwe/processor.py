import io
import logging
from abc import ABC

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from goodwe.exceptions import InvalidDataException
from goodwe.utils import get_float_from_buffer, get_int_from_buffer

logger = logging.getLogger(__name__)


@dataclass(init=True, order=True)
class ProcessorResult:
    sort_index: datetime = field(init=False)
    date: datetime
    volts_dc: float
    current_dc: float
    volts_ac: float
    current_ac: float
    frequency_ac: float
    generation_today: float
    generation_total: float
    rssi: float
    operational_hours: float
    temperature: float
    power: float
    status: str

    def __post_init__(self) -> None:
        self.sort_index = self.date

    def __str__(self) -> str:
        return f'{self.date.strftime("%Y-%m-%d %H:%M:%S")}: (status: {self.status}, power: {self.power})'


class AbstractDataProcessor(ABC):
    def process_data(self, data: bytes) -> ProcessorResult:
        """Process the data provided by the GoodWe inverter and return ProcessorResult"""

    def set_validator(self, validator_fn: Callable[[bytes], bool]):
        """Set a validator for the processor to use when processing data from the inverter"""


class GoodWeXSProcessor(AbstractDataProcessor):
    _buffer: io.BytesIO
    _validator: Callable[[bytes], bool]
    _use_validator: bool

    def process_data(self, data: bytes) -> ProcessorResult:
        """Process the data provided by the GoodWe XS inverter and return ProcessorResult"""
        if self._use_validator and not self._validator(data):
            logger.debug(f'received invalid data: {data}')
            raise InvalidDataException

        with io.BytesIO(data) as buffer:
            self._buffer = buffer
            result = ProcessorResult(
                date=self._get_date(),
                volts_dc=self._get_volts_dc(),
                current_dc=self._get_current_dc(),
                volts_ac=self._get_volts_ac(),
                current_ac=self._get_current_ac(),
                frequency_ac=self._get_frequency_ac(),
                generation_today=self._get_generation_today(),
                generation_total=self._get_generation_total(),
                rssi=self._get_rssi(),
                operational_hours=self._get_operational_hours(),
                temperature=self._get_temperature(),
                power=self._get_power(),
                status=self._get_status(),
            )

        return result

    def set_validator(self, validator_fn: Callable[[bytes], bool]):
        """Set a validator for the processor to use when processing data from the inverter"""
        self._validator = validator_fn
        self._use_validator = self._validator is not None

    def _get_date(self) -> datetime:
        """Retrieve time stamp from GoodWe data"""
        position_year = 5
        self._buffer.seek(position_year)
        year = 2000 + int.from_bytes(self._buffer.read(1), byteorder='big')
        month = int.from_bytes(self._buffer.read(1), byteorder='big')
        day = int.from_bytes(self._buffer.read(1), byteorder='big')
        hour = int.from_bytes(self._buffer.read(1), byteorder='big')
        minute = int.from_bytes(self._buffer.read(1), byteorder='big')
        second = int.from_bytes(self._buffer.read(1), byteorder='big')

        return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    def _get_volts_dc(self) -> float:
        """Retrieve volts_dc from GoodWe data"""
        position = 11
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_current_dc(self) -> float:
        """Retrieve current_dc from GoodWe data"""
        position = 13
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_volts_ac(self) -> float:
        """Retrieve volts_ac from GoodWe data"""
        position = 41
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_current_ac(self) -> float:
        """Retrieve current_ac from GoodWe data"""
        position = 47
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_frequency_ac(self) -> float:
        """Retrieve frequency_ac from GoodWe data"""
        position = 53
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.01, 2)

    def _get_generation_today(self) -> float:
        """Retrieve generation_today from GoodWe data"""
        position = 93
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_generation_total(self) -> float:
        """Retrieve generation_total from GoodWe data"""
        position = 97
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 2)

    def _get_rssi(self) -> float:
        """Retrieve rssi from GoodWe data"""
        position = 149
        return get_int_from_buffer(self._buffer, position, 2, 'big')

    def _get_operational_hours(self) -> float:
        """Retrieve operational_hours from GoodWe data"""
        position = 101
        return get_int_from_buffer(self._buffer, position, 2, 'big')

    def _get_temperature(self) -> float:
        """Retrieve rssi from GoodWe data"""
        position = 87
        return get_float_from_buffer(self._buffer, position, 2, 'big', 0.1, 1)

    def _get_power(self) -> float:
        """Retrieve rssi from GoodWe data"""
        position = 61
        return get_int_from_buffer(self._buffer, position, 2, 'big')

    def _get_status(self) -> str:
        """Retrieve rssi from GoodWe data"""
        position = 63
        value = get_int_from_buffer(self._buffer, position, 2, 'big')

        modes = {
            0: 'Wait mode',
            1: 'Normal',
            2: 'Error',
            3: 'Check mode'
        }

        return modes[value]
