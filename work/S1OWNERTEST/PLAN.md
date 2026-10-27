# S1OWNERTEST plan

1. Confirm user-nonpackaged module lookup and empty-device legacy unload paths.
2. Build a GPU-free client probe with explicit init/uninit markers. First load
   exercises host bytes/default-denied publication, consumes the software latch,
   then detaches into quarantine. A later load must observe that same owner state.
3. Add fixed owner/client staging to the cardless runner without changing QEMU
   options. Bind both binary hashes and validate ordered reload evidence.
4. Host-test staging and failure/result parsing. Build/link both native components.
5. Commit prepared host work after make check. Check running guests, then run one
   disposable cardless test. Preserve a reported stop and ask before another run.
6. Archive bounded evidence, re-pin shared tools and complete the handoff/checks.
