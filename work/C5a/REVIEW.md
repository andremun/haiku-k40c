# Review C5a (scaffold, 2026-10-13): ACCEPT

- The binary, the JSON and the document agree with the log (`make check`,
  which recomputes all three from `reference/linux-run/compute_test.log`).
- Corrected by the reviewer: `work/C5a/RESULT.md` and the task log gave
  143 descriptor fields, 29 table rows and 7 source lines. The files
  have 155, 30 and 8. The numbers in a result file must be read from
  the output, not counted by hand.
- The question "why NVF1 and not GK110" in RESULT.md: NVF1 is Mesa's
  name for chipset 0xf1, which Nouveau calls GK110B (dmesg-nouveau.txt).
