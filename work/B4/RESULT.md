# Task B4 Result: Linux dependency map

## Summary

Analyzed 70 Nouveau source files (non-other-chip class) for Linux kernel
symbol usage. Found 139 unique symbols across 6 categories.

| Category | Count | Description |
|---|---|---|
| C-replace | 47 | Direct Haiku equivalent exists |
| A-reimplement | 57 | Must be reimplemented in the driver |
| X-not-linux | 25 | Nouveau internals or hardware constants |
| D-ignore | 9 | AGP/write-combining; not used by Haiku driver |

## Outputs

- `tools/linux_deps.py`: Classification tool with map for all 139 symbols.
  Includes `--check` mode for deterministic output verification.
- `analysis/linux_deps.json`: Machine-readable dependency map (139 entries,
  sorted by symbol) with counts, example locations, categories, haiku_api,
  headers, and notes.
- `analysis/linux_deps.md`: Human-readable report (279 lines), grouped by
  subsystem with tables and a "Differences that matter" section.

## Key decisions

### Atomic functions
All atomic (`atomic_set`, `atomic_get`, `atomic_add`, `atomic_test_and_set`)
and refcount (`refcount_*`, `kref_*`) entries map to `headers/os/support/SupportDefs.h`.
Note: `user_atomic.h` only has user-space syscalls (`_user_atomic_*`); kernel
atomics are in `SupportDefs.h`.

### Standard C functions
`malloc`, `calloc`, `free`, `snprintf`, `sprintf`, `strlcpy` use `header: null`
because they are standard C library functions, not Haiku kernel APIs.

### Spinlock/IRQ functions
`spin_lock_irqsave` and `spin_lock_irq` map to
`acquire_spinlock` + `disable_interrupts` (headers/os/drivers/KernelExport.h).
`spin_unlock_irqrestore` and `spin_unlock_irq` map to
`release_spinlock` + `restore_interrupts`. Haiku has no `enable_interrupts` —
use `restore_interrupts(token)` which was returned by `disable_interrupts()`.

### Firmware loading
`request_firmware` and `release_firmware` are D-ignore: only called in
`gf100_gr_load_fw` for external firmware files that the GK110 driver does not use.

### List operations
Linux `list_entry`/`list_for_each_entry` require `container_of`, which must be
reimplemented via `offsetof` or pointer arithmetic in Haiku.

## Verification

- `make check` passes with 0 failures.
- `tools/linux_deps.py --check` passes (JSON consistent with tool).

## Open questions

1. `pci_is_pcie` is marked A-reimplement (read PCI config space). The exact
   Haiku equivalent for PCIe capability detection is not yet confirmed.
2. `schedule_work`/`INIT_WORK`/`flush_work` (workqueue) — Haiku threads or
   timer-based approach needs design.
3. `BUG`/`BUG_ON`/`WARN_ON` — graceful error handling strategy for Haiku
   driver not yet defined.
