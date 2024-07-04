"""Simple test script to scan inverter present on local network"""
import asyncio
import logging
import sys

import goodwe
from goodwe.exceptions import InverterError
from goodwe.protocol import ProtocolCommand, UdpInverterProtocol

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def try_command(command, ip):
    print(f"Trying command: {command}")
    try:
        response = asyncio.run(
            ProtocolCommand(bytes.fromhex(command), lambda x: True).execute(UdpInverterProtocol(ip, 8899, 0x7f)))
        print(f"Response to {command} command: {response.raw_data.hex()}")
    except InverterError:
        print(f"No response to {command} command")


result = asyncio.run(goodwe.search_inverters()).decode("utf-8").split(",")
print(f"Located inverter at IP: {result[0]}, mac: {result[1]}, name: {result[2]}")

# EM/ES
try_command("AA55C07F0102000241", result[0])
# DT (SolarGo)
try_command("7F03753100280409", result[0])

print(f"Identifying inverter at IP: {result[0]}")
inverter = asyncio.run(goodwe.discover(result[0]))
print(
    f"Identified inverter model: {inverter.model_name}, serialNr: {inverter.serial_number}"
)
