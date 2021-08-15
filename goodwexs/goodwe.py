import asyncio

from goodwexs.const import MAGIC_PACKET
from goodwexs.processor import Processor, ProcessResult
from goodwexs.protocol import UDPClientProtocol


class GoodWeInverter:
    def __init__(self, inverter_address: tuple[str, int], processor: Processor):
        self.address = inverter_address
        self.processor = processor

    async def request_data(self) -> ProcessResult:
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
