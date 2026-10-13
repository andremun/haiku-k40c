# Haiku K40c software review outcome

**Date:** 2026-10-13  
**Package:** `haiku-k40c-review-20261013b.zip`, identifying commit `698f4af`  
**Outcome:** Proceed with S1 preparation and host implementation. **Require design corrections and a concrete safety plan before the first Haiku hardware-write experiment.** The supplied package is not an implementation-ready channel recipe and does not establish S1 without GR.

The project has useful preparation: small encoding components, trace-backed channel observations, a reported successful Linux reference workload, and an explicit incremental goal. Those justify continuing the experiment. They do not yet establish that a freshly assigned card can consume a Haiku GPFIFO entry with GR and its firmware omitted.

## Scope and evidence limits

I unpacked the archive into [haiku-k40c-review](haiku-k40c-review/), read `REVIEW-READ-FIRST.md`, followed its document sequence, inspected all four C++ component implementations, the test/build setup, the comparison tool, and relevant hardware models and reference logs. I ran the available host suite and additional targeted probes. I did not change the supplied source, project status, or historical review records, and did not access hardware or start a VM.

Evidence labels in this report:

- **KNOWN / host-tested:** reproduced by executing the included software on the CPU.
- **KNOWN / supplied capture:** present in an included log; the hardware event was not rerun here.
- **SOURCE_ONLY:** supported by source or a source citation; not proof of the proposed Haiku sequence.
- **INFERRED:** a reasonable interpretation requiring a targeted hardware test.
- **UNKNOWN:** insufficient supplied evidence.

The archive excludes the pinned Nouveau/Mesa source trees and register captures. It also excludes the root Makefile/checker, register database, trace-comparison implementation, and some analysis JSON inputs. Consequently, I cannot independently reproduce the full register analysis or the historical 155-field QMD comparison. Upstream source browsing was used only for supplementary checks; the available Code Browser pages describe a newer kernel revision, not the package's pinned 6.12 tree. The reference run used kernel 6.8. These versions must not be treated as interchangeable evidence.

## What was verified

| Item | Result | Meaning |
|---|---|---|
| Included C++ suite, `make -s -C tests` | **9 executables, 550 checks, all pass** | The supplied host examples and acceptance checks pass. |
| Two Python trace suites | Silently skipped; direct execution fails to import their tool | The package's claim of 11 passing programs is not reproducible from this archive. |
| Repository `make check` | Unavailable: no target | The full project's required checks cannot be run here. |
| QMD comparison `--check` | Fails: missing Mesa header; other required JSON files also absent | The reported 155/155 result is retained as historical evidence, not independently recertified. |
| Linux reference result | Included log says NVF1, 1,024 elements, zero wrong, PASS | Good supplied evidence that this workload ran through the Linux stack. |
| `ref_qmd` | 10 smoke checks pass | Useful check of selected fields, not an independent 155-field comparison. |
| Additional host probes | Multiple reproducible defects; two UBSan failures | Passing existing tests leave meaningful validation and state-management gaps. |

Commands, outputs, and reproducible probes are in [review-evidence/RESULTS.md](review-evidence/RESULTS.md).

## Confirmed software findings

Priorities: **P1** should be addressed before using these components for hardware bring-up; **P2** should be addressed before broadening their supported inputs. These are review findings, not applied fixes.

### F1 — P1: mixed page sizes bypass overlap validation

**KNOWN / host-tested.** `src/mmu/PageTable.cpp:186` checks `translate(pva)` only at each new page's starting address. A 4 KiB mapping at VA `0x1000` is missed when a new 128 KiB mapping begins at VA `0`. The probe creates both mappings successfully, leaving two conflicting entries under one directory entry.

`translate()` then searches tables in insertion order (`PageTable.cpp:335`), so the model's answer cannot be relied upon as a hardware page-walk oracle for such a state. Fix overlap validation to cover the full requested interval across both page sizes. Test both insertion orders and overlap within the interior of a large page.

### F2 — P1: unmap can report success without removing a mapping

**KNOWN / host-tested.** `src/mmu/PageTable.cpp:285` accepts any mapping that `translate()` finds, but its clearing loop at line 296 requires the caller's page size to match the table. Mapping a 128 KiB page and requesting a 4 KiB unmap returns normally while leaving the mapping intact.

This could invalidate a future driver's assumption that DMA access ended before memory was reused. Either reject incompatible unmaps before mutation or explicitly split large mappings. Test that every successful unmap removes exactly the advertised range.

### F3 — P1: address and page-size validation is incomplete

**KNOWN / host-tested.** `src/mmu/PageTable.cpp:165` checks `va + size` after unsigned addition. `map(0x1000, 0, 0xfffffffffffff000, 12, VRAM)` wraps the end to zero and succeeds with no mappings. There is also no physical-range validation: mapping physical address `1ULL << 40` succeeds, but `translate()` masks it down to zero at line 364.

Both `map()` and `unmap()` compute `1ULL << pageShift` before checking the shift (lines 177 and 276). A shift of 64 triggers undefined behavior; UBSan reproduces it in `map()`.

Validate the shift first; use subtraction-based bounds checks for VA and physical intervals, and validate allocated table addresses/alignment. Confirm the supported physical width for every target before choosing its exact bound. Check all validation before changing state.

### F4 — P1: the QMD comparison tool can succeed despite incomplete or differing results

**KNOWN / host-tested.** In `tools/qmd_compare.py`, unknown fields are skipped (line 200), unrecognized symbolic values become zero (line 132), and short word arrays can supply implicit zero bits (line 109). Normal mode finishes without a failure exit for nonzero differences. `--check` compares regenerated JSON to stored JSON, without requiring zero differences, and reads but never compares the Markdown text (lines 255–259).

A synthetic two-field reference produced only one compared row, one difference, and successful normal completion. With that JSON persisted and intentionally stale Markdown, `--check` still exited zero. This does **not** show that the historical 155-field match is wrong; it shows that the tool is not sufficient to guard future comparisons.

Fail on unknown fields/enums, invalid bit ranges, wrong word count, missing/duplicate rows, and unexpected field coverage. Distinguish a report-generation command from a verification command; verification must reject differences and validate both generated files. Replace unrestricted `eval()` with a limited arithmetic parser when reading header expressions.

### F5 — P2: launch-descriptor validation admits overflow and undefined reads

**KNOWN / host-tested.** `src/compute/LaunchDesc.cpp:68` adds `0xff` to a 32-bit input before promoting it. `sharedMemSize = 0xffffffff` wraps and encodes zero rather than throwing. Promote before addition and validate the supported resource limit.

`Qmd::get()` at line 48 does not enforce the 64-bit width limit that `set()` enforces. `get(64, 0)` triggers a shift-by-64 UBSan error at line 59. Reject widths above 64. Separately, `buildQmd()` masks `localMemLow` before width validation, so its public promise to reject values that do not fit needs clarification or stronger validation.

These inputs are outside the fixed reference job; they do not contradict its passing smoke checks.

### F6 — P1: binding an object during a pending packet corrupts the command stream

**KNOWN / host-tested.** `src/fifo/PushBuffer.cpp:82` appends a header and class value without checking `hasPending_`, unlike the other packet-start operations. The sequence `begin(1, 0x100, 1); bindObject(1, 0xa1c0); data(0x1234);` is accepted and the resulting stream fails the decoder.

Make `bindObject()` obey the pending-packet guard. Also provide a checked finalization path before submission: `words()` currently returns an incomplete packet if its payload has not been finished.

### F7 — P2: malformed register traces can be accepted with truncated values

**KNOWN / host-tested.** `src/hw/RegisterIO.cpp:185` parses with `stoul()` and casts to `uint32_t` without range checks or checking that the entire token was consumed. On this 64-bit host, `W 0x100000000 0x100000001` becomes offset zero, value one.

Reject out-of-range values, partial numeric tokens, and unexpected trailing tokens. Otherwise a trace parser can hide errors in evidence used for review. `TraceMMIO` itself is a useful strict ordered replay abstraction, but only after validated input.

## Answers to the package's review questions

### 1. Is S1 achievable without GR and firmware?

**INFERRED: plausible for narrowly defined FIFO consumption; UNKNOWN for the actual proposed configuration.** The package does not prove it. Its successful Linux run initialized the wider driver, including GR. Observing channel creation before per-channel GR context generation is not proof that global GR initialization was unnecessary.

Define S1's exact payload before implementing it. A source-verified FIFO-local no-op or control operation may avoid dispatching to GR; binding the compute class or sending an engine method changes that assumption. Identify the required runlist, device mask, channel-group mode, and whether scheduling requests an engine context even for the chosen payload. The GK110 FIFO table has distinct channel/group and engine hooks; these must be traced through the pinned implementation. Supplementary [upstream GK110 FIFO source](https://codebrowser.dev/linux/linux/drivers/gpu/drm/nouveau/nvkm/engine/fifo/gk110.c.html) confirms that distinction, but does not establish a no-GR hardware result.

For the experiment, record GET before submission, publish exactly one entry, and require observed GET advancement to the new PUT within a deadline, with no relevant MMU/PBDMA/scheduler faults. GET equal to PUT at initial zero is not evidence. FIFO consumption also does not prove an engine completed work; S2/S3 need a completion fence or equivalent source-verified mechanism and correct readback visibility.

### 2. What is missing between PCI discovery and channel enable?

**The missing kick is only one part of the gap.** `docs/05-fifo-design.md` remains an outline with unresolved implementation decisions.

| Gap | Required resolution for S1 |
|---|---|
| Initial device state | Define PCI memory decoding/bus mastering, power state, identity validation, reset ownership, and the initialized state guaranteed by assignment/firmware. Do not rely on an undocumented preceding Linux driver session. |
| BAR/instance-memory bootstrap | Choose the first working method to write VRAM objects before the BAR address spaces exist, then define BAR mapping initialization. The imem/bar dependencies currently form an unexplained bootstrap cycle. |
| Real GPU memory allocation | Specify addresses, sizes, alignment, lifetime, zeroing, and CPU/GPU mappings for directory/tables, RAMFC, USERD, GPFIFO, command storage, and runlist buffers. `malloc()` alone does not supply these GPU-visible objects. |
| Host MMU model integration | `AddressSpace` keeps table data in private CPU vectors and hardcodes newly allocated table targets to VRAM. Define how bytes are exported/written to GPU memory; calling `map()` does not program hardware. |
| MMU configuration and visibility | Select page-size configuration, resolve the framebuffer scratch-memory dependency, and define TLB invalidation. BAR flush and GPU TLB invalidation are separate steps. The MMU design explicitly omits the latter. |
| FIFO topology | Resolve PBDMA mask, runlist association, run-queue mapping, and software versus hardware channel-group mode. A one-channel runlist is not automatically a one-entry runlist when a group header is needed. |
| Channel bind | Design step 9 omits channel-indexed register offsets and encoded instance pointer, and reverses the documented runlist-before-instance order. Replace prose with parameterized, source-backed operations; do not replay captured addresses. |
| Submission | Include USERD initialization, command/entry publication, ordering and write completion, PUT update, and a resolved GK110B doorbell policy. The host `GpFifo::push()` changes a vector only. |
| Polling and faults | Use observed pointer advancement with bounded waits and capture relevant fault state. Decide interrupt masking or servicing explicitly; the design enables interrupts while proposing no complete handler. |
| Failure and teardown | Stop/disable, preempt or kick using the selected channel/group mode, wait for quiescence, update/remove runlist entries, unbind, invalidate mappings, then release memory. Specify timeout behavior that retains resources until DMA is known stopped. |

The package already cites `nv50_dma_push()` but leaves the publication protocol unresolved. An [older upstream Nouveau implementation](https://sbexr.rabexc.org/latest/sources/2e/9962891446d501.html) visibly performs a barrier and buffer readback before updating USERD PUT, followed by a conditional doorbell. This is supplementary SOURCE_ONLY evidence that encoding a ring entry is not the whole submission operation. Verify the exact 6.8/6.12 path before choosing Haiku equivalents.

### 3. Are the hardware-safety limits sufficient?

**They are a useful foundation, but the package does not demonstrate an enforceable, complete safety boundary.** VFIO/IOMMU protection must cover the entire assigned group and guest DMA mappings; the [Linux VFIO documentation](https://www.kernel.org/doc/html/v6.15/driver-api/vfio.html) makes groups the unit of isolation. The package says interrupt remapping is unverified and the reset method is `bus`. DMA isolation does not establish that a bus reset leaves neighboring devices unaffected. Verify reset scope and recovery separately.

An address allow-list should also constrain writable bits, allowed values, lifecycle stage, and command/object contents. A permitted broad engine-enable write (`0xffffffff` to master control in the FIFO design) can affect units outside S1. Source provenance identifies where a value came from; it is not a safety classification. Unknown register semantics and indirect windows need particular review.

No runtime allow-list is implemented by the supplied `RegisterIO`; it contains mock and trace backends only. Before hardware writes, require enforcement in the real backend, bounded polls, fault snapshots, resource retention on failed quiescence, verified cooling/temperature monitoring, and a tested recovery procedure for the dedicated card. A guest restart is not a demonstrated guarantee of device recovery.

The archive's passthrough document still says a reboot restores default binding even though its later attach-at-boot section describes persistent initramfs configuration. Its AGENTS rules and gate notes also describe different authorization states. Establish one current operational policy and recovery procedure before execution. This review performed no passthrough actions.

### 4. Which SOURCE_ONLY statements are most at risk?

1. **“S1 needs no graphics engine or firmware.”** This is a dependency-elimination hypothesis, not a consequence of a Linux trace with the full stack initialized.
2. **“Framebuffer MMU scratch memory can be skipped until S3.”** The MMU design asserts this, while the framebuffer model marks its allocation required and leaves its purpose unresolved. Resolve whether the exact S1 translation path needs it before omission.
3. **“Fault handlers are logging-only stubs and can be skipped.”** The full interrupt/recovery behavior is not reproduced in the package. Polling permits a smaller driver, but requires fault detection and safe termination rather than assuming faults are harmless.
4. **“The listed subsystems form the minimum chain.”** PCI/device initialization, power management, clocks, thermals, and memory preparation cannot be dismissed by counting callgraph constructors. The read-first explicitly acknowledges the stale PMU classification; GR design already restores hooks previously omitted as graphics-only.
5. **“A Haiku memory-map call replaces Linux DMA mapping.”** Resolve pinning, scatter/gather, DMA address width, coherency, and the address domain. CPU virtual, guest physical/DMA, GPU virtual, VRAM physical, and BAR aperture addresses are different quantities.
6. **“Channel state/queue idle proves compute completion.”** It does not establish shader completion or output visibility. The minimum-chain readback also loosely says BAR0; choose the actual aperture/window and synchronization protocol.
7. **“Function-table capability flags imply default behavior.”** For example, `chan.md` calls the RAMFC `priv = true` flag a privileged default, while its own RAMFC write description takes a separate `priv` argument. Verify actual call-site choices rather than infer runtime settings from capability tables.

Additional MMU audit item: `kLptInvalid = 2` exists but is never used by the model. The [upstream GK104 VMM source](https://codebrowser.dev/linux/linux/drivers/gpu/drm/nouveau/nvkm/subdev/mmu/vmmgk104.c.html) distinguishes large-table invalid entries that suppress corresponding small PTEs. Verify large/small fallback semantics against the pinned code before presenting the host translator as a hardware-equivalent model. This is an audit question, not a claim that every zero-filled table here is wrong.

## Recommended next work and acceptance gate

1. Fix F1–F4 and F6, add regression cases for the reproduced failures, and include the missing trace-comparison implementation and exact QMD inputs in a reproducible review bundle. Fix F5/F7 before relying on generic inputs or parsed traces.
2. Refresh the FIFO/MMU/minimum-chain documents into one S1 dependency sequence. Each operation should name its input address domain, exact source-backed encoding, visibility requirement, deadline, error test, and rollback action. Separate Linux observations from untested omissions.
3. Choose the exact S1 packet and channel/group mode. Verify their no-GR premise against pinned sources and an appropriate reference experiment; do not expand to CE/GR on an unexplained timeout.
4. Implement and review the Haiku memory/MMIO backends, safety enforcement, and bounded polling. Test initialization, publication, injected failures, and teardown on host mocks. A strict whole-Linux-trace match is unsuitable across different polling and background activity; compare selected causal operations and invariants.
5. Run the existing read-only P1 stage before writes. Authorize a concrete P2/P3 test only after device identity, isolation, reset scope, recovery, and the reviewed operation list are established. S1 acceptance requires recorded pointer progress, absence of relevant faults, and successful quiescence/cleanup.

**Decision:** Keep the S1-first strategy. The preparation supports a controlled engineering experiment, but neither the current host test result nor the Linux reference run closes the gaps needed for a safe, reproducible Haiku channel submission.
