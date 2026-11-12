#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Host model of the GK110B GR engine start, in the order of Nouveau.

The model emits register accesses through an Io object (rd, wr). It holds no
register table of its own: tables and microcode come from the pinned Nouveau
sources through tools/gr/tables.py. Each step names its source lines. The
trace oracle (tools/gr/oracle.py) runs it against the Linux reference trace.
This is a reference for the native code and a check of the source reading.
HOST_ONLY: nothing here is card evidence.
"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tables

GR = tables.GR


def gpc_bcast(r):  # gf100.h:42.
    return 0x418000 + r


def gpc_unit(t, r):  # gf100.h:43.
    return 0x500000 + t * 0x8000 + r


def ppc_unit(t, m, r):  # gf100.h:44.
    return 0x503000 + t * 0x8000 + m * 0x200 + r


def tpc_unit(t, m, r):  # gf100.h:45.
    return 0x504000 + t * 0x8000 + m * 0x800 + r


def rop_unit(u, r):  # gf100.h:41.
    return 0x410000 + u * 0x400 + r


def microcode(header, name):
    """One uint32_t array of a fuc3 header (firmware/manifest.yaml lists the four)."""
    text = (GR / "fuc" / header).read_text()
    found = re.search(r"static uint32_t " + name + r"\[\] = \{\n(.*?)\n\};", text, re.S)
    if not found:
        raise ValueError(f"{header}: array {name} not found")
    body = re.sub(r"/\*.*?\*/", "", found.group(1), flags=re.S)
    return [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]{8}", body)]


class Topology:
    """Unit counts read by gf100_gr_oneinit (gf100.c:2008-2032)."""

    def __init__(self, io, ppc_max=2):  # gk110b.c:131 ppc_nr = 2.
        self.rop_nr = (io.rd(0x409604) & 0x001F0000) >> 16  # gf100.c:1001.
        self.gpc_nr = io.rd(0x409604) & 0x0000001F  # gf100.c:2009.
        self.tpc_nr, self.ppc_mask, self.ppc_tpc_mask = [], [], []
        for i in range(self.gpc_nr):
            self.tpc_nr.append(io.rd(gpc_unit(i, 0x2608)) & 0xFF)  # gf100.c:2011; u8 tpc_nr (gf100.h:107).
            mask, units = 0, []
            for j in range(ppc_max):
                units.append(io.rd(gpc_unit(i, 0x0C30 + j * 4)))  # gf100.c:2016.
                if units[-1]:
                    mask |= 1 << j
            self.ppc_mask.append(mask)
            self.ppc_tpc_mask.append(units)
        self.tpc_max = max(self.tpc_nr)
        self.tpc_total = sum(self.tpc_nr)
        self.ppc_max = ppc_max
        # gf100_gr_oneinit_sm_id (gf100.c:1895-1910): SM order, TPC first, then GPC.
        self.sm = [(gpc, tpc) for tpc in range(self.tpc_max) for gpc in range(self.gpc_nr) if tpc < self.tpc_nr[gpc]]
        self.tiles()

    def tiles(self):
        """gf100_gr_oneinit_tiles (gf100.c:1913-1986)."""
        primes = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61)
        fixed = {15: 6, 14: 5, 13: 2, 11: 7, 10: 6, 7: 1, 5: 1, 3: 2, 2: 1, 1: 1}
        if self.tpc_total in fixed:
            self.screen_tile_row_offset = fixed[self.tpc_total]
        else:
            self.screen_tile_row_offset = 3
            for prime in primes:
                if self.tpc_total % prime:
                    self.screen_tile_row_offset = prime
                    break
        order = list(range(self.gpc_nr))
        done = False
        while not done:
            done = True
            for i in range(self.gpc_nr - 1):
                if self.tpc_nr[order[i + 1]] > self.tpc_nr[order[i]]:
                    order[i], order[i + 1] = order[i + 1], order[i]
                    done = False
        factor = 2 if (self.gpc_nr * self.tpc_max) & 1 else 1
        denom = self.gpc_nr * self.tpc_max * factor
        frac = [self.tpc_nr[order[i]] * self.gpc_nr * factor for i in range(self.gpc_nr)]
        run = [frac[i] + i * self.tpc_max * factor - denom // 2 for i in range(self.gpc_nr)]
        self.tile = []
        while len(self.tile) < self.tpc_total:
            for j in range(self.gpc_nr):
                if run[j] * 2 >= denom:
                    if len(self.tile) < 255:  # The kernel array is not bounded here; the count is.
                        self.tile.append(order[j])
                    run[j] += frac[j] - denom
                else:
                    run[j] += frac[j]
        self.tile = self.tile[: max(self.tpc_total, len(self.tile))]


def mask(io, addr, clear, value):
    """nvkm_mask: read, then always write (trace lines 616784-616799)."""
    old = io.rd(addr)
    io.wr(addr, (old & ~clear & 0xFFFFFFFF) | value)
    return old


def csdata(io, writes, falcon, starstar, base):
    """gf100_gr_init_csdata (gf100.c:1706-1745): register list for the context-switch code."""
    io.wr(falcon + 0x01C0, 0x02000000 + starstar)
    star = io.rd(falcon + 0x01C4)
    temp = io.rd(falcon + 0x01C4)
    star = max(star, temp)
    io.wr(falcon + 0x01C0, 0x01000000 + star)
    addr, prev, xfer = 0xFFFFFFFF, 0xFFFFFFFF, 0
    for row in writes:
        head = (row["addr"] - base) & 0xFFFFFFFF
        tail = head + row["count"] * row["pitch"]
        while head < tail:
            if head != ((prev + 4) & 0xFFFFFFFF) or xfer >= 32:
                if xfer:
                    xfer -= 1
                    io.wr(falcon + 0x01C4, (xfer << 26) | addr)
                    star += 4
                addr, xfer = head, 0
            prev = head
            xfer += 1
            head += row["pitch"]
    xfer -= 1
    io.wr(falcon + 0x01C4, ((xfer << 26) & 0xFFFFFFFF) | addr)
    io.wr(falcon + 0x01C0, 0x01000004 + starstar)
    io.wr(falcon + 0x01C4, star + 4)


def load(io, falcon, data, code):
    """nvkm_falcon_v1_load_dmem and _load_imem (falcon/v1.c:29-90), port 0, tag 0."""
    io.wr(falcon + 0x1C0, 0x01000000)  # v1.c:76.
    for word in data:
        io.wr(falcon + 0x1C4, word)  # v1.c:78.
    io.wr(falcon + 0x180, 0x01000000)  # v1.c:38-39.
    for index, word in enumerate(code):
        if index & 0x3F == 0:
            io.wr(falcon + 0x188, index >> 6)  # v1.c:42-43 tag every 256 bytes.
        io.wr(falcon + 0x184, word)  # v1.c:44.


def zbc(io):
    """gf100_gr_zbc_init (gf100.c:1005-1041) with the LTC part (ltc/gf100.c:56-72, 16 entries)."""
    colors = ((1, [0] * 4, [0] * 4), (2, [0x3F800000] * 4, [0xFFFFFFFF] * 4),
              (4, [0] * 4, [0] * 4), (4, [0x3F800000] * 4, [0x3F800000] * 4))
    for index, (fmt, ds, l2) in enumerate(colors, 1):
        mask(io, 0x17EA44, 0x0000000F, index)  # ltc/gf100.c:59.
        for k in range(4):
            io.wr(0x17EA48 + k * 4, l2[k])  # ltc/gf100.c:60-63.
        for k in range(4):
            io.wr(0x405804 + k * 4, ds[k])  # gf100.c:53-56.
        io.wr(0x405814, fmt)
        io.wr(0x405820, index)
        io.wr(0x405824, 0x00000004)  # gf100.c:58-60.
    for index, value in enumerate((0x00000000, 0x3F800000), 1):
        mask(io, 0x17EA44, 0x0000000F, index)  # ltc/gf100.c:70.
        io.wr(0x17EA58, value)  # ltc/gf100.c:71.
        io.wr(0x405818, value)  # gf100.c:104.
        io.wr(0x40581C, 1)
        io.wr(0x405820, index)
        io.wr(0x405824, 0x00000005)  # gf100.c:105-107.
    for index in range(5, 16):  # gf100.c:1032-1033, unused colour entries.
        io.wr(0x405814, 0)
        io.wr(0x405820, index)
        io.wr(0x405824, 0x00000004)
    for index in range(3, 16):  # gf100.c:1034-1035, unused depth entries.
        io.wr(0x40581C, 0)
        io.wr(0x405820, index)
        io.wr(0x405824, 0x00000005)


def init(io, t, inits, packs, mmu_wr, mmu_rd):
    """gf100_gr_init (gf100.c:2342-2463) with the hooks of gk110b_gr (gk110b.c:105-141)."""
    mask(io, 0x400500, 0x00010001, 0x00000000)  # gf100.c:2347.
    io.wr(0x418880, io.rd(0x100C80) & 0x00000001)  # gf100.c:2271 init_gpc_mmu.
    io.wr(0x4188A4, 0x03000000)
    for reg in (0x418888, 0x41888C, 0x418890, 0x418894):
        io.wr(reg, 0x00000000)
    io.wr(0x4188B4, mmu_wr >> 8)  # gf100.c:2277.
    io.wr(0x4188B8, mmu_rd >> 8)  # gf100.c:2278.
    for addr, data, _ in tables.expand("gk110b_gr_pack_mmio", inits, packs):
        io.wr(addr, data)  # gf100.c:2360.
    io.rd(0x400700)  # gf100.c:1061 wait_idle.
    enabled = io.rd(0x000200) & 0x1000
    io.rd(0x002640)  # nvkm_fifo_ctxsw_in_progress, the GR engine status (fifo/gk104.c:206).
    busy = io.rd(0x40060C) & 1
    if enabled and busy:
        raise RuntimeError("GR busy at wait_idle")
    io.wr(gpc_unit(0, 0x3018), 0x00000001)  # gk104.c:433 vsc_stream_master.
    bank = [0] * 32
    tile_nr = (t.tpc_total + 31) & ~31  # gf117.c:129.
    for i in range(0, tile_nr, 8):
        data = 0
        for j in range(8):
            if i + j < t.tpc_total:
                data |= bank[t.tile[i + j]] << (j * 4)
                bank[t.tile[i + j]] += 1
        io.wr(gpc_bcast(0x0980 + (i // 8) * 4), data)  # gf117.c:139.
    magic = -(-0x00800000 // t.tpc_total)  # gf117.c:127 DIV_ROUND_UP.
    for gpc in range(t.gpc_nr):
        io.wr(gpc_unit(gpc, 0x0914), t.screen_tile_row_offset << 8 | t.tpc_nr[gpc])
        io.wr(gpc_unit(gpc, 0x0910), 0x00040000 | t.tpc_total)
        io.wr(gpc_unit(gpc, 0x0918), magic)
    io.wr(gpc_bcast(0x3FD4), magic)  # gf117.c:150.
    io.wr(gpc_bcast(0x08AC), io.rd(0x100800))  # gf100.c:2285 num_active_ltcs.
    fbp = io.rd(0x120074)  # gk104.c:409.
    mask(io, 0x408850, 0x0000000F, fbp)
    mask(io, 0x408958, 0x0000000F, fbp)
    io.wr(0x400500, 0x00010001)  # gf100.c:2385.
    io.wr(0x400100, 0xFFFFFFFF)
    io.wr(0x40013C, 0xFFFFFFFF)
    io.wr(0x400124, 0x00000002)
    io.wr(0x409C24, 0x000E0001)  # gf100.c:2258-2259, built-in microcode.
    for reg in (0x404000, 0x404600, 0x408030, 0x406018, 0x404490):
        io.wr(reg, 0xC0000000)  # gf100.c:2399-2407.
    io.wr(0x407020, 0x40000000)  # gk104.c:393.
    io.wr(0x405840, 0xC0000000)
    io.wr(0x405844, 0x00FFFFFF)
    mask(io, 0x419CC0, 0x00000008, 0x00000008)  # gf100.c:2242.
    for gpc in range(t.gpc_nr):
        for tpc in range(t.tpc_nr[gpc]):
            io.wr(tpc_unit(gpc, tpc, 0x48C), 0xC0000000)
    for bit in (0x1000, 0x2000, 0x4000, 0x8000):  # gk110.c:342-345.
        mask(io, 0x419EB4, bit, bit)
    for bit in (0x1000, 0x2000, 0x4000, 0x8000):  # gk110.c:346-349.
        mask(io, 0x419EB4, bit, 0)
    for gpc in range(t.gpc_nr):  # gk104.c:420-426.
        for ppc in range(t.ppc_max):
            if t.ppc_mask[gpc] & (1 << ppc):
                io.wr(ppc_unit(gpc, ppc, 0x038), 0xC0000000)
    for gpc in range(t.gpc_nr):  # gf100.c:2426-2443.
        for reg in (0x0420, 0x0900, 0x1028, 0x0824):
            io.wr(gpc_unit(gpc, reg), 0xC0000000)
        for tpc in range(t.tpc_nr[gpc]):
            io.wr(tpc_unit(gpc, tpc, 0x508), 0xFFFFFFFF)
            io.wr(tpc_unit(gpc, tpc, 0x50C), 0xFFFFFFFF)
            io.wr(tpc_unit(gpc, tpc, 0x224), 0xC0000000)  # gf100.c:2226.
            io.wr(tpc_unit(gpc, tpc, 0x084), 0xC0000000)
            io.wr(tpc_unit(gpc, tpc, 0x644), 0x001FFFFE)  # gf100.c:2218-2219.
            io.wr(tpc_unit(gpc, tpc, 0x64C), 0x0000000F)
        io.wr(gpc_unit(gpc, 0x2C90), 0xFFFFFFFF)
        io.wr(gpc_unit(gpc, 0x2C94), 0xFFFFFFFF)
    for rop in range(t.rop_nr):  # gf100.c:2206-2211.
        io.wr(rop_unit(rop, 0x144), 0x40000000)
        io.wr(rop_unit(rop, 0x070), 0x40000000)
        io.wr(rop_unit(rop, 0x204), 0xFFFFFFFF)
        io.wr(rop_unit(rop, 0x208), 0xFFFFFFFF)
    for reg in (0x400108, 0x400138, 0x400118, 0x400130, 0x40011C, 0x400134):
        io.wr(reg, 0xFFFFFFFF)  # gf100.c:2447-2450, 2196-2197.
    io.wr(0x400054, 0x34CE3464)  # gf100.c:2188.
    zbc(io)


def ctxctl(io, inits, packs):
    """gf100_gr_init_ctxctl_int (gf100.c:1831-1880). Returns the context image size."""
    io.wr(0x000260, 0)  # mc/gf100.c:64 unk260.
    load(io, 0x409000, microcode("hubgk110.fuc3.h", "gk110_grhub_data"),
         microcode("hubgk110.fuc3.h", "gk110_grhub_code"))
    load(io, 0x41A000, microcode("gpcgk110.fuc3.h", "gk110_grgpc_data"),
         microcode("gpcgk110.fuc3.h", "gk110_grgpc_code"))
    io.wr(0x000260, 1)
    rows = lambda pack: [row for entry in packs[pack] for row in inits[entry["init"]]]
    csdata(io, rows("gk110_grctx_pack_hub"), 0x409000, 0x000, 0x000000)  # gf100.c:1860-1864.
    csdata(io, rows("gk110_grctx_pack_gpc_0"), 0x41A000, 0x000, 0x418000)
    csdata(io, rows("gk110_grctx_pack_gpc_1"), 0x41A000, 0x000, 0x418000)
    csdata(io, rows("gk110b_grctx_pack_tpc"), 0x41A000, 0x004, 0x419800)
    csdata(io, rows("gk110_grctx_pack_ppc"), 0x41A000, 0x008, 0x41BE00)
    io.wr(0x40910C, 0x00000000)  # gf100.c:1867.
    io.wr(0x409100, 0x00000002)
    for _ in range(100000):  # gf100.c:1869-1872, 2000 ms in the kernel.
        if io.rd(0x409800) & 0x80000000:
            break
    else:
        raise RuntimeError("FECS did not report ready")
    return io.rd(0x409804)  # gf100.c:1878.


# gk110b_grctx (ctxgk110b.c:73-107).
BUNDLE_SIZE, BUNDLE_MIN_DEPTH, BUNDLE_TOKEN_LIMIT = 0x3000, 0x180, 0x600
ATTRIB_NR_MAX, ATTRIB_NR, ALPHA_NR_MAX, ALPHA_NR = 0x324, 0x218, 0x7FF, 0x648
PAGEPOOL_SIZE = 0x8000
CB_RESERVED = 0x80000  # ctxgf100.c:1436.


def attrib_cb_size(t):
    return 0x20 * (ATTRIB_NR_MAX + ALPHA_NR_MAX) * t.tpc_total  # ctxgf100.c:1067.


def wait_idle(io):
    """gf100_gr_wait_idle (gf100.c:1049-1075)."""
    for _ in range(100000):
        io.rd(0x400700)
        enabled = io.rd(0x000200) & 0x1000
        chsw = io.rd(0x002640)  # GR engine status (fifo/gk104.c:206,258-266).
        busy = io.rd(0x40060C) & 1
        active = bool(chsw & 0x80000000) and bool(chsw & 0x00008000)
        if not enabled or (not busy and not active):
            return
    raise RuntimeError("GR not idle")


def mmio(io, inits, packs, pack):
    for addr, data, _ in tables.expand(pack, inits, packs):
        io.wr(addr, data)


def icmd(io, inits, packs, pack):
    """gf100_gr_icmd (gf100.c:1095-1132)."""
    io.wr(0x400208, 0x80000000)
    data, first = 0, True
    for entry in packs[pack]:
        for row in inits[entry["init"]]:
            if first or data != row["data"]:
                io.wr(0x400204, row["data"])
                data = row["data"]
            first = False
            for index in range(row["count"]):
                addr = row["addr"] + index * row["pitch"]
                io.wr(0x400200, addr)
                if addr & 0xFFFF == 0xE100:
                    wait_idle(io)
                for _ in range(100000):  # gf100.c:1123-1126.
                    if not io.rd(0x400700) & 0x00000004:
                        break
                else:
                    raise RuntimeError("icmd not accepted")
    io.wr(0x400208, 0x00000000)


def mthd(io, inits, packs, pack):
    """gf100_gr_mthd (gf100.c:1135-1157)."""
    data, first = 0, True
    for entry in packs[pack]:
        ctrl = 0x80000000 | entry["type"]
        for row in inits[entry["init"]]:
            if first or data != row["data"]:
                io.wr(0x40448C, row["data"])
                data = row["data"]
            first = False
            for index in range(row["count"]):
                io.wr(0x404488, ctrl | (((row["addr"] + index * row["pitch"]) << 14) & 0xFFFFFFFF))


def patches(io, t, pagepool, bundle, attrib):
    """The per-context register values (ctxgf100.c:1011-1061, ctxgk104.c:864-891, ctxgf117.c:244-275).

    In context generation they are register writes. For a channel the same pairs
    go into its mmio list (gf100.c:469-479). io.patch is that choice.
    """
    io.patch(0x40800C, pagepool >> 8)
    io.patch(0x408010, 0x80000000)
    io.patch(0x419004, pagepool >> 8)
    io.patch(0x419008, 0x00000000)
    io.patch(0x4064CC, 0x80000000)  # ctxgk104.c:890.
    io.patch(0x408004, bundle >> 8)
    io.patch(0x408008, 0x80000000 | (BUNDLE_SIZE >> 8))
    io.patch(0x418808, bundle >> 8)
    io.patch(0x41880C, 0x80000000 | (BUNDLE_SIZE >> 8))
    io.patch(0x4064C8, (min(BUNDLE_MIN_DEPTH, BUNDLE_SIZE // 0x20) << 16) | BUNDLE_TOKEN_LIMIT)  # ctxgk104.c:879-883.
    io.patch(0x418810, 0x80000000 | attrib >> 12)
    io.patch(0x419848, 0x10000000 | attrib >> 12)
    io.patch(0x405830, (ATTRIB_NR << 16) | ALPHA_NR)  # ctxgf117.c:256.
    io.patch(0x4064C4, ((ALPHA_NR // 4) << 16) | 0xFFFF)
    bo, ao = 0, ATTRIB_NR_MAX * t.tpc_total
    for gpc in range(t.gpc_nr):
        for ppc in range(t.ppc_max):
            count = bin(t.ppc_tpc_mask[gpc][ppc] & 0xFF).count("1")  # gf100.c:2023 hweight8.
            if not t.ppc_mask[gpc] & (1 << ppc):
                continue
            o = ppc_unit(gpc, ppc, 0)
            io.patch(o + 0xC0, (1 << 28) | ((ATTRIB_NR * count) << 16) | bo)
            bo += ATTRIB_NR_MAX * count
            io.patch(o + 0xE4, ((ALPHA_NR * count) << 16) | ao)
            ao += ALPHA_NR_MAX * count
    data0, data1 = io.rd(0x17E91C), io.rd(0x17E920)  # ctxgk104.c:867-872.
    io.patch(0x17E91C, data0)
    io.patch(0x17E920, data1)


def floorsweep(io, t):
    """gf100_grctx_generate_floorsweep (ctxgf100.c:1303-1339) with the gk110b hooks."""
    for sm, (gpc, tpc) in enumerate(t.sm):
        io.wr(tpc_unit(gpc, tpc, 0x698), sm)  # ctxgf100.c:1296-1299.
        io.wr(tpc_unit(gpc, tpc, 0x4E8), sm)
        io.wr(gpc_unit(gpc, 0x0C10 + tpc * 4), sm)
        io.wr(tpc_unit(gpc, tpc, 0x088), sm)
        io.wr(gpc_unit(gpc, 0x0C08), t.tpc_nr[gpc])  # ctxgf100.c:1288-1289.
        io.wr(gpc_unit(gpc, 0x0C8C), t.tpc_nr[gpc])
    for base in (0x405870, 0x406028):  # gf100.c:2169-2183: ds pass, then pd pass.
        gpc = 0
        for i in range(4):
            data = 0
            for j in range(8):
                if gpc < t.gpc_nr:
                    data |= t.tpc_nr[gpc] << (j * 4)
                    gpc += 1
            io.wr(base + i * 4, data)
    tile = t.tile + [0xFF] * 32  # gf100.c:2057 memset 0xff.
    data = [0] * 6
    for i in range(32):
        data[i // 6] |= (tile[i] & 0x07) << ((i % 6) * 5)  # ctxgf117.c:206-207.
    shift, ntpcv = 0, t.tpc_total
    while not ntpcv & (1 << 4):
        ntpcv = (ntpcv << 1) & 0xFF
        shift += 1
    data20 = (ntpcv << 16) | (shift << 21) | (((1 << 5) % ntpcv) << 24)
    data21 = 0
    for i in range(1, 7):
        data21 |= ((1 << (i + 5)) % ntpcv) << ((i - 1) * 5)
    word = (t.tpc_total << 8) | t.screen_tile_row_offset
    io.wr(0x418BB8, word)
    for i in range(6):
        io.wr(0x418B08 + i * 4, data[i] & 0xFFFFFFFF)
    io.wr(0x41BFD0, word | data20)
    io.wr(0x41BFE4, data21)
    for i in range(6):
        io.wr(0x41BF00 + i * 4, data[i] & 0xFFFFFFFF)
    io.wr(0x4078BC, word)
    for i in range(6):
        io.wr(0x40780C + i * 4, data[i] & 0xFFFFFFFF)
    count = [[bin(m & 0xFF).count("1") for m in units] for units in t.ppc_tpc_mask]
    for i in range(32):  # ctxgk104.c:922-966 alpha/beta tables.
        atarget = max(t.tpc_total * i // 32, 1)
        btarget = t.tpc_total - atarget
        alpha = atarget < btarget
        amask = bmask = 0
        for gpc in range(t.gpc_nr):
            for ppc in range(t.ppc_max):
                tpcs = count[gpc][ppc]
                if alpha:
                    abits = tpcs if atarget else 0
                    bbits = tpcs - abits
                else:
                    bbits = tpcs if btarget else 0
                    abits = tpcs - bbits
                pmask = t.ppc_tpc_mask[gpc][ppc]
                left = tpcs
                while left > abits:
                    pmask &= pmask - 1
                    left -= 1
                amask |= pmask << (gpc * 8)
                pmask ^= t.ppc_tpc_mask[gpc][ppc]
                bmask |= pmask << (gpc * 8)
                atarget -= min(abits, atarget)
                btarget -= min(bbits, btarget)
                if abits > 0 or bbits > 0:
                    alpha = not alpha
        for j in range(0, t.gpc_nr, 4):
            io.wr(0x406800 + i * 0x20 + j, amask & 0xFFFFFFFF)
            io.wr(0x406C00 + i * 0x20 + j, bmask & 0xFFFFFFFF)
            amask >>= 32
            bmask >>= 32
    for i in range(8):
        io.wr(0x4064D0 + i * 4, 0x00000000)  # ctxgf117.c:193-194.
    io.wr(0x405B00, (t.tpc_total << 8) | t.gpc_nr)  # ctxgk104.c:918.
    mask(io, 0x419F78, 0x00000008, 0x00000000)  # ctxgk110.c:829.


def generate(io, t, inits, packs, instance, pagepool, bundle, attrib):
    """gf100_grctx_generate (ctxgf100.c:1438-1560): the golden context.

    The caller maps the context memory at a channel address and writes that
    address plus CB_RESERVED to words 0x210 and 0x214 of the instance block
    after the SCC RAM step (ctxgf100.c:1483-1487): io.context_pointer().
    """
    io.wr(0x404170, 0x00000012)  # ctxgf100.c:1450 FE power mode force on.
    for _ in range(100000):
        if not io.rd(0x404170) & 0x00000010:
            break
    io.wr(0x409614, 0x00000070)  # gf100.c:2470-2478 FECS reset.
    io.delay(10)
    mask(io, 0x409614, 0x00000700, 0x00000700)
    io.delay(10)
    io.rd(0x409614)
    io.wr(0x404170, 0x00000010)  # ctxgf100.c:1465 auto.
    for _ in range(100000):
        if not io.rd(0x404170) & 0x00000010:
            break
    io.wr(0x40802C, 0x00000001)  # ctxgf100.c:1471 SCC RAM.
    io.context_pointer()
    io.wr(0x409840, 0x80000000)  # ctxgf100.c:1504-1510 make the channel current.
    io.wr(0x409500, 0x80000000 | (instance >> 12))
    io.wr(0x409504, 0x00000001)
    for _ in range(100000):
        if io.rd(0x409800) & 0x80000000:
            break
    else:
        raise RuntimeError("FECS did not accept the channel")
    io.wr(0x000260, 0)  # gf100_grctx_generate_main, ctxgf100.c:1349.
    for pack in ("gk110_grctx_pack_hub", "gk110_grctx_pack_gpc_0", "gf100_grctx_pack_zcull",
                 "gk110_grctx_pack_gpc_1", "gk110b_grctx_pack_tpc", "gk110_grctx_pack_ppc"):
        mmio(io, inits, packs, pack)  # ctxgf100.c:1352-1357.
    wait_idle(io)
    idle_timeout = mask(io, 0x404154, 0xFFFFFFFF, 0x00000000)
    patches(io, t, pagepool, bundle, attrib)
    for reg, bit in ((0x418C6C, 0x1), (0x41980C, 0x10), (0x41BE08, 0x4), (0x4064C0, 0x80000000),
                     (0x405800, 0x08000000), (0x419C00, 0x8)):
        mask(io, reg, bit, bit)  # ctxgk104.c:897-902.
    floorsweep(io, t)
    wait_idle(io)
    icmd(io, inits, packs, "gk110_grctx_pack_icmd")
    # ctxgf100.c:1387-1390: gf100_gr_icmd runs again for sw_veid_bundle_init. The
    # GK110B has no such list, so only the two bracket writes remain (gf100.c:1102,1131).
    io.wr(0x400208, 0x80000000)
    io.wr(0x400208, 0x00000000)
    io.wr(0x404154, idle_timeout)
    mthd(io, inits, packs, "gk110_grctx_pack_mthd")
    io.wr(0x000260, 1)
    mask(io, 0x419EB0, 0x00001000, 0x00001000)  # ctxgk110.c:820; r418800 writes nothing (ctxgk104.c:857).
    wait_idle(io)
    mask(io, 0x409B04, 0x80000000, 0x00000000)  # ctxgf100.c:1518-1526 context unload.
    io.wr(0x409000, 0x00000100)
    for _ in range(100000):
        if not io.rd(0x409B00) & 0x80000000:
            break
    else:
        raise RuntimeError("context unload did not end")
