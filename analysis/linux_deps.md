# Linux Dependency Map

This document lists all Linux kernel symbols called by the 70 Nouveau source
files relevant to the GK110 (Tesla K40c) GPU driver, with their replacement
strategy for the Haiku driver.

## Summary

| Category | Count | Description |
|---|---|---|
| C-replace | 47 | Direct Haiku equivalent exists |
| A-reimplement | 57 | Must be reimplemented in the driver |
| X-not-linux | 25 | Nouveau internals or hardware constants |
| D-ignore | 9 | AGP/write-combining; not used by Haiku driver |

## Memory Allocation (C-replace, 12 entries)

Linux kernel allocators provide zeroing, overflow checks, and virtual mapping
that Haiku's standard C functions do not replicate in the same call.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `alloc_page` | — | A-reimplement (page allocator) |
| `kfree` | 15 | `free` (standard C) |
| `kmemdup` | 2 | `malloc` + `memcpy` |
| `kmalloc` | 39 | `malloc` (standard C) |
| `kvmalloc` | 4 | `malloc` (standard C, no fallback) |
| `kvmalloc_array` | 1 | `malloc` with manual overflow check |
| `kvcalloc` | 1 | `calloc` (standard C) |
| `kvfree` | 1 | `free` (standard C) |
| `kvzalloc` | 1 | `calloc` (standard C) |
| `kzalloc` | 45 | `calloc` (standard C, zeroed) |
| `struct_size` | 1 | `malloc` with manual size computation |
| `vfree` | 1 | `free` (standard C, no vmap cleanup) |
| `vmap` | 3 | A-reimplement (custom virtual mapping) |
| `vunmap` | 2 | A-reimplement (custom unmap) |
| `__free_page` | 1 | A-reimplement (page release) |
| `memcpy_toio` | 2 | `memcpy` (standard C) |
| `memcpy_fromio` | 2 | `memcpy` (standard C) |
| `memset_io` | 1 | `memset` (standard C) |

## Locking (C-replace, 9 entries)

Linux spinlocks and mutexes map to Haiku's spinlock and mutex APIs. The irqsave/irqrestore variants additionally manipulate interrupt state.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `mutex_init` | 22 | `mutex_init` |
| `mutex_lock` | 57 | `mutex_lock` |
| `mutex_unlock` | 56 | `mutex_unlock` |
| `mutex_destroy` | 2 | `mutex_destroy` |
| `mutex_is_locked` | 1 | A-reimplement (debug assertion) |
| `spin_lock` | 114 | `acquire_spinlock` |
| `spin_unlock` | 115 | `release_spinlock` |
| `spin_lock_irqsave` | 6 | `acquire_spinlock` + `disable_interrupts` |
| `spin_unlock_irqrestore` | 6 | `release_spinlock` + `restore_interrupts` |
| `spin_lock_irq` | 3 | `acquire_spinlock` + `disable_interrupts` |
| `spin_unlock_irq` | 3 | `release_spinlock` + `restore_interrupts` |
| `spin_lock_init` | 24 | `acquire_spinlock` (no init needed) |

## List Operations (C-replace / A-reimplement, 14 entries)

Linux `struct list_head` is a doubly-linked list with embedded pointers.
Haiku's `BList` / `list` type is similar but the entry macros (`list_entry`,
`list_for_each_entry`) use `container_of` which must be reimplemented.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `INIT_LIST_HEAD` | 70 | `list_add_link_to_tail` + `list_add_item` (or `{0}` init) |
| `list_add` | 5 | `list_add_link_to_head` |
| `list_add_tail` | 1 | `list_add_link_to_tail` |
| `list_del` | 3 | Manual unlink (Haiku has no list_remove) |
| `list_del_init` | 2 | Manual unlink + reinit |
| `list_empty` | 3 | Check if first link is NULL |
| `list_for_each_entry` | 5 | Manual iteration with container_of |
| `list_for_each_entry_safe` | 2 | Manual temp pointer iteration |
| `list_first_entry` | 1 | Manual first-element access |
| `list_first_entry_or_null` | 1 | Empty check + first access |
| `list_last_entry` | 1 | Linear scan (BList has no tail pointer) |
| `list_move_tail` | 1 | `list_move_to_list` |
| `list_entry` | 4 | Manual offset computation |

## Red-Black Tree (A-reimplement, 6 entries)

Linux `struct rb_tree` has no Haiku equivalent. All RB-tree operations must be
reimplemented or replaced with a hash table / sorted array.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `rb_erase` | 1 | A-reimplement (full RB-tree) |
| `rb_first` | 1 | A-reimplement |
| `rb_insert_color` | 1 | A-reimplement |
| `rb_link_node` | 1 | A-reimplement |
| `rb_next` | 1 | A-reimplement |
| `rb_entry` | 1 | Manual offset computation |

## Atomics (C-replace, 8 entries)

Haiku provides `int32` atomic functions in `SupportDefs.h`:
`atomic_set`, `atomic_get`, `atomic_get_and_set`, `atomic_add`,
`atomic_test_and_set`. Linux's `atomic_inc`/`atomic_dec` map to
`atomic_add` with +1/-1.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `atomic_set` | 76 | `atomic_set` |
| `atomic_read` | 40 | `atomic_get` |
| `atomic_inc` | 65 | `atomic_add` (with +1) |
| `atomic_dec` | 33 | `atomic_add` (with -1) |
| `atomic_inc_return` | 1 | `atomic_get_and_set` (loop) |
| `atomic_dec_and_test` | 3 | `atomic_get_and_set` (with zero check) |
| `atomic_xchg` | 1 | `atomic_get_and_set` |
| `atomic_cmpxchg` | 1 | `atomic_test_and_set` |

## Reference Counts (C-replace / A-reimplement, 7 entries)

Linux `refcount_t` and `kref` use the same atomic primitives as the general
atomic API but add overflow protection. Haiku atomics lack overflow checks.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `refcount_set` | 1 | `atomic_set` |
| `refcount_inc` | 1 | `atomic_add` (no overflow check) |
| `refcount_dec_and_test` | 1 | `atomic_get_and_set` (no overflow check) |
| `refcount_inc_not_zero` | 1 | `atomic_test_and_set` (loop) |
| `refcount_dec_and_mutex_lock` | 1 | A-reimplement (atomic + mutex) |
| `kref_init` | 2 | `atomic_set` |
| `kref_get` | 2 | `atomic_get_and_set` (no overflow check) |
| `kref_put` | 1 | A-reimplement (refcount + callback) |

## Time and Scheduling (A-reimplement / C-replace, 8 entries)

Linux jiffies-based timing has no direct Haiku equivalent; Haiku uses
`bigtime_t` (microseconds) which avoids wraparound issues.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `msleep` | 6 | `snooze` (Haiku uses microseconds) |
| `usleep_range` | 2 | `snooze` (exact, no range) |
| `msecs_to_jiffies` | 2 | Direct conversion (bigtime_t) |
| `time_before` | 1 | Direct comparison (no wraparound) |
| `timeout` | 1 | Direct comparison (bigtime_t) |
| `schedule_work` | 5 | A-reimplement (use threads or timers) |
| `INIT_WORK` | 5 | A-reimplement (thread setup) |
| `flush_work` | 5 | Thread join |

## Firmware Loading (C-replace, 2 entries)

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `request_firmware` | 4 | `fopen` + `fread` (file I/O) |
| `release_firmware` | 3 | `free` (standard C) |

## DMA Operations (C-replace / A-reimplement, 5 entries)

Linux DMA mapping is platform-specific. The Haiku driver needs custom DMA
descriptor handling for the GPU.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `dma_map_page` | 5 | `malloc` (standard C) |
| `dma_unmap_page` | 3 | `free` (standard C) |
| `dma_mapping_error` | 1 | A-reimplement (custom error checking) |
| `dma_free_coherent` | 1 | A-reimplement (custom DMA cleanup) |
| `sg_next` | 1 | A-reimplement (custom descriptor format) |
| `sg_dma_len` | 1 | A-reimplement (custom descriptor format) |

## AGP / PCI (D-ignore, 8 entries)

These symbols relate to AGP and MSI interrupt handling, which the Haiku driver
does not use. The K40c uses direct BAR access and a different interrupt model.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `agp_enable` | 1 | D-ignore |
| `agp_backend_acquire` | 1 | D-ignore |
| `agp_backend_release` | 1 | D-ignore |
| `agp_copy_info` | 1 | D-ignore |
| `arch_phys_wc_add` | 2 | D-ignore (no write-combining) |
| `arch_phys_wc_del` | 2 | D-ignore |
| `pci_enable_msi` | 1 | D-ignore |
| `pci_disable_msi` | 1 | D-ignore |
| `pci_is_pcie` | 1 | A-reimplement (read PCI config) |

## Arithmetic and Bit Macros (A-reimplement, 26 entries)

These are compile-time C macros, not runtime functions. In Haiku, use
direct expressions or standard C equivalents.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `ARRAY_SIZE` | 2 | `sizeof(x) / sizeof(x[0])` |
| `ALIGN` | 2 | `(x + a - 1) & ~(a - 1)` |
| `ALIGN_DOWN` | 1 | `x & ~(a - 1)` |
| `BIT` | 4 | `1 << x` |
| `BIT_ULL` | 1 | `1ULL << x` |
| `BUG` | 1 | A-reimplement (graceful error handling) |
| `BUG_ON` | 2 | A-reimplement (error check) |
| `WARN_ON` | 3 | A-reimplement (debug logging) |
| `container_of` | 3 | Pointer arithmetic with offset |
| `DIV_ROUND_UP` | 1 | `(n + d - 1) / d` |
| `hweight32` | 1 | Bit-counting algorithm |
| `hweight8` | 1 | Bit-counting algorithm |
| `ilog2` | 1 | `__builtin_clz` or loop |
| `IS_ALIGNED` | 2 | `(x & (a - 1)) == 0` |
| `IS_ERR` | 1 | Custom error pointer scheme |
| `PTR_ERR` | 1 | Custom error pointer scheme |
| `ERR_PTR` | 1 | Custom error pointer scheme |
| `likely` | 1 | No branch prediction attribute |
| `lower_32_bits` | 1 | `x & 0xFFFFFFFF` |
| `max` | 1 | Standard `max` or ternary |
| `max_t` | 1 | Standard `max` with cast |
| `min` | 1 | Standard `min` or ternary |
| `min_t` | 1 | Standard `min` with cast |
| `order_base_2` | 1 | `ilog2` or loop |
| `unlikely` | 1 | No branch prediction attribute |
| `upper_32_bits` | 1 | `(u64 >> 32)` |
| `do_div` | 1 | Standard 64-bit division |
| `__ffs` | 1 | Bit scanning or loop |
| `for_each_set_bit` | 1 | Custom bit iteration |
| `find_first_zero_bit` | 1 | Custom bit search |

## Print and Debug (A-reimplement / C-replace, 3 entries)

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `printk` | 10 | A-reimplement (kernel logging API) |
| `snprintf` | 28 | `snprintf` (standard C) |
| `sprintf` | 2 | `sprintf` (standard C) |
| `strscpy` | 1 | `strlcpy` (standard C) |

## Differences That Matter

### Interrupt state preservation
`spin_lock_irqsave` saves the current interrupt state and disables interrupts,
then acquires the lock. On unlock, `spin_unlock_irqrestore` restores the exact
previous state. Haiku's `disable_interrupts` returns a `cpu_status` token;
`restore_interrupts(token)` restores it. The `spin_unlock_irq` variant (which
unconditionally enables interrupts) maps to `release_spinlock` +
`restore_interrupts(B_INTERRUPTS_ENABLED)`.

### Zeroed memory
`kzalloc` and `kvmalloc_array` zero the allocated memory. Haiku `malloc` does
not zero; use `calloc` when zeroing is needed. For large allocations where
Linux falls back to page-level allocation (`kvmalloc`), the Haiku driver must
manually zero after allocation.

### Firmware loading
Linux `request_firmware` searches a standard path and loads the file atomically.
Haiku has no equivalent; use `fopen`/`fread`/`fclose` with a configurable
firmware path. The firmware blob must be freed with `free` after use.

### Reference count overflow protection
Linux `refcount_t` saturates at `INT_MAX` instead of wrapping. Haiku atomic
functions do not check for overflow; the driver must add explicit checks
around `atomic_add` calls for reference counting.

### List iteration
Linux `list_for_each_entry` uses `container_of` to derive the containing
struct from the `list_head` member offset. Haiku has no `container_of` macro;
compute the offset manually using `offsetof` or pointer arithmetic. The
iteration pattern requires a temporary pointer for safe deletion during
traversal.

### Red-black tree
Linux code uses RB-trees for address-space management and page tracking.
Haiku has no built-in RB-tree; implement a minimal RB-tree or replace with
a hash table where the usage pattern allows.

### DMA mapping
Linux `dma_map_page` returns a bus address for device DMA access. The Haiku
driver must allocate physically contiguous memory and track its bus address
manually, as Haiku has no DMA mapping API.

### Atomic increment/decrement
Linux `atomic_inc` / `atomic_dec` are single instructions on x86. Haiku
`atomic_add` is also a single instruction but must be called with explicit
`+1` or `-1` parameters. For `atomic_inc_return` and `atomic_dec_and_test`,
use `atomic_get_and_set` in a loop with compare-and-swap semantics.
