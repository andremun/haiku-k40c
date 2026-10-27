> **Claude Code review of the S1 batch (2026-10-27/28), and changes to make**
>
> **Verdict:** ACCEPT the batch (S1BOARD through S1D0PACKAGE). No Important defects in the parts that can touch the card. Scope of this review: the progress document, ADRs 006-008, the D0 stage, and every path that can reach the card. Not a line-by-line read of all 278 files.
>
> **Checked and accepted:**
> - The hardware gate holds. POST, board and I2C refuse any backend that is not a host simulation (`src/devinit/Board.cpp:32,43`, `BoundPost.cpp:8`, `I2c.cpp:10,95`). No native module can write the card yet.
> - D0 is a read-only stage. The guest side is the unchanged B5 identity probe plus `tools/haiku/selftest/map_owner.cpp`, which makes no PCI, BAR or device call. The card sees only the identity read and the VFIO reset at start.
> - The `IO` helper sequence matches `init.c:1640-1651`. `tools/board_trace.py` compares it with trace lines 45579-45598. ZM_CR uses `0x601000 + port` (`vga.c:52`).
> - The strace-based observer licensing is correct: an original MIT decoder, built into a private strace build that is never distributed or linked into the driver.
> - `make check`, `make vm-tools-test` and `tools/haiku/d0_stage.py --check` pass. `d0_run.py --check` stops only at the missing R5 stream.
> - The progress document is honest about scope and labels.
>
> **Rule change, already committed (bdc6317, user decision 2026-10-28):** ADR 008 and `AGENTS.md` now say that ADR 008 approves read-only stages only. A write stage needs the user's go-ahead each time, before it runs: A7, the first write of each C3 stage, or any stage whose driver can write a GPU register, program the card or start device DMA. Present the reviewed stage package (command, driver hashes, the writes it can make, stop conditions) and wait for an explicit yes. One yes covers one run of one stage. Do not start a write stage on the strength of ADR 008.
>
> **R5 changes (user decision: filtered stream in the home folder, only during card stages).** The user runs:
>
> ```
> sudo journalctl -k -b -f --no-pager --output=short-monotonic | grep --line-buffered -iE 'dmar|amd-vi|iommu|vfio|remapping|0000:04:00|aer|pcie bus error' > ~/k40-s1-kernel.log
> ```
>
> Changes in `tools/haiku/d0_kernel_log.py` and its tests:
> 1. Path: replace the fixed `/tmp/k40-s1-kernel.log` (line 15) with `~/k40-s1-kernel.log`, overridable by an environment variable (for example `K40_KERNEL_LOG`). Keep `O_NOFOLLOW`, the regular-file check and the owner check. The redirect runs in the user's shell, so the file belongs to the user.
> 2. Keep the reader detection (`find_reader`, `REQUIRED`). The piped journalctl keeps those options. When grep dies, journalctl exits on SIGPIPE and the pidfd check sees it. Add a test for that case.
> 3. The baseline check (line 44) still works: with `-b`, the boot's own DMAR/VFIO lines pass the filter. Keep the error message clear if the filtered baseline is empty.
> 4. Add PCIe AER to the fault rule: `FAULT` (line 16) must also stop on AER and "PCIe Bus Error" lines for `0000:04:00.0` or its root port. Today the grep keeps them, but `FAULT` would not stop on them.
> 5. Evidence wording: the log is filtered. A pass means "no new line of the filtered classes", not "a clean kernel log". Record the filter pattern in each run's evidence.
> 6. Update R5 in `docs/REQUESTS.md` and the commands in `docs/D0-STAGE-REVIEW.md` to the new command and path. Say that the user starts the stream only for a card stage and stops it afterwards.
> 7. Nit: `d0_run.py --check` prints a Python traceback when the log is missing (`d0_kernel_log.py:35`). Print one line that points to R5.
>
> Then run D0 (read-only, approved under ADR 008). After any launcher stop, report and ask first (ADR 006).
>
> **Order of work after D0 (reviewer advice):** the critical path is A7, the POST. The card is not set up when a guest starts (`0x02240c` bit 1 is 0, `nvkm/subdev/devinit/gf100.c:101`), so no FIFO or DMA stage can work before POST. Make the next macro task the native POST integration: connect the bound POST and board helpers to a real register backend behind a stage gate. End it with an A7 stage package for the user's go-ahead, holding:
> - the exact command and driver hashes;
> - the full list of register writes the script can make on this ROM (from `devinit_preflight`);
> - the readiness checks after POST (identity, timer, memory size, scratch test);
> - the stop conditions.
>
> Do not build more mapping or visibility machinery before A7. D1, the first device DMA, comes after POST and also needs the user's go-ahead.
>
> **Notes from B5 that apply to A7:**
> - Haiku loaded the probe twice in one boot (B5 serial lines 901-904, 912-915). A write-stage driver must run its start-up sequence once only. The owner one-shot latch must cover POST.
> - The PCI command register was `0x0007`: bus mastering was already on before our driver ran (INFERRED: set by OVMF or Haiku). Record it before POST. Do not assume the card cannot reach host memory.
>
> **Nit:** new files write the name as "Mario Andres Munoz", older ones as "Mario Andrés Muñoz". Pick one rule: ASCII in Python and C comments, the full form elsewhere, for example. Write it in `AGENTS.md` ("License").