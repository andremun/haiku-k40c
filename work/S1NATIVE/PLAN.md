# S1NATIVE plan

1. Follow pinned Haiku module reference counting, KEEP_LOADED, uninitialization,
   and legacy driver reload behavior. Distinguish resident image from initialized state.
2. Select a separate permanent owner module for startup state and NativePool.
   Keep provider implementations and all referenced data in that owner.
3. Implement only a source-supported host/native owner contract and failure tests.
4. Inspect fixed guest configuration and specify missing DMA/visibility proof.
   Do not turn GPA into a verified IOVA without evidence.
5. Cross-compile/link native changes with the matching kernel. No VM or card run.
6. Update documentation, source licensing/provenance, status and result.
   Run make check before each commit; re-pin shared tools only if changed.
