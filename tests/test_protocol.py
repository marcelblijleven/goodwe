from typing import Callable
from unittest import TestCase, mock

from goodwe.exceptions import MaxRetriesException, ProcessingException
from goodwe.protocol import UDPClientProtocol


class TestUDPClientProtocol(TestCase):
    def setUp(self) -> None:
        self.future = mock.Mock()
        self.processor = mock.Mock()
        self.protocol = UDPClientProtocol(message='636f666665650d0a', future=self.future, process_func=self.processor)

    def test_datagram_received(self):
        data = b'this is mock data'
        self.protocol.datagram_received(data, ('127.0.0.1', 1337))
        self.future.set_result.assert_called_once()
        self.processor.assert_called_once_with(data)

    def test_datagram_received_process_exception(self):
        data = b'this is mock data'

        self.protocol.processor.side_effect = TypeError
        self.protocol.datagram_received(data, ('127.0.0.1', 1337))
        self.processor.assert_called_once_with(data)
        self.future.set_result.assert_not_called()
        self.future.set_exception.assert_called_once_with(ProcessingException)

    def test_error_received(self):
        exc = Exception('something went wrong')
        self.protocol.error_received(exc)
        self.future.set_exception.assert_called_once_with(exc)

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_connection_made(self, mock_get_event_loop):
        transport = mock.Mock()
        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop

        mock_retry_mechanism = mock.Mock()
        self.protocol.retry_mechanism = mock_retry_mechanism
        self.protocol.connection_made(transport)

        transport.sendto.assert_called_with(self.protocol.message)
        mock_get_event_loop.assert_called()
        mock_loop.call_later.assert_called_with(1, mock_retry_mechanism)

    def test_connection_lost(self):
        self.future.done.return_value = True
        self.protocol.connection_lost(None)
        self.future.cancel.assert_not_called()

    def test_connection_lost_not_done(self):
        self.future.done.return_value = False
        self.protocol.connection_lost(None)
        self.future.cancel.assert_called()

    def test_retry_mechanism(self):
        self.protocol.transport = mock.Mock()
        self.protocol._send_message = mock.Mock()
        self.future.done.return_value = True
        self.protocol.retry_mechanism()

        self.protocol.transport.close.assert_called()
        self.protocol._send_message.assert_not_called()

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_retry_mechanism_two_retries(self, mock_get_event_loop):
        def call_later(_: int, retry_func: Callable):
            retry_func()

        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop
        mock_loop.call_later = call_later

        self.protocol.transport = mock.Mock()
        self.future.done.side_effect = [False, False, True]
        self.protocol.retry_mechanism()

        self.protocol.transport.close.assert_called()
        self.assertEqual(self.protocol._retries, 2)

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_retry_mechanism_max_retries(self, mock_get_event_loop):
        def call_later(_: int, retry_func: Callable):
            retry_func()

        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop
        mock_loop.call_later = call_later

        self.protocol.transport = mock.Mock()
        self.future.done.side_effect = [False, False, False, False, False]
        self.protocol.retry_mechanism()
        self.future.set_exception.assert_called_once_with(MaxRetriesException)
        self.assertEqual(self.protocol._retries, 4)