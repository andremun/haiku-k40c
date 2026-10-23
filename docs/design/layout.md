# Layout and code rules

This file states what the repository must look like after Phase 2 of the alignment
plan (`haiku-k40c-llm/docs/refactor-spec.md`). The task system, the evidence labels
and the generated-file `--check` options stay as they are. They are the model for
the other three repositories.

## 1. What changes

| Area | Today | Target |
|---|---|---|
| VM tools | `tools/haiku/` here, two `app_vm.py` copies and two transfer servers in other repositories | `tools/haiku/` holds all of them (ADR 001): `setup.sh`, `vm-test.sh`, `cardless_run.py`, `app_vm.py` (merged, with `--kvm` and `--memory-mib`), `transfer_server.py` (atomic writes, `job*` uploads to `logs/`) |
| VM disks | `opencode-haiku/vm/`, `haiku-k40c-llm/vm/` | `HAIKU_VM_DIR` (default `~/haiku-vm`), outside every repository |
| `cardless_run.py` default disk | `../haiku-k40c-llm/vm/system.qcow2` | `$HAIKU_VM_DIR/system.qcow2` |
| Reference sources | symbolic links into `~/llm-server/agent-refs/` | `K40_REFS` setting, filled by `tools/restore_verification_refs.py` (ADR 002) |
| `opencode.json` | absolute paths to `/home/unimelb.edu.au/...` | `~`-relative paths if OpenCode accepts them. Otherwise one documented machine path. |
| Python headers | 16 of 38 files have the MIT header | all authored files |
| Python text | 30 of 38 files have non-ASCII bytes | ASCII only (replace em dashes and arrows in comments) |
| CI | none | `.github/workflows/check.yml`: `make check` after the reference restore, Ubuntu, no GPU, no VM |

## 2. What does not change

- `tools/check_repo.py` stays hidden from the agent and keeps its role (ADR 003 keeps this for Claude Code and Codex).
- File names that generators or checks use: `docs/04-*.md` to `docs/08-*.md`, `docs/tasks/`, `work/`, `analysis/`, `hardware/`, `registers/`, `firmware/`.
- `reference/` content and the captures in `reference/linux-run*/` and `reference/pci/`.
- The hardware safety rules in `AGENTS.md`.

## 3. Documentation targets

- `docs/HAIKU_BUILD_TEST.md` gains a section "Persistent cardless VM" when the merged `app_vm.py` arrives. It replaces the description in `docs/history/20261015-haiku-vm-handoff.md`.
- `docs/HAIKU_ENVIRONMENT.md` stays the install record of the toolchain.

## 4. Acceptance checks

1. `make check` shows the same result set as before Phase 2 on the same machine. In the cloud session of 23 October 2026 it had 273 failures. Absent reference trees caused them.
2. `make check` passes on the T7610 with the restored references.
3. `make haiku-selftest` prints `MMIO read16 [BAR2+0x500] = 0xb0c5`.
4. `cardless_run.py --kvm` gives `k40_os: PASS` with a disk in `HAIKU_PERSISTENT_VM_DIR` (user step).
5. `git grep -l '/home/unimelb.edu.au'` lists only `docs/history/`, `work/` evidence and provenance JSON.

## 5. As built (23 October 2026)

| Item | Result |
|---|---|
| VM tools | Done. `tools/haiku/app_vm.py`, `transfer_server.py` and `job.sh` merged from the other repositories. `tests/test_vm_tools.py` (19 checks) covers upload routing, name and size checks, atomic writes, job status handling and the monitor allowlist. One change: `app_vm.py` checks the ISO only for a first install, because an installed VM does not need it. |
| VM disk variable | `HAIKU_PERSISTENT_VM_DIR` (default `~/haiku-vm`), not `HAIKU_VM_DIR`. `tools/haiku/config.sh` already uses `HAIKU_VM_DIR` for the throw-away test VM. |
| `cardless_run.py` default disk | `$HAIKU_PERSISTENT_VM_DIR/system.qcow2` |
| Reference sources | Done. `reference/*` link into `.refs/`. `make refs` creates `.refs` and fetches the pins. In the cloud session of 23 October 2026 four of five sources restored. Mesa failed: the session proxy blocks `gitlab.freedesktop.org`. |
| Python text | Comments and docstrings are ASCII. Eight generator tools keep non-ASCII characters in output string literals (dashes and arrows), so that the generated files stay the same. |
| Headers | Added to every authored Python and shell file that had none. |
| Defect | `tools/check_repo.py` had an invalid escape sequence in an f-string (`SyntaxWarning`, an error in later Python versions). Fixed. |
| CI | `.github/workflows/check.yml`: `make refs`, `make check` with task A3 skipped and `K40_CI_NO_VBIOS=1` (the VBIOS image is private: `tests/test_devinit_rom.py` reports NOT RUN in CI, and still fails locally when the image is missing), `make vm-tools-test`. |
| `make check` | Same failure set as before the code changes, with the restored sources: 18 failures. Each comes from the absent Mesa tree or the private VBIOS image. |
| `opencode.json` paths | Superseded: ADR 003 removed `opencode.json`. |
| Design document renames | Not done. They gain little, and generators and checks use the names. |

