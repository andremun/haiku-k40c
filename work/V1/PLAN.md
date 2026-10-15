# V1: cardless verification toward S1

Date: 2026-10-16 (Australia/Melbourne).

User-directed follow-up: revise possible mistakes made by "Local" and move
closer to machine-dependent implementation. This is a new verification pass,
not an endorsement of the rejected A3 work or a replacement for hardware tests.
Do not read the reviewer implementation. Do not use the task-a3 branch.

1. Run the existing checks before changing code; record environment failures.
2. Independently test range/parsing boundaries in the host helpers and fix
   reproducible failures, preserving the existing acceptance tests.
3. Add a freestanding S1 experiment controller and backend contract: explicit
   preparation, publication before PUT, new GET progress, fault/deadline checks,
   quiescence before release, and retained memory when quiescence is not proven.
4. Host-test normal and injected failure paths. No real MMIO or PCI access.
5. Record verification gates and machine-dependent inputs still needed. The user
   will provide a solution for the absent ROM later. Do not treat absent ROM,
   missing pinned sources or missing cross-toolchain as evidence against S1.
6. Update status and commit locally. Do not push. If full make check remains
   blocked, label the task partial/blocked, never DONE.
