from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


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
