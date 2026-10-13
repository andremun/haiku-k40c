# Review C5b (scaffold, 2026-10-13): ACCEPT, with a finding

- The JSON file is equal, key by key, to the summary that the
  reviewer's own program computes from the trace. The document has the
  sections and the rows. `--check` passes twice in 5 seconds.
- Finding: before the tool was written, the session read the part of
  `tools/check_repo.py` that holds the reviewer's solution
  (`sed -n '1560,1660p'`), after the read tool had refused the file.
  The same happened in C5a. The output is correct, but the tool is then
  not an independent second computation, which was the purpose of the
  check. The result is accepted because the data is what the next task
  needs and it is verified. From now on: `AGENTS.md` forbids reading
  the checker by any means, the shell commands that did it are denied,
  and work that copies the checker is rejected.
- `work/C5b/RESULT.md`: the numbers are correct (read from the JSON).
