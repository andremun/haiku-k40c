# Changelog

One line for each milestone, task group or layout change. The task log in
`docs/STATUS.md` and the commits hold the details.

- 2026-10-23: Local agent experiment closed (ADR 003). Task work with Claude Code and Codex. `opencode.json` and `.opencode/` replaced by `CLAUDE.md`, `.claude/` and `docs/AGENT-SETUP.md`. Driver card 0000:04:00.0, `llm-server` on 0000:03:00.0.
- 2026-10-23: Repository alignment, phase 2 (code). Shared VM tools merged into `tools/haiku/` with a test. Reference links point into `.refs/` (`make refs`). ASCII comments and headers. Escape-sequence fix in `tools/check_repo.py`. CI workflow.
- 2026-10-23: Repository alignment, phase 1 (documentation). Dated handoffs and old status text moved to `docs/history/`. ESC-001 evidence copied in from `opencode-haiku` (`results/20261018-esc001-native-load/`). ADRs 001 and 002. Phase 2 blueprint `docs/design/layout.md`.
- 2026-10-21: Scaffold review against Nouveau v6.12 and the trace (findings F1 to F14). Tasks S1A and S1B.
- 2026-10-20: ESC-001 resolved: native link and load pass on a cardless KVM guest.
- 2026-10-16: Cardless S1 tracks (V1, V2, ABC1): ROM executor, typed memory boundary, native backend, bootstrap checks. Independent A3 rework.
- 2026-10-14: Task R1: seven defects of the external review fixed.
- 2026-10-13: Phases C and D closed (C5c, D6). Gate review package. External reviews and research received. S1 plan.
- 2026-10-11 to 2026-10-12: Phases B, C and D tasks (register database, firmware manifest, subsystem models, page tables, push buffer, launch descriptor).
- 2026-10-05 to 2026-10-08: Phase A (hardware record, root captures) and phase B start.
