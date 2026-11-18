# Runtime interface of the driver (proposed)

2026-11-13. Task RTIOCTL. Answers Q2 to Q5 of `docs/OPEN_QUESTIONS.md` for
`haiku-k40c-llm` (runtime contract v0.2). Header: `src/runtime/k40_ioctl.h`.
Status: PROPOSED. No device node implements it. The answers use what the S3 host
work established. They are design decisions, not card results.

## Answers

| Question | Answer |
|---|---|
| Q2: private ioctl set on the device node? | Yes. One node, `/dev/misc/k40c`, eight operations: query, allocate, write, read, load module, dispatch, wait, release. One open at a time. The open creates the context (channel, GR context); the close tears it down. |
| Q3: who places the code segment and the built-in library? | The driver. The code segment is one owned record, set once at context creation with CODE_ADDRESS (`nve4_compute.c:83-85`). `load module` copies kernel code into it and returns its offset as the handle. Version 1 refuses a kernel with relocations, so no built-in library is placed. The library is added with the first kernel that needs one. |
| Q4: mapping at allocation or at first binding? | At allocation. The channel address of a buffer is fixed when it is allocated, and its page-table entries are written then. A binding only writes the 64-bit address into constant buffer 0. |
| Q5: completion signal of the polling stage? | Two levels. GP_GET shows only that the entry was fetched (S1, S2 host tests). Completion of a job is the engine idle state plus the fault registers (GR interrupt and trap, FECS interrupt, MMU fault). `wait` polls these with a deadline. A semaphore release written by the GPU (descriptor fields RELEASE0, RELEASE1) is the later replacement; it needs a card result first. |

## Mapping to runtime contract v0.2

| Contract | Driver |
|---|---|
| `query_device` | `K40_QUERY` |
| `allocate(size, alignment, domain)` | `K40_ALLOCATE`. VRAM only: Q7 (host DMA visibility) is open, so there is no host-memory domain. |
| `upload`, `download` | `K40_WRITE`, `K40_READ` through the slow window. Refused with `K40_BUSY` while the buffer is bound to a job in flight. |
| `load_module(artifact)` | `K40_LOAD_MODULE` with the argument table of the artifact |
| `dispatch(module, grid, block, bindings)` | `K40_DISPATCH`. The driver checks handle, range and access mode, writes the addresses into constant buffer 0, builds the descriptor (D5), submits. |
| `wait(fence, deadline)` | `K40_WAIT` |
| `release`, `close_context` | `K40_RELEASE`, close. A timeout or fault poisons the context; its records stay retained until the guest ends (as every stage so far). |

## Limits of version 1

- One context, one channel, one job in flight. No interrupts.
- Transfers go through the slow window. Measured in S1: about 0.1 to 0.5 s for
  1 MiB. A 22 GB model is out of reach this way; a BAR1 mapping of buffers is the
  next step and needs its own review.
- Constant buffer 7 (driver data) and the descriptor are owned by the driver.
  Kernel arguments are in constant buffer 0, 64 KiB (`nve4_compute.c:623`).
- The interface exists only after rung 5 passes. A context that failed once is
  poisoned for good in this version.

## Open

- The device node itself, its policy (which writes the guard accepts for
  general jobs) and its tests. The S3 stage accepts one fixed job only.
- Whether engine idle is a correct completion signal for back-to-back jobs: UNKNOWN.
