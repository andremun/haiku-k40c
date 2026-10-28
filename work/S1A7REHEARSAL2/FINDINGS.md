# Findings

KNOWN: the previous serial capture discovers .k40_identity_probe.partial and
.k40_a7_stage.partial (lines 852 and 862). The prior pass criteria were incomplete.
The earlier evidence is retained. No card was present in that rehearsal.

The user supplied Claude's correction and accepted the FIFO/I2C guards and
BoundPost refactor. No GPU permission change is needed. ESC-003 remains resolved
in direction, with task validation reopened until this rework passes.

The pinned Haiku legacy loader source watches modification time changes
(legacy_drivers.cpp:805-825). The cardless-only reload command touches the final
client/identity files and scans devfs after the failed open. It never opens again.
A read-only ABI diagnostic reports resident owner load counts and boot state.
The prepare counter must remain one across the client reload. Constructor and
client init never prepare storage or activate the physical execution permit.

A separate cardless export saved the guest's libroot.so under ~/haiku-cross/lib/.
The existing runner's kernel_x86_64 transfer slot carried libroot bytes in this
export-only job. runtime.json labels that transport explicitly and binds the
library and real guest kernel hashes. This was not a driver or GPU test.
Consulted cross-tree Haiku sources: system/glue/start_dyn.c:31-46,
runtime_loader/runtime_loader.cpp:770-771, headers/private/system/syscalls.h:273-274.
The helper uses raw _kern_open status, preserving B_ERROR as 0xffffffff.

Claude reported that make check needs the ~/mediaflux network mount, which
dropped during review. This session has an existing checked local ROM copy in
~/haiku-cross/vbios selected through K40_VBIOS. Default network paths can fail
when that mount is absent. Verification still enforces exact source/capture hashes.
