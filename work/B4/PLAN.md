# Plan: B4 Rework (fix 19 make check failures)

All 19 failures are classification/haiku_api errors in `tools/linux_deps.py`.
The JSON tool output is correct (counts, examples match the rule).

## Fixes

1. **List functions** (4): `INIT_LIST_HEAD` → `list_init`, `list_del` /
   `list_del_init` → `list_remove_link`, `list_empty` → `list_is_empty`.
   Verified in `reference/haiku/headers/private/kernel/util/list.h`.

2. **Atomic/references** (4): `atomic_dec_and_test`, `atomic_inc_return`,
   `kref_get`, `refcount_dec_and_test` → `atomic_add` (returns old value,
   not new). Verified in `SupportDefs.h:285`.

3. **Spinlock init** (1): `spin_lock_init` → `B_INITIALIZE_SPINLOCK` /
   `B_SPINLOCK_INITIALIZER`. Verified in `KernelExport.h:30-31`.

4. **DMA** (2): `dma_map_page` → A-reimplement with `get_memory_map`,
   `dma_unmap_page` → A-reimplement with no haiku_api.

5. **Firmware** (2): `request_firmware` / `release_firmware` → D-ignore.

6. **Bit/mutex** (4): `set_bit`/`__set_bit` → C-replace `atomic_or`,
   `clear_bit` → C-replace `atomic_and`, `__mutex_init` → C-replace `mutex_init`.

7. **printk** (1): → C-replace `dprintf` (`KernelExport.h`).

8. Regenerate `analysis/linux_deps.json` and rewrite `analysis/linux_deps.md`.
