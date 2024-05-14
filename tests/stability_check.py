import asyncio
import logging
import sys
from importlib.metadata import version

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


async def get_runtime_data():
    i = 1
    inverter = await goodwe.connect('127.0.0.1', 502)

    while True:
        logger.info("################################")
        logger.info("          Request %d", i)
        logger.info("################################")
        await inverter.read_runtime_data()
        await asyncio.sleep(5)
        i += 1


asyncio.run(get_runtime_data())
