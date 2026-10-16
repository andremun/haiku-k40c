# A4/A6: devinit execution contract and host core

2026-10-16. Sources pinned by `reference/MANIFEST.md`; per-opcode citations,
NVIDIA identifiers/condition attributes, decoder lines and source hashes are
in generated `analysis/devinit_sources.json` (`tools/devinit_sources.py --check`).
This is a new independent implementation, not code from the rejected A3 branch.

## Inputs and compatibility rule

The ROM and independent decoder are available and reproducible. A3 now checks
observed log/listing agreement, but its presentation counts include table rows.
It is not the executable program model. The executor reads raw bytes with
bounds checks and uses explicit condition/macro pointers and cached RAM group
selection. Callers must separately validate BIT-I/M dispatch, all reachable
opcodes/branches and helper/preinit effects before a production executor exists.
Nouveau behavior is the compatibility reference when documentation differs.

The cross-reference covers 24 observed opcode names plus potential ZM_REG_GROUP
(0x91), found by the raw-ROM structural preflight. Five board/helper
operations are delegated and default-denied: ZM_I2C_BYTE, ZM_CR, IO, GPIO,
GPIO_NE. The other 20 have a freestanding host simulation implementation.
No hardware backend exists for this interpreter. It refuses a backend that
identifies itself as anything other than host simulation. Do not bypass that
flag to run on a card; a reviewed hardware integration is a later change.

## Semantics and differences that matter

- Execution is Nouveau's bit-state model: execute==1 or (execute&5)==5;
  conditions set skip, RESUME clears it, NOT toggles it, and forced execution
  overrides skip. Calls share state; it is not a Boolean stack of conditions.
- The physical register wrapper must resolve encoded/contextual registers and
  enforce stage permissions. The host interpreter delegates that work; it
  does not assume every register operand is a literal safe BAR offset.
- CONDITION reads the indexed register/mask/value condition. CONDITION_TIME
  caps attempts at min(retry*50,100), sleeps 20 ms after a failed attempt and
  sets skip on exhaustion. Timeout is not a successful readiness check.
- TIME follows Nouveau's microsecond path below 1000 and its `(usec+900)/1000`
  millisecond conversion above it. The printed usec value alone is not an
  exact Linux sleep-duration trace.
- NV_REG keeps the supplied mask bits. COPY_NV_REG keeps destination dmask,
  then ORs the shifted/masked/XORed source. The decoder's rendered `& ~mask`
  wording must not override Nouveau's actual preservation mask.
- MACRO uses the macro data table at index*8 in this Nouveau path. NVIDIA marks
  the opcode deprecated; no new interpretation through a macro-index table is
  substituted. Missing macro table is a no-op as in Nouveau.
- RAM_RESTRICT_ZM_REG_GROUP selects one value per row, based on a pre-resolved
  group count/index. Nouveau caches RAM configuration on this generation to
  avoid repeated strap reads affecting the memory controller (init.c:445-458).
- RESET_BEGUN/END are markers; treating them as physical reset requests is wrong.
- IO is **not only VGA port I/O**. On NV50+ port 0x3c3/data 1 causes MMIO writes
  and waits in Nouveau (init.c:1623-1660). Therefore the earlier suggestion to
  omit legacy VGA operations cannot establish compatible bring-up. Even skipped
  IO is sent to the denied helper boundary, rather than silently hiding those
  unconditional helper effects. A5 must review this operation too.
- GPIO_NE applies defaults to functions outside the exclusion list, including
  mux/routing effects. I2C requires board bus resolution and 7-bit address
  conversion, not just register-range permission. No approval is inferred from
  ROM origin. The unresolved device remains denied.

## Safety limits and intentional restrictions

Bounds, recursion depth, instruction budget, host monotonic deadline and invalid
shift checks fail closed. Unknown opcodes never become NOPs. Partial side effects
are possible before a later error in simulation; the current core is not an
all-path preflight validator and must not be connected to hardware.

Structured nonzero REPEAT blocks are implemented. Zero-count loops, END_REPEAT
outside a loop, and DONE inside a repeat are rejected instead of attempting
Nouveau's corner-case control flow. These are intentional unsupported cases,
not claimed compatible execution. Delays and each backend call must be bounded;
the host budget cannot interrupt a callback that blocks. Table selection and
pre-POST device/helper initialization remain caller obligations.

Tests cover changing condition results, timeout-to-skip, NOT/RESUME/forced state,
calls/repeats, register masks and copies, RAM selection, macros, skipped writes,
board denial, invalid operands, read bounds, unknown opcodes, recursion/budget,
clock rollback, and the hard hardware-backend refusal. All are HOST_SIMULATION_ONLY.
No claim of A7 readiness or production A6 completion follows from these tests.

## Raw-ROM structural coverage

`tools/devinit_preflight.py` follows main/extra script pointers and both
conditional call/jump alternatives directly from the verified ROM, using
pinned BIT-I/M and opcode-length rules. It reports 530 potential instruction
starts, 25 opcode values and no structural issues for this ROM. Every observed
nonzero instruction offset is covered. This is independent of the decoder's
presentation-line inventory. It found a potential ZM_REG_GROUP instruction
(0x91) absent from observed execution; the core now handles its repeated writes
to one register. Numeric values come from the generated report, not a claim
that every path executed.

This closure is limited to direct/table control flow of the selected opcode
set. It does not validate condition/table semantics, helper side effects,
caller/display scripts outside POST roots, board targets, table overlap,
GPU readiness or correctness of real execution. Unknown instructions fail
preflight and execution. Hardware integration still requires those reviews.

The actual ROM is also exercised in 128 artificial host-backend scenarios
(eight RAM selections, two fallback register profiles, eight POST roots).
These tests permit dummy board callbacks without performing their effects;
they validate bounds/control behavior only. They do not establish compatibility
of board/helper execution or any successful initialization of the card.

`analysis/devinit_trace_join.json` links each observed instruction interval to
BAR-access counts and raw trace line ranges by their shared kernel clock. This
is time correlation, not semantic equivalence: same-time log messages, other
workers and helpers outside MMIO prevent a causal completeness claim. Skipped
intervals with accesses are review candidates, not automatic executor defects.
