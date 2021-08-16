# GoodWe
Get inverter data from a Goodwe XS inverter

This only has been tested with a GoodWe GW1000XS inverter.

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
    processor = GoodWeXSProcessor(validator_func=None)
    inverter = GoodWeInverter(inverter_address=(ip_address, 8899), processor=processor)
    data = await inverter.request_data()
    print(f'power is {data.power} at {data.date:%H:%M:%S}')

asyncio.run(get_data())
```

