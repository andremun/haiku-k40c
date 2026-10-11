# C3d Findings

## Source files read
- `nvkm/engine/fifo/gk110.c:36` — gk110_chan_preempt (10 lines)
- `nvkm/engine/fifo/gk104.c:40-120` — stop, start, unbind, bind, bind_inst, ramfc_write, ramfc table, userd table
- `nvkm/engine/fifo/gf100.c:118-148` — userd_clear, gf100_chan_inst

## Key observations

1. The chan table (gk110_chan) is NOT a member of nvf1_chipset; it's an extra model whose constructor is gk110_fifo_new and whose table is gk110_chan.

2. gk110_chan_preempt is the only GK110-specific channel function; all others are inherited from gk104/gf100.

3. bind() internally calls bind_inst() — not a separate top-level table member. bind_inst is not in the gk110_chan table but is called by bind.

4. All channel control registers use offset pattern: 0x800000 + (chan->id * 8) for instance block, 0x800004 + (chan->id * 8) for control.

5. ramfc_write uses nvkm_wo32 (write-through-kmap) which is not tracked in the MMIO access database (only nvkm_wr32 and nvkm_mask are).

6. gf100_chan_userd_clear writes to 10 different shadow-register offsets in the USERD area.

## Rework history
- 1 rework: fixed evidence line numbers for 5 members (userd.clear, ramfc.write, unbind, start, stop) where initial line numbers pointed to blank lines or the wrong function.
