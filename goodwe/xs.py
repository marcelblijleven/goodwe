import logging
from datetime import datetime
from typing import Callable

from goodwe.exceptions import InvalidDataException
from goodwe.processor import ProcessorResult, AbstractDataProcessor
from goodwe.utils import *

logger = logging.getLogger(__name__)


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
        return read_voltage(self._buffer, 11)

    def _get_current_dc(self) -> float:
        """Retrieve current_dc from GoodWe data"""
        return read_current(self._buffer, 13)

    def _get_volts_ac(self) -> float:
        """Retrieve volts_ac from GoodWe data"""
        return read_voltage(self._buffer, 41)

    def _get_current_ac(self) -> float:
        """Retrieve current_ac from GoodWe data"""
        return read_voltage(self._buffer, 47)

    def _get_frequency_ac(self) -> float:
        """Retrieve frequency_ac from GoodWe data"""
        return read_freq(self._buffer, 53)

    def _get_generation_today(self) -> float:
        """Retrieve generation_today from GoodWe data"""
        return read_power_k2(self._buffer, 93)

    def _get_generation_total(self) -> float:
        """Retrieve generation_total from GoodWe data"""
        return read_power_k2(self._buffer, 97)

    def _get_rssi(self) -> float:
        """Retrieve rssi from GoodWe data"""
        return read_bytes2(self._buffer, 149)

    def _get_operational_hours(self) -> float:
        """Retrieve operational_hours from GoodWe data"""
        return read_bytes2(self._buffer, 101)

    def _get_temperature(self) -> float:
        """Retrieve rssi from GoodWe data"""
        return read_temp(self._buffer, 87)

    def _get_power(self) -> float:
        """Retrieve rssi from GoodWe data"""
        return read_power2(self._buffer, 61)

    def _get_status(self) -> str:
        """Retrieve rssi from GoodWe data"""
        return read_work_mode_dt(self._buffer, 63)
