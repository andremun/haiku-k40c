# Immutable POST binding and access policy (S1POST)

The new binding owns the exact approved ROM, derives its execution inputs, and
checks accesses against the current instruction. It remains a host simulation.
The snapshot/parser/policy are freestanding; the bound execution adapter still
uses hosted board helpers. No hardware backend or native owner integration is
provided by this task.

## Owned inputs

`PostImage` copies all 181760 bytes before computing SHA-256. The only approved
digest is ADR 004's existing identity. It accepts no caller digest, table pointer,
root, execution flags or RAM index. The snapshot and layout are private; no
mutable view is exposed. Copy and move are deleted. Source-buffer mutation after
construction cannot change execution. The caller supplies a valid source extent
and serializes selection/execution. Store both image and layout in persistent
storage or a host heap, never on a kernel stack.

`PostLayout` performs bounded BIT-I/M parsing, main/extra root selection, direct
call coverage, reviewed opcode lengths, structured repeat checks, condition and
macro entry bounds, register inputs, shifts, generated ranges, and selected
GPIO/CCB layouts. Referenced condition/macro entries cannot overlap instructions.
Its public non-owning inspect method is for inspection/tests and grants no approval.
Only PostImage's own private parse participates in execution.

All paths to the selected POST roots are conservatively inspected. Feasible
conditions, call depth and termination are not proved statically. Runtime limits
remain mandatory. This is an exact-image subset, not a general BIOS parser.
Contextual, unknown-bit and unaligned register encodings are rejected. The pinned
Nouveau wrapper can normalize/mangle them (`bios/init.c:144-178`); the approved
ROM's audited operands require none of that handling. No default head/OR/link is
invented. Display encoder roots outside POST remain excluded.

`selectRam` requires a host backend and reads the strap once per image, including
failed attempts. The source read is 0x101000 mask 0x3c shifted by 2
(`bios/ramcfg.c:29-33`). Group resolution follows BIT-M and M0203 first-match plus
fallback semantics. Invalid groups fail, with no modulo conversion or retry.
RAM-restricted opcodes use the cached group. Explicit register operands in the
ROM remain separately governed by their own instruction permissions.

## Execution and permissions

`BoundPost::runPost` accepts budgets only. It requires approved immutable inputs
and successful RAM selection. It executes main roots followed by the extra root,
with fresh execution flags per root (`bios/init.c:2331-2344`). One total step
budget and host deadline cover all roots. Every guarded register/byte/I2C effect
checks the deadline and monotonic clock. Callbacks must themselves be bounded.
The image permits one attempted POST; the guest-wide persistent latch must still
be supplied by native owner integration before hardware use.

Access policy is per decoded instruction offset, register, width and read/write
direction. It derives core operands, every generated sequence address, and used
condition/macro operands from the private snapshot. It also derives the approved
IO/CRTC/GPIO effects and dedicated I2C pin register from source-backed helper rules.
Unknown instruction positions, payload interiors, wrong widths, unknown encodings
and unrelated registers are denied. Addresses are not taken from captured DMA values.

ADR 004's six rows now live in freestanding BoardPolicy.* and are shared with the
older hosted adapter. Their digest, offsets, opcodes and meaning are unchanged.
GPIO at 0x89c2 remains denied if active. Skipped IO retains its two waits without
register effects. Guarded helpers use the snapshot; I2C bus/address/register/value
must match its approved descriptor and pairs. The host I2C transaction callback
remains a trusted bounded transport. Physical transport wiring is still gated.

The policy constrains operation addresses, directions and widths. The interpreter
and helper implementations produce write values and ordering. This is not an
independent proof of every written bit or a replacement for stage review.
No ROM hash, parser success, cached group, or access match authorizes hardware.
Both supplied transports must report host simulation, and that gate is preserved.
Partial simulated effects can precede failure; no cleanup/recovery is implied.

## Evidence and tests

`tools/post_policy.py` independently decodes access candidates and queries the
compiled `tests/post_probe.cpp`. Its generated aggregate report is
`work/S1POST/policy-check.json`; --check compares exact text without writing.
The report binds ROM, policy and source hashes and always sets production_eligible
false. It is checked by make check under the existing private-ROM skip rule.
Synthetic parser and tool tests also run without the private ROM.

KNOWN from the approved ROM/source: 530 potential starts, eight POST roots,
777 allowed operation tuples (218 read, 559 write). The 34,128 positive/negative
queries match the compiled policy. This is SOURCE_ONLY semantic evidence.

The host exercise covers mutation, wrong images, missing selection, failed strap
read/retry refusal, hardware refusal, execution retry refusal, I/O failure, timeout,
clock rollback and total budget exhaustion. Across both fallback register profiles
and all 16 strap candidates, 16 artificial scenarios complete; 16 stop at the
explicitly denied GPIO. Neither outcome is hardware bring-up evidence.
The original board trace comparison still matches all 20 IO/CRTC accesses.

PostImage.cpp, BoardPolicy.cpp and Sha256.cpp cross-compile against the matching
Haiku headers with freestanding C++, no RTTI/exceptions, and frame warnings above
4096 bytes treated as errors. They have not been loaded or executed natively.
BoundPost remains hosted through its board helpers. No VM or card stage ran.

## Remaining integration

A later task must place the immutable snapshot and executor in the persistent
owner, supply freestanding reviewed helpers and stage transports, and prove that
all lifetimes and the guest-wide latch apply to that execution. Preserve the
existing default-denied DMA contract. Verified IOVA/visibility, VRAM ownership,
fault/readiness coverage and quiescence remain open. A7 still requires review and
the user's explicit go-ahead. No write-stage package is ready from this task alone.
