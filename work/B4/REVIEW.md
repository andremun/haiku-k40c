# Review of B4, attempt 1 (2026-10-11): REWORK

The symbol list, counts and examples are right, the tool works, and most
of the 139 decisions are good (the macro group, memory, mutex and
spinlock functions). 19 checks now fail. Keep the tool and change its
table. Before you write a Haiku name, open the header and read the
declaration: `grep -n NAME reference/haiku/headers/PATH`.

## Defects

1. **List functions.** The review says "Haiku lists do not have a remove
   operation". They do. Read `reference/haiku/headers/private/kernel/util/list.h`
   (150 lines): `list_init`, `list_remove_item`, `list_remove_link`,
   `list_is_empty`. Fix `INIT_LIST_HEAD`, `list_del`, `list_del_init`,
   `list_empty`, and check the other `list_` entries against that file.
2. **Atomic and reference counts.** `atomic_add(&v, n)` returns the old
   value (`headers/os/support/SupportDefs.h:285`), so it replaces
   increment, decrement, "decrement and test" (old value 1) and
   "increment and return". `atomic_get_and_set` does not count. Fix
   `atomic_dec_and_test`, `atomic_inc_return`, `kref_get`,
   `refcount_dec_and_test`; check `kref_put` and `refcount_inc_not_zero`.
3. **`spin_lock_init`** is not `acquire_spinlock`. A Haiku spinlock is
   initialized with `B_INITIALIZE_SPINLOCK` or `B_SPINLOCK_INITIALIZER`
   (`headers/os/drivers/KernelExport.h`).
4. **DMA.** `dma_map_page` gives the device a bus address for a page of
   memory. `malloc` and `free` do not do that. Haiku: `get_memory_map`
   (and `lock_memory`) in `KernelExport.h`. Fix `dma_map_page`,
   `dma_unmap_page`; check `dma_mapping_error` and `dma_free_coherent`
   (look at `create_area` in `headers/os/kernel/OS.h`).
5. **Firmware.** `request_firmware` and `release_firmware` are called
   only in `gf100_gr_load_fw`, which loads the external firmware files.
   Task C2 found that the driver uses the built-in arrays and never
   takes that path: category `D-ignore`. (The first task text said
   `C-replace`; that was wrong.) `fopen` from a boot loader header is
   not a kernel API.
6. **`X-not-linux` used for Linux symbols.** `set_bit`, `clear_bit`,
   `__set_bit` and `__mutex_init` are Linux. Look at `atomic_or` and
   `atomic_and` for the bit functions.
7. **`printk`**: Haiku has `dprintf` (`KernelExport.h`).
8. Write `analysis/linux_deps.md` again from the new table.

## What was good

One session, the rule implemented exactly (139 symbols, counts right),
honest notes on the macros and on the red-black tree functions.
