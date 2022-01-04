"""Simple test script to check inverter UDP protocol communication"""
import asyncio
import logging
import sys

import goodwe

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

# Set the appropriate IP address
IP_ADDRESS = "192.168.1.14"
FAMILY = "ET"  # One of ET, EH, ES, EM, DT, NS, XS or None to detect family automatically
COMM_ADDR = None  # Usually 0xf7 for ET/EH or 0x7f for DT/D-NS/XS, or None for default value
TIMEOUT = 1
RETRIES = 3

inverter = asyncio.run(goodwe.connect(IP_ADDRESS, FAMILY, COMM_ADDR, TIMEOUT, RETRIES))
print(f"Identified inverter\n"
      f"- Model: {inverter.model_name}\n"
      f"- SerialNr: {inverter.serial_number}\n"
      f"- Version: {inverter.software_version}"
      )

# response = asyncio.run(inverter.read_runtime_data(True))

## Set inverter time
#
print(asyncio.run(inverter.read_setting('time')))
# print(asyncio.run(inverter.write_setting('eco_mode_1_switch', -127)))
print(asyncio.run(inverter.read_setting('eco_mode_2')))
# asyncio.run(inverter.write_setting('time', datetime.datetime.now()))
# print(asyncio.run(inverter.read_setting('time')))

# for sensor in inverter.sensors():
#    if sensor.id_ in response:
#        print(f"{sensor.id_}: \t\t {sensor.name} = {response[sensor.id_]} {sensor.unit}")

# response = asyncio.run(goodwe.protocol.ModbusReadCommand(0x88b8, 43).execute(IP_ADDRESS, PORT))
# print(response.hex())

# response = asyncio.run(inverter.read_settings_data())

# for setting in inverter.settings():
#    value = asyncio.run(inverter.read_settings(setting.id_))
#    print(f"{setting.id_}: \t\t {setting.name} = {value} {setting.unit}")

# asyncio.run(inverter.set_operation_mode(2))
# response = asyncio.run(inverter.get_operation_mode())
# print(response)
# response = asyncio.run(inverter.write_setting('grid_export_limit', 3999))
# print(response)

# async def run_in_parallel(inverter):
#    a, b, c, = await asyncio.gather(inverter.get_grid_export_limit(), inverter.get_ongrid_battery_dod(), inverter.read_runtime_data())
#    print(a)
#    print(b)
#    print(c)

# asyncio.run(run_in_parallel(inverter))
