import asyncio
import logging

from typing import Tuple, Optional, Callable

from goodwe.exceptions import ProcessingException, MaxRetriesException
from goodwe.processor import ProcessorResult

logger = logging.getLogger(__name__)


class UDPClientProtocol(asyncio.transports.DatagramTransport):
    transport: asyncio.DatagramTransport

    def __init__(self, message: str, future: asyncio.Future, process_func: Callable[[bytes], ProcessorResult]):
        super().__init__()
        self.message = bytes.fromhex(message)
        self.future = future
        self.processor = process_func

        self._retries = 0
        self._retry_timeout = 1
        self._max_retries = 4

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """On datagram received"""
        logger.debug(f'datagram received: {len(data)} bytes from {addr}')

        try:
            processed_data = self.processor(data)
            self.future.set_result(processed_data)
        except (TypeError, ValueError) as e:
            logger.debug(f'exception occurred during processing inverter data: {e}')
            self.future.set_exception(ProcessingException)

    def error_received(self, exc: Exception) -> None:
        """On error received"""
        logger.debug(f'error received: {exc}')
        self.future.set_exception(exc)

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """On connection made"""
        logger.debug(f'connection made to address {transport.get_extra_info("peername")}')
        self.transport = transport
        self._send_message()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """On connection lost"""
        # Cancel Future on connection lost
        if not self.future.done():
            self.future.cancel()

        if exc is not None:
            logger.debug(f'connection lost: {exc}')

    def _send_message(self) -> None:
        """Send message via transport"""
        logger.debug('sending message to transport')
        self.transport.sendto(self.message)

        loop = asyncio.get_event_loop()
        loop.call_later(self._retry_timeout, self.retry_mechanism)

    def retry_mechanism(self) -> None:
        """Retry mechanism to prevent hanging transport"""
        # If future is done we can close the transport
        if self.future.done():
            logger.debug('future is done, closing transport')
            return self.transport.close()

        # Start retrying
        if self._retries < self._max_retries:
            logger.debug(f'retrying: {self._retries + 1}/{self._max_retries}')
            self._retries += 1
            self._send_message()
        else:
            logger.debug('max number of retries reached, closing transport')
            self.future.set_exception(MaxRetriesException)
