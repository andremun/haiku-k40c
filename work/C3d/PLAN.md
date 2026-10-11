# Plan for C3d: Subsystem model for chan

## Steps

1. List all 17 members from `analysis/hwmodel/chan.json` (done).
2. Read source for 6 functions: gk104_chan_stop, gk104_chan_start,
   gk104_chan_unbind, gk104_chan_bind, gk104_chan_ramfc_write,
   gk104_chan_bind_inst (caller of bind), gf100_chan_userd_clear,
   gk110_chan_preempt.
3. For each member, decide role, needed_for_compute, what, certainty,
   evidence, and depends_on.
4. Write `analysis/hwmodel/decisions/chan.json`.
5. Run `python3 tools/hwmodel.py && make check 2>&1 | grep chan`.
6. Fix any failures, then handoff.

## Key sources
- `reference/nouveau/nvkm/engine/fifo/gk110.c:36` — gk110_chan_preempt
- `reference/nouveau/nvkm/engine/fifo/gk104.c:40-120` — stop, start,
  unbind, bind, bind_inst, ramfc_write, ramfc table, userd table
- `reference/nouveau/nvkm/engine/fifo/gf100.c:118-148` — userd_clear,
  gf100_chan_inst
