#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Images of the first compute job: layout, push buffer, descriptor, constant buffer 7.

The job is the one of the Linux reference run: firmware/compute_add1.bin,
out[i] = in[i] + 1 for 1024 elements, 16 blocks of 64 threads. The compute
class sequence follows Mesa 25.2.8 (nve4_compute.c). Channel addresses are
software choices of this driver, so every image here is a constant.

  launch.py --check   compare the descriptor with the reference run (D6 data)
                      and print a summary. Writes nothing.

SOURCE_ONLY: an mmiotrace holds no push-buffer words. Nothing here ran on a card.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MESA = ROOT / "reference/mesa/src/gallium/drivers/nouveau"
PAGE = 0x1000
TPC_TOTAL = 15  # KNOWN for this card, work/S3GR/FINDINGS.md; mp_count = units >> 8 (nvc0_screen.c:1065, gf100.c:1166).
ELEMENTS, BLOCK = 1024, 64  # reference/linux-run: 1024 elements, local_size_x = 64.

# nve4_compute.xml.h method numbers (subchannel 1, nvc0_winsys.h:45).
SUBCHANNEL, CLASS = 1, 0xA1C0  # nv_object.xml.h:209.
SHARED_BASE, LOCAL_BASE = 0x0214, 0x077C  # nve4_compute.xml.h:131,188.
LAUNCH_DESC_ADDRESS, LAUNCH = 0x02B4, 0x02BC  # nve4_compute.xml.h:165,170.
MP_TEMP_SIZE_HIGH = 0x02E4  # nve4_compute.xml.h:176, two entries of 12 bytes.
TEMP_ADDRESS_HIGH = 0x0790  # nve4_compute.xml.h:190.
SERIALIZE = 0x0110  # nv_object.xml.h:284.


def define(header, name):
    text = (MESA / header).read_text()
    found = re.search(r"#define\s+" + re.escape(name) + r"\s+(0x[0-9a-fA-F]+|\d+)\s*$", text, re.M)
    if not found:
        raise ValueError(f"{header}: {name} not found")
    return int(found.group(1), 0)


def align(value, to):
    return (value + to - 1) // to * to


def tls_bytes():
    """nvc0_screen_resize_tls_area(screen, 128 * 16, 0, 0x200) (nvc0_screen.c:648-668, 1068)."""
    size = (128 * 16 + 0) * 32 + 0x200
    size *= 64  # chipset >= 0xe0: 64 warps.
    size = align(size, 0x8000) * TPC_TOTAL
    return align(size, 1 << 17)


def layout():
    """Owned records in allocation order: name, bytes, channel VA, writable by the GPU."""
    attrib = align(0x20 * (0x324 + 0x7FF) * TPC_TOTAL, PAGE)  # ctxgf100.c:1067; ctxgk110b.c:95-98.
    context = align(0x80000 + 0x4EA00, PAGE)  # ctxgf100.c:1436,1474; context size KNOWN.
    sizes = [
        ("Text", 0x80000, False), ("Tls", tls_bytes(), True), ("Txc", 0x20000, False),
        ("Aux", PAGE, False), ("Qmd", PAGE, False), ("Input", PAGE, False), ("Output", PAGE, True),
        ("PagePool", 0x8000, True), ("Bundle", 0x3000, True), ("Attrib", attrib, True),
        ("Context", context, True), ("MmioList", PAGE, False),
    ]
    regions, va = {}, 0x10100000  # no source: software channel VA, above GPFIFO and push pages.
    for name, size, writable in sizes:
        va = align(va, 1 << 17)  # no source: 128 KiB steps keep the map easy to read.
        regions[name] = dict(bytes=size, va=va, writable=writable)
        va += size
    if va > 0x18000000:
        raise ValueError("layout leaves the one-table window")
    return regions


def header(op, count, method):
    """nvc0_winsys.h:66-88: 1 incrementing, 3 non-incrementing, 4 immediate."""
    return (op << 29) | (count << 16) | (SUBCHANNEL << 13) | (method >> 2)


def push_words(regions):
    """nve4_screen_compute_setup (nve4_compute.c:44-178), then nve4_launch_grid (:870-879)."""
    words = []

    def begin(method, *data):
        words.append(header(1, len(data), method))
        words.extend(value & 0xFFFFFFFF for value in data)

    text, tls, txc, qmd = (regions[name]["va"] for name in ("Text", "Tls", "Txc", "Qmd"))
    per_mp = regions["Tls"]["bytes"] // TPC_TOTAL
    begin(0x0000, CLASS)  # nve4_compute.c:51-52.
    begin(TEMP_ADDRESS_HIGH, tls >> 32, tls)  # :54-56.
    for index in range(2):  # :61-70.
        begin(MP_TEMP_SIZE_HIGH + 0xC * index, per_mp >> 32, per_mp & ~0x7FFF, 0xFF)
    begin(LOCAL_BASE, 0xFF << 24)  # :78-79.
    begin(SHARED_BASE, 0xFE << 24)  # :80-81.
    begin(define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_CODE_ADDRESS_HIGH"), text >> 32, text)  # :83-85.
    begin(0x0310, 0x400)  # :95-96, class 0xa1c0 >= NVF0.
    begin(define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_TIC_ADDRESS_HIGH"), txc >> 32, txc,
          define("nvc0/nvc0_screen.h", "NVC0_TIC_MAX_ENTRIES") - 1)  # :99-102.
    begin(define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_TSC_ADDRESS_HIGH"), (txc + 65536) >> 32, txc + 65536,
          define("nvc0/nvc0_screen.h", "NVC0_TSC_MAX_ENTRIES") - 1)  # :103-106.
    words.append(header(3, 64, 0x0248))  # :113-115 non-incrementing.
    words.extend(0x38000 | index for index in range(63, -1, -1))
    words.append(header(4, 0, SERIALIZE))  # :116 immediate 0.
    begin(define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_TEX_CB_INDEX"), 7)  # :119-120.
    flush = define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_FLUSH")
    begin(flush, define("nvc0/nve4_compute.xml.h", "NVE4_COMPUTE_FLUSH_CB"))  # :174-175.
    setup = len(words)
    begin(LAUNCH_DESC_ADDRESS, qmd >> 8)  # :870-871.
    begin(LAUNCH, 0x3)  # :873-874.
    begin(SERIALIZE, 0)  # :880-881.
    return words, setup


def qmd_fields():
    """Bit ranges of cla0c0qmd.h (QMDV00_06): name -> (text with i, values of named constants)."""
    fields, named = {}, {}
    for line in (MESA / "nvc0/cla0c0qmd.h").read_text().splitlines():
        found = re.match(r"#define\s+NVA0C0_QMDV00_06_(\w+)(\(i\))?\s+(.+)", line.strip())
        if not found:
            continue
        name, indexed, value = found.groups()
        if value.startswith("MW("):
            fields[name] = value[3:-1]
        elif re.fullmatch(r"0x[0-9a-fA-F]+", value):
            named[name] = int(value, 16)
    return fields, named


class Qmd:
    def __init__(self):
        self.words = [0] * 64
        self.fields, self.named = qmd_fields()

    def bits(self, name, index=None):
        text = self.fields[name]
        if index is not None:
            text = text.replace("(i)", str(index))
        high, low = text.split(":")
        value = lambda part: eval(part, {"__builtins__": {}})  # digits, + * ( ) only, checked below.
        if not re.fullmatch(r"[0-9+*() ]+", high + low):
            raise ValueError("unexpected bit expression")
        return value(high), value(low)

    def set(self, name, value, index=None):
        if isinstance(value, str):
            value = self.named[name + "_" + value]
        high, low = self.bits(name, index)
        if value >> (high - low + 1):
            raise ValueError(f"{name}: value does not fit")
        for bit in range(low, high + 1):
            word, shift = divmod(bit, 32)
            self.words[word] = (self.words[word] & ~(1 << shift)) | (((value >> (bit - low)) & 1) << shift)

    def get(self, name, index=None):
        high, low = self.bits(name, index)
        return sum(((self.words[bit // 32] >> (bit % 32)) & 1) << (bit - low) for bit in range(low, high + 1))


CODE_OFFSET = 0x7F100  # KNOWN: PROGRAM_OFFSET of the reference run (firmware/compute_add1.md).


def descriptor(regions):
    """nve4_compute_setup_launch_desc (nve4_compute.c:574-624) for the reference job."""
    qmd = Qmd()
    for name in ("INVALIDATE_TEXTURE_HEADER_CACHE", "INVALIDATE_TEXTURE_SAMPLER_CACHE", "INVALIDATE_TEXTURE_DATA_CACHE",
                 "INVALIDATE_SHADER_DATA_CACHE", "INVALIDATE_SHADER_CONSTANT_CACHE"):
        qmd.set(name, "TRUE")
    qmd.set("RELEASE_MEMBAR_TYPE", "FE_SYSMEMBAR")
    qmd.set("CWD_MEMBAR_TYPE", "L1_SYSMEMBAR")
    qmd.set("API_VISIBLE_CALL_LIMIT", "NO_CHECK")
    qmd.set("SASS_VERSION", 0x30)
    qmd.set("PROGRAM_OFFSET", CODE_OFFSET)
    qmd.set("CTA_RASTER_WIDTH", ELEMENTS // BLOCK)
    qmd.set("CTA_RASTER_HEIGHT", 1)
    qmd.set("CTA_RASTER_DEPTH", 1)
    qmd.set("CTA_THREAD_DIMENSION0", BLOCK)
    qmd.set("CTA_THREAD_DIMENSION1", 1)
    qmd.set("CTA_THREAD_DIMENSION2", 1)
    qmd.set("SHARED_MEMORY_SIZE", 0)
    qmd.set("SHADER_LOCAL_MEMORY_LOW_SIZE", 0)
    qmd.set("SHADER_LOCAL_MEMORY_HIGH_SIZE", 0)
    qmd.set("SHADER_LOCAL_MEMORY_CRS_SIZE", 0x800)
    qmd.set("L1_CONFIGURATION", "DIRECTLY_ADDRESSABLE_MEMORY_SIZE_16KB")
    qmd.set("REGISTER_COUNT", 5)  # reference/linux-run/compute_test.log:263.
    qmd.set("BARRIER_COUNT", 0)
    aux = regions["Aux"]["va"]
    qmd.set("CONSTANT_BUFFER_ADDR_LOWER", aux & 0xFFFFFFFF, 7)  # nve4_compute.c:535-546,620-621.
    qmd.set("CONSTANT_BUFFER_ADDR_UPPER", aux >> 32, 7)
    qmd.set("CONSTANT_BUFFER_SIZE", 1 << 11, 7)
    qmd.set("CONSTANT_BUFFER_VALID", "TRUE", 7)
    return qmd


def aux_words(regions):
    """Constant buffer 7 of the compute stage: offset -> 32-bit word (nvc0_context.h:116-160)."""
    words = {}
    grid = (BLOCK, 1, 1, ELEMENTS // BLOCK, 1, 1, 0, 1)  # nve4_compute.c:504-511: block, grid, 0, work_dim.
    for index, value in enumerate(grid):
        words[0x100 + index * 4] = value  # NVC0_CB_AUX_GRID_INFO.
    for index, name in enumerate(("Input", "Output")):  # GLSL bindings 0 and 1.
        base, va = 0x2A0 + index * 16, regions[name]["va"]  # NVC0_CB_AUX_BUF_INFO; nve4_compute.c:431-434.
        words[base], words[base + 4], words[base + 8], words[base + 12] = va & 0xFFFFFFFF, va >> 32, ELEMENTS * 4, 0
    return words


def code():
    data = (ROOT / "firmware/compute_add1.bin").read_bytes()
    if hashlib.sha256(data).hexdigest() != "02944d8f43830afad4f9d6538a1a26810085aea98a6520b09f7b5c9cce3ed417":
        raise ValueError("compute_add1.bin differs from the reference run")
    return data


def input_word(index):
    return (0x9E3779B1 * (index + 1)) & 0xFFFFFFFF  # no source: software test pattern.


def check():
    regions = layout()
    words, setup = push_words(regions)
    qmd = descriptor(regions)
    reference = json.loads((ROOT / "analysis/linux_run_shader.json").read_text())["qmd"]
    equal = different = 0
    for row in reference:
        found = re.fullmatch(r"(\w+?)(?:\((\d+)\))?", row["name"])
        name, index = found.group(1), found.group(2)
        if name not in qmd.fields:
            raise ValueError("reference field not in the header: " + name)
        want = row["value"]
        want = int(want, 16) if want.startswith("0x") else qmd.named[name + "_" + want]
        ours = qmd.get(name, int(index) if index is not None else None)
        if ours == want:
            equal += 1
        elif name in ("CONSTANT_BUFFER_ADDR_LOWER", "CONSTANT_BUFFER_ADDR_UPPER") and index == "7":
            different += 1  # Our constant buffer 7 has another address, by layout.
        else:
            raise ValueError(f"descriptor field {row['name']}: reference {want:x}, ours {ours:x}")
    if regions["Qmd"]["va"] & 0xFF or regions["Aux"]["va"] & 0xFF:
        raise ValueError("descriptor and constant buffers need 256-byte alignment")  # nve4_compute.c:541,753-757.
    if CODE_OFFSET + len(code()) > regions["Text"]["bytes"] - 0x800:
        raise ValueError("code leaves the text heap")  # nvc0_screen.c:706-710.
    if len(words) * 4 > PAGE:
        raise ValueError("push buffer leaves its page")
    return regions, words, setup, equal, different


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    regions, words, setup, equal, different = check()
    total = sum(region["bytes"] for region in regions.values())
    print(f"compute launch: {len(regions)} records, {total} bytes, push buffer {len(words)} words "
          f"({setup} set-up, {len(words) - setup} launch); descriptor equals the reference run in {equal} fields, "
          f"{different} differ by layout (constant buffer 7 address); SOURCE_ONLY")


if __name__ == "__main__":
    main()
