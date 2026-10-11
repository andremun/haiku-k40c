# Review of B5, attempt 1 (2026-10-11): REWORK

The format is right and the tool works (`--check` passes, registers match
B3). The content is not accepted. The first check was too loose; it is
stricter now, and `make check` shows 12 failures on this attempt.

Keep `tools/min_chain.py` and change its tables. Do not start again.

## Defects

1. **Reasons written from the names, not from the source.** Several are
   wrong: `mc` is not a memory controller, `privring` is not a ring
   buffer, `top` has nothing to do with several GPUs, `imem` is not
   "instantiated memory", HWW is not a workqueue. Before you write a
   reason for a subsystem, run `grep -rn "device->NAME\|nvkm_NAME_"
   nvkm/engine/gr/gf100.c nvkm/engine/fifo/gk104.c nvkm/subdev/fb
   nvkm/subdev/mc nvkm/core | head -5` (NAME is the subsystem). If the
   GR, FIFO or FB code uses it, it is `needed` and the reason names the
   file and line. If nothing uses it, say that.
2. **`optional` is used for 20 of 31 subsystems.** Four of these are
   needed: `top` (`nvkm/engine/fifo/gk104.c:764`), `ltc`
   (`nvkm/engine/gr/gf100.c:94`), `timer` (`nvkm_msec`,
   `nvkm/engine/gr/gf100.c:758`), `privring` (register bus to the GR
   units). Check the other sixteen with the grep of point 1.
3. **Steps 1, 3, 4 and 5 name only a constructor.** `*_new` allocates a
   structure. Add the function that starts the hardware (look for
   `.init =` in the same file), or set the status to `partly-known`.
4. **The channel is the last step, after the launch.** A job needs, in
   this order after `gf100_gr_init`: the firmware start
   (`gf100_gr_init_ctxctl_int`, `nvkm/engine/gr/gf100.c:1831`, this one
   belongs to the GR step), the channel (`gk104_chan_ramfc_write`,
   `gk104_runl_commit` in `nvkm/engine/fifo/gk104.c`), the GR context of
   the channel (`gf100_gr_chan_new` at `nvkm/engine/gr/gf100.c:377`,
   `gf100_grctx_generate` at `nvkm/engine/gr/ctxgf100.c:1436`), and only
   then the Mesa setup and launch.
5. **The chain stops at the launch.** Add the steps after it: how the
   job end is seen, and reading the result buffer. Status `unknown` is a
   correct answer where the analysis has nothing; say what is missing.
6. **`init` is marked `compute`.** It is `gf100_gr_init`, which calls
   all the other hooks: `both`.
7. `min_chain.md` says "Four hooks are graphics-only" and lists three.
   Write the document again from the new JSON.

## What was good

One session, no context compaction, the tool derives lines and registers
itself, and the firmware entries are right.

# Review of B5, attempt 2 (2026-10-11): ACCEPT

All 12 failures are fixed. The chain now has 17 steps in the right order
(engines, firmware start, channel, GR context, Mesa setup, launch, wait,
read back), 11 needed subsystems, and the steps that the analysis does
not cover are marked `partly-known` or `unknown` with a reason.

Limits of this result, for the tasks that use it:

- The attempt fixed what the check named and nothing more. The reasons of
  the 16 `optional` subsystems are still written from the names. The
  scaffold checked them with grep against the GR, FIFO, FB, MC and core
  code: `bus`, `ce`, `devinit`, `dma`, `fuse`, `i2c`, `iccsense`, `mxm`,
  `sw` and `volt` are not used there; `bios`, `clk` and `gpio` are used
  only by the memory reclocking code in `fb/ram*.c`; `pci` only to
  rearm MSI (`core/intr.c:179`); `therm` only for clock gating
  (`gr/gf100.c:2369`). So `optional` holds for these, but do not quote
  their `reason` texts.
- `pmu`: `gf100_gr_oneinit` calls `nvkm_pmu_pgob(device->pmu, false)`
  (`gr/gf100.c:2006`), which switches power gating off. Whether the K40c
  needs this after the video BIOS has run is not known. The scaffold
  changed the `pmu` reason in `tools/min_chain.py` to say this (status
  stays `optional`) and regenerated the JSON. Phase C should settle it.
- The `use` values of the GR hooks other than `init`, `init_zcull` and
  the two ROP hooks are not verified.
- Steps 6, 8, 9 and 10 (`top`, `ltc`, `timer`, `privring`) name no
  function. Their init functions are work for C3.
