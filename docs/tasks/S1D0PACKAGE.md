# Macro task S1D0PACKAGE: concrete read-only mapping observation package

## Why

The typed model and source-checked userspace decoder now exist. Build the closed
D0 package before a physical run. D0 must verify actual map coverage while native
storage remains owned; it does not enable DMA publication or prove visibility.

## Inputs

Read docs/STATUS.md, docs/DMA-CONTRACT.md (D0), docs/D0-OBSERVER.md,
work/S1D0OBSERVER/RESULT.md, ADR 005/006/008 and docs/HAIKU_BUILD_TEST.md.
Use the reviewed card/cardless launchers, guest lock/watchdog, transfer helpers,
NativeOwner/OwnerClient and existing identity probe. Read only their relevant files.

## Outputs

- Plan the stage's exact native and host effects, source/hash binding and limits.
- Build a memory-only native owner client with a unique D0 role tag. It allocates,
  checks CPU bytes, reports its complete logical GPA/extent/token and retains the
  whole native backing in the permanent owner through the host evidence cutoff.
  No guessed IOVA, publication, PCI writes or GPU MMIO writes.
- Use the existing exact identity-only probe if GPU identity is required. Preserve
  B5 and vm-test.sh unchanged. Create a separate closed launcher/stage validator.
- Bind actual group/device/container association and realized DMA address space.
  Capture complete successful setup/maps/removal with the exact pinned observer.
  Reject unproved multi-thread FD histories, unknown operations and truncation.
  Define a live guest/host cutoff handshake before releasing storage/terminating.
- Preserve all VFIO/card safety checks twice. Observer supervision must target
  the actual QEMU child, not leave it running if strace dies. Use an independent
  600 s watchdog, one guest, disposable overlay and incremental write-once evidence.
  Keep all supervisor/control options fixed. No arbitrary subprocess/QEMU arguments.
- Check availability of required fault baselines without root. Record exact
  necessary user read-only commands in docs/REQUESTS.md if access is unavailable.
  Do not silently proceed without a required baseline or clear faults.
- Run host fault tests and compile/link probes against matching kernel. Recheck
  enlarged owner/client lifetime in one prepared cardless run if useful. After any
  launcher-reported stop follow ADR 006 and ask before another run.
- Write a concrete stage review/risk document with exact command, hashes, evidence
  parser criteria and remaining limits. No physical D0 run in this package task.
- Update licensing/status/work records, regenerate affected reports and app tool
  pin if required, run make check, commit. Next task runs the checked D0 package
  only once prerequisites and required review close. ADR 008 supplies approval.

## Limits

No physical card/PCI/BAR operation, root, binding, reset or push in this task.
A prepared cardless check is allowed. No native provider, physical write or inferred
visibility. Do not bypass review, fault-baseline or ADR 006 stop gates.
