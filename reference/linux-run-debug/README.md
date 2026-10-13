# Reference run with the driver's debug log (2026-10-13)

The same job as `reference/linux-run/`, in the same guest on the same
card, with Nouveau loaded as `modprobe nouveau debug=trace`. Result:
PASS, renderer NVF1.

- `dmesg.txt.xz`: the kernel log, 6,086 lines. The lines between
  `MARK compute_test start` (line 4699) and `MARK compute_test end`
  (line 6081) are the job. Nouveau prints what it does: `fifo:` lines
  for channels and the runlist (`RAMRL`), `gr:` lines for the graphics
  engine, `mmu:` lines for address-space work, `ioctl:` lines for each
  request of the user program.
- `mmiotrace.txt.xz`: the register trace of this run (901,738 lines),
  with the same two markers. Both files use the kernel clock, so a
  time in one can be found in the other. Line numbers are NOT those of
  `reference/linux-run/mmiotrace.txt.xz`: this is another run.
- `debug_run.sh`: the script that was run in the guest.

Read with `xz -dc reference/linux-run-debug/dmesg.txt.xz | sed -n '4699,4760p'`.
