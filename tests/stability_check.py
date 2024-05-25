import asyncio
import logging
import sys
from importlib.metadata import version

from pymodbus.client import AsyncModbusTcpClient

# Force the local files, not pip installed lib
sys.path.insert(0, '..')
sys.path.insert(0, '../../../GoodWe')
import goodwe

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)
logger = logging.getLogger(__name__)

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    module_ver = version('goodwe')
    print("WARNING !!!")
    print("==============================")
    print(f"You are executing code with installed pip version goodwe:{module_ver}")
    print("You are not testing the local files, if that was what you meant !!!")
    print("==============================")
except ModuleNotFoundError:
    pass


async def pymodbus(ip):
    client = AsyncModbusTcpClient(host=ip)  # Create client object
    await client.connect()  # connect to device, reconnect automatically

    await client.read_holding_registers(35000, 33, slave=0xf7)
    await client.read_holding_registers(47547, 6, slave=0xf7)
    await client.read_holding_registers(47589, 6, slave=0xf7)

    i = 4
    while True:
        logger.info("################################")
        logger.info("          Request %d", i)
        logger.info("################################")
        await client.read_holding_registers(35100, 125, slave=0xf7)
        await client.read_holding_registers(37000, 24, slave=0xf7)
        await client.read_holding_registers(36000, 45, slave=0xf7)
        # await client.read_holding_registers(36000, 58, slave=0xf7)
        # await client.read_holding_registers(35301, 61, slave=0xf7)
        await asyncio.sleep(10)
        i += 1


async def read_modbus_range(ip, port, register, length):
    inverter = await goodwe.connect(host=ip, port=port, family="ET", timeout=1, retries=3)
    # inverter.set_keep_alive(False)

    i = 1
    while True:
        logger.info("################################")
        logger.info("          Request %d", i)
        logger.info("################################")
        await goodwe.protocol.ModbusRtuReadCommand(0xf7, register, length).execute(
            goodwe.protocol.UdpInverterProtocol(ip, port, 1, 3))
        await asyncio.sleep(5)
        i += 1


async def get_runtime_data(ip, port):
    inverter = await goodwe.connect(host=ip, port=port, family="ET", timeout=1, retries=3)
    # inverter.set_keep_alive(False)

    i = 1
    while True:
        logger.info("################################")
        logger.info("          Request %d", i)
        logger.info("################################")
        await inverter.read_runtime_data()
        await asyncio.sleep(5)
        i += 1


# asyncio.run(pymodbus('127.0.0.1'))
# asyncio.run(read_modbus_range('192.168.2.14', 8899, 35100, 125))
asyncio.run(get_runtime_data('127.0.0.1', 502))
