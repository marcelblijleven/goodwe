import logging
from typing import Tuple

from .exceptions import ProcessingException
from .processor import ProcessorResult, AbstractDataProcessor
from .xs import GoodWeXSProcessor

logger = logging.getLogger(__name__)

class GoodWeInverter:
    def __init__(self, inverter_address: Tuple[str, int], processor: AbstractDataProcessor):
        self.address = inverter_address
        self.processor = processor

    async def request_data(self) -> ProcessorResult:
        try:
            logger.debug('awaiting future')
            data = await self.processor.get_runtime_data_command().execute(self.address[0], 1, 3)
            return self.processor.process_data(data)
        except (TypeError, ValueError) as e:
            logger.debug(f'exception occurred during processing inverter data: {e}')
            raise ProcessingException
