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
