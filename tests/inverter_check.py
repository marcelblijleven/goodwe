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
COMM_ADDR = 0xf7  # Usually 0xf7 for ET/EH/EM/ES or 0x7f for DT/D-NS/XS, or None for default value
TIMEOUT = 1
RETRIES = 3

inverter = asyncio.run(goodwe.connect(IP_ADDRESS, FAMILY, COMM_ADDR, TIMEOUT, RETRIES))
print(f"Identified inverter\n"
      f"- Model: {inverter.model_name}\n"
      f"- SerialNr: {inverter.serial_number}\n"
      f"- Version: {inverter.software_version}\n"
      f"- Firmware: {inverter.arm_version}"
      )

# -----------------
# Read runtime data
# -----------------
# response = asyncio.run(inverter.read_runtime_data(True))
# for sensor in inverter.sensors():
#    if sensor.id_ in response:
#        print(f"{sensor.id_}: \t\t {sensor.name} = {response[sensor.id_]} {sensor.unit}")

# -------------
# Read settings
# -------------
# response = asyncio.run(inverter.read_settings_data())
# for setting in inverter.settings():
#    if setting.id_ in response:
#        print(f"{setting.id_}: \t\t {setting.name} = {response[setting.id_]} {setting.unit}")

# -----------------
# Set inverter time
# -----------------
# print(asyncio.run(inverter.read_setting('time')))
# asyncio.run(inverter.write_setting('time', datetime.datetime.now()))
# print(asyncio.run(inverter.read_setting('time')))

# ------------------------------
# Set inverter grid export limit
# ------------------------------
# print(asyncio.run(inverter.get_grid_export_limit()))
# asyncio.run(inverter.set_grid_export_limit(4000))
# print(asyncio.run(inverter.get_grid_export_limit()))

# ---------------------------
# Set inverter operation mode
# ---------------------------
# print(asyncio.run(inverter.get_operation_mode()))
# asyncio.run(inverter.set_operation_mode(2))
# print(asyncio.run(inverter.get_operation_mode()))

# --------------------
# Set inverter setting
# --------------------
# print(asyncio.run(inverter.read_setting('grid_export_limit')))
# asyncio.run(inverter.write_setting('grid_export_limit', 4000))
# print(asyncio.run(inverter.read_setting('grid_export_limit')))

# -------------------------------
# Execute modbus protocol command
# -------------------------------
# response = asyncio.run(goodwe.protocol.ModbusReadCommand(COMM_ADDR, 0x88b8, 0x21).execute(IP_ADDRESS, TIMEOUT, RETRIES))
# print(response.hex())

# -------------------------------
# Execute AA55 protocol command
# -------------------------------
# response = asyncio.run(goodwe.protocol.Aa55ProtocolCommand("010200", "0182").execute(IP_ADDRESS, TIMEOUT, RETRIES))
# print(response.hex())


# -----------------
# Test parallel requests
#
# async def run_in_parallel(inverter):
#    a, b, c, = await asyncio.gather(inverter.get_grid_export_limit(), inverter.get_ongrid_battery_dod(),
#                                    inverter.read_runtime_data())
#    print(a)
#    print(b)
#    print(c)
#
# asyncio.run(run_in_parallel(inverter))
