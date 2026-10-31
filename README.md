# haiku-k40c

Native Haiku compute driver for the NVIDIA Tesla K40c (GK110B). Design:
`docs/design/design.md`. Specification: `docs/design/specification.md`.
License: MIT (`LICENSE`, `docs/licensing.md`). Changes: `CHANGELOG.md`.

## Disclaimer

This is research code. It is not production code.

I made it as part of a project that tests the Tesla K40c hardware under Haiku. I like
unusual operating systems, and Haiku is an interesting one. That is the main reason this
project exists.

The code is not meant for inclusion in Haiku, HaikuPorts or any other Haiku project.
AI coding agents generated most of it ("vibe coding"). I publish the code, the tools
and the records so that others can use what the project found: people who port GPU
drivers to Haiku or another system, or who study NVIDIA Kepler hardware.

Use it at your own risk. The license gives no warranty.

## Purpose

A Haiku kernel driver that runs one verified compute job on a Tesla K40c, built from a
study of the open-source Nouveau driver. It is a hobby project. It is not production
software and it may never reach the goal.

## State

The project is on hold since 2026-10-31 (`docs/decisions/011-project-on-hold.md`).

Milestone S1 passed on the card. A native Haiku driver ran the card's start-up script
(POST), reached VRAM through its own BAR1 page tables, and one channel on the copy-engine
runlist consumed one host command: no fault, clean teardown
(`results/20261031-batch1-a7-bar1-d198d424/`). The copy job (S2) and the compute job (S3)
are not done. `docs/STATUS.md` has the details and the task log.

## Tools that others can use

The tools work on the pinned Nouveau, Mesa and envytools trees (`reference/MANIFEST.md`)
and on a Linux reference run of a compute job on this card. Most of them are not specific
to Haiku. They can help a port of Nouveau, or of one Nouveau path, to another kernel.

| Need | Tools and data | Why it helps |
|---|---|---|
| Know what Linux really does | `reference/linux-run-debug/`: mmiotrace and debug log of a Nouveau compute run on this card (Linux 6.8). `tools/trace_summary.py`, `tools/trace_lines.py` (a named range of the trace), `tools/load_trace.py`, `tools/compare_register_traces.py` | The trace is the oracle. A port can compare its own write sequence with the full Linux sequence. The S1 stall came from one write that only the full trace showed. |
| Find the code a port needs | `tools/nouveau_files.py`, `tools/callgraph.py`, `tools/min_chain.py`, `tools/extract_mmio.py`, `tools/linux_deps.py` | They list the Nouveau files of one chipset, the call graph from its constructors, the smallest chain to one compute job, its register accesses, and the Linux kernel symbols that a port must replace. |
| Name registers | `tools/rnndb.py`, `tools/build_regdb.py`, `tools/hwmodel.py`, `hardware/registers/*.yaml` | Register names and fields from envytools, and a register model per subsystem, with sources. |
| Run the start-up script | `tools/build_nvbios.py`, `tools/devinit_inventory.py`, `tools/devinit_closure.py`, `tools/post_policy.py`, `tools/board_trace.py`; `src/devinit/` | An offline inventory of the VBIOS start-up script, and a bounded interpreter with an allow-list for the board operations. |
| Launch compute | `tools/compute_launch.py`, `tools/shader_extract.py`, `tools/qmd_compare.py`, `firmware/compute_add1.bin` | The compute path of Mesa's Nouveau driver, the shader and launch descriptor of the reference run, and a comparison of our descriptor with it. |
| Keep constants honest | `tools/provenance.py`, the citation rule of `make check` | Each hardware constant in `src/` cites a pinned source line or says that it has none (`docs/register-provenance.md`). |
| Develop on Haiku | `tools/haiku/` (cross toolchain, test VM, cardless runs, VFIO card runs), `scripts/passthrough.sh` | Build a Haiku driver on Linux and test it in a VM, with or without the card. |
| Run hardware stages safely | `tools/a7/`, `tools/memstage/` | Single-use run packages with hashes and grants, cardless rehearsal, host checks, and validators that re-derive a run from its log. |
| Reuse the driver code | `src/` (about 7,600 lines; `src/os/`, `src/memnative/` and `src/a7/NativePlatform.cpp` hold the Haiku part) and `tests/` | The register, MMU, BAR1, channel and push-buffer code is separate from the Haiku layer. Host tests run it against simulated devices built from trace values. |

## Why a native driver

There are two ways to get a GPU driver on Haiku. A compatibility layer runs the Linux
driver code on shims of the Linux kernel interfaces, as FreeBSD does with LinuxKPI for its
DRM drivers. A native driver implements only what the job needs, with Haiku's own
interfaces. For the K40c the Linux route means Nouveau: the NVIDIA open kernel modules
support only Turing and later GPUs.

A native driver has these advantages:

- **It is small enough to check.** The S1 path is about 7,600 lines, not the Nouveau
  and DRM stack. Each register write has a cited source, and a review can read all of it.
- **It controls every write.** A resident policy allows only the planned writes, in
  order. Teardown runs after any failure. A large driver behind a shim is much harder
  to bound like this.
- **It uses Haiku's model directly.** Kernel add-ons, areas and the device manager are
  used as they are. A shim must imitate Linux behaviour (memory management, workqueues,
  the DMA interface, firmware loading), and faults in the imitation are hard to find.
- **It does not follow Linux internals.** The Linux kernel has no stable internal
  interface. A compatibility layer must change when Linux changes.
- **It documents the hardware.** Each step is written down with its source and its
  evidence label, which helps the next port.

The disadvantages are also real. A native driver gives only the path that was written:
no display, no power management, no other GPU family. Each new feature costs a new study.
A compatibility layer gives the whole feature set of the Linux driver at once, and
user-space stacks such as Mesa expect the Linux DRM interfaces. For broad hardware
support a compatibility layer is the better route. For one narrow compute path that
must be checked on old hardware, a native driver is easier to make correct.

Until 23 October 2026 the repository was also a test of a local LLM coding agent. That
experiment is closed (`docs/decisions/003-end-local-agent-experiment.md`). Its record is
in `work/`, the task log of `docs/STATUS.md` and
`docs/history/20261023-local-agent-experiment.md`.

| Part | Written by | Trust |
|---|---|---|
| `AGENTS.md`, `docs/PHASES.md`, `docs/design/`, `.claude/`, `tools/check_repo.py`, `tools/haiku/`, `scripts/`, `reference/pci/` | The user, with Claude (Anthropic) as assistant | Reviewed |
| Task outputs to 2026-10-23: `hardware/`, `analysis/`, `registers/`, `firmware/`, `work/` | The local agent. Commits start with the task ID (`A1: ...`). | As labelled. A claim is KNOWN, INFERRED or UNKNOWN, and a register is SOURCE_ONLY until it is verified. `make check` verifies format and some facts, not completeness. |
| Task outputs from 2026-10-23, later the driver source | Claude Code or Codex, with cloud models. Same commit and evidence rules. | As above |
| `docs/STATUS.md`, `docs/OPEN_QUESTIONS.md` | Both | Check against the task log and the reviews |

Agent output can contain confident errors, including citations of files
that do not exist. Do not use a register value or a command sequence from
this repository on real hardware without checking its source.

## Cards

| Card | Use |
|---|---|
| K40c 0000:04:00.0 | The driver: captures, passthrough (`docs/PASSTHROUGH.md`), hardware tests. During the hold it returns to `llm-server` (decision 011). |
| K40c 0000:03:00.0 | `llm-server` in mode `one`, for `optima-agent-bench`. Not for driver work. |

## Working with Claude Code or Codex

Run `claude` or `codex` in this directory. Both read `AGENTS.md` (Claude Code through
`CLAUDE.md`). Setup and permissions: `docs/AGENT-SETUP.md`.

Start a new session for each task. The repository is the memory:
`docs/STATUS.md`, `docs/tasks/<task>.md`, `work/<task>/`. The task steps are in
`AGENTS.md` ("Session protocol"). Claude Code also has them as skills: `/next`,
`/handoff`, `/escalate` and `/review`. Review a branch or pull request with
`/pr-review` ([REVIEW.md](REVIEW.md)).

## Layout

| Path | Content |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Rules for coding agents (safety, evidence, protocol). `CLAUDE.md` points to `AGENTS.md`. |
| `.claude/` | Claude Code permissions and skills: task steps and `/pr-review`. |
| `REVIEW.md` | What a review reports and how severe it is. |
| `docs/` | Status, phases, open questions, requests, design documents. |
| `reference/` | Pinned read-only sources (`MANIFEST.md`) and PCI captures. |
| `tools/` | Analysis scripts and `check_repo.py`. |
| `tools/haiku/` | Cross-compile a Haiku driver on Linux and load it in a test VM (`docs/HAIKU_BUILD_TEST.md`). `setup.sh` builds the toolchain and VM in `~/haiku-cross`. |
| `hardware/`, `analysis/`, `registers/`, `firmware/` | Task outputs. |
| `work/` | Per-task plans, findings and results. |
| `escalations/` | Problems that need a decision. |
| `results/` | Evidence that is not a task output, with an index (`results/README.md`). |
| `docs/history/` | Dated handoffs and old status text. Read-only. Not for task work. |
| `docs/decisions/` | Architecture decision records. |
| `docs/design/layout.md` | Target layout for the next cleanup phase. |
| `scripts/capture_user.sh`, `scripts/capture_root.sh` | Read-only PCI captures: without root, and for the user to run with sudo. Run both after a hardware change, then `tools/hardware_record.py`. |

## Haiku B5 identity launcher

`tools/haiku/card_run.py` runs the read-only identity stage authorized by ADR 005.
It accepts only the development card, a B5-tagged probe, and a disposable VM overlay.
See [the build and test guide](docs/HAIKU_BUILD_TEST.md#b5-identity-stage-with-the-development-card)
for checks, commands, evidence files, and the ten-minute limit.
Run `make vm-tools-test` for host-only launcher tests.
