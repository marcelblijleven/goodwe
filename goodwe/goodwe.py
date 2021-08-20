import asyncio
import logging
from typing import Tuple

from goodwe.const import MAGIC_PACKET
from goodwe.dt import DT
from goodwe.eh import EH
from goodwe.es import ES
from goodwe.et import ET
from goodwe.exceptions import InverterError
from goodwe.inverter import Inverter
from goodwe.processor import ProcessorResult, AbstractDataProcessor
from goodwe.protocol import UDPClientProtocol, _UdpInverterProtocol, Aa55ProtocolCommand
from goodwe.xs import GoodWeXSProcessor

logger = logging.getLogger(__name__)


class GoodWeInverter:
    def __init__(self, inverter_address: Tuple[str, int], processor: AbstractDataProcessor):
        self.address = inverter_address
        self.processor = processor

    async def request_data(self) -> ProcessorResult:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        message = MAGIC_PACKET
        # noinspection PyTypeChecker
        transport, _ = await loop.create_datagram_endpoint(
            lambda: UDPClientProtocol(message, future, self.processor.process_data),
            remote_addr=self.address
        )

        try:
            logger.debug('awaiting future')
            await future
            return future.result()
        finally:
            logger.debug('closing transport')
            transport.close()


async def search_inverters() -> bytes:
    """Scan the network for inverters

    Raise InverterError if unable to contact any inverter
    """
    logger.debug("Searching inverters by broadcast to port 48899")
    loop = asyncio.get_running_loop()
    on_response_received = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _UdpInverterProtocol(
            "WIFIKIT-214028-READ".encode("utf-8"),
            lambda r: True,
            on_response_received,
        ),
        remote_addr=("255.255.255.255", 48899),
        allow_broadcast=True,
    )
    try:
        await on_response_received
        result = on_response_received.result()
        if result is not None:
            return result
        else:
            raise InverterError("No response received to broadcast request")
    except asyncio.CancelledError:
        raise InverterError("No valid response received to broadcast request") from None
    finally:
        transport.close()


async def discover(host: str, port: int = 8899, timeout: int = 2, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified value and answer appropriate Inverter instance

    Raise InverterError if unable to contact or recognise supported inverter
    """
    failures = []

    if ET in _REGISTRY or ES in _REGISTRY or EH in _REGISTRY:
        # Try the common AA55C07F0102000241 command first and detect inverter type from serial_number
        try:
            logger.debug("Probing inverter at %s:%s", host, port)
            response = await Aa55ProtocolCommand("010200", "0182").execute(host, port, timeout, retries)
            model_name = response[12:22].decode("ascii").rstrip()
            serial_number = response[38:54].decode("ascii")
            if "ETU" in serial_number:
                software_version = response[71:83].decode("ascii").strip()
                logger.debug("Detected ET inverter %s, S/N:%s", model_name, serial_number)
                return ET(host, port, timeout, retries, model_name, serial_number, software_version)
            elif "ESU" in serial_number:  # TODO: check if ESU is indeed in the seriual number
                software_version = response[58:70].decode("ascii").strip()
                # arm_version = response[71:83].decode("ascii").strip()
                logger.debug("Detected ES inverter %s, S/N:%s", model_name, serial_number)
                return ES(host, port, timeout, retries, model_name, serial_number, software_version)
            elif "EHU" in serial_number:  # TODO: check if version is correct
                software_version = response[54:66].decode("ascii")
                logger.debug("Detected EH inverter %s, S/N:%s", model_name, serial_number)
                return EH(host, port, timeout, retries, model_name, serial_number, software_version)
        except InverterError as ex:
            failures.append(ex)

    # Probe inverter specific protocols
    for inverter in _REGISTRY:
        i = inverter(host, port, timeout, retries)
        try:
            logger.debug("Probing %s inverter at %s:%s", inverter.__name__, host, port)
            await i.read_device_info()
            logger.debug(
                "Detected %s protocol inverter %s, S/N:%s",
                inverter.__name__,
                i.model_name,
                i.serial_number,
            )
            return i
        except InverterError as ex:
            failures.append(ex)
    raise InverterError(
        "Unable to connect to the inverter at "
        f"host={host} port={port}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )


# registry of supported inverter models
# TODO: it breaks when EH is not first with EH inverter
_REGISTRY = [EH, ET, DT, ES]
