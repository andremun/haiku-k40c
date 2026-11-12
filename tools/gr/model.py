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
        self.tpc_nr, self.ppc_mask = [], []
        for i in range(self.gpc_nr):
            self.tpc_nr.append(io.rd(gpc_unit(i, 0x2608)) & 0xFF)  # gf100.c:2011; u8 tpc_nr (gf100.h:107).
            mask = 0
            for j in range(ppc_max):
                if io.rd(gpc_unit(i, 0x0C30 + j * 4)):  # gf100.c:2016.
                    mask |= 1 << j
            self.ppc_mask.append(mask)
        self.tpc_max = max(self.tpc_nr)
        self.tpc_total = sum(self.tpc_nr)
        self.ppc_max = ppc_max
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
