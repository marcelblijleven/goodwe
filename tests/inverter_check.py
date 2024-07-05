"""Simple test script to check inverter UDP protocol communication"""
import asyncio
import logging
import sys
from importlib.metadata import version

# Force the local files, not pip installed lib
sys.path.insert(0, '../goodwe')
sys.path.insert(0, '../../goodwe')

import goodwe

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

module_ver = None
try:
    module_ver = version('goodwe')
except ModuleNotFoundError:
    pass

if module_ver:
    print("WARNING !!!")
    print("==============================")
    print(f"You are executing code with installed pip version goodwe:{module_ver}")
    print("You are not testing the local files, if that was what you meant !!!")
    print("==============================")

# Set the appropriate IP address
IP_ADDRESS = "192.168.2.14"
PORT = 8899
FAMILY = "ET"  # One of ET, EH, ES, EM, DT, NS, XS or None to detect family automatically
COMM_ADDR = 0xf7  # Usually 0xf7 for ET/EH/EM/ES or 0x7f for DT/D-NS/XS, or None for default value
TIMEOUT = 1
RETRIES = 3

inverter = asyncio.run(goodwe.connect(IP_ADDRESS, PORT, FAMILY, COMM_ADDR, TIMEOUT, RETRIES))
print(f"Identified inverter\n"
      f"- Model: {inverter.model_name}\n"
      f"- SerialNr: {inverter.serial_number}\n"
      f"- Rated power: {inverter.rated_power}\n"
      f"- A/C output type: {inverter.ac_output_type}\n"
      f"- Firmware: {inverter.firmware}\n"
      f"- ARM firmware: {inverter.arm_firmware}\n"
      f"- Modbus version: {inverter.modbus_version}\n"
      f"- DSP1 version: {inverter.dsp1_version}\n"
      f"- DSP2 version: {inverter.dsp2_version}\n"
      f"- DSP svn version: {inverter.dsp_svn_version}\n"
      f"- Arm version: {inverter.arm_version}\n"
      f"- ARM svn version: {inverter.arm_svn_version}\n"
      )

# -----------------
# Read runtime data
# -----------------
response = asyncio.run(inverter.read_runtime_data())
for sensor in inverter.sensors():
    if sensor.id_ in response:
        print(f"{sensor.id_}: \t\t {sensor.name} = {response[sensor.id_]} {sensor.unit}")

# -------------
# Read sensorr
# -------------
# print(asyncio.run(inverter.read_sensor('vpv1')))

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
# asyncio.run(inverter.set_operation_mode(goodwe.OperationMode.BACKUP))
# print(asyncio.run(inverter.get_operation_mode()))

# --------------------
# Set inverter setting
# --------------------
# print(asyncio.run(inverter.read_setting('grid_export_limit')))
# asyncio.run(inverter.write_setting('grid_export_limit', 4000))
# print(asyncio.run(inverter.read_setting('grid_export_limit')))

# --------------------
# Get inverter modbus setting
# --------------------
# print(asyncio.run(inverter.read_setting('modbus-47000')))

# -------------------------------
# Execute modbus RTU protocol command
# -------------------------------
# response = asyncio.run(goodwe.protocol.ModbusRtuReadCommand(COMM_ADDR, 0x88b8, 0x21).execute(
#    goodwe.protocol.UdpInverterProtocol(IP_ADDRESS, PORT, TIMEOUT, RETRIES)))
# print(response)

# -------------------------------
# Execute modbus TCP protocol command
# -------------------------------
# response = asyncio.run(goodwe.protocol.ModbusTcpReadCommand(180, 301, 3).execute(
#    goodwe.protocol.TcpInverterProtocol('192.168.1.13', 502, TIMEOUT, RETRIES)))
# print(response.response_data().hex())

# -------------------------------
# Execute AA55 protocol command
# -------------------------------
# response = asyncio.run(goodwe.protocol.Aa55ProtocolCommand("010200", "0182").execute(
#    goodwe.protocol.UdpInverterProtocol(IP_ADDRESS, PORT, TIMEOUT, RETRIES)))
# print(response)

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
