# Findings

The user directly approves the exact current package as a minor change:
"I approve because this is not a major change."
No independent Claude acceptance was supplied. This is direct user authorization,
not a claimed Claude review. One launch only. D1 and retries are not authorized.
The b0c24e4 package and all consumed markers must remain unchanged.

Exactly one launch: results/20261029-a7-069cb71b. Result PASS in 134.02 s.
POST 88805 us; diagnostic drain 21694572 us.
537 active/38 skipped; exact Linux PC/active sequence after excluding its 23
synthetic offset-zero REPEAT log messages. No evidence contradiction remains.
Both sensor pairs: four address NACKs with clean STOP, then ReferenceNack.
Nine condition polls complete, with two samples at three PCs and one at six.
Fresh witness target 0x16d2000; encoded programming 0x16d20.
Actual post-POST flush readback zero; cause UNKNOWN. Re-arm callback succeeds;
no readback after re-arm. Timer, 11520 MiB and three-dword scratch checks pass.
Pending zero INFERRED from guarded PASS, not raw telemetry. Complete owner retains
its reference. R5 unchanged, no allowances, host command 0x0002/master off.
Owned QEMU/tracer exited; pgrep found no QEMU. Approval consumed, no retry.
Report generator checks raw-capture/source hashes and normalized instruction
selection. No S1/DMA-publication/coherency claim. D1 remains unapproved.

Final full make check and result_report.py --check pass. Host-wide process
inventory (vm_guard.refuse_running_guest) also confirms no QEMU system guest.
The b0c24e4 generated review entry is preserved as the pre-run package snapshot;
current outcome is in STATUS and the run README. No reviewed source/binary changed.
