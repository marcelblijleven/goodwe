import logging

from .dt import DT
from .processor import ProcessorResult, AbstractDataProcessor
from .protocol import ProtocolCommand
from .sensor import *

logger = logging.getLogger(__name__)


class GoodWeXSProcessor(AbstractDataProcessor):

    def __init__(self):
        self.dummy_inverter = DT("localhost")

    def process_data(self, data: bytes) -> ProcessorResult:
        """Process the data provided by the GoodWe XS inverter and return ProcessorResult"""
        sensors = self.dummy_inverter._map_response(data[5:-2], self.dummy_inverter.sensors())

        return ProcessorResult(
            date=sensors['timestamp'],
            volts_dc=sensors['vpv1'],
            current_dc=sensors['ipv1'],
            volts_ac=sensors['vgrid1'],
            current_ac=sensors['igrid1'],
            frequency_ac=sensors['fgrid1'],
            generation_today=sensors['e_day'],
            generation_total=sensors['e_total'],
            # this is just response checksum
            rssi=self._get_rssi(data),
            operational_hours=sensors['h_total'],
            temperature=sensors['temperature'],
            power=sensors['ppv'],
            status=sensors['work_mode_label'])

    def _get_rssi(self, data) -> float:
        """Retrieve rssi from GoodWe data"""
        with io.BytesIO(data) as buffer:
            return read_bytes2(buffer, 149)

    def get_runtime_data_command(self) -> ProtocolCommand:
        """Answer protocol command for reading runtime data"""
        return self.dummy_inverter._READ_DEVICE_RUNNING_DATA
