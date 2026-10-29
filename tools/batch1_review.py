#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind the first-batch plan/tasks to checked A7 evidence and current source inputs.

Reads local files/Git and runs only the offline A7 report check. Writes a planning
review JSON; --check compares exact text without writes, network, VM or hardware.
This binds the planning revision. Later implementation changes require a new
review record and are not validated by the old planning input hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work/S1BATCH1PLAN/review-inputs.json"
TASKS = (
    ("S1MEMCONTRACT", (), "Evidence and operation contract"),
    ("S1MEMARENA", ("S1MEMCONTRACT",), "Owned VRAM and address ledger"),
    ("S1MEMFAULTS", ("S1MEMCONTRACT",), "Scoped baselines and diagnostics"),
    ("S1MEMUPLOAD", ("S1MEMARENA", "S1MEMFAULTS"), "Physical VRAM upload/readback"),
    ("S1MEMMMU", ("S1MEMUPLOAD", "S1MEMFAULTS"), "BAR/MMU bootstrap and witness"),
    ("S1MEMPACKAGE", ("S1MEMMMU",), "Reviewed immutable experiment package"),
)
INPUTS = (
    "AGENTS.md",
    "REVIEW.md",
    "docs/S1-BATCH1-REVIEW.md",
    "docs/S1-PLAN.md",
    "docs/PHASES.md",
    "docs/OPEN_QUESTIONS.md",
    "docs/DMA-CONTRACT.md",
    "docs/MEMORY-CONTRACT.md",
    "docs/S1-INTEGRATION-CHOICES.md",
    "docs/S1-RECIPE.md",
    "docs/tasks/S1BATCH1PLAN.md",
    "docs/tasks/S1A7RUN7.md",
    "work/S1A7RUN7/RESULT.md",
    "work/S1A7RUN7/report.json",
    "results/20261029-a7-069cb71b/README.md",
    "work/S1A7BUFFER/package.json",
    "src/memory/Memory.h",
    "src/memory/ArmedReference.h",
    "src/os/HaikuMemory.h",
    "src/os/NativeOwner.h",
    "src/mmu/PageTable.h",
    "src/runtime/Bootstrap.h",
    "src/runtime/S1Experiment.h",
    "src/a7/ExecutionPermit.h",
    "src/a7/Owner.h",
    "tools/a7/result_report.py",
    "tools/batch1_review.py",
    "docs/decisions/005-single-branch-macro-reviews-passthrough.md",
    "docs/decisions/006-approval-after-launcher-stop.md",
    "docs/decisions/007-batch-sequential-host-tasks.md",
    "docs/decisions/008-s1-hardware-approval.md",
    "docs/decisions/009-allow-vfio-enable-line.md",
    "docs/decisions/010-a7-sensor-address-nack.md",
)


def revision(ref):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", ref + "^{commit}"], text=True
    ).strip()


def render():
    subprocess.run(
        [sys.executable, str(ROOT / "tools/a7/result_report.py"), "--check"],
        check=True,
        cwd=ROOT,
    )
    a7 = json.loads((ROOT / "work/S1A7RUN7/report.json").read_text())
    if a7["result"]["status"] != "pass" or a7["result"]["S1_complete"]:
        raise ValueError("unexpected A7 evidence scope")
    seen = set()
    tasks = []
    for task, dependencies, role in TASKS:
        if any(dependency not in seen for dependency in dependencies):
            raise ValueError("task dependency order")
        path = "docs/tasks/" + task + ".md"
        if not (ROOT / path).read_text().startswith("# " + task + ":"):
            raise ValueError("task header/path mismatch")
        tasks.append(
            dict(
                id=task,
                path=path,
                depends_on=list(dependencies),
                role=role,
                commit_policy="one task per commit",
                hardware_run=False,
            )
        )
        seen.add(task)
    names = sorted(set(INPUTS) | {task["path"] for task in tasks})
    return (
        json.dumps(
            dict(
                scope="HOST_ONLY planning/review preparation; batch not implemented or authorized",
                review_entry="docs/S1-BATCH1-REVIEW.md",
                separate_verdicts=["A7 result evidence", "First-batch design"],
                a7_result_commit=revision("dfb7cd8"),
                a7_implementation_commits=[
                    revision(ref) for ref in ("0b450b1", "210e5ee", "b0c24e4")
                ],
                a7=dict(
                    folder=a7["folder"],
                    scope=a7["scope"],
                    post_wall_us=a7["telemetry"]["post_wall_us"],
                    diagnostic_drain_us=a7["telemetry"]["diagnostic_drain_us"],
                    instruction_selection=a7["instruction_selection"],
                    flush=a7["flush"],
                    readiness=a7["readiness"],
                    kernel=a7["kernel"],
                    teardown=a7["teardown"],
                    approval=a7["approval"],
                    prior_approval_available=False,
                ),
                proposed_stage="S1_MEMORY_BOOTSTRAP (design label only)",
                planned_tasks=tasks,
                general_host_dma_visibility_verified=False,
                implementation_ready=False,
                hardware_authorized=False,
                s1_complete=False,
                future_run_gate="complete source gates, implementation review, exact package and explicit one-run yes",
                input_sha256={
                    name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in names
                },
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("first-batch review inputs differ")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
