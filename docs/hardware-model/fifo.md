# fifo: Hardware Model

## Purpose
The FIFO engine takes commands from the command buffers of channels and hands them to the engines of the card (for a compute job: GR, and the copy engine CE) through runlists and PBDMA units (runq). gk104_fifo_init sets the USERD base in BAR1 (0x002254), acknowledges all interrupts (0x002100) and enables them (0x002140). The tables named by the function table hold the runlist operations (build, commit, block, allow), the PBDMA setup, the engine status queries and the MMU fault handling. For milestone S1 the Haiku driver needs the init members, the runlist members update, insert_chan, commit, wait and pending, runq.init, and the engine context members; the fault and interrupt members can start as logging only. The per-channel table (channel control block, bind, start) is not part of this model.

## Nouveau files

- Constructor: **gk110_fifo_new** (`nvkm/engine/fifo/gk110.c:128`)
- Function table: **gk110_fifo** (`nvkm/engine/fifo/gk110.c:107`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| chid_nr | gk104_fifo_chid_nr | data | True | 0 |
| chid_ctor | gk110_fifo_chid_ctor | init | True | 0 |
| runq_nr | gf100_fifo_runq_nr | data | True | 2 |
| runl_ctor | gk104_fifo_runl_ctor | init | True | 0 |
| init | gk104_fifo_init | init | True | 3 |
| init_pbdmas | gk104_fifo_init_pbdmas | init | True | 2 |
| intr | gk104_fifo_intr | interrupt | True | 12 |
| intr_mmu_fault_unit | gf100_fifo_intr_mmu_fault_unit | interrupt | False | 4 |
| intr_ctxsw_timeout | gf100_fifo_intr_ctxsw_timeout | interrupt | False | 0 |
| mmu_fault | gk104_fifo_mmu_fault | data | False | 0 |
| recover | gf100_fifo_mmu_fault_recover | runtime | False | 1 |
| access | gf100_fifo_mmu_fault_access | data | False | 0 |
| engine | gk104_fifo_mmu_fault_engine | data | False | 0 |
| reason | gk104_fifo_mmu_fault_reason | data | False | 0 |
| hubclient | gk104_fifo_mmu_fault_hubclient | data | False | 0 |
| gpcclient | gk104_fifo_mmu_fault_gpcclient | data | False | 0 |
| nonstall | gf100_fifo_nonstall | data | False | 0 |
| init | gf100_fifo_nonstall_allow | init | True | 1 |
| fini | gf100_fifo_nonstall_block | teardown | True | 1 |
| runl | gk110_runl | data | False | 0 |
| size | 8 | data | True | 0 |
| update | nv50_runl_update | runtime | True | 0 |
| insert_cgrp | gk110_runl_insert_cgrp | runtime | True | 0 |
| insert_chan | gk104_runl_insert_chan | runtime | True | 0 |
| commit | gk104_runl_commit | runtime | True | 2 |
| wait | nv50_runl_wait | runtime | True | 0 |
| pending | gk104_runl_pending | runtime | True | 1 |
| block | gk104_runl_block | runtime | True | 1 |
| allow | gk104_runl_allow | runtime | True | 1 |
| fault_clear | gk104_runl_fault_clear | runtime | True | 1 |
| preempt_pending | gf100_runl_preempt_pending | runtime | True | 1 |
| runq | gk104_runq | data | False | 0 |
| init | gk104_runq_init | init | True | 2 |
| intr | gk104_runq_intr | interrupt | True | 0 |
| intr_0_names | gk104_runq_intr_0_names | data | False | 0 |
| idle | gk104_runq_idle | runtime | True | 1 |
| engn | gk104_engn | data | False | 0 |
| chsw | gk104_engn_chsw | runtime | True | 0 |
| cxid | gk104_engn_cxid | runtime | True | 0 |
| mmu_fault_trigger | gf100_engn_mmu_fault_trigger | runtime | True | 3 |
| mmu_fault_triggered | gf100_engn_mmu_fault_triggered | runtime | True | 3 |
| ctor | gk104_ectx_ctor | init | True | 0 |
| bind | gk104_ectx_bind | init | True | 0 |
| engn_ce | gk104_engn_ce | data | False | 0 |
| chsw | gk104_engn_chsw | runtime | True | 0 |
| cxid | gk104_engn_cxid | runtime | True | 0 |
| mmu_fault_trigger | gf100_engn_mmu_fault_trigger | runtime | True | 3 |
| mmu_fault_triggered | gf100_engn_mmu_fault_triggered | runtime | True | 3 |

## Dependencies
imem, mc, top

## KNOWN

- **chid_ctor**: Creates the channel-ID allocator by calling nvkm_chid_new with the FIFO channel event type. (`nvkm/engine/fifo/gk110.c:95`)
- **runl_ctor**: Iterates over top devices with valid runlists and constructs per-runlist structures. (`nvkm/engine/fifo/gk104.c:756`)
- **init**: Writes the USERD base in BAR1 to 0x002254 (when USERD is in BAR1), then 0xffffffff to 0x002100 and 0x7fffffff to 0x002140 (interrupt status and enable) (`nvkm/engine/fifo/gk104.c:744`)
- **init_pbdmas**: Writes a mask to select which PBDMA units to enable and clears their interrupt-pending bits. (`nvkm/engine/fifo/gk104.c:735`)
- **intr**: Reads interrupt status and mask registers, dispatches to handlers for bind, context-switch, dropped faults, and runlist interrupts. (`nvkm/engine/fifo/gk104.c:652`)
- **intr_mmu_fault_unit**: Processes MMU faults reported by the MMU fault unit by reading fault registers and logging details. (`nvkm/engine/fifo/gf100.c:696`)
- **intr_ctxsw_timeout**: Blocks runlists and triggers MMU faults on engines whose context switch timed out. (`nvkm/engine/fifo/gf100.c:618`)
- **mmu_fault**: MMU fault sub-table defining recover, access, engine, reason, hubclient, and gpcclient members. (`nvkm/engine/fifo/gk104.c:588`)
- **recover**: Looks up the engine that caused the MMU fault and invokes its mmu_fault_triggered callback for context-switch timeout recovery. (`nvkm/engine/fifo/gf100.c:534`)
- **access**: Enum table mapping MMU fault access type codes to human-readable strings.
- **engine**: Enum table mapping MMU fault engine codes to engine names and associated engine types.
- **reason**: Enum table mapping MMU fault reason codes to human-readable fault reason strings.
- **hubclient**: Enum table mapping MMU fault hub client codes to human-readable client identification strings.
- **gpcclient**: Enum table mapping MMU fault GPC client codes to human-readable client identification strings.
- **nonstall**: Nonstall interrupt event table with init and fini functions for enabling and disabling the nonstall interrupt. (`nvkm/engine/fifo/gf100.c:462`)
- **init**: Enables nonstall interrupts by setting bit 31 of register 0x002140. (`nvkm/engine/fifo/gf100.c:440`)
- **fini**: Disables nonstall interrupts by clearing bit 31 of register 0x002140. (`nvkm/engine/fifo/gf100.c:451`)
- **runl**: Runlist sub-table with size, update, insert, commit, wait, and management functions for hardware scheduling. (`nvkm/engine/fifo/gk110.c:80`)
- **size**: The size in bytes of one entry in the runlist descriptor table.
- **update**: Allocates a RAMDT buffer, maps it, and calls insert_cgrp and insert_chan to populate entries for each channel group and channel. (`nvkm/engine/fifo/nv50.c:285`)
- **insert_cgrp**: Writes a channel-group descriptor into the runlist buffer at the given offset using hardware-defined bit fields. (`nvkm/engine/fifo/gk110.c:72`)
- **insert_chan**: Writes the channel ID into the runlist buffer at the given offset. (`nvkm/engine/fifo/gk104.c:452`)
- **commit**: Programs the hardware with the runlist base address and entry count via MMIO registers. (`nvkm/engine/fifo/gk104.c:430`)
- **wait**: Polls the runlist update-pending bit with a timeout and returns success or -ETIMEDOUT. (`nvkm/engine/fifo/nv50.c:224`)
- **pending**: Reads a runlist status register and tests bit 20 to determine whether an update is pending. (`nvkm/engine/fifo/gk104.c:422`)
- **block**: Sets bit 0 of register 0x002630 for the runlist to block its scheduled channels. (`nvkm/engine/fifo/gk104.c:416`)
- **allow**: Clears bit 0 of register 0x002630 for the runlist to allow its scheduled channels to run. (`nvkm/engine/fifo/gk104.c:410`)
- **fault_clear**: Writes the runlist ID bit to register 0x00262c to clear pending faults for that runlist. (`nvkm/engine/fifo/gk104.c:404`)
- **preempt_pending**: Reads register 0x002634 and tests bit 20 to determine whether a preemption is pending. (`nvkm/engine/fifo/gf100.c:370`)
- **runq**: Run queue sub-table with init, interrupt, and idle functions for PBDMA command buffer execution. (`nvkm/engine/fifo/gk104.c:396`)
- **init**: Initialises the run queue base and writes interrupt masks and interrupt-enable masks to the run queue hardware registers. (`nvkm/engine/fifo/gk104.c:379`)
- **intr**: Calls the handlers of both interrupt registers of the PBDMA unit and returns whether either had a pending interrupt (`nvkm/engine/fifo/gk104.c:370`)
- **idle**: Reads the run queue status register and tests bits 13 to 15 to determine whether the run queue is idle. (`nvkm/engine/fifo/gk104.c:289`)
- **engn**: Engine sub-table with context-switch, context-ID, MMU fault, constructor, and bind functions for per-engine channel context management. (`nvkm/engine/fifo/gk104.c:271`)
- **chsw**: Reads the engine status register and returns true when the engine is busy and awaiting context-switch acknowledgement. (`nvkm/engine/fifo/gk104.c:259`)
- **cxid**: Reads the engine status and returns the channel or channel-group ID of the channel currently loaded on the engine. (`nvkm/engine/fifo/gk104.c:245`)
- **mmu_fault_trigger**: Increments the refcount of triggered MMU faults on this runlist, enables nonstall interrupts, and writes 0x100 to register 0x002100 to trigger an MMU fault on the engine. (`nvkm/engine/fifo/gf100.c:222`)
- **mmu_fault_triggered**: Reads the engine MMU-fault-triggered status bit from the MMU-fault register, clears it, and decrements the triggered-fault refcount. (`nvkm/engine/fifo/gf100.c:202`)
- **ctor**: Gets a VMM mapping for the engine context and maps the instance memory into it. (`nvkm/engine/fifo/gk104.c:178`)
- **bind**: Maps the virtual context address into the instance memory at per-engine pointers determined by the engine type. (`nvkm/engine/fifo/gk104.c:134`)
- **engn_ce**: Engine table for the copy engine (CE): channel switch, context ID and MMU fault functions, without the context members of the GR table (`nvkm/engine/fifo/gk104.c:281`)
- **chsw**: Reads the engine status register and returns true when the engine is busy and awaiting context-switch acknowledgement. (`nvkm/engine/fifo/gk104.c:259`)
- **cxid**: Reads the engine status and returns the channel or channel-group ID of the channel currently loaded on the engine. (`nvkm/engine/fifo/gk104.c:245`)
- **mmu_fault_trigger**: Increments the refcount of triggered MMU faults on this runlist, enables nonstall interrupts, and writes 0x100 to register 0x002100 to trigger an MMU fault on the engine. (`nvkm/engine/fifo/gf100.c:222`)
- **mmu_fault_triggered**: Reads the engine MMU-fault-triggered status bit from the MMU-fault register, clears it, and decrements the triggered-fault refcount. (`nvkm/engine/fifo/gf100.c:202`)

## INFERRED

- **chid_nr**: Returns the maximum number of channels that this FIFO engine supports. (`nvkm/engine/fifo/gk104.c:802`)
- **runq_nr**: Returns the number of run queue (PBDMA) units present on this chipset. (`nvkm/engine/fifo/gf100.c:927`)
- **intr_0_names**: Table of names for the bits of the first PBDMA interrupt register (names such as HCE_RE_ILLEGAL_OP; HCE is not expanded in the source)

## UNKNOWN

(none)
