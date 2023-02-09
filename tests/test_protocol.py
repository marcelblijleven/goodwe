from typing import Callable
from unittest import TestCase, mock

from goodwe.exceptions import MaxRetriesException
from goodwe.protocol import Aa55ReadCommand, Aa55WriteCommand, Aa55WriteMultiCommand, ModbusReadCommand, \
    ModbusWriteCommand, ModbusWriteMultiCommand, ProtocolCommand, UdpInverterProtocol


class TestUDPClientProtocol(TestCase):
    def setUp(self) -> None:
        self.command = ProtocolCommand(bytes.fromhex('636f666665650d0a'), lambda x: True)
        self.response_future = mock.Mock()
        #        self.processor = mock.Mock()
        self.protocol = UdpInverterProtocol(self.response_future, self.command, 1, 3)

    def test_datagram_received(self):
        data = b'this is mock data'
        self.protocol.datagram_received(data, ('127.0.0.1', 1337))
        self.response_future.set_result.assert_called_once()

    #        self.processor.assert_called_once_with(data)

    #    def test_datagram_received_process_exception(self):
    #        data = b'this is mock data'

    #        self.protocol.processor.side_effect = TypeError
    #        self.protocol.datagram_received(data, ('127.0.0.1', 1337))
    #        self.processor.assert_called_once_with(data)
    #        self.future.set_result.assert_not_called()
    #        self.future.set_exception.assert_called_once_with(ProcessingException)

    def test_error_received(self):
        exc = Exception('something went wrong')
        self.protocol.error_received(exc)
        self.response_future.set_exception.assert_called_once_with(exc)

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_connection_made(self, mock_get_event_loop):
        transport = mock.Mock()
        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop

        mock_retry_mechanism = mock.Mock()
        self.protocol._retry_mechanism = mock_retry_mechanism
        self.protocol.connection_made(transport)

        transport.sendto.assert_called_with(self.protocol.command.request)
        mock_get_event_loop.assert_called()
        mock_loop.call_later.assert_called_with(1, mock_retry_mechanism)

    def test_connection_lost(self):
        self.response_future.done.return_value = True
        self.protocol.connection_lost(None)
        self.response_future.cancel.assert_not_called()

    def test_connection_lost_not_done(self):
        self.response_future.done.return_value = False
        self.protocol.connection_lost(None)
        self.response_future.cancel.assert_called()

    def test_retry_mechanism(self):
        self.protocol._transport = mock.Mock()
        self.protocol._send_message = mock.Mock()
        self.response_future.done.return_value = True
        self.protocol._retry_mechanism()

        self.protocol._transport.close.assert_called()
        self.protocol._send_message.assert_not_called()

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_retry_mechanism_two_retries(self, mock_get_event_loop):
        def call_later(_: int, retry_func: Callable):
            retry_func()

        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop
        mock_loop.call_later = call_later

        self.protocol._transport = mock.Mock()
        self.response_future.done.side_effect = [False, False, True]
        self.protocol._retry_mechanism()

        self.protocol._transport.close.assert_called()
        self.assertEqual(self.protocol._retries, 2)

    @mock.patch('goodwe.protocol.asyncio.get_event_loop')
    def test_retry_mechanism_max_retries(self, mock_get_event_loop):
        def call_later(_: int, retry_func: Callable):
            retry_func()

        mock_loop = mock.Mock()
        mock_get_event_loop.return_value = mock_loop
        mock_loop.call_later = call_later

        self.protocol._transport = mock.Mock()
        self.response_future.done.side_effect = [False, False, False, False, False]
        self.protocol._retry_mechanism()
        self.response_future.set_exception.assert_called_once_with(MaxRetriesException)
        self.assertEqual(self.protocol._retries, 3)

    def test_modbus_read_command(self):
        command = ModbusReadCommand(0xf7, 0x88b8, 0x0021)
        self.assertEqual(bytes.fromhex('f70388b800213ac1'), command.request)

    def test_modbus_write_command(self):
        command = ModbusWriteCommand(0xf7, 0xb798, 0x0002)
        self.assertEqual(bytes.fromhex('f706b7980002bac6'), command.request)

    def test_modbus_write_multi_command(self):
        command = ModbusWriteMultiCommand(0xf7, 0xb798, bytes.fromhex('08070605'))
        self.assertEqual(bytes.fromhex('f710b79800020408070605851b'), command.request)

    def test_aa55_read_command(self):
        command = Aa55ReadCommand(0x0701, 16)
        self.assertEqual(bytes.fromhex('AA55C07F011A030701100274'), command.request)

    def test_aa55_write_command(self):
        command = Aa55WriteCommand(0x0560, 0x0002)
        self.assertEqual(bytes.fromhex('AA55C07F023905056001000202E6'), command.request)

    def test_aa55_write_multi_command(self):
        command = Aa55WriteMultiCommand(0x0701, bytes.fromhex('08070605'))
        self.assertEqual(bytes.fromhex('AA55C07F02390B0701040807060502AA'), command.request)
