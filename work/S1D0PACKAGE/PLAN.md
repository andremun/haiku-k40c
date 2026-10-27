# S1D0PACKAGE plan

1. Implement a memory-only D0 owner client: bounded CPU pattern, GPA/extent/token,
   then consume the resident latch and retain its entire native backing. Never
   publish an IOVA, touch PCI or write GPU registers. Keep the identity probe separate.
2. Extend the original observer decoder only for group/container/device association,
   with owned /dev/null tests and new binary/source metadata. Preserve archived
   S1D0OBSERVER traces. Prove fixed -D supervision with harmless owned children.
3. Build a separate closed D0 launcher and role validator. Reuse reviewed safety
   checks, lock, exact identity role and transfer concepts without changing B5 or
   cardless QEMU commands. Bind actual QEMU/tracer PIDs and fixed image/source hashes.
4. Hold native storage across a live host cutoff; match group/device/container,
   realized DMA address space and full successful maps. Preserve fault baselines.
   Do not enable native DMA publication or claim payload/coherency proof.
5. Test supervisor loss, deadlines, parser gaps, identity/extent mismatches and
   role confusion. Link native units and prepare one cardless owner lifetime check.
6. Write exact stage review/effects/commands, run make check and commit package.
   Physical D0 execution is a later task. ADR 008 provides hardware approval but
   missing baseline, implementation/review or ADR 006 stop gates still apply.

Initial checks: no QEMU guest running. The account cannot read the system kernel
journal. R5 requests a read-only human-started log stream. Work continues on code
and cardless preparation; no physical run until monitoring is available.
