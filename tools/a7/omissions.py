# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Describe deliberate A7 omissions from source-selected Linux preinit.

Pure immutable-ROM inspection. build.py generates the JSON and checks its exact
text. This module has no device, file-writing or execution entry point.
"""


def inventory(rom, selected_pin):
    def u(at, size):
        if at < 0 or at + size > len(rom):
            raise ValueError("CCB omission input outside ROM")
        return int.from_bytes(rom[at : at + size], "little")

    # bios/dcb.c:35,48; bios/i2c.c:32-62,107-116.
    dcb = u(0x36, 2)
    if not dcb or u(dcb + 6, 4) != 0x4EDCBDCB:
        raise ValueError("unexpected DCB omission inputs")
    table = u(dcb + 4, 2)
    version, header, count, stride = (u(table + at, 1) for at in range(4))
    if version != 0x40 or header < 5 or stride < 4:
        raise ValueError("omission inventory needs the reviewed CCB 4.0")
    u(table, header + count * stride)
    buses = []
    pads = set()
    for index in range(count):
        raw = u(table + header + index * stride, 4)
        kind = raw >> 24
        if kind == 5:
            drive = raw & 15
            share = ((raw >> 9) & 127) if raw & 0x100 else 255
            reg = 0xD014 + drive * 0x20  # i2c/busgf119.c:93.
            buses.append(
                dict(ccb_index=index, drive=drive, register=hex(reg), share=share)
            )
            if share != 255:
                pads.add(share)
        elif kind == 6 and raw & 0x100:
            pads.add(raw & 15)  # bios/i2c.c:113-116.
    others = [row for row in buses if int(row["register"], 16) != selected_pin]
    if len(buses) != 8 or len(others) != 7 or pads != {0, 1, 2, 3}:
        raise ValueError("reviewed bus/pad omissions differ")
    return [
        dict(
            operation="hybrid AUX pad power-off",
            phase="Linux I2C preinit",
            registers=[hex(0xE50C + pad * 0x50) for pad in sorted(pads)],
            width=4,
            mask="0x1",
            value="0x1",
            verification="KNOWN / SOURCE_ONLY",
            source="i2c/base.c:177-180; i2c/pad.c:77-81; i2c/padgf119.c:28-39; i2c/padg94.c:33-37",
            reason="A7 uses only the dedicated unshared script bus. It has no AUX/display client. This is a scoped omission, not Linux-preinit equivalence or hardware proof of non-use.",
        ),
        dict(
            operation="other I2C bus initialization",
            phase="Linux I2C preinit",
            buses=others,
            registers=[row["register"] for row in others],
            width=4,
            value="0x7",
            verification="KNOWN / SOURCE_ONLY",
            source="bios/i2c.c:107-116; i2c/base.c:179-180; i2c/busgf119.c:65-69,93",
            reason="Both approved ZM_I2C_BYTE instructions resolve to dedicated CCB bus 2. A7 initializes only that bus and does not initialize unrelated display buses.",
        ),
        dict(
            operation="ROM shadow disable/restore",
            phase="ROM acquisition before POST",
            registers=["0x88050"],
            width=4,
            mask="0x1",
            values=["clear bit", "set bit"],
            verification="KNOWN / SOURCE_ONLY",
            source="bios/shadowrom.c:41-55; pci/base.c:66-74; pci/nv40.c:41-44; pci/gk104.c:208-210",
            reason="A7 hashes and copies the approved ROM from a host file. It does not acquire firmware through the hardware PROM aperture, so no shadow toggle is needed for its input path.",
        ),
    ]
