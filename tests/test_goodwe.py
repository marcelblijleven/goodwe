from unittest import IsolatedAsyncioTestCase, mock


class TestGoodWeInverter(IsolatedAsyncioTestCase):
    @mock.patch('goodwe.asyncio.get_running_loop')
    async def test_request_data(self, mock_get_running_loop):
        # TODO
        pass
