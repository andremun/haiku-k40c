# Changelog

One line for each milestone, task group or layout change. The task log in
`docs/STATUS.md` and the commits hold the details.

- 2026-10-28: S1D0THREAD adds syscall-stop TGID and kernel FD-table proof to the private observer. Owned shared/private-table tests pass. D0 retry approval is limited to one run.
- 2026-10-28: Apply Claude's filtered R5 journal changes. The first physical D0 attempt stops on unproved task/FD sharing. Evidence is retained. No retry or DMA publication occurs.
- 2026-10-27: S1D0PACKAGE prepares a closed mapping observation stage with retained native memory, bounded tracing and fault monitoring. Host and cardless checks pass. Physical D0 awaits R5. S1 remains incomplete.
- 2026-10-27: S1B2 connects typed memory ownership to native Haiku DMA32 allocation. The cardless aligned readback and cleanup probe passes. Device IOVA publication remains denied without verification.
- 2026-10-27: S1BOARD adds the exact ADR 004 ROM policy and host-only board helpers. IO/CRTC accesses match the Linux capture. The hardware gate stays closed. ADRs 006 and 007 record retry approval and batched host work.
- 2026-10-27: ADR 005 records main-only work, macro reviews, and read-only Haiku passthrough. S1B5 adds the guarded launcher. The cardless rerun passes, and PMC_BOOT_0 is HARDWARE_VERIFIED under Haiku. No bring-up, DMA, or compute claim.
- 2026-10-24: Security fixes. Root scripts run only files equal to `origin/main`, run git as the user and write no repository file as root (`scripts/root-guard.sh`); `GPU_BDF` is checked. `transfer_server.py`: write-once job logs, an upload budget, `--port 0 --port-file`; `vm-test.sh` and `setup.sh` use it instead of servers on fixed ports. Monitor sockets of `app_vm.py` and `cardless_run.py` moved from `/tmp` to the VM or run folder. Edits to `scripts/` and `tools/guest/` ask first.
- 2026-10-23: Review rules: `REVIEW.md`, the `/pr-review` skill (`.claude/skills/pr-review/`) and a "Review guidelines" section in `AGENTS.md` for Codex. Q1 closed and assumption S1 updated after ADR 003. Questions Q2 to Q5 from `haiku-k40c-llm`.
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
