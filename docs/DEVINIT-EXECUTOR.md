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
operations are delegated and default-denied by the base backend: ZM_I2C_BYTE, ZM_CR, IO, GPIO,
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
- ZM_REG (0x7a) to `0x000200` sets bit 0 of the value (init.c:1901-1902).
  Only this opcode has the rule. The ROM has `ZM_REG R[0x000200] = 0x00002020`
  at 0x8638; the Linux run wrote `0x2021` (mmiotrace line 45511,
  TRACE_VERIFIED). The 2026-10-16 core omitted the rule; fix in task S1A,
  test `tests/accept/s1a_accept.cpp`.
- IO is **not only VGA port I/O**. On NV50+ port 0x3c3/data 1 causes MMIO writes
  and waits in Nouveau (init.c:1623-1656). Therefore the earlier suggestion to
  omit legacy VGA operations cannot establish compatible bring-up. Even skipped
  IO is sent to the denied helper boundary, rather than silently hiding those
  unconditional helper effects. A5 must review this operation too.
- GPIO_NE applies defaults to functions outside the exclusion list, including
  mux/routing effects. I2C requires board bus resolution and 7-bit address
  conversion, not just register-range permission. No approval is inferred from
  ROM origin. ADR 004 permits the specified write to the unidentified device. Its identity remains UNKNOWN.

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

## S1BOARD: permission-bearing host adapter

`src/devinit/Board.cpp` implements `PolicyBackend` and four helper semantics.
This adapter remains host-only. It does not change the interpreter hardware gate.
Both the register backend and the byte/I2C transport must report host simulation.
The base backend still denies every board operation unless a reviewed adapter supplies it.

`PolicyBackend` copies the exact-size ROM and computes SHA-256 over that owned copy.
The six policy rows contain the ADR 004 hash, ROM offset, and opcode.
Wrong hashes, offsets, opcodes, lengths, or payload bytes fail before helper effects.
The caller's buffer cannot change the bound snapshot. No caller-supplied digest grants permission.
Denied operations and helper outcomes reach the transport audit callback.
`PolicyBackend::run` uses the owned ROM and propagates helper I/O failures to the interpreter.

The helper boundary has these semantics:

- `IO` uses the NV50+ register sequence and byte-wide VGA MMIO.
  Its two 10 ms waits still run when skipped. Skipped IO performs no register or port access.
- `ZM_CR` writes the index and value to the two byte-wide CRTC MMIO addresses.
- `ZM_I2C_BYTE` reads the ROM's CCB default index and converts the stored address to seven bits.
  The transport receives the resolved bus descriptor and one register/value pair per call.
  An unavailable bus or NACK stops the run.
- `GPIO_NE` excludes the listed functions and unused entries, then applies table defaults.
  GK110B uses GK104 GPIO with GF119 drive/reset helpers (device/base.c:1779, gpio/gk104.c:64-69).
  Drive direction, level, latch, and routing fields follow those helpers.
  Duplicate functions retain Nouveau's repeated reset and first-match logic behavior.

DCB 3.0 through 4.1 headers, GPIO 4.1 entries, and CCB 4.0 NVIO/4.1 PMGR entries
are the reviewed table formats here. The approved ROM uses DCB 4.0, GPIO 4.1, and CCB 4.0.
Other layouts fail closed. No display-output context is supplied for I2C index 0xff.
The approved instructions use index 0x80, so no display-output fallback is needed.

Physical I2C transactions and bus initialization remain transport/pre-start integration work.
No physical byte/MMIO transport is provided. The current adapter owns STL storage and is host-only.
A4 prerequisites, B2 mappings, and A7 one-shot startup remain separate tasks.
Failures can follow partial simulated effects. No rollback or safe hardware cleanup is implied.
Callbacks must be bounded. The interpreter checks its deadline after the helper returns.

`tools/board_trace.py` compares the IO sequence and following CRTC write against
`reference/linux-run-debug/mmiotrace.txt.xz:45579-45598`.
The capture supplies initial read values, never a replay of its writes.
The generated report is `work/S1BOARD/trace-check.json`.
Run `python3 tools/board_trace.py --check` to compare it without writing.
The comparison verifies access facts for that captured state. It is not a hardware helper run.
