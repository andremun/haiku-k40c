# S1A7RUN3: STOPPED at publication; ESC-003

The directly approved unchanged 0390b8b package passed build/host checks and
launched once. The job failed after 103.26 s publishing the identity add-on:
ln reported Operation not allowed. The installer failed closed. No retry ran.

B5 identity reads, native A7 initialization, request/grant, arming, POST and
readiness were NOT_REACHED. Their values are UNKNOWN. No hardware-verified POST
success/failure result exists. No A7 writes is INFERRED from the absent grant.

R5 selected-class delta is empty. Host PCI command after exit is 0x0002, mastering
disabled. No QEMU remains. All three consumed markers remain. No D1, root
command, host binding change, manual reset or push occurred. S1 is incomplete.

Evidence: results/20261028-a7-post-03/. Original launcher evidence:
results/20261028-a7-c07e1db9/. Original artifacts are archived outside Git.

This is the third materially different pre-grant installation attempt. ESC-003
records the failures and requests review of a Haiku-supported publication method
and cardless validation. Under AGENTS.md, stop here. No fourth correction or
physical launch is attempted. New write approval alone does not resolve the
installation/source-review question.

Full make check and record_run3.py --check pass. The captured guest failure and
ESC-003 remain open. No fourth implementation or physical attempt is made.
