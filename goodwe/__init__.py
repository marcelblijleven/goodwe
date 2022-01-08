from __future__ import annotations

import asyncio
import logging
from typing import Type

from .dt import DT
from .es import ES
from .et import ET
from .exceptions import InverterError, RequestFailedException
from .goodwe import GoodWeXSProcessor, AbstractDataProcessor, GoodWeInverter
from .inverter import Inverter, Sensor, SensorKind
from .protocol import ProtocolCommand, UdpInverterProtocol, Aa55ProtocolCommand

logger = logging.getLogger(__name__)

# Inverter family names
ET_FAMILY = ["ET", "EH", "BT", "BH"]
ES_FAMILY = ["ES", "EM", "BP"]
DT_FAMILY = ["DT", "MS", "NS", "XS"]

# Serial number tags to identify inverter type
ET_MODEL_TAGS = ["ETU", "EHU", "BTU", "BHU"]
ES_MODEL_TAGS = ["ESU", "EMU", "BPU", "BPS"]
DT_MODEL_TAGS = ["DTU", "MSU", "DTN", "DSN"]

# supported inverter protocols
_SUPPORTED_PROTOCOLS = [ET, DT, ES]


async def connect(host: str, family: str = None, comm_addr: int = 0, timeout: int = 1, retries: int = 3) -> Inverter:
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
        inv = ET(host, comm_addr, timeout, retries)
    elif family in ES_FAMILY:
        inv = ES(host, comm_addr, timeout, retries)
    elif family in DT_FAMILY:
        inv = DT(host, comm_addr, timeout, retries)
    else:
        return await discover(host, timeout, retries)

    logger.debug("Connecting to %s family inverter at %s.", family, host)
    await inv.read_device_info()
    logger.debug("Connected to inverter %s, S/N:%s.", inv.model_name, inv.serial_number)
    return inv


async def discover(host: str, timeout: int = 1, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified value and answer appropriate Inverter instance

    Raise InverterError if unable to contact or recognise supported inverter
    """
    failures = []

    # Try the common AA55C07F0102000241 command first and detect inverter type from serial_number
    try:
        logger.debug("Probing inverter at %s.", host)
        response = await Aa55ProtocolCommand("010200", "0182").execute(host, timeout, retries)
        model_name = response[12:22].decode("ascii").rstrip()
        serial_number = response[38:54].decode("ascii")

        inverter_class: Type[Inverter] | None = None
        for model_tag in ET_MODEL_TAGS:
            if model_tag in serial_number:
                logger.debug("Detected ET/EH/BT/BH inverter %s, S/N:%s.", model_name, serial_number)
                inverter_class = ET
        for model_tag in ES_MODEL_TAGS:
            if model_tag in serial_number:
                logger.debug("Detected ES/EM/BP inverter %s, S/N:%s.", model_name, serial_number)
                inverter_class = ES
        for model_tag in DT_MODEL_TAGS:
            if model_tag in serial_number:
                logger.debug("Detected DT/MS/D-NS/XS inverter %s, S/N:%s.", model_name, serial_number)
                inverter_class = DT
        if inverter_class:
            i = inverter_class(host, 0, timeout, retries)
            await i.read_device_info()
            return i

    except InverterError as ex:
        failures.append(ex)

    # Probe inverter specific protocols
    for inv in _SUPPORTED_PROTOCOLS:
        i = inv(host, 0, timeout, retries)
        try:
            logger.debug("Probing %s inverter at %s.", inv.__name__, host)
            await i.read_device_info()
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
    loop = asyncio.get_running_loop()
    command = ProtocolCommand("WIFIKIT-214028-READ".encode("utf-8"), lambda r: True)
    response_future = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: UdpInverterProtocol(response_future, command, 1, 3),
        remote_addr=("255.255.255.255", 48899),
        allow_broadcast=True,
    )
    try:
        await response_future
        result = response_future.result()
        if result is not None:
            return result
        else:
            raise InverterError("No response received to broadcast request.")
    except asyncio.CancelledError:
        raise InverterError("No valid response received to broadcast request.") from None
    finally:
        transport.close()
