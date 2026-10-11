# Plan: B4 Rework attempt 3 (fix 6 remaining failures)

The tool output and JSON are correct (139 symbols, counts right).
6 failures remain: 5 classification errors + 1 markdown table count.

## Fixes

1. **`printk`** in CLASSIFY: change from A-reimplement→C-replace,
   haiku_api=["dprintf"], header=KernelExport.h (via boot/platform.h).
2. **`set_bit`/`clear_bit`/`__set_bit`**: add to CLASSIFY as C-replace,
   haiku_api=["atomic_or"] / ["atomic_and"], header=SupportDefs.h.
3. **`__mutex_init`**: add to CLASSIFY as C-replace with mutex_init.
4. **Markdown generation**: add `write_md()` function to the tool that
   writes `analysis/linux_deps.md` from the JSON entries. Update `--check`
   to also verify the markdown file.
5. **Missing groups in markdown**: add X-not-linux group and the 4 missing
   symbols (memcmp, memcpy, memset, __mutex_init) to their groups.

## Verification

Run `make check` (expect 0 failures).
