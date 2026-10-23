# S1 plan: verification follow-up and scaffold review of 2026-10-20 (history)

Moved from `docs/S1-PLAN.md` on 23 October 2026. The 2026-10-21 review in that file supersedes them.

## Verification follow-up (2026-10-16)

[The verification gates](S1-VERIFICATION.md) record a new pass to revise
possible mistakes made by "Local" and get closer to machine-dependent
implementation. V1 adds independent host regressions and a freestanding S1
controller/backend contract; it does not complete B2/B3 or C2/C3. The ROM
was subsequently located in `~/mediaflux/vbios/` and verified against its
recorded hash (see `reference/vbios/README.md`). V2 restored all five pinned
source inputs and rebuilt the independent decoder;
full repository checks now pass. ABC1 rebuilt the native cross-toolchain and
cross-compiled the backend/core components; native link/load and actual S1
remain pending. See `docs/ABC-CARDLESS-OUTCOME.md`.

## Scaffold review 2026-10-20

The V1, V2 and ABC1 work (2026-10-16 to 2026-10-18) was done outside
the local agent, by user-directed sessions. The scaffold has read the
outcome documents and checked these points:

- Verified against Nouveau v6.12: `0x002634` is channel preemption and
  the runlist is committed through `0x002270`/`0x002274`
  (`gk104.c:436-447`, `gf100.c:43`); `TIME` operands are microseconds
  (`init.c:1781-1795`); `IO` to port `0x3c3` with data `1` has register
  side effects (`init.c:1631-1647`).
- `make check` passes on this host (2026-10-20). Three of the four
  generated checks pass. `tools/devinit_sources.py --check` fails here:
  it needs `reference/envytools/nvbios/nvbios.c`, but the envytools
  reference is a sparse checkout (`docs/`, `rnndb/`), and
  `tools/restore_verification_refs.py --check` reports it "clean"
  without seeing the gap. To fix in the next task.
- ESC-001 is resolved: a KVM cardless guest links and loads the probe.
  `/dev/kvm` is now present on this host.

Not yet reviewed in detail by the scaffold: the A3 rework outputs, the
executor core (`src/devinit/`), the memory layer (`src/memory/`), the
Haiku backend (`src/os/`) and `docs/S1-RECIPE.md`. The table below
gives their state as their authors recorded it.

**New item for the board-operations decision (A5).** The `IO` helper
for port `0x3c3` writes card registers, not only a VGA port: it masks
bit 30 of `0x000200` (the engine-enable register) off and on, sets bits
in `0x00e18c`, and writes the display registers `0x614100` and
`0x614900`, with two 10 ms waits. The K40c has no display output, so
whether those display writes are safe on this card is unknown. This
joins the four decisions in `docs/BOARD-OPERATIONS.md`.

**Next steps, in order. None starts without the user.**

1. Scaffold review of the items listed above as not yet reviewed, with
   findings fixed on the host. No card.
2. Fix the envytools reference gap so that every generated check runs.
3. User decisions: the five board-operation items, and the third
   opinion (outside review) before any card stage.
4. Remaining host work: B2 real allocation and mapping adapter, A4
   production helpers and pre-start state, C2 open choices (MMU,
   routing, quiescence).
5. First card stage: B5 identity reads only, in the KVM guest with the
   development card passed through. A slow-window read writes its
   selector, so B5 must not use it.
