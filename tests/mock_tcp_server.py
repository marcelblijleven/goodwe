import asyncio


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        print(data.hex())
        tx = data[0:2]
        payload = data[2:].hex()

        if payload == "00000006f70388b80021":
            self.transport.write(tx + bytes.fromhex(
                "00000027f703420002271000fe393031304b4554553030305730303030475731304b2d45542020000a000a00a7001700ed30343032392d31302d53313130323034312d32332d533030"))
        elif payload == "00000006f703b9bb0006":
            self.transport.write(tx + bytes.fromhex("0000000bf7030c00000937007f000000140000"))
        elif payload == "00000006f703b9e50006":
            self.transport.write(tx + bytes.fromhex("0000000bf7030c0000173b030003e800500000"))
        elif payload == "00000006f703891c007d":
            self.transport.write(tx + bytes.fromhex(
                "00000083f703fa18041d171202000000000000000000000000000000000000000000000000000000000000000000000000096e000e138a0000012a09700005138a000000380980000e1389000001410001000002a6fffffff300000000000000000969000e138a0001000000ed096f0002138c0001000000360984000713890001000000040000007000000070000000a900000113000001a0000501640000013d40001ec00f5e0f8700100000029700020000002000010000000000000004986800000240000414b70000801601fc000002bf00000005590e00ed00017d79006900014d7900480008000500000000000000000000000002000040000302860000"))
        elif payload == "00000006f70390880018":
            self.transport.write(tx + bytes.fromhex(
                "0000001ef7033000ff01000001014a000a0019000000500060000800000101000000000000000000000000000000000000000000000000"))
        elif payload == "00000006f7038ca0002d":
            self.transport.write(tx + bytes.fromhex(
                "00000033f7035a00010039000a00000001ffddff91009b000802caff64fde80145fffc138a4a84c2a44b331528ffffffddffffff910000009b00000008000000b00000008100000198000002cafffffed9ffffff32000001d6000003cc00010003"))
        else:
            self.transport.write(bytes.fromhex("00000000"))
        # print('Close the client socket')
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
