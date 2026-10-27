# Macro task S1BOARD: Board-operation policy and helpers

## Why

Claude accepted S1B5. ADR 004 authorizes six observed instruction locations on
one ROM. Implement their semantics on the host without opening the hardware gate.

## Inputs

Read AGENTS.md, REVIEW.md, ADR 004, docs/DEVINIT-EXECUTOR.md,
src/devinit/, and the existing devinit tests. Follow these pinned sources:
- nvkm/subdev/bios/init.c:215-300,1033-1050,1623-1656,2191-2224.
- nvkm/engine/disp/vga.c:27-52,104-108.
- nvkm/subdev/gpio/base.c:41-92, gf119.c:27-65, gk104.c:62-80.
- nvkm/subdev/bios/dcb.c:28-62, gpio.c:33-128, i2c.c:32-143.
- nvkm/subdev/i2c/base.c:48-75 and include/nvkm/subdev/i2c.h.
Use the private ROM from reference/vbios/README.md for offline checks only.
Read capture lines 45579-45598 of reference/linux-run-debug/mmiotrace.txt.xz.

## Outputs

- Record Claude's supplied S1B5 ACCEPT and the future retry rule.
- A policy with exactly six rows (ROM SHA-256, offset, opcode), default deny.
- Helpers for IO, ZM_CR, ZM_I2C_BYTE, and GPIO_NE.
- IO preserves Nouveau's unconditional two 10 ms waits when skipped.
- I2C resolves the ROM's default bus and uses 7-bit addresses.
- GPIO_NE uses ROM defaults and mux/routing fields, preserving exclusions.
- A host-only adapter connects policy and helpers to the interpreter.
- Host tests cover policy mismatches, errors, waits, tables, and hardware refusal.
- A tool compares IO register accesses with the recorded trace.
- Update documentation, licensing, status, and work/S1BOARD/ records.
- Regenerate docs/register-provenance.md with tools/provenance.py for the new constants.

## Limits

No hardware, VM, host binding, or GPU reset. Keep the interpreter hardware gate.
Do not implement the later B2, A4, or C2 macro tasks.
Do not copy Nouveau code or embed firmware payloads in committed files.
Do not edit reference files, tests/accept/, or tools/check_repo.py.

## Check

Run make check before every commit. Use synthetic tests for helper semantics,
then verify policy and capture matching against the external ROM and pinned trace.
Record commands, source pins, and logs. Keep all new results HOST_ONLY or SOURCE_ONLY
unless their exact facts match the recorded Linux trace (TRACE_VERIFIED).
