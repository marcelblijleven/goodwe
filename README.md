# GoodWe

[![PyPi](https://img.shields.io/pypi/v/goodwe.svg)](https://pypi.python.org/pypi/goodwe/)
[![Python Versions](https://img.shields.io/pypi/pyversions/goodwe.svg)](https://github.com/marcelblijleven/goodwe/)
[![Build Status](https://github.com/marcelblijleven/goodwe/actions/workflows/publish.yaml/badge.svg)](https://github.com/marcelblijleven/goodwe/actions/workflows/publish.yaml)
![License](https://img.shields.io/github/license/marcelblijleven/goodwe.svg)

Library for connecting to GoodWe inverter over local network and retrieving runtime sensor values and configuration
parameters.

It has been reported to work on GoodWe ET, EH, BT, BH, ES, EM, BP, DT, MS, D-NS, and XS families of inverters. It may
work on other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication
protocols.

(If you can't communicate with the inverter despite your model is listed above, it is possible you have old ARM firmware
version. You should ask manufacturer support to upgrade your ARM firmware (not just inverter firmware) to be able to
communicate with the inveter via UDP.)

## Usage

1. Install this package `pip install goodwe`
2. Write down your GoodWe inverter's IP address (or invoke `goodwe.search_inverters()`)
3. Connect to inverter and read all runtime data, example below

```python
import asyncio
import goodwe


async def get_runtime_data():
    ip_address = '192.168.1.14'

    inverter = await goodwe.connect(ip_address)
    runtime_data = await inverter.read_runtime_data()

    for sensor in inverter.sensors():
        if sensor.id_ in runtime_data:
            print(f"{sensor.id_}: \t\t {sensor.name} = {runtime_data[sensor.id_]} {sensor.unit}")


asyncio.run(get_runtime_data())
```

or the old way (for XS inverters only), create a processor and inverter instance:

```python
import asyncio
from goodwe import GoodWeInverter, GoodWeXSProcessor


async def get_data():
    ip_address = '192.168.200.100'
    processor = GoodWeXSProcessor()
    inverter = GoodWeInverter(inverter_address=(ip_address, 8899), processor=processor)
    data = await inverter.request_data()
    print(f'power is {data.power} at {data.date:%H:%M:%S}')


asyncio.run(get_data())
```

## References and useful links

- https://github.com/mletenay/home-assistant-goodwe-inverter
- https://github.com/yasko-pv/modbus-log
- https://github.com/tkubec/GoodWe
- https://github.com/OpenEMS/openems
