# 001. This repository owns the Haiku VM tools

Date: 2026-10-23. Status: accepted (alignment plan decision D4).

## Context

Three repositories ran Haiku VMs with their own tools: `tools/haiku/` here,
`tools/app_vm.py` and `tools/transfer_server.py` in `haiku-k40c-llm` and in
`opencode-haiku` (two diverged copies). Two repositories booted the disk of
`opencode-haiku`. `tools/haiku/cardless_run.py` defaults to a disk in `haiku-k40c-llm`.

## Decision

`tools/haiku/` owns the cross toolchain, the throw-away test VM, the persistent
cardless VM runner and the transfer server. VM disks live outside every repository,
in the folder that `HAIKU_VM_DIR` names. Other repositories pin this repository by
commit and file hash. They keep no copies.

The rule of `vm-test.sh` stays: no host device is ever given to a VM by these tools.

## Consequences

Phase 2 merges the two `app_vm.py` versions into `tools/haiku/` with all their options.
It keeps the atomic transfer server. It changes the default disk path of `cardless_run.py`
to `HAIKU_VM_DIR`. `docs/design/layout.md` states the target.
