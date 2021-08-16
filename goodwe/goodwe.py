import asyncio

from typing import Tuple

from goodwe.const import MAGIC_PACKET
from goodwe.processor import GoodWeXSProcessor, ProcessorResult
from goodwe.protocol import UDPClientProtocol


class GoodWeInverter:
    def __init__(self, inverter_address: Tuple[str, int], processor: GoodWeXSProcessor):
        self.address = inverter_address
        self.processor = processor

    async def request_data(self) -> ProcessorResult:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        message = MAGIC_PACKET
        # noinspection PyTypeChecker
        transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPClientProtocol(message, future, self.processor.process_data),
            remote_addr=self.address
        )

        try:
            await future
            return future.result()
        finally:
            transport.close()
