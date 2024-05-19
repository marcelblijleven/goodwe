from __future__ import annotations

import asyncio
import logging

from .const import GOODWE_TCP_PORT, GOODWE_UDP_PORT
from .dt import DT
from .es import ES
from .et import ET
from .exceptions import InverterError, RequestFailedException
from .inverter import Inverter, OperationMode, Sensor, SensorKind
from .model import DT_MODEL_TAGS, ES_MODEL_TAGS, ET_MODEL_TAGS
from .protocol import ProtocolCommand, UdpInverterProtocol, Aa55ProtocolCommand

logger = logging.getLogger(__name__)

# Inverter family names
ET_FAMILY = ["ET", "EH", "BT", "BH"]
ES_FAMILY = ["ES", "EM", "BP"]
DT_FAMILY = ["DT", "MS", "NS", "XS"]

# Initial discovery command
DISCOVERY_COMMAND = Aa55ProtocolCommand("010200", "0182")


async def connect(host: str, port: int = GOODWE_UDP_PORT, family: str = None, comm_addr: int = 0, timeout: int = 1,
                  retries: int = 3, do_discover: bool = True) -> Inverter:
    """Contact the inverter at the specified host/port and answer appropriate Inverter instance.

    The specific inverter family/type will be detected automatically, but it can be passed explicitly.
    Supported inverter family names are ET, EH, BT, BH, ES, EM, BP, DT, MS, D-NS and XS.

    Inverter communication address may be explicitly passed, if not the usual default value
    will be used (0xf7 for ET/EH/BT/BH/ES/EM/BP inverters, 0x7f for DT/MS/D-NS/XS inverters).

    Since the UDP communication is by definition unreliable, when no (valid) response is received by the specified
    timeout, it is considered lost and the command will be re-tried up to retries times.

    Raise InverterError if unable to contact or recognise supported inverter.
    """
    if family in ET_FAMILY:
        inv = ET(host, port, comm_addr, timeout, retries)
    elif family in ES_FAMILY:
        inv = ES(host, port, comm_addr, timeout, retries)
    elif family in DT_FAMILY:
        inv = DT(host, port, comm_addr, timeout, retries)
    elif do_discover:
        return await discover(host, port, timeout, retries)
    else:
        raise InverterError("Specify either an inverter family or set do_discover True")

    logger.debug("Connecting to %s family inverter at %s:%s.", family, host, port)
    await inv.read_device_info()
    logger.debug("Connected to inverter %s, S/N:%s.", inv.model_name, inv.serial_number)
    return inv


async def discover(host: str, port: int = GOODWE_UDP_PORT, timeout: int = 1, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified value and answer appropriate Inverter instance

    Raise InverterError if unable to contact or recognise supported inverter
    """
    failures = []

    if port == GOODWE_UDP_PORT:
        # Try the common AA55C07F0102000241 command first and detect inverter type from serial_number
        try:
            logger.debug("Probing inverter at %s:%s.", host, port)
            response = await DISCOVERY_COMMAND.execute(UdpInverterProtocol(host, port, timeout, retries))
            response = response.response_data()
            model_name = response[5:15].decode("ascii").rstrip()
            serial_number = response[31:47].decode("ascii")

            i: Inverter | None = None
            for model_tag in ET_MODEL_TAGS:
                if model_tag in serial_number:
                    logger.debug("Detected ET/EH/BT/BH/GEH inverter %s, S/N:%s.", model_name, serial_number)
                    i = ET(host, port, 0, timeout, retries)
                    break
            if not i:
                for model_tag in ES_MODEL_TAGS:
                    if model_tag in serial_number:
                        logger.debug("Detected ES/EM/BP inverter %s, S/N:%s.", model_name, serial_number)
                        i = ES(host, port, 0, timeout, retries)
                        break
            if not i:
                for model_tag in DT_MODEL_TAGS:
                    if model_tag in serial_number:
                        logger.debug("Detected DT/MS/D-NS/XS/GEP inverter %s, S/N:%s.", model_name, serial_number)
                        i = DT(host, port, 0, timeout, retries)
                        break
            if i:
                await i.read_device_info()
                logger.debug("Connected to inverter %s, S/N:%s.", i.model_name, i.serial_number)
                return i

        except InverterError as ex:
            failures.append(ex)

    # Probe inverter specific protocols
    for inv in [ET, DT, ES]:
        i = inv(host, port, 0, timeout, retries)
        try:
            logger.debug("Probing %s inverter at %s.", inv.__name__, host)
            await i.read_device_info()
            await i.read_runtime_data()
            logger.debug("Detected %s family inverter %s, S/N:%s.", inv.__name__, i.model_name, i.serial_number)
            return i
        except InverterError as ex:
            failures.append(ex)
    raise InverterError(
        "Unable to connect to the inverter at "
        f"host={host}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )


async def search_inverters() -> bytes:
    """Scan the network for inverters.
    Answer the inverter discovery response string (which includes it IP address)

    Raise InverterError if unable to contact any inverter
    """
    logger.debug("Searching inverters by broadcast to port 48899")
    command = ProtocolCommand("WIFIKIT-214028-READ".encode("utf-8"), lambda r: True)
    try:
        result = await command.execute(UdpInverterProtocol("255.255.255.255", 48899, 1, 0))
        if result is not None:
            return result.response_data()
        else:
            raise InverterError("No response received to broadcast request.")
    except asyncio.CancelledError:
        raise InverterError("No valid response received to broadcast request.") from None
