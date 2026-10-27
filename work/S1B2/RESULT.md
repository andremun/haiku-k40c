# S1B2 result — 2026-10-27

DONE for native host/cardless scope. Batched macro review remains pending.

- Connected memory::Backend to native contiguous host allocation and aligned CPU/GPA views.
- Added k40_os_allocate_dma32 using Haiku's B_32_BIT_CONTIGUOUS contract.
- Kept GPA and device IOVA distinct. No native identity mapper is supplied.
- Mapping and visibility require an explicit verified provider. Default submission stays denied.
- NativePool preserves partial allocations, mappings, tokens, and quarantine across adapter recreation.
- Cleanup unmaps before freeing. Failed release blocks address queries and further use.
- Added host regressions for that partial-release hazard and native cleanup failures.
- Added the cardless C++ memory probe. No PCI or BAR access occurs in it.
- Cardless result parsing now rejects failure followed by a reload PASS.

Validation: make check and make vm-tools-test pass.
Memory adapter: 146 checks. Generic memory: 44. C backend: 78. All pass.
All three native probes link against the matching kernel.
The cardless memory probe passes both devfs loads in one 50.75-second run.
Evidence: results/20261027-b2-native-memory/. Command, hashes, launch and serial logs are saved.
The exported guest kernel matches the raw cross-link kernel byte for byte.
This is native OS evidence only, not GPU or DMA evidence.

Shared tools are re-pinned to owner commit 54db484 in haiku-k40c-llm.
Its make check passes. The generated pin includes the memory probe and build helper.

No physical card stage, root, host binding change, reset, or push ran.
A native IOVA/visibility provider, GPU-VA mappings, and physical VRAM allocation remain gated.
They need the later A4/C2 integration and separately approved hardware evidence.
The pool owner must remain loaded while any active or quarantined record exists.
Next: A4 pre-start state, then C2 choices, under ADR 007.
