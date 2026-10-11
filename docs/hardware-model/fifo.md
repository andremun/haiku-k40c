# fifo: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk110_fifo_new** (`nvkm/engine/fifo/gk110.c:128`)
- Function table: **gk110_fifo** (`nvkm/engine/fifo/gk110.c:107`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| chid_nr | gk104_fifo_chid_nr | None | None | 0 |
| chid_ctor | gk110_fifo_chid_ctor | None | None | 0 |
| runq_nr | gf100_fifo_runq_nr | None | None | 2 |
| runl_ctor | gk104_fifo_runl_ctor | None | None | 0 |
| init | gk104_fifo_init | None | None | 3 |
| init_pbdmas | gk104_fifo_init_pbdmas | None | None | 2 |
| intr | gk104_fifo_intr | None | None | 12 |
| intr_mmu_fault_unit | gf100_fifo_intr_mmu_fault_unit | None | None | 4 |
| intr_ctxsw_timeout | gf100_fifo_intr_ctxsw_timeout | None | None | 0 |
| mmu_fault | gk104_fifo_mmu_fault | None | None | 0 |
| recover | gf100_fifo_mmu_fault_recover | None | None | 1 |
| access | gf100_fifo_mmu_fault_access | None | None | 0 |
| engine | gk104_fifo_mmu_fault_engine | None | None | 0 |
| reason | gk104_fifo_mmu_fault_reason | None | None | 0 |
| hubclient | gk104_fifo_mmu_fault_hubclient | None | None | 0 |
| gpcclient | gk104_fifo_mmu_fault_gpcclient | None | None | 0 |
| nonstall | gf100_fifo_nonstall | None | None | 0 |
| init | gf100_fifo_nonstall_allow | None | None | 1 |
| fini | gf100_fifo_nonstall_block | None | None | 1 |
| runl | gk110_runl | None | None | 0 |
| size | 8 | None | None | 0 |
| update | nv50_runl_update | None | None | 0 |
| insert_cgrp | gk110_runl_insert_cgrp | None | None | 0 |
| insert_chan | gk104_runl_insert_chan | None | None | 0 |
| commit | gk104_runl_commit | None | None | 2 |
| wait | nv50_runl_wait | None | None | 0 |
| pending | gk104_runl_pending | None | None | 1 |
| block | gk104_runl_block | None | None | 1 |
| allow | gk104_runl_allow | None | None | 1 |
| fault_clear | gk104_runl_fault_clear | None | None | 1 |
| preempt_pending | gf100_runl_preempt_pending | None | None | 1 |
| runq | gk104_runq | None | None | 0 |
| init | gk104_runq_init | None | None | 2 |
| intr | gk104_runq_intr | None | None | 0 |
| intr_0_names | gk104_runq_intr_0_names | None | None | 0 |
| idle | gk104_runq_idle | None | None | 1 |
| engn | gk104_engn | None | None | 0 |
| chsw | gk104_engn_chsw | None | None | 0 |
| cxid | gk104_engn_cxid | None | None | 0 |
| mmu_fault_trigger | gf100_engn_mmu_fault_trigger | None | None | 3 |
| mmu_fault_triggered | gf100_engn_mmu_fault_triggered | None | None | 3 |
| ctor | gk104_ectx_ctor | None | None | 0 |
| bind | gk104_ectx_bind | None | None | 0 |
| engn_ce | gk104_engn_ce | None | None | 0 |
| chsw | gk104_engn_chsw | None | None | 0 |
| cxid | gk104_engn_cxid | None | None | 0 |
| mmu_fault_trigger | gf100_engn_mmu_fault_trigger | None | None | 3 |
| mmu_fault_triggered | gf100_engn_mmu_fault_triggered | None | None | 3 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
