"""Simple test script to check inverter UDP protocol communication"""
import asyncio
import logging
import sys

import goodwe as inverter

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

# Set the appropriate IP address
IP_ADDRESS = "192.168.1.14"
PORT = 8899
# One of ET, EH, ES, EM, DT, NS, XS or None to detect family automatically
FAMILY = "ET"
TIMEOUT = 2
RETRIES = 3

inverter = asyncio.run(inverter.connect(IP_ADDRESS, PORT, FAMILY, TIMEOUT, RETRIES))
print(f"Identified inverter\n"
      f"- Model: {inverter.model_name}\n"
      f"- SerialNr: {inverter.serial_number}\n"
      f"- Version: {inverter.software_version}"
      )

response = asyncio.run(inverter.read_runtime_data(True))

for sensor in inverter.sensors():
    if sensor.id_ in response:
        print(f"{sensor.id_}: \t\t {sensor.name} = {response[sensor.id_]} {sensor.unit}")

# response = asyncio.run(inverter.read_settings_data())

# for (sensor, _, _, unit, name, _) in inverter.settings():
#    print(f"{sensor}: \t\t {name} = {response[sensor]} {unit}")
