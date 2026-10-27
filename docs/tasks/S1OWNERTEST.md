# Macro task S1OWNERTEST: cardless owner load and reload evidence

## Why

S1NATIVE implements a separate KEEP_LOADED owner and client API. Source checks,
host tests and native linking do not prove module load or driver reload lifetime.
Validate the owner in the cardless Haiku guest before any hardware integration.

## Inputs

Read docs/STATUS.md, docs/HAIKU_BUILD_TEST.md, docs/NATIVE-OWNER.md,
work/S1NATIVE/RESULT.md and the guarded cardless runner/job protocol.
Use src/os/{HaikuOwnerModule,OwnerClient,NativeOwner}.*, runtime/BootState.h,
and the pinned Haiku module/legacy-driver lifecycle ranges cited in the owner doc.

## Outputs

- A GPU-free native client probe that verifies allocation/readback, denied
  publication, cleanup and one-shot/quarantine state across actual client unloads.
- Minimal cardless staging support for the owner module and client, with fixed
  destinations, evidence hashes, host tests and no extra QEMU options.
- Verify user-writable module lookup/staging from pinned source first. Do not
  install through root or change the base disk; use a disposable overlay.
- Build/link both components against the matching kernel. Run one prepared
  cardless test, with explicit evidence of init/uninit and retained owner state.
- Update shared-tool pin if shared files change, documentation, licensing,
  provenance, status and work/S1OWNERTEST/{PLAN,FINDINGS,RESULT}.md.
  Run make check before commit.

## Limits

No physical card, PCI/BAR, root, host binding, reset or push. The owner remains
DMA-denied; startup markers are software test state, not bring-up.
Ask before stopping any running VM. After any launcher-reported stop, preserve
evidence and ask before another run under ADR 006. Host diagnosis may continue.
A missing reload or incomplete lifetime observation cannot be called a pass.
