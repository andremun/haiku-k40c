# S1A6 findings

- KNOWN from pinned init.c: POST starts fresh interpreter state for each main
  root, then the extra root. Condition and macro inputs use BIT I offsets 6/4.
- KNOWN from ramcfg.c and M0203.c: BIT M v2 can use first matching M0203 strap
  entry, then translation/identity fallback. Live strap selection remains UNKNOWN.
- Generated report: 530 potential starts, 25 opcodes, 438 register references.
  Input bounds and reviewed layouts pass. All 16 strap candidates map into 8 groups.
- The seventh reachable board instruction, GPIO at 0x89c2, remains denied if active.
  No condition-feasibility proof or full bring-up claim follows from structural coverage.
- SOURCE_ONLY: dedicated GF119 internal-bit candidate sends address, register,
  and data MSB first. ACK failures, I/O errors, stretch exhaustion, host deadline,
  rollback and stalled-clock callback budget fail closed. STOP preserves primary
  and cleanup errors. A failed transaction requires explicit host reinitialization.
- Internal Linux bit timing is CONFIG_NOUVEAU_I2C_INTERNAL-dependent. The capture
  configuration is UNKNOWN. No automatic retry or recovery pulses were added.
- Host wire tests decode transitions and inject each read/write/delay failure.
  908 UBSan checks pass. Closure mutation/check-mode suite: 10 tests pass.
- Native immutable input binding, physical transport/stage policy, persistent
  boot owner, verified DMA, owned VRAM and readiness remain gated.
- Full make check passes with zero failures; generated input audit and exact-ROM board exercise pass. Check log saved in check-final.log.
