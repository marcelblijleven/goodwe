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
        await client.read_holding_registers(36000, 58, slave=0xf7)
        await client.read_holding_registers(35301, 61, slave=0xf7)
        await asyncio.sleep(5)
        i += 1


async def get_runtime_data(ip):
    inverter = await goodwe.connect(host=ip, port=502, timeout=1, retries=3)
    # inverter.keep_alive = False

    i = 1
    while True:
        logger.info("################################")
        logger.info("          Request %d", i)
        logger.info("################################")
        await inverter.read_runtime_data()
        await asyncio.sleep(5)
        i += 1


# asyncio.run(pymodbus('127.0.0.1'))
asyncio.run(get_runtime_data('127.0.0.1'))
