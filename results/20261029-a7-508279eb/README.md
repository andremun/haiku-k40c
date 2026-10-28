# Fifth approved A7 attempt: POST ran, stopped at the MAX6649 I2C write

Run 2026-10-29 by Claude Code, after the user's explicit yes for one run of
package build/a7/package-run5/ (commit 0f96f68). `build.py --check` and
`run.py --host-check` passed. Command: `python3 tools/a7/run.py --run-approved-A7-once`.
The consumed marker remains. No retry ran (ADR 006).

KNOWN / HARDWARE_VERIFIED under Haiku (serial.log):
- B5 identity: PMC_BOOT_0 0x0f1240a1, PCI command 0x0007 (lines 839-850).
- Owner prepared, card reserved, flush target armed before the script at guest
  physical 0x15fc000 (`ARM_BEFORE a=0x15fc000 b=0x15fc0`, line 863). The host
  witness and grant were exchanged (request.bin, grant.bin, cutoff.json).
- The card's start-up script ran: 532 instructions executed, 38 skipped
  (Linux reference: 560 and 38). Executed board operations: IO 0x8506 (line 931),
  ZM_CR 0x850b (932), ZM_I2C_BYTE to device 0x20 at 0x862f (1001, completed),
  GPIO_NE 0x89b7 (1007), ZM_CR 0x85e8 (1393).
- The script stopped at 0xab8d, opcode 0x4d, ZM_I2C_BYTE to the MAX6649 at
  I2C 0x4c: `POST_RESULT a=0x5 b=0xab8d` (line 1434). Error 5 is `Io`
  (src/devinit/Interpreter.h). Then `FAIL startup a=0x4 b=0x9`, owner Failed
  and storage retained (`RETAINED a=0x1 b=0x3`, lines 1435-1436).
- Post-POST readback, re-arm and readiness were NOT_REACHED.

R5: kernel-before.log and kernel-after.log are identical; no new filtered line
and no allowed line (result.json `allowed_kernel_lines` empty). Teardown: host
PCI command 0x0002 after exit, bus mastering off. No QEMU remains.

UNKNOWN: why the 0x4c transfer failed. The serial log does not record the I2C
error class. The Linux run waited about 100 ms with no MMIO access between this
instruction (dmesg line 3185, 11.700316 s) and its bus acquire (11.800115 s);
mmiotrace shows no access between 11.7003 s and 11.8001 s. The Linux transfer
then took 16.4 ms, with gaps up to 3 ms after releasing the lines.

The card was left partly initialised by an incomplete POST until the next VFIO
open, which resets it. This is not a POST success and not S1 evidence.
