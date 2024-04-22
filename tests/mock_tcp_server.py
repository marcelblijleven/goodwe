import asyncio


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        if data.hex() == "f70388b800213ac1":
            self.transport.write(bytes.fromhex(
                "aa55f703420002271000fe393031304b4554553030305730303030475731304b2d45542020000a000a00a7001700ed30343032392d31302d53313130323034312d32332d5330300d8f"))
        elif data.hex() == "f703b9bb00068427":
            self.transport.write(bytes.fromhex("aa55f7030c00000937007f00000014000089eb"))
        elif data.hex() == "f703b9e50006e5f5":
            self.transport.write(bytes.fromhex("aa55f7030c0000173b030003e8005000005268"))

        print('Close the client socket')
        # self.transport.close()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: EchoServerProtocol(),
        '127.0.0.1', 502)

    async with server:
        await server.serve_forever()


asyncio.run(main())
