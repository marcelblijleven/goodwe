import asyncio


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def datagram_received(self, data, addr):
        payload = data.hex()
        print(payload)

        if payload == "f70388b800213ac1":
            # Device info - READ 33 registers from 35000
            self.transport.sendto(bytes.fromhex(
                "aa55f703420002271000fe393031304b4554553030305730303030"), addr)
            # Intentional split to test packet fragmentation
            self.transport.sendto(bytes.fromhex(
                "475731304b2d45542020000a000a00a7001700ed30343032392d31302d53313130323034312d32332d5330300d8f"),
                addr)
        elif payload == "f703b9bb00068427":
            # Eco mode - READ 6 registers from 47547
            self.transport.sendto(bytes.fromhex("aa55f7030c00000937007f00000014000089eb"), addr)
        elif payload == "f703b9e50006e5f5":
            # Peak shaving - READ 6 registers from 47589
            self.transport.sendto(bytes.fromhex("aa55f7030c0000173b030003e8005000005268"), addr)
        elif payload == "f703891c007d7ae7":
            # Running data - READ 125 registers from 35100
            self.transport.sendto(bytes.fromhex(
                "aa55f703fa180510163a0a0000000000000000000000000000000000000000000000000000000000000000000000000993001713870000020c0999000613860000004309b3000c1386000000f00001000003310000000a00000000000000000993000c13860001000000ae09970006138600010000007709b500031387000100000003000000ba00000078000000db00000148000001df000501700000014a40001f500fa80f8100140000033c00020000002000010000000000000004b900000001640004321c000081ae013a000002bf000000056c8300d10001845700560001538f004d0008000000000000000000000000000002000040000303310000c258aa55f703fa180510163a0a0000000000000000000000000000000000000000000000000000000000000000000000000993001713870000020c0999000613860000004309b3000c1386000000f00001000003310000000a00000000000000000993000c13860001000000ae09970006138600010000007709b500031387000100000003000000ba00000078000000db00000148000001df000501700000014a40001f500fa80f8100140000033c00020000002000010000000000000004b900000001640004321c000081ae013a000002bf000000056c8300d10001845700560001538f004d0008000000000000000000000000000002000040000303310000c258"),
                addr)
        elif payload == "f70390880018fc7c":
            # Battery data - READ 24 registers from 37000
            self.transport.sendto(bytes.fromhex(
                "aa55f7033000ff010000010154000a00190000004e006000080000010100000000000000000000000000000000000000000000000016eb"),
                addr)
        elif payload == "f7038ca0002dbbf3":
            # Meter data - READ 45 registers from 36000
            self.transport.sendto(bytes.fromhex(
                "aa55f7035a0001004a000a0000000100aeff53001d001e02500216fccd0030001c13874a8cd9d04b333e0e000000aeffffff530000001d0000001e0000008400000003000001c90000025000000149ffffff2e000001ef0000040b00010003166c"),
                addr)
        else:
            self.transport.sendto(bytes.fromhex("00000000"), addr)
        # print('Close the client socket')
        # self.transport.close()


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('127.0.0.1', 8899))

    try:
        await asyncio.sleep(3600)  # Serve for 1 hour.
    finally:
        transport.close()


asyncio.run(main())
