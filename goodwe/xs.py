import logging
from typing import Callable

from goodwe.dt import DT
from goodwe.exceptions import InvalidDataException
from goodwe.processor import ProcessorResult, AbstractDataProcessor
from goodwe.utils import *

logger = logging.getLogger(__name__)


class GoodWeXSProcessor(AbstractDataProcessor):
    _validator: Callable[[bytes], bool]
    _use_validator: bool

    def process_data(self, data: bytes) -> ProcessorResult:
        """Process the data provided by the GoodWe XS inverter and return ProcessorResult"""
        if self._use_validator and not self._validator(data):
            logger.debug(f'received invalid data: {data}')
            raise InvalidDataException

        sensors = DT._map_response(data[5:-2], DT.sensors())

        return ProcessorResult(
            date=sensors['timestamp'],
            volts_dc=sensors['vpv1'],
            current_dc=sensors['ipv1'],
            volts_ac=sensors['vgrid1'],
            current_ac=sensors['igrid1'],
            frequency_ac=sensors['fgrid1'],
            generation_today=sensors['e_day'],
            generation_total=sensors['e_total'],
            rssi=self._get_rssi(data), # this is just response checksum
            operational_hours=sensors['h_total'],
            temperature=sensors['temperature'],
            power=sensors['ppv'],
            status=sensors['work_mode_label'])

    def set_validator(self, validator_fn: Callable[[bytes], bool]):
        """Set a validator for the processor to use when processing data from the inverter"""
        self._validator = validator_fn
        self._use_validator = self._validator is not None

    def _get_rssi(self, data) -> float:
        """Retrieve rssi from GoodWe data"""
        with io.BytesIO(data) as buffer:
            return read_bytes2(buffer, 149)
