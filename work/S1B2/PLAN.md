# S1B2 native memory adapter plan

1. Connect the memory ownership interface to the native Haiku allocator.
2. Use B_32_BIT_CONTIGUOUS for prospective DMA storage, based on Haiku's nvidia driver.
3. Keep GPA, CPU view, verified IOVA, and GPU VA distinct. Supply no implicit GPA-to-IOVA conversion.
4. Inject mapping and visibility operations. Default publication and submission stay closed.
5. Track partial allocations, unmap-before-free order, failed release, and quarantine without losing ownership.
6. Add host fault-injection tests and compile/link a cardless native memory probe.
7. Run make check, preserve the native cardless result if run, and re-pin shared tools after a tool change.
8. Continue with A4 pre-start research and C2 choices under ADR 007. No GPU write stage.
