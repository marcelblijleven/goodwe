"""Manual integration check for DTLS transport — requires a real dongle.

Not run by the standard test suite. Invoke directly when verifying against
hardware that advertises ``dtls_port:8899`` in its UDP/48899 discovery response.

Usage:
    python tests/manual_dtls_check.py <dongle_ip> [family]

family defaults to DT (single-phase MS / D-NS / XS / PSC etc.).
"""

import asyncio
import os
import sys

import goodwe


async def main(host: str, family: str) -> int:
    print(f"[*] connecting to {host} via DTLS, family={family} ...")
    inv = await goodwe.connect(host, family=family, dtls=True, retries=2, timeout=2)
    print(f"    model:  {inv.model_name}")
    print(f"    serial: {inv.serial_number}")
    print(f"    rated:  {inv.rated_power} W")

    data = await inv.read_runtime_data()
    print()
    print("Sample sensors:")
    keys = ("timestamp", "vgrid1", "fgrid1", "igrid1", "total_power",
            "temperature", "e_day", "e_total", "h_total", "work_mode")
    for k in keys:
        v = data.get(k)
        unit = next((s.unit for s in inv.sensors() if s.id_ == k), "")
        print(f"  {k:>15s} = {v} {unit}")

    await inv._protocol.close()
    print()
    print("[+] DTLS transport round-trip OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    host = sys.argv[1]
    family = sys.argv[2] if len(sys.argv) > 2 else "DT"
    sys.exit(asyncio.run(main(host, family)))
