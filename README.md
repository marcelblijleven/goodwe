# GoodWe

[![PyPi](https://img.shields.io/pypi/v/goodwe.svg)](https://pypi.python.org/pypi/goodwe/)
[![Python Versions](https://img.shields.io/pypi/pyversions/goodwe.svg)](https://github.com/marcelblijleven/goodwe/)
[![Build Status](https://github.com/marcelblijleven/goodwe/actions/workflows/publish.yaml/badge.svg)](https://github.com/marcelblijleven/goodwe/actions/workflows/publish.yaml)
![License](https://img.shields.io/github/license/marcelblijleven/goodwe.svg)

Library for connecting to GoodWe inverter over local network and retrieving runtime sensor values and configuration
parameters.

It has been reported to work with GoodWe ET, EH, BT, BH, ES, EM, BP, DT, MS, D-NS, and XS families of inverters. It
should work with other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported
communication protocols.
In general, if you can connect to your inverter with the official mobile app (SolarGo/PvMaster) over Wi-Fi (not
bluetooth), this library should work.

(If you can't communicate with the inverter despite your model is listed above, it is possible you have old ARM firmware
version. You should ask manufacturer support to upgrade your ARM firmware (not just inverter firmware) to be able to
communicate with the inverter via UDP.)

White-label (GoodWe manufactured) inverters may work as well, e.g. General Electric GEP (PSB, PSC) and GEH models are
know to work properly.

Since v0.4.x the library also supports standard Modbus/TCP over port 502.
This protocol is supported by the V2.0 version of LAN+WiFi communication dongle (model WLA0000-01-00P).

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

## References and useful links

- https://github.com/mletenay/home-assistant-goodwe-inverter
- https://github.com/yasko-pv/modbus-log
- https://github.com/tkubec/GoodWe
