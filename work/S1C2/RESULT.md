# S1C2 result — 2026-10-27

DONE for source-design scope; grouped review pending.

- Added docs/S1-INTEGRATION-CHOICES.md with selected callback/source anchors.
- Chose mode 17 and 4 KiB S1 mappings; preserved scratch allocation dependencies.
- Specified owned VRAM bootstrap, separate BAR contexts, and IOVA distinctions.
- Specified serialized PDB-specific invalidation and bounded status checks.
- Chose software-only group, channel-only runlist entry and channel-ID preempt.
- Required live TOP/PBDMA discovery; identified its write-stage boundary.
- Defined conservative stop/preempt/remove/idle/unbind/release obligations.
- Corrected old 2 ms timeout, GR-only scratch and GPA-as-DMA claims.
- Updated recipe, plan, licensing, current task, and host follow-up task text.

Validation: make check passes. Documentation task; no runtime code changed.
No VM/card stage, physical access, root, reset, binding change, or push ran.
All new hardware mechanics are SOURCE_ONLY, not physical verification.

Native DMA/visibility, VRAM ownership, transport and preflight closure,
readiness/fault coverage, GR omission, and teardown proof remain open.
No hardware write-stage package is ready for approval yet.
Next host task: S1A6 executor closure and bounded board transport.
