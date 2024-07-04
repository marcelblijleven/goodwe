import asyncio


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def datagram_received(self, data, addr):
        payload = data.hex()
        print(payload)

        if payload == "aa55c07f0102000241":
            # Device info
            self.transport.sendto(bytes.fromhex(
                "aa557fc001824d323532354b4757353034382d4553412331300000000000000000000000000039353034384553413030305730303030333630303431302d30343032352d3235203431302d30323033342d323001102f"),
                addr)
        elif payload == "aa55c07f0106000245":
            # Running data
            self.transport.sendto(bytes.fromhex(
                "aa557fc001868c09270047020fe60042010214000200500118000400000032000064006464020000010a11009e0ce11389010a11000303e11389010202010000000000023780000053c3012600770001ad1510c30100200100000001000003e500000840000018051a0e0e120000000000000000000000000000000000000000000000000000ca260000baab0200000000000012e1"),
                addr)
        elif payload == "aa55c07f0109000248":
            # Settings data
            self.transport.sendto(bytes.fromhex(
                "aa557fc00189560000000000000000000000000001000100010000000a00d2024000f0008001e0000a000f0000000000000064024003e8001e00f20000000000000000023f000000070000000000000001038403e801e0000a000000220c12"),
                addr)
        elif payload == "aa55c07f011a030701040268":
            # Read eco_mode_1
            self.transport.sendto(bytes.fromhex(
                "aa557fc0019a08000000000000007f0360"),
                addr)
        elif payload == "aa55c07f032c0500000000000272":
            self.transport.sendto(bytes.fromhex(
                "aa557fc003ac010602f4"),
                addr)
        elif payload == "aa55c07f032d0500000000000273":
            self.transport.sendto(bytes.fromhex(
                "aa557fc003ad010602f5"),
                addr)
        elif payload == "aa55c07f02390507000100010287":
            self.transport.sendto(bytes.fromhex(
                "aa557fc002b901060300"),
                addr)
        elif payload == "aa55c07f033601000278":
            self.transport.sendto(bytes.fromhex(
                "aa557fc003b6010602fe"),
                addr)
        elif payload == "aa55c07f03590100029b":
            self.transport.sendto(bytes.fromhex(
                "aa557fc003d901060321"),
                addr)
        else:
            self.transport.sendto(bytes.fromhex("00000000"), addr)
        # print('Close the client socket')
        # self.transport.close()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('127.0.0.1', 8899))

    try:
        await asyncio.sleep(3600)  # Serve for 1 hour.
    finally:
        transport.close()


asyncio.run(main())
