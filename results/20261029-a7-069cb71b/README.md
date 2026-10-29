# A7 buffered POST and readiness — PASS

2026-10-29. One directly user-approved launch of unchanged package-buffer from
commit b0c24e4. User: "I approve because this is not a major change."
No independent Claude ACCEPT is claimed. Approval is consumed; no retry ran.

## Scope

KNOWN / HARDWARE_VERIFIED for this K40c (0000:04:00.0) under Haiku: the native
POST executor returned success at ROM 0xac0c, and its independent
readiness checks passed. This is not S1 success, compute execution, D1, DMA payload
publication or coherency evidence. The mapping witness remains structural only.

Command: `K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom" python3 tools/a7/run.py --run-approved-A7-once`.
All commands/artifact hashes, captures and sources are bound by
`work/S1A7RUN7/report.json` (`tools/a7/result_report.py --check`).
The exact launched suite is also embedded in launch.json.

- Manifest SHA-256: `a4b47b8a3e8f56d533170b0bccad3e3f037ed03e627b1d16e017248f0b244bdd`.
- Owner SHA-256: `944bdaf424789914a7b8a8b8fe3af272ea1f4d93d387e931d336aa084ce4c087`.
- Client SHA-256: `d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122`.
- Helper SHA-256: `58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977`.
- Identity SHA-256: `8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f`.
- Kernel SHA-256: `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62`.
- ROM SHA-256: `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`.

## Instruction selection and I2C

Native trace: 537 active and 38 skipped instructions. Linux's raw 560/38 totals
include 23 synthetic offset-zero REPEAT messages, documented in
analysis/devinit_inventory.md:60 (Nouveau bios/init.c:658-677,724-733).
Removing those messages gives the exact same 575 PC/active-state entries as
Haiku. Native opcode bytes also match the approved ROM. This establishes
instruction selection, not register-value or helper-timing equivalence.

The 0x20 transaction completed. For each intended sensor pair at 0xab8d,
address 0x4c, registers 0x19/0x0d, value 0x73, the driver recorded four address
NACKs at phase Address/bit 8 with successful bounded STOP. Attempts 1-3 report
RetryAddress; attempt 4 reports ReferenceNack and continues. This matches the
approved ADR 010 outcome and Linux capture. Sensor configuration/presence is
not established. No payload after an address NACK is INFERRED from the code
path; there is no native per-bit wire trace. All nine attempt records are saved.

## Timing

| Reported measure | Microseconds |
|---|---:|
| POST elapsed | 88805 |
| Requested delays | 83798 |
| Measured delay intervals | 84847 |
| Measured MMIO-call intervals, total | 2256 |
| Maximum MMIO-call interval | 104 |
| Deferred diagnostic drain | 21694572 |

There were 453 delay calls and 1654 measured MMIO calls.
MMIO intervals include scheduling and timestamp overhead, not pure device latency.
Of nine condition instructions, 0x8ec8, 0x85a2 and 0x9b9e sampled twice; the
others sampled once. All final matches were true in the raw POLL_STATE records.
The buffer retained 635 records with no overflow or clock fault.

POST completed in about 89 ms; deferred output took about 21.7 s outside the
10 s POST/15 s controller budgets. Together with the native logger benchmark,
this strongly supports diagnostic overhead as the run6 timeout cause (INFERRED).
The exact past run6 time breakdown remains UNKNOWN. Total guest time was
134.02 s within the unchanged 600 s deadline.

## Flush page and readiness

The fresh structural witness covers candidate GPA/IOVA 0x16d2000.
IOVA=GPA remains INFERRED. The pre-POST programming event gives encoded value
0x16d20; reaching POST implies callback success. There
is no initial register readback. Actual post-POST readback of 0x100c10 is **0**.
The driver then programmed the same encoded value again and completed readiness.
There is no readback after that second write. Why the post-POST readback is zero
is UNKNOWN; do not assume the register retained the initial programming.

Timer advanced from 0x5418360 to 0x551fb20. VRAM size
was 11520 MiB. Scratch passed at three sampled dwords in the owned
page starting 0x40000 (offsets 0, 0x100, 0xffc), with pattern and
complement passes plus BAR flush. This is not full-page or DMA validation.
Pending 0x100 was zero before/after scratch by the unchanged guarded PASS path
(INFERRED; no separate raw pending-value event). The owner retained token 1 in
Complete state 2. No allocation was released while the guest could reference it.

## Host end state

The R5 before/after files are byte-identical (15998 bytes),
with zero selected-class delta and no allowed_kernel_lines entry. This is the
filtered R5 scope, not a claim about a clean full kernel log.
Teardown records host PCI command 0x0002, bus mastering off, and owned QEMU/tracer
exit. A separate process-table check found no QEMU guest. No manual reset or root
command ran. The consumed marker remains in build/a7/package-buffer/.
