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
            # Device info - READ 33 registers from 35000
            self.transport.write(tx + bytes.fromhex(
                "00000045f70342007913ba0000353530303045534e303030"))
            # Intentional split to test packet fragmentation
            self.transport.write(bytes.fromhex(
                "5730303030475736303030455332300006000619ce0008016a30343034382d30362d53303630323032302d30382d533031"))
        elif payload == "00000006f703b9bb0006":
            # Eco mode - READ 6 registers from 47547
            self.transport.write(tx + bytes.fromhex("0000000ff7030c0000173b5500fc1800640fff"))
        elif payload == "00000006f703b9e50006":
            # Peak shaving - READ 6 registers from 47589
            self.transport.write(tx + bytes.fromhex("0000000ff7030c0000091efa7f03e800000fff"))
        elif payload == "00000006f703891c007d":
            # Running data - READ 125 registers from 35100
            self.transport.write(tx + bytes.fromhex(
                "000000fdf703fa180510070e1b0fca00020000005e07e80004000000520000000000000000000000000000000000000201096d00121385000001a4000000000000000000000000000000000000000000010000019c00000015fffffffc000001a40970000313850001000000000000000000000000000000000000000000000000000000000000019f00000000000000000000000000000176000001ff000001be00000fd2ffff020b00390000012b00020000005100010201000000000000646a0000000000006ad0000008920025000010c00000000089dd0025000028150000000025f8002c0000000000000000000000000000000010000140000301290000"))
        elif payload == "00000006f70390880018":
            # Battery data - READ 24 registers from 37000
            self.transport.write(tx + bytes.fromhex(
                "00000033f7033000ff007d000100de006400780000002d00640001000000220000000000000000000100010001000100e300d80cc90cc4"))
        elif payload == "00000006f7038ca0002d":
            # Meter data - READ 45 registers from 36000
            self.transport.write(tx + bytes.fromhex(
                "0000005df7035a00060000000a00000001fffc00000000fffc02160514863c863c051413860000000000000000fffffffc0000000000000000fffffffc00000216000000000000000000000216fffffd8c0000000000000000fffffd8c00000005"))
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
