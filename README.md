# GoodWe
Get inverter data from a Goodwe solar inverter.

It has been reported to work on GoodWe ET, EH, ES, EM, DT, D-NS and XS families of inverters.
It may work on other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols.

## Usage
1. Your GoodWe inverter should already be connected to your home network, and accept UDP messages at port 8899.
2. Write down your GoodWe inverter's IP address
3. Install this package `pip install goodwe`
4. Create an processor and inverter instance, example below

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
or connect to inverter and read all runtime data
```python
import asyncio
import goodwe

async def get_runtime_data():
    ip_address = '192.168.1.14'
    port = 8899
    inverter_family = "ET" # One of ET, EH, ES, EM, DT, NS, XS or None do detect family automatically

    inverter = await goodwe.connect(ip_address, port, inverter_family)
    runtime_data = await inverter.read_runtime_data()

    for (sensor, _, _, unit, name, _) in inverter.sensors():
        if sensor in runtime_data:
            print(f"{sensor}: \t\t {name} = {runtime_data[sensor]} {unit}")

asyncio.run(get_runtime_data())
```


