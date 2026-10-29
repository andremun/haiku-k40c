# Sixth approved A7 attempt: POST timeout before the sensor operation

Run on 2026-10-29 after the user supplied Claude's ACCEPT review of 2818763
and explicitly authorized one run of build/a7/package-i2c/. Prelaunch
build.py --check and run.py --host-check passed. R5 was live, VFIO group 23
belonged to mariom1, and no QEMU guest was running. The exact reviewed owner,
client, helper and identity hashes matched. No source/artifact change preceded
execution. The consumed marker remains. No retry occurred (ADR 006).

Command (repository root):

```sh
K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom" python3 tools/a7/run.py --run-approved-A7-once
```

launch.json records source commit 28187634b07f5cc9613025cb9e714e035891a249,
the complete suite/hashes, fixed 0000:04:00.0 VFIO group and QEMU command.
Package manifest SHA-256: e2a6920582db33493dfaf6d7f39b858c0b205f2baacc3f71b848e128d41ed0e5.
Owner: a14758b05384bf5669ac49795903709e1dd5a9c70beccc8a7cf46787c1c625c3.
Client: d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122.
Helper: 58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977.
Identity: 8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f.
Other exact hashes, including observer/kernel/ROM, are in launch.json's suite.

## Native observations

KNOWN / HARDWARE_VERIFIED for this card under Haiku only (serial.log):

- B5 reports PCI command 0x0007 and PMC_BOOT_0 0x0f1240a1 twice (877-878,
  888-889). Native preparation and the request/grant exchange completed.
- Pre-POST arm write was issued for candidate IOVA/GPA 0x15df000, encoded as
  0x15df0 for register 0x100c10 (901). The later script entries establish that
  the programming callback returned successfully. The old register value was
  not read. Structural mapping witness is in cutoff.json, with request.bin and
  grant.bin. IOVA=GPA remains INFERRED, not a payload visibility claim.
- The 0x862f I2C operation to address 0x20, register 0xdd, value 0x03 reports
  Complete on attempt 1, primary None, cleanup None, phase Value/ACK bit 8
  (1040-1045). Transfer guard elapsed is 969 us, cleanup 33 us, 432 guard
  operations. This is the driver's transaction result, not device readback.
- There are 490 SCRIPT_ACTIVE and 38 SCRIPT_SKIPPED entries. Counts are trace
  entries, including the final attempted instruction, not proof that every
  associated write completed. Linux's reference counts are 560 and 38.
- POST_RESULT a=0x9 b=0x85d6 (1436) is Error::Timeout. FAIL startup follows,
  then RETAINED a=0x1 b=0x3 (1437-1438): Failed owner, retained reference.
- The 0xab8d sensor operation was NOT_REACHED. There are no sensor I2C records.
  The new sensor address-NACK continuation policy was not exercised on hardware.
- Post-POST 0x100c10 readback/re-arm, timer, VRAM size, scratch and pending-register
  readiness checks were NOT_REACHED. Their values/results remain UNKNOWN.

This is a hardware-executed POST failure under Haiku, not POST success or S1
success. No readiness result is established. K40-A7-END alone is not a pass.

## Stop interpretation and containment

KNOWN: error value 9 maps to Timeout in src/devinit/Interpreter.h. The POST
software budget defaults to 10,000,000 us. Both Interpreter::deadline and
BoundPost::guard can return this error. Opcode 0x7a at the reported PC is a
register-write instruction, not a register-poll instruction. The log does not
identify which guard fired or whether that last register write was issued.
UNKNOWN: why this run exhausted its budget earlier than run5. Scheduling,
tracing/logging overhead and card behaviour are not separated by this capture.
Do not call this a proven GPU hang, I2C timeout or missing-settle failure.
The overall guest elapsed time is 144.8 s, below the 600-second watchdog.

kernel-before.log and kernel-after.log are byte-identical (15998 bytes each).
This is an empty R5 selected-class delta, not a clean full-kernel-log claim.
result.json records no allowed_kernel_lines. teardown.json records host PCI
command 0x0002, bus mastering disabled. The owned guest/tracer exited. A real
host process check found no QEMU. No manual reset, root action or retry occurred.

The launcher stopped on the native failure before job-output.txt/job.exit were
uploaded. Those files are absent. The raw serial failure and result.json are
the verdict. The package is consumed even though POST failed. Another run needs
a new explicit approval after review of its concrete package (ADR 006/008).
