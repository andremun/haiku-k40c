# B5 macro-task plan

1. Record ADR 005 and update repository rules and review scope. Check and commit.
2. Build a separate guarded B5 launcher, stage-tag the identity probe, and add host refusal tests.
3. Apply the four S1C/S1D review fixes and document launcher use.
4. Verify the host state without changing binding. Build both native probes.
5. Run the pending cardless KVM check, then one authorized B5 identity stage.
6. Save dated command, hash, launch, serial, and result evidence. Stop on a hang or panic.
7. Run make check and vm-tools-test, commit, re-pin shared tools, and hand off the macro task.

No VM was running at task start. A read-only host process check found no QEMU.
The saved ~/haiku-vm/pid was stale. Both monitor sockets were absent.
