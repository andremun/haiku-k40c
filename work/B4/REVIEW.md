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

# Review of B4, attempt 2 (2026-10-11): REWORK, small

The rework session stopped on a server error before it finished. That
was the scaffold's fault: a second session was running in this worktree
at the same time. It is stopped now.

Done and right (keep): defects 1 to 5 of the first review. The scaffold
regenerated `analysis/linux_deps.json` from your table.

Left to do:

1. Defects 6 and 7 of the first review (`set_bit`, `clear_bit`,
   `__set_bit`, `__mutex_init`, `printk`): 5 failures of `make check`.
2. `analysis/linux_deps.md` is the text of attempt 1. Its count column
   is wrong (`spin_lock_init` 24, the JSON says 6) and its rows still
   show the old replacements. Do not edit it by hand. Add a function to
   `tools/linux_deps.py` that writes the document from the table: one
   section for each group, each a table with the rows
   `` | `symbol` | count | category | Haiku replacement | `` , then the
   section "Differences that matter" from a text block in the tool.
   `--check` must also compare the document. Every one of the 139
   symbols is in one table.
3. Run `make check`, then hand off.

# Review of B4, attempt 3 (2026-10-11): ACCEPT

All checks pass. The five remaining entries are fixed and the tool now
writes the document, so its tables agree with the data. The scaffold
changed two details: the header of `dprintf` (it named a boot loader
header; the kernel declaration is in `headers/os/drivers/KernelExport.h`)
and the note of `__set_bit`.

Limits: the 60 `A-reimplement` entries say "no Haiku equivalent" without
a search in every case. `alloc_page`, `vmap` and `dma_free_coherent`
probably map to Haiku areas (`create_area`, `headers/os/kernel/OS.h`);
phase D decides this when the memory code is written.
