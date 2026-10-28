# Findings

## Initial prerequisite audit (superseded by the resolution below)

- D0 passed structurally and its guest ended. It does not supply a current A7
  mapping grant, provider publication or physical payload/coherency proof.
- KNOWN / SOURCE_ONLY: GK110 selects the GF100 flush-target hook. FB preinit
  writes the target before nvkm_devinit_post. The source chain is in ESC-002.
  Writing the target is not itself proof that device DMA starts before POST.
- The current host candidate requires a verified address and published buffer
  before preinit. The permanent native owner deliberately installs no provider.
  Thus wiring the physical backend to the current controller would fail closed.
- The requested POST-before-D1 order needs a decision on separating an arm-only
  experimental reference from production DMA publication. I did not replace the
  missing provider with GPA-as-IOVA or a caller-supplied Boolean.
- ESC-002 records the precise software-contract conflict and candidate separation.
  Native binding and the executable A7 package are incomplete. Hardware gates,
  one-shot state and quarantine are unchanged. No write-stage approval was asked.

## Resumed implementation after Claude resolution

- ESC-002 is RESOLVED by the supplied review recorded in CLAUDE-ESC002-REVIEW.md.
  Arm-only references precede POST, with a register readback and second arming
  write afterwards. D1 and Q7 remain separate. No physical A7 run is approved.
- ArmedReference has no payload read/write/publish/free API. Storage is zeroed
  before exposure and retained immediately, including partial failure. It does
  not set the normal allocation's verified, published or visible fields.
- PreStart now uses that type and mirrors both target writes. Its host suite
  passes 166 checks, including a changed post-POST readback and per-step failures.
- Physical helpers use an owner-minted ExecutionPermit, never hostSimulation.
  The resident A7 module alone will hold the permit, platform, image and latch.
  Mixed simulation/physical transport pairs are denied.
- The fresh witness bridge uses a single-use host-generated Ed25519 package key.
  The guest gets only the public key. A fixed frame binds package nonce, owner
  challenge, exact token/GPA/extent/IOVA and the live proof digest. The native
  authority verifies the signature before arming. This is not a DMA provider.
- Verification-only orlp/ed25519 sources are pinned outside reference/. They carry
  the zlib license. No signing/seed/key-exchange code is linked into the kernel.
  The wrapper rejects noncanonical signature scalars. Host OpenSSL creates keys.
- Haiku's exported secure_random_value supplies an owner-instance challenge.
  Its clock/counter-based implementation is not claimed as cryptographic entropy.
  Host package keys are fresh and a host-side consumed marker prevents a second
  launch using the same package. The fixed guest job never reboots the guest.
- A stage-only device stream lets the shell hold one descriptor during the
  witness handshake. It transfers fixed-size query/grant frames, not arbitrary
  addresses or callbacks. Owner state survives driver reload and rejects repeats.
- New source audit for readiness follows GF108/GF100 memory probing selected by
  GK104 RAM, and the NV04 timer read hook selected by NV41. The Linux capture
  reports 11520 MiB physical FB memory, distinct from nvidia-smi's usable total.
- The scratch reservation uses the first source-derived normal-heap page after
  the 256 KiB VGA head, rejects mixed memory, and excludes the 1 MiB VBIOS tail.
  PRAMIN selector is zero for that page, with data window offset 0x40000. This
  is a standalone exclusive-owner experiment, not a production VRAM allocator.
- No VFIO reset at guest end is assumed. A7 must document a reviewed host VFIO
  teardown and verify stopped process/bus-master disable without a manual reset.
  Incorrect but mapped IOVAs can corrupt guest RAM. IOMMU faults alone are not
  an unconditional safety guarantee. The native code checks the exact full extent.

## Host validation and package

- Actual NativePlatform/NativeStorage tests pass 4129 assertions with injected OS
  APIs. PCI reservation precedes mapping; duplicates and failed reservations deny
  access; writes without the owner permit fail. Zero/alignment and partial native
  allocation retention pass. No native free/recovery call is made.
- Actual stream-client tests pass 22 assertions: partial frames, bad user copies,
  exact length, one submission, detach and rejected reload.
- Owner/authority UBSan fixtures cover 32 ROM/strap cases (16 complete), all 192
  single-byte mutations, seven signed scope errors, noncanonical S, I2C failure
  and non-advancing GPU timer. They use only a public RFC test key.
- Eight launcher tests cover fresh structural coverage, late close/partial
  record/identity/kernel/role/R5 stops, private-key route refusal, write-once HTTP
  evidence and read-only PCI teardown checks. No fixture starts a VM or accesses
  a device. Full host tests need local-socket permission outside the sandbox.
- Both A7 native artifacts cross-link against the matching kernel. No A7 module
  load, GPU write or new guest has occurred. Package --check passes. The complete
  possible script register-write inventory has 544 rows, plus driver writes.
- KNOWN current host-only observation: development PCI command was 0x0002 when
  inspected after the ended D0 guest. This is not A7 teardown evidence. Upstream
  v6.8 VFIO close clears mastering before cleanup; exact Ubuntu -138 source was
  not retrieved. Proposed end boundary: owned QEMU/tracer exit plus observed
  master disable. Review this explicitly; no reset at guest end is assumed.
- A7 uses the stricter R5 rule: every new selected-class line stops, including
  informational VFIO/DMAR or corrected AER. The native latch is one-shot, and the
  host package consumed marker prevents another launch. ADR 006 still requires
  reporting and permission after any launcher stop.
- The first full check found 21 new constant lines without recognized provenance
  annotations and a stale generated table. Added pinned citations for hardware
  facts and explicit software/RFC/capture annotations for wire/crypto/comparison
  constants, then regenerated provenance. Reviewer check code was not changed.
- Source-bound POST, owner-POST and DMA reports were regenerated after shared
  headers changed. Historical D0 binaries and cutoff evidence were not rebound
  to new sources and no D0 guest was rerun.
- The final generator chain also found a stale S1BOARD trace-check source binding.
  Regeneration changes only four source hashes. The same 20 captured accesses
  still match, with the same two skipped IO waits. Its failed check log is kept
  in make-check-board-report.log. No historical physical capture was modified.
- The silent remaining generator failure was the S1POST input-closure report's
  source binding. Regeneration preserves 530 starts, zero unresolved inputs and
  production_eligible=false. Every generator now passes individually with failure
  propagation enabled. The full host suite also passes (tests-final.log). The
  combined final make check is rerun after these corrections. No reviewer check
  or accepted physical evidence was changed.
- The teardown source generator now compares the entire generated record under
  --check, not only its source hashes. Its added host fixture rejects changed
  metadata and proves the check does not write or fetch data. Eight launcher
  and package-boundary tests pass in total.

- Final combined make check PASSES, including the repository checker (zero
  failures), all source/generator checks and the complete host suite. The A7
  package, host-check and external-source --check commands also pass. Both native
  links pass. No guest was launched and the package consumed marker is absent.
