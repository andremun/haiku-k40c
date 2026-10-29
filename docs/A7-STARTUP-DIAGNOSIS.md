# A7 timeout: Haiku startup and diagnostic overhead

2026-10-29. Host-only investigation, S1A7STARTUP. No guest, card access or reset.
The reviewed package and its consumed marker remain unchanged.

## Finding

**INFERRED:** synchronous serial diagnostics, VM exits and observer overhead are
likely contributors to run6 exhausting our POST wall-clock budget. This is a
better-supported explanation than a missing generic Haiku startup step.
**UNKNOWN:** how much of the budget went to logging, condition polling, MMIO,
sleep overshoot or vCPU scheduling. The evidence does not establish logging as
the sole cause. Do not extend the timeout or change hardware sequencing on this
basis alone.

**KNOWN, saved capture:** run6 stopped with software `Error::Timeout` (9) at ROM
PC `0x85d6`, after 490 active and 38 skipped instruction entries. The sensor
operation at `0xab8d` was not reached. This run therefore cannot diagnose run5's
sensor failure or test ADR 010's bounded address-NACK policy. See
`results/20261029-a7-2aadfd99/README.md` and Q9.

## What Haiku requires at startup

The [Haiku Book driver introduction](https://api.haiku.nz/topics/device-drivers/introduction.html)
explains device publication through devfs and dispatch of application operations
to driver hooks. It also distinguishes drivers from kernel-only modules.
These pages retain BeOS-era paths and details; use the pinned implementation for
current behaviour, rather than treating every example as a Haiku prescription.

| Startup question | Source and assessment |
|---|---|
| Must POST happen while the driver loads? | **KNOWN, SOURCE_ONLY:** pinned `legacy_drivers.cpp` loads through `init_hardware` and `init_driver`, publishes nodes and dispatches subsequent open/write hooks. Our client defers preparation to open and POST to the authenticated grant's write hook. This is normal syscall context, not an interrupt handler. No ten-second POST rule was found in this path. |
| Can hardware setup wait until open? | **KNOWN, SOURCE_ONLY:** the stock older-NVIDIA driver performs mapping/resource setup on first open (`graphics/nvidia/driver.c:885-996`). This is a lifecycle example, not a Kepler initialization recipe. It supports separating publication from hardware setup. |
| Does PCI reservation initialize or reset the GPU? | **KNOWN, SOURCE_ONLY:** `pci/pci.cpp:173-253` reserves the matching device through device-manager ownership. It supplies no GPU POST/reset sequence. Our native backend separately checks memory decoding and maps the BAR. |
| Are delay units wrong? | **KNOWN, SOURCE_ONLY:** `NativePlatform.cpp:61-65` uses `system_time()` microseconds, `spin()` for short waits and `snooze()` for longer waits. Haiku `timer.cpp:444` implements microsecond spin; `thread.cpp:1497` enters the snooze path. No milliseconds/microseconds mismatch was found. |
| Are we sleeping under an IRQ-disabling driver lock? | **KNOWN, source:** the owner's atomic try-guard does not disable IRQs. Debug output restores the previous IRQ state before returning. No evidence shows POST running as an interrupt callback. This does not prove every runtime scheduling property. |
| Is serial debug output free or deferred? | **KNOWN, SOURCE_ONLY:** it is synchronous and uses IRQ-disabled locking. See below. |

Pinned Haiku revision: `49a0af9585d80e42240af63ab66e31e9873f59b8`.
Primary source links: [legacy hooks](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/device_manager/legacy_drivers.cpp),
[stock NVIDIA lifecycle](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/add-ons/kernel/drivers/graphics/nvidia/driver.c),
[PCI reservation](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/add-ons/kernel/bus_managers/pci/pci.cpp).
The complete running kernel's correspondence to this source pin remains
unestablished; the exact saved kernel's relevant serial routine was also inspected.

Moving GPU writes into `init_driver` would expose them to automatic discovery
and reload before the signed grant. There is no evidence to justify that change.

## Our deadline includes diagnostic work

**KNOWN, source:** `Interpreter.h:15` sets the default POST budget to 10,000,000
microseconds. `Interpreter.cpp:47-53` compares elapsed backend wall time against
that limit. `BoundPost` applies its own aggregate guard. The native backend uses
Haiku `system_time()`, so synchronous logging, sleeps and time not scheduled on a
vCPU all count. This is our fail-closed software limit, not a GPU timeout register
or a Haiku loader deadline.

Each `SCRIPT_ACTIVE`/`SCRIPT_SKIPPED` entry reaches `Owner::Transport::trace`
(`Owner.cpp:119`) and then kernel `dprintf` (`NativePlatform.cpp:77`). At PC
`0x85d6`, the ROM instruction is `ZM_REG` (opcode `0x7a`) for `0x61c080`, a simple
write rather than a poll. **UNKNOWN:** whether that write completed and which
aggregate check first detected exhaustion. A trace entry precedes execution; it
is not a per-write completion certificate.

## Serial and observer cost

**KNOWN, SOURCE_ONLY:** Haiku
[`debug.cpp:1644-1665`](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/debug/debug.cpp)
formats the message and calls debug output under an interrupt-disabling lock.
The x86
[`arch_debug_console.cpp`](https://github.com/haiku/haiku/blob/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/arch/x86/arch_debug_console.cpp)
polls UART status and emits characters individually. Disassembly of
`arch_debug_serial_puts` in the exact saved kernel
(`2da9a5b9...`) confirms `cli`, port input/output and the character loop.
`work/S1A7STARTUP/source-pins.json` records source and disassembly hashes.

**KNOWN, upstream baseline:** QEMU v6.2.0's
[`serial.c:232-278`](https://github.com/qemu/qemu/blob/v6.2.0/hw/char/serial.c)
passes individual transmit bytes to its character backend. `char-fd.c:38-47`
passes them to the output channel; `channel-file.c:112-123` uses `writev`.
`kvm-all.c:2853,2890-2896` shows KVM execution and I/O-exit handling. This is an
upstream mechanism reference, not proof of every Ubuntu patch or the live syscall
count. **INFERRED:** per-character guest port I/O and backend writes amplify
observer cost.

The observer uses ptrace syscall/path filters without seccomp-BPF. Its local
primary manual (`build/observer/strace-source/doc/strace.1.in:1536-1555`) explains
why ordinary filtering does not remove stops for unprinted syscalls. The native
observer's descriptor-table proof also consumes lifecycle information beyond
printed VFIO accesses. Enabling seccomp as a shortcut needs a separate proof
review; it is not a safe incidental performance edit.

An inert host benchmark used the exact observer binary and 20,837 bytes, the
run6 serial volume from its first script entry to `POST_RESULT`. Three samples per
case measured the writer loop with `CLOCK_MONOTONIC`:

| Host regular-file case | Median seconds |
|---|---:|
| One-byte writes, untraced | 0.329 |
| One-byte writes, observer | 2.659 |
| 4096-byte chunks, untraced | 0.000171 |
| 4096-byte chunks, observer | 0.000620 |
| One-byte writes plus two inert syscalls each, untraced | 0.337 |
| Same with observer | 5.992 |

The final case ranged from 5.041 to 7.860 s. Extra syscalls were `gettid`, **not
KVM operations**. The benchmark used the production syscall/signal filter with
an unmatched inert path, omitted daemonization, and touched no device. It does
not measure Haiku, emulate UART timing or attribute run6's ten seconds. It shows
that filtered-out syscall traffic can have material and variable cost on this
host. Raw samples and exact parameters are in `work/S1A7STARTUP/host-bench/`.

Do not derive a QEMU time bound from the legacy Book's 19200-baud description.
The pinned Haiku source defaults to 115200. Physical 8N1 transmission of 20,837
bytes would take 10.85 s at 19200 or 1.81 s at 115200, but QEMU is not a physical
wire paced by those figures. Neither scenario establishes actual guest timing.

## What the ROM path can and cannot explain

**KNOWN, saved capture/ROM arithmetic:** all 528 run6 instruction entries match
the prefix of run5 exactly, including active/skipped state. There is no observed
branch divergence before this stop. Explicit `TIME` and `IO` delays on both
paths sum to only 22,421 microseconds. This is **not the total possible wait**.

Nine active `CONDITION_TIME` instructions precede the stop: `0x8ec8`, `0x8b2f`,
`0x8b33`, `0x8c47`, `0x8c4b`, `0x8588`, `0x85a2`, `0x9b66`, `0x9b9e`.
Each can sample up to 100 times with 20 ms after an unsuccessful sample. The
combined conservative bound is 18 seconds before aggregate guards intervene.
Each completed and reached its adjacent active RESUME instruction. **UNKNOWN:**
actual sample counts and elapsed time. Slow hardware conditions or sleep
overshoot could consume a substantial fraction of the budget without a distinct
poll error. Linux timing does not establish Haiku timing. The generated
`path-analysis.json` deliberately leaves these counts UNKNOWN.

Boot TSC calibration values differ by about 0.01% between the two runs, and both
select the APIC timer. No gross calibration change was found. This does not rule
out vCPU descheduling or a forward time jump; neither was measured.

The VFIO trace contains device acquisition but no printed device-reset ioctl.
Its path filter does not cover all anonymous device-descriptor ioctls. Thus
absence of that line proves neither absence of a VFIO reset nor a cold ASIC.
Do not add a manual reset experiment. Run6's unchanged R5 stream and disabled
bus mastering after exit remain bounded observations, not successful POST.

## Proposed next package, for review

1. Record instruction traces in a fixed-size, preallocated memory buffer during
   POST. Keep every entry and fail closed on overflow. Dump it after the operation
   returns, before `POST_RESULT`/fatal markers that make the host stop collecting.
   Avoid a large kernel-stack buffer or allocation in the hardware path.
2. Add bounded phase timing: POST wall time, condition sample counts/last values,
   requested and actual delay totals, diagnostic-output time and maximum MMIO
   latency. Preserve the one-shot owner and all hardware permissions.
3. Measure the native output path with and without the observer in a cardless
   guest before offering another physical package. The present host benchmark is
   a mechanism test only. Do not change the observer's mapping proof casually.
4. Keep the existing POST, owner and guest deadlines initially. Assess measured
   timing before proposing a reviewed deadline change. Do not subtract diagnostic
   time from the safety clock.

No new pad/power/PCI writes, added sensor settle delay or alternative startup
sequence follows from this investigation. A new card package still needs review
and an explicit one-run approval. S1 remains incomplete; D1 remains unapproved.

## Reproduce this analysis without hardware

Run `python3 tools/a7/startup_sources.py --check`,
`python3 tools/a7/startup_audit.py --check` and
`python3 tools/a7/startup_bench.py --check`. These compare saved records without
network access, guest launches or new measurements. Source capture generation
uses fixed URLs outside read-only `reference/`. Benchmark generation creates an
exclusive results directory and refuses to overwrite the saved samples.
