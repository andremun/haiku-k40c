# S1BOARD findings — 2026-10-27

## Scope and review

The user supplied Claude's S1B5 ACCEPT and authorized the next host-only macro task.
Record: work/S1B5/REVIEW.md. ADR 006 now requires user approval after any launcher stop.
The A7 one-shot requirement and B2/A7 bus-mastering note are in docs/S1-PLAN.md.
No VM, card, host binding, or GPU reset command ran in this macro task.

## Source facts (KNOWN / SOURCE_ONLY unless stated otherwise)

The six allowed locations and the image hash come from ADR 004.
GK110B chooses gk104_gpio_new (device/base.c:1779).
GK104 uses GF119 drive/reset and has 32 lines (gpio/gk104.c:64-69).
GF119 reset writes direction/level, the latch, and routing fields (gpio/gf119.c:27-64).
GPIO_NE selects functions outside its exclusion list (bios/init.c:2191-2224).
Duplicate functions repeat the reset. Logic comes from the first matching function/line
(bios/gpio.c:125-128, gpio/base.c:80-92). The implementation preserves that behavior.
The actual ROM has DCB 4.0, GPIO 4.1, and CCB 4.0. Inspect the external ROM, not a device.
Default I2C index comes from CCB header byte four, not a fixed bus number
(i2c/base.c:53-64). The helper resolves it and supplies the physical bus descriptor.
A physical I2C engine/adapter and pre-start bus initialization remain outside this task.

## Host results

The current C++ unit suite reports 572 checks and zero failures.
SHA-256 matches Python hashlib for 13 deterministic inputs across padding boundaries.
The real-ROM exercise allows exactly six rows and rejects changed ROM/payloads,
truncation, null/overflow inputs, and the Linux-skipped GPIO at 0x89c2.
The owned snapshot survives mutation of the caller buffer.
An I2C failure stops the interpreter. Skipped IO waits reach its deadline.
Both transports must identify as host simulations; hardware remains disabled.

KNOWN / TRACE_VERIFIED access facts: the generated host IO/CRTC events match
all 20 accesses at mmiotrace.txt.xz:45579-45598. The last two belong to ZM_CR.
Skipped IO emits only the two 10 ms waits. Report: tools/board_trace.py compare_io,
work/S1BOARD/trace-check.json. This is host comparison, not a card run.

The first full make check found missing per-line constant annotations and an outdated
register-provenance document. Helper tests and trace comparison still passed.
Added pinned source citations, marked software-only hash/permission values explicitly,
and regenerated docs/register-provenance.md with tools/provenance.py.
No reviewer check was changed. No functional helper change was needed for those failures.
