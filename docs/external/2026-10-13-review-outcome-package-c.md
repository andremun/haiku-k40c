# Updated Haiku K40c review — package 20261013c

**Reviewed:** 2026-10-13  
**Inputs:** `haiku-k40c-review-20261013c.zip` and the separately attached `S1-PLAN.md`  
**Outcome:** Continue host preparation, E3 analysis, and development of E0–E2 tooling. **Revise E4 before approving a hardware replay.** The new FIFO evidence improves the plan, but a flat list of recorded writes is not yet a sound bring-up procedure.

The strongest new finding is that device initialization cannot be omitted for the recorded guest setup. The weakest new claim is that replaying the debug log is a small, sufficient substitute for initialization. The included log directly shows state-dependent operations, skipped instructions, timed waits, and I²C/GPIO activity. It also shows that the proposed initialization-success bit is set by the script itself.

This is a continuation of the software review, not execution of the development plan. No GPU, PCI, BAR, passthrough, reset, or VM operation was performed. The supplied source and historical project documents were left unchanged.

## What changed, and what did not

The archive was extracted separately into [haiku-k40c-review-c](haiku-k40c-review-c/), preserving the earlier snapshot. The attached plan is byte-for-byte identical to `docs/S1-PLAN.md` in the archive.

The document changes are limited to `REVIEW-READ-FIRST.md`, `docs/05-fifo-design.md`, and the new `docs/S1-PLAN.md` and `docs/HAIKU_BUILD_TEST.md`. All **8 source files, 12 test files, and 2 tools are unchanged**. Despite some newer archive timestamps, `analysis/linux_deps.md` is unchanged too.

| Previous concern | Updated assessment |
|---|---|
| Stop without a kick/preempt step | Addressed in the added FIFO section, including polling and removal order. Integrate it into the actual implementation sequence. |
| Unknown PBDMA count and mask | The update records three units and mask `0x7`, with trace citations. The omitted MMIO capture prevents independent rechecking here. |
| Channel-indexed bind pointer omitted from prose | Correct encoding and offsets are now documented in the added section; older design step 9 remains incomplete. |
| Channel-group/runlist mode unspecified | The reference debug log independently supports two channel entries and count two, without additional hardware group entries. Choosing this mode for S1 substantially narrows the problem. |
| Doorbell unresolved | Now given a specific SOURCE_ONLY justification for no doorbell on this chip. Verify the cited pinned class-selection path when implementing submission; ordering/write completion is still required. |
| Initial device state unresolved | The new plan explicitly recognizes initialization as required for this recorded guest setup. Good correction. |
| Host defects F1–F7 | All remain open: no relevant code changed. |
| Package completeness/test claims | Unchanged: nine executable programs run, not eleven; full repository and QMD checks are still not reproducible from the archive. |

The reference log at lines 4934–4938 reports two channels, entries at successive eight-byte offsets, and a commit count of two. This supports the chosen runlist mode. It does not prove that the same channel can run with global GR initialization omitted.

## Verification of the new snapshot

`make -s -C haiku-k40c-review-c/tests` completed successfully: **nine executables, 550 checks, zero failures**. The two Python trace suites are still gated out because `tools/compare_register_traces.py` is absent.

The earlier independent C++ probe was rebuilt against the new source and rerun. It reproduces:

- Overlapping small/large mappings accepted.
- Wrong-page-size unmap returning with the mapping still present.
- Wrapped VA interval accepted with no mapping created.
- Physical address outside the model's 40-bit representation accepted and translated to zero.
- Shared-memory-size overflow encoding zero.
- `bindObject()` accepting a pending packet and corrupting the stream.
- Oversized trace values accepted and truncated.

Both sanitizer probes fail again: a 65-bit `Qmd::get()` read shifts by 64; `AddressSpace::map()` with page shift 64 shifts before validation. The unchanged comparator retains the previously reproduced problems with skipped fields, unrecognized values, mismatch exit status, and unchecked Markdown output. These findings do not disprove the fixed Linux reference job; they limit reliance on these helpers during bring-up.

The evidence and rerun instructions are in [review-evidence-c/RESULTS.md](review-evidence-c/RESULTS.md). The full earlier defect descriptions remain in [REVIEW-OUTCOME.md](REVIEW-OUTCOME.md).

## Main new findings about E4 replay

### C1 — P1: the debug log is not a literal list of executed writes

`docs/S1-PLAN.md:40` describes the debug log as recording every register write and proposes sending the same writes in order. The actual supplied log includes:

| Evidence in `reference/linux-run-debug/dmesg.txt.xz` | Consequence |
|---|---|
| Lines 1040–1044: condition followed by `ZM_REG` and `NV_REG` with `[ ]` | Instructions printed in the log may be skipped. Matching an assignment-looking line is insufficient. |
| Line 1036 and other active `TIME` entries | Delays belong to the program semantics; a write-only list loses them. |
| Lines 1236–1242: `CONDITION_TIME`, repeated condition checks about 20 ms apart, then further writes | Progress depends on live hardware state, not merely the preceding write order. |
| Active `NV_REG`, `COPY_NV_REG`, and `COPY_ZM_REG` instructions | Writes may preserve or derive values from current register contents. The debug text often describes an operation rather than its resolved bus value. |
| Lines 1131–1138 and 3184–3200: `ZM_I2C_BYTE` and I²C bus/pad activity | Board transactions and helper-side effects must be accounted for. |
| Line 1145: active `GPIO_NE`; line 1187: skipped `GPIO` | A general register-only parser misses a board-control operation, and naive inclusion could execute a skipped one. |

The audit found seven active `TIME` instructions, nine active `CONDITION_TIME` instructions, two active `ZM_I2C_BYTE` instructions, and one active `GPIO_NE` instruction. These are debug-state counts, not independently verified bus transactions.

For supplementary validation, [upstream Nouveau's script interpreter](https://codebrowser.dev/linux/linux/drivers/gpu/drm/nouveau/nvkm/subdev/bios/init.c.html) distinguishes executable versus skipped log markers, gates accesses on execution state, implements delays and polling, and delegates I²C/GPIO operations. This is a newer upstream revision, not a replacement for checking the package's pinned source.

**Required change:** E3 must produce an operation-level inventory and establish completeness against the matching raw MMIO capture, helper implementations, and VBIOS data. Do not generate E4 by extracting apparent writes from `dmesg` alone. If using actual MMIO writes instead, annotate waits, conditions, indirect transactions, and state-sensitive values; raw writes alone still omit their semantics.

### C2 — P1: E4's initialized-bit test can be circular

`docs/S1-PLAN.md:78` accepts E4 when the initialized bit is set and the replay trace matches Linux. But log line **3169** explicitly applies:

```text
NV_REG R[0x02240c] &= 0xfffffffd |= 0x00000002
```

The replay itself can set bit 1 even if earlier memory or clock initialization failed. Matching emitted writes confirms that the executor emitted its table; it does not demonstrate hardware readiness.

[Upstream `gf100_devinit_preinit()`](https://codebrowser.dev/linux/linux/drivers/gpu/drm/nouveau/nvkm/subdev/devinit/gf100.c.html) treats this bit as a devinit marker and notes that it clears on suspend. That supports its use to choose whether to initialize, but not as independent proof that an experimental replay succeeded.

**Required change:** retain the marker as one consistency check, add independent source-backed readiness checks and per-operation timeout/failure handling, and define a small, bounded VRAM read/write verification on reserved scratch memory before E5 relies on VRAM. Choose its address and safety limits from reviewed allocation/bootstrap logic, rather than inventing a test address. Capture fault/status evidence before and after. If a prerequisite fails, stop before the remaining writes and do not proceed to E5 merely because the marker is set.

### C3 — P1: same card plus same reset does not establish identical replay preconditions

The plan recognizes branch variation but understates the conditions needed to rule it out. A bus reset, warm guest restart, suspend/resume, and cold power-on need not produce equivalent state. Timing, training completion, external board controllers, preserved register bits, or prior initialization may differ.

The supplied log also shows `devinit`, privring, GPIO, I²C, and FIFO preinitialization **before** “running init tables” (for example, lines 842–920). Replaying only the script section may omit its prerequisites. The initial-state claim should be narrowed to the recorded setup; the log does not prove every guest start always leaves every card uninitialized.

**Required change:** define an explicit start-state contract: exact board identity and VBIOS hash, reset mechanism and successful completion, expected initialized state, relevant straps/configuration, and the preceding required setup. Require dynamic branch/readiness checks or guards at the points they matter. If a guard fails, abort; do not force captured outcomes.

The decision is not simply “flat replay or port all 2,300 lines.” A reviewed executor for the observed path can preserve RMW, copying, waits, conditions, and audited helper operations without becoming a general VBIOS interpreter. If those semantics cannot be reconstructed reliably, port the required interpreter/dependencies before E4. Its size and schedule must be measured after the dependency inventory; the plan's weeks-versus-days estimate is not established by this package.

### C4 — P1: script provenance does not resolve the safety-policy conflict

The proposed policy permits clock writes derived from a script while prohibiting all voltage, fan, and firmware-chip writes. The logged path includes active GPIO and I²C instructions. Their actual board functions and effective target writes are not classified in the package. It would be wrong to assert that they control voltage or cooling without mapping them; it would also be wrong to declare the replay compliant without that mapping.

**Required change:** audit every direct and indirect operation, including I²C device/register targets and GPIO functions. Distinguish reading VBIOS from writing the firmware chip. Preserve explicit prohibitions unless the user separately approves a concrete policy change. If a necessary initialization operation conflicts with that policy, report the exact operation and dependency instead of silently skipping it or granting a general script exception.

Use an immutable, reviewed operation manifest with stage, address/target, writable bits/value constraints, operation order, deadlines, provenance, and build/table hashes. A stage number and permitted address ranges alone cannot establish that the driver emits the approved sequence. The hardware MMIO backend and helper paths must enforce the policy; host mocks alone do not enforce it on the card.

## Assessment of the S1 premise and remaining path

**S1 without GR/context-switch firmware remains INFERRED, not proven.** The no-hardware-group runlist mode and no-doorbell source argument remove two uncertainties. They do not establish which engine dependencies the chosen channel mask and command require.

The plan still needs an exact source-verified FIFO-local payload, its encoded words, channel device mask, runlist/run-queue configuration, publication protocol, and fault checks. Binding a compute class would introduce an engine dependency. Explicitly establish that the selected FIFO operation can progress without a GR context or global GR initialization; the existing Linux run initialized the full stack.

“No firmware” also needs more precise wording: E4 depends on the card's VBIOS initialization program. The intended S1 claim should concern omission of GR FECS/GPCCS context-switch microcode, not absence of all firmware involvement. Active reclocking/power-management features can remain outside S1, while boot-time power/clock prerequisites and cooling remain part of its operating contract.

The remaining gaps from the earlier review are still material: actual GPU-visible allocation and byte upload, BAR/instance-memory bootstrap, MMU scratch dependency, page-size selection, TLB invalidation, submission visibility, bounded fault polling, and safe teardown. The host `AddressSpace` and `GpFifo` manipulate CPU vectors; they do not program GPU memory. A no-doorbell path still requires publishing data before updating PUT.

## Changes recommended to the stage gates

| Stage | Review outcome and stronger acceptance condition |
|---|---|
| E0 | Prepare tooling and logging. Separate no-device VM checks from actual assignment. Reset and PCI configuration can change hardware state even when the guest driver makes no BAR writes. Validate identity, isolation, reset scope, and host-controlled recovery before assignment. |
| E1 | Keep the read-only identity stage. Use the approved driver/build and validate MMIO mapping bounds; success is identity and mapping evidence, not proof of interrupt support. |
| E2 | Define the safe register list and preconditions. Compare stable values/masked fields, not all values indiscriminately against one capture. Differences should prevent E4 until understood. |
| E3 | Make this the immediate analysis priority. Produce script/helper semantics, executed/skipped distinction, prerequisite order, safety classification, and trace-to-operation provenance. Include the matching raw capture and pinned source excerpts needed to review it. |
| E4 | Replace blind write replay with a reviewed semantic procedure. Require guards, waits, independent readiness and scratch-memory checks, fault evidence, and a tested recovery path. First write run uses the reviewed E4 build/table. |
| E5 | Split memory/bootstrap work into independently checked steps. Validate GPU-visible contents, address domains, BAR flush, and TLB invalidation. Resolve the existing mapping defects before this stage depends on the helper. |
| E6 | Integrate the FIFO addendum into a single ordered recipe. Check schedule/enable state and absence of faults; include preempt/kick and quiescence before releasing resources. Captured physical addresses are examples, not values to reuse. |
| E7 | Record GET before submission, publish one verified entry, and observe GET advance to the new PUT within a deadline. Equal initial zero pointers are insufficient. Include fault snapshots and demonstrated teardown. |

Each first-write stage should be reviewed on **its own** operations and binary, not approved solely because the preceding stage passed (`S1-PLAN.md:105`). “Only while bound to the guest driver” should identify the actual host `vfio-pci` binding and assigned IOMMU group, as distinct from the Haiku guest driver.

The ten-minute limit and stop-on-hang policy are useful. Make the timeout host-enforced and independent of the guest, preserve logs incrementally, and establish whether shutdown actually quiesces/reset-recovers the card. Verify the bus reset's impact on other devices separately from DMA isolation. Stopping the guest is not itself evidence that the device recovered.

The claim that E0/E1 test interrupt delivery conflicts with both their read-only acceptance tests and the explicit omission of interrupts. Remove that claim, or introduce a separately reviewed interrupt test only if later milestones require it. For S1, specify interrupt masking plus polling of relevant fault sources; the older FIFO design still enables interrupts without a complete handling policy.

## Highest-risk statements after this update

1. **“B is good enough to reach S1.”** Not demonstrated; the logged program contains semantics omitted by flat replay.
2. **“The debug log records every register write.”** It logs skipped operations and abstractions, while helpers can emit additional accesses. Completeness requires corroboration.
3. **“The initialized bit proves successful initialization.”** The script directly sets it.
4. **“S1 needs no GR.”** Still requires an exact payload and dependency proof or controlled hardware evidence.
5. **“Script-origin clock writes are inherently safe/compliant.”** Their origin does not establish the safety of the full board-control path in the proposed initial state.
6. **“RAMFC values can be copied without understanding them.”** Full interpretation is not always necessary, but every context-dependent field, address, privilege, and mask must be parameterized and audited. Opaque literals need exact provenance and a justified chip/path match.
7. **“A trace match proves the stage.”** It supports sequence fidelity; functional readiness, state progression, and safe cleanup need separate evidence.

**Final recommendation:** retain the staged S1-first approach, accept the new initialization dependency, and credit the FIFO corrections. Proceed with E3 and host/read-only preparation. Do not approve E4 as currently specified; turn it into a state-aware, independently validated initialization procedure and close the existing host defects that its later stages will rely on.
