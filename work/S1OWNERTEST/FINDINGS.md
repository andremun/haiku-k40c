# S1OWNERTEST findings

- KNOWN/SOURCE_ONLY: module lookup searches user-nonpackaged add-ons and resolves
  generic/k40c_owner/v1 to the generic/k40c_owner image. Legacy lookup also searches
  user add-ons. An empty-node driver with zero users unloads after publication.
- The guest job resolves its user add-on path with finddir. No privileged install
  or base-disk modification is needed; owner precedes client staging.
- Native probe performs host pattern readback and clean release, then consumes
  only the software latch and retains one host allocation. Later init/uninit
  cycles must observe the same token and failed/quarantined owner state.
- Host probe lifecycle: 13 checks pass. Runner staging/parser suite: 4 tests pass,
  including wrong tokens, lost state, missing unload, malformed events, ELF roles.
- Both native components link against the matching kernel. No guest has run yet.
- Fixed QEMU arguments are unchanged. Owner mode records both ELF hashes and
  source commit, checks uploaded kernel hash, and refuses generic PASS evidence.
- Native reload, module residency, and actual retention remain UNKNOWN until run.
- Prepared full make check passes with zero failures. No guest run yet; commit this snapshot before launch.

- First prepared cardless run PASSES in 52.57 seconds. Source 45923d6.
  Evidence: results/20261027-owner-reload/. No retry occurred.
- Native phase1 init/uninit: lease 1, token 2. The reload uses lease 2 and the
  same token, Failed state, owned=1/quarantine=1, followed by phase2 uninit/PASS.
- Owner/client hashes match staged artifacts; uploaded kernel hash matches the
  expected link kernel. QEMU exited through normal runner cleanup.
- Application shared tools re-pinned to 45923d6 in commit 0d59079. Its offline/host
  checks pass outside the sandbox. A first sandboxed server check did not start;
  this was a host CPU test, not another VM run or a launcher stop.
- This is native OS lifetime evidence, not DMA or K40c evidence. Failed OS release
  paths and physical references were not exercised by this successful cardless run.
- Final make check passes with zero failures. Both source and application working changes are ready for the final handoff; no second guest was started.
