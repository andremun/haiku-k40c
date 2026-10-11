# Linux Dependency Map

This document lists all Linux kernel symbols called by the 70 Nouveau source
files relevant to the GK110 (Tesla K40c) GPU driver, with their replacement
strategy for the Haiku driver.

## Summary

| Category | Count | Description |
|---|---|---|
| C-replace | 61 | Direct Haiku equivalent exists |
| A-reimplement | 60 | Must be reimplemented in the driver |
| X-not-linux | 8 | Nouveau internals or hardware constants |
| D-ignore | 10 | AGP/write-combining; not used by Haiku driver |

## Memory Allocation (21 entries)

Linux kernel allocators provide zeroing, overflow checks, and virtual mapping that Haiku's standard C functions do not replicate in the same call.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `alloc_page` | 2 | A-reimplement (alloc_page allocates a single kernel page. Haiku needs a pag) |
| `__free_page` | 3 | A-reimplement (__free_page releases a single kernel page. Haiku has no page) |
| `kfree` | 32 | `free` |
| `kmemdup` | 1 | `malloc` `memcpy` |
| `kmalloc` | 7 | `malloc` |
| `kvmalloc` | 1 | `malloc` |
| `kvmalloc_array` | 2 | `malloc` |
| `kvcalloc` | 1 | `calloc` |
| `kvfree` | 5 | `free` |
| `kvzalloc` | 1 | `calloc` |
| `kzalloc` | 39 | `calloc` |
| `struct_size` | 1 | `malloc` |
| `vfree` | 10 | `free` |
| `vmap` | 1 | A-reimplement (vmap maps page frames into contiguous virtual address space.) |
| `vunmap` | 1 | A-reimplement (vunmap releases virtual mapping created by vmap. Haiku needs) |
| `memcpy` | 4 | `memcpy` |
| `memcpy_fromio` | 1 | `memcpy` |
| `memcpy_toio` | 1 | `memcpy` |
| `memset` | 5 | `memset` |
| `memset_io` | 1 | `memset` |
| `memcmp` | 3 | `memcmp` |

## Locking (13 entries)

Linux spinlocks and mutexes map to Haiku's spinlock and mutex APIs. The irqsave/irqrestore variants additionally manipulate interrupt state.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `__mutex_init` | 1 | `mutex_init` |
| `mutex_init` | 14 | `mutex_init` |
| `mutex_lock` | 36 | `mutex_lock` |
| `mutex_unlock` | 44 | `mutex_unlock` |
| `mutex_destroy` | 9 | `mutex_destroy` |
| `mutex_is_locked` | 1 | A-reimplement (mutex_is_locked checks if a mutex is held. Haiku has no publ) |
| `spin_lock` | 14 | `acquire_spinlock` |
| `spin_unlock` | 14 | `release_spinlock` |
| `spin_lock_irqsave` | 8 | `acquire_spinlock` `disable_interrupts` |
| `spin_unlock_irqrestore` | 10 | `release_spinlock` `restore_interrupts` |
| `spin_lock_irq` | 5 | `acquire_spinlock` `disable_interrupts` |
| `spin_unlock_irq` | 5 | `release_spinlock` `restore_interrupts` |
| `spin_lock_init` | 6 | `B_INITIALIZE_SPINLOCK` `B_SPINLOCK_INITIALIZER` |

## List Operations (13 entries)

Linux `struct list_head` is a doubly-linked list with embedded pointers. Haiku's `BList` / `list` type is similar but the entry macros use `container_of` which must be reimplemented.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `INIT_LIST_HEAD` | 20 | `list_init` |
| `list_add` | 6 | `list_add_link_to_head` |
| `list_add_tail` | 14 | `list_add_link_to_tail` |
| `list_del` | 17 | `list_remove_link` |
| `list_del_init` | 2 | `list_remove_link` `list_init` |
| `list_empty` | 5 | `list_is_empty` |
| `list_for_each_entry` | 11 | A-reimplement (list_for_each_entry is a container_of-based loop macro. Haik) |
| `list_for_each_entry_safe` | 8 | A-reimplement (list_for_each_entry_safe allows deleting entries during iter) |
| `list_first_entry` | 1 | A-reimplement (list_first_entry returns the first entry of a list. Haiku ne) |
| `list_first_entry_or_null` | 2 | A-reimplement (list_first_entry_or_null returns the first entry or NULL. Ha) |
| `list_last_entry` | 1 | A-reimplement (list_last_entry returns the last entry of a list. Haiku stru) |
| `list_move_tail` | 1 | `list_move_to_list` |
| `list_entry` | 1 | A-reimplement (list_entry is a container_of macro to get struct from list m) |

## Red-Black Tree (6 entries)

Linux `struct rb_tree` has no Haiku equivalent. All RB-tree operations must be reimplemented or replaced with a hash table / sorted array.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `rb_entry` | 6 | A-reimplement (rb_entry is a container_of macro for rb_node embedded in a s) |
| `rb_erase` | 2 | A-reimplement (rb_erase removes a node from a red-black tree. Haiku has no ) |
| `rb_first` | 1 | A-reimplement (rb_first returns the leftmost (smallest) node. Haiku needs R) |
| `rb_insert_color` | 2 | A-reimplement (rb_insert_color rebalances the RB-tree after insertion. Haik) |
| `rb_link_node` | 2 | A-reimplement (rb_link_node links a node into a parent tree. Haiku needs RB) |
| `rb_next` | 1 | A-reimplement (rb_next returns the next node in in-order traversal. Haiku n) |

## Atomics (8 entries)

Haiku provides `int32` atomic functions in `SupportDefs.h`: `atomic_set`, `atomic_get`, `atomic_get_and_set`, `atomic_add`, `atomic_test_and_set`. Linux's `atomic_inc`/`atomic_dec` map to `atomic_add` with +1/-1.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `atomic_set` | 8 | `atomic_set` |
| `atomic_read` | 5 | `atomic_get` |
| `atomic_inc` | 3 | `atomic_add` |
| `atomic_dec` | 1 | `atomic_add` |
| `atomic_inc_return` | 3 | `atomic_add` |
| `atomic_dec_and_test` | 2 | `atomic_add` |
| `atomic_xchg` | 2 | `atomic_get_and_set` |
| `atomic_cmpxchg` | 2 | `atomic_test_and_set` |

## Reference Counts (8 entries)

Linux `refcount_t` and `kref` use the same atomic primitives as the general atomic API but add overflow protection. Haiku atomics lack overflow checks.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `refcount_set` | 7 | `atomic_set` |
| `refcount_inc` | 3 | `atomic_add` |
| `refcount_dec_and_test` | 3 | `atomic_add` |
| `refcount_inc_not_zero` | 3 | `atomic_test_and_set` |
| `refcount_dec_and_mutex_lock` | 2 | A-reimplement (refcount_dec_and_mutex_lock decrements and acquires a mutex ) |
| `kref_init` | 3 | `atomic_set` |
| `kref_get` | 3 | `atomic_add` |
| `kref_put` | 3 | A-reimplement (kref_put decrements a kref and calls the release callback wh) |

## Time and Scheduling (8 entries)

Linux jiffies-based timing has no direct Haiku equivalent; Haiku uses `bigtime_t` (microseconds) which avoids wraparound issues.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `msleep` | 1 | `snooze` |
| `usleep_range` | 1 | `snooze` |
| `msecs_to_jiffies` | 1 | A-reimplement (msecs_to_jiffies converts milliseconds to jiffies. Haiku tim) |
| `time_before` | 1 | A-reimplement (time_before checks if one jiffy timestamp is before another ) |
| `timeout` | 1 | A-reimplement (timeout is a helper macro for timeout loops with jiffies. Ha) |
| `schedule_work` | 1 | A-reimplement (schedule_work queues a work item on a workqueue for deferred) |
| `INIT_WORK` | 1 | A-reimplement (INIT_WORK initializes a work item with a handler function. H) |
| `flush_work` | 1 | A-reimplement (flush_work waits for a work item to complete. Haiku has no w) |

## Firmware Loading (2 entries)

Linux firmware loading is filesystem-based. The Haiku driver uses built-in firmware arrays and does not need external file loading.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `request_firmware` | 2 | D-ignore (request_firmware loads firmware from filesystem. Only gf100_) |
| `release_firmware` | 1 | D-ignore (release_firmware frees a firmware blob from request_firmware) |

## DMA Operations (6 entries)

Linux DMA mapping is platform-specific. The Haiku driver needs custom DMA descriptor handling for the GPU.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `dma_map_page` | 2 | `get_memory_map` `lock_memory` |
| `dma_unmap_page` | 2 | `unlock_memory` |
| `dma_mapping_error` | 2 | A-reimplement (dma_mapping_error checks if a DMA mapping failed. Haiku DMA ) |
| `dma_free_coherent` | 1 | A-reimplement (dma_free_coherent releases coherent DMA memory. Haiku has no) |
| `sg_next` | 1 | A-reimplement (sg_next returns the next scatterlist entry. Haiku has no sca) |
| `sg_dma_len` | 1 | A-reimplement (sg_dma_len returns the DMA length of a scatterlist entry. Ha) |

## AGP / PCI (9 entries)

These symbols relate to AGP and MSI interrupt handling, which the Haiku driver does not use. The K40c uses direct BAR access and a different interrupt model.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `agp_enable` | 2 | D-ignore (agp_enable enables AGP mode. Haiku driver does not use AGP; ) |
| `agp_backend_acquire` | 2 | D-ignore (agp_backend_acquire acquires the AGP backend. Haiku driver d) |
| `agp_backend_release` | 2 | D-ignore (agp_backend_release releases the AGP backend. Haiku driver d) |
| `agp_copy_info` | 1 | D-ignore (agp_copy_info copies AGP GATT table info. Haiku driver does ) |
| `arch_phys_wc_add` | 1 | D-ignore (arch_phys_wc_add adds a write-combining memory region. Haiku) |
| `arch_phys_wc_del` | 1 | D-ignore (arch_phys_wc_del removes a write-combining region. Haiku dri) |
| `pci_enable_msi` | 1 | D-ignore (pci_enable_msi enables MSI interrupts. Haiku driver uses a d) |
| `pci_disable_msi` | 1 | D-ignore (pci_disable_msi disables MSI interrupts. Haiku driver does n) |
| `pci_is_pcie` | 3 | A-reimplement (pci_is_pcie checks if a device is PCIe. Haiku driver reads P) |

## Arithmetic and Bit Macros (33 entries)

These are compile-time C macros, not runtime functions. In Haiku, use direct expressions or standard C equivalents.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `BIT` | 24 | A-reimplement (BIT(x) is a compile-time shift macro, not a function call. H) |
| `BIT_ULL` | 5 | A-reimplement (BIT_ULL(x) is a compile-time 64-bit shift macro. Haiku can u) |
| `upper_32_bits` | 10 | A-reimplement (upper_32_bits extracts the upper 32 bits of a 64-bit value. ) |
| `lower_32_bits` | 9 | A-reimplement (lower_32_bits extracts the lower 32 bits of a 64-bit value. ) |
| `ALIGN` | 8 | A-reimplement (ALIGN(x, a) rounds x up to the next multiple of a. Haiku can) |
| `ALIGN_DOWN` | 1 | A-reimplement (ALIGN_DOWN(x, a) rounds x down to the previous multiple of a) |
| `min` | 12 | A-reimplement (min(x, y) is a compile-time comparison macro with type safet) |
| `min_t` | 3 | A-reimplement (min_t(type, x, y) is a typed comparison macro. Haiku can use) |
| `max` | 5 | A-reimplement (max(x, y) is a compile-time comparison macro with type safet) |
| `max_t` | 5 | A-reimplement (max_t(type, x, y) is a typed comparison macro. Haiku can use) |
| `DIV_ROUND_UP` | 3 | A-reimplement (DIV_ROUND_UP(n, d) computes (n + d - 1) / d at compile time.) |
| `order_base_2` | 1 | A-reimplement (order_base_2(n) computes the log2 of the next power of two. ) |
| `ARRAY_SIZE` | 7 | A-reimplement (ARRAY_SIZE(x) is a compile-time array size macro. Haiku can ) |
| `unlikely` | 8 | A-reimplement (unlikely(x) is a branch prediction hint macro. Haiku has no ) |
| `likely` | 7 | A-reimplement (likely(x) is a branch prediction hint macro. Haiku has no br) |
| `IS_ERR` | 12 | A-reimplement (IS_ERR() checks if a pointer is an error value (encoded errn) |
| `PTR_ERR` | 11 | A-reimplement (PTR_ERR() extracts the errno from an error pointer. Haiku ne) |
| `ERR_PTR` | 3 | A-reimplement (ERR_PTR() encodes an errno as an error pointer. Haiku needs ) |
| `IS_ALIGNED` | 9 | A-reimplement (IS_ALIGNED(x, a) checks if x is aligned to a. Haiku can use ) |
| `WARN_ON` | 40 | A-reimplement (WARN_ON(condition) logs a warning if condition is true. Haik) |
| `BUG_ON` | 6 | A-reimplement (BUG_ON(condition) triggers a kernel panic. Haiku driver shou) |
| `BUG` | 2 | A-reimplement (BUG() triggers a kernel panic unconditionally. Haiku driver ) |
| `do_div` | 1 | A-reimplement (do_div divides a 64-bit value by a 32-bit divisor, modifying) |
| `container_of` | 25 | A-reimplement (container_of computes struct pointer from member address. Ha) |
| `set_bit` | 1 | `atomic_or` |
| `clear_bit` | 1 | `atomic_and` |
| `__set_bit` | 2 | `atomic_or` |
| `__ffs` | 3 | A-reimplement (__ffs finds the first set bit in a 64-bit value. Haiku has n) |
| `for_each_set_bit` | 2 | A-reimplement (for_each_set_bit iterates over set bits in a bitmap. Haiku h) |
| `find_first_zero_bit` | 1 | A-reimplement (find_first_zero_bit finds the first unset bit in a bitmap. H) |
| `ilog2` | 2 | A-reimplement (ilog2 computes the integer log2 of a value. Haiku has no ilo) |
| `hweight32` | 1 | A-reimplement (hweight32 counts set bits in a 32-bit value. Haiku has no hw) |
| `hweight8` | 1 | A-reimplement (hweight8 counts set bits in a byte. Haiku has no hweight; im) |

## Print and Debug (4 entries)

Linux printk provides log levels; Haiku dprintf has the same format-string semantics.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `printk` | 1 | `dprintf` |
| `snprintf` | 3 | `snprintf` |
| `sprintf` | 2 | `sprintf` |
| `strscpy` | 2 | `strlcpy` |

## X-not-linux (8 entries)

These symbols are not Linux kernel infrastructure. They are hardware constants or Nouveau-internal definitions that were caught by the call-matching rule.

| Symbol | Count | Haiku Replacement |
|---|---|---|
| `CLR_PTES` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `FBP` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `LTC` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `MAP_PTES` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `PTE` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `REF_PTES` | 1 | X-not-linux (This is a hardware constant or macro, not a Linux function. ) |
| `bool` | 1 | X-not-linux (This symbol is not standard Linux kernel infrastructure. It ) |
| `d` | 1 | X-not-linux (This is a Nouveau-internal function, not a Linux kernel func) |

## Differences That Matter

### Interrupt state preservation

`spin_lock_irqsave` saves the current interrupt state and disables interrupts, then acquires the lock. On unlock, `spin_unlock_irqrestore` restores the exact previous state. Haiku's `disable_interrupts` returns a `cpu_status` token; `restore_interrupts(token)` restores it.

### Zeroed memory

`kzalloc` and `kvmalloc_array` zero the allocated memory. Haiku `malloc` does not zero; use `calloc` when zeroing is needed.

### Firmware loading

Linux `request_firmware` searches a standard path and loads the file atomically. The driver uses built-in firmware arrays and never takes this path: these symbols are D-ignore.

### Reference count overflow protection

Linux `refcount_t` saturates at `INT_MAX` instead of wrapping. Haiku atomic functions do not check for overflow; the driver must add explicit checks.

### Bit manipulation

`set_bit` and `clear_bit` manipulate single bits in a word. Haiku `atomic_or` and `atomic_and` with the appropriate mask provide the same operation.

### Print and debug

`printk` is the Linux kernel logging function with log levels. Haiku `dprintf` has the same format-string semantics but no log-level system.

### Mutex initialization

`__mutex_init` is the internal mutex initialiser used by Nouveau. Haiku `mutex_init` provides the same functionality.

### Atomic increment/decrement

Linux `atomic_inc` / `atomic_dec` are single instructions on x86. Haiku `atomic_add` is also a single instruction but must be called with explicit `+1` or `-1` parameters.
