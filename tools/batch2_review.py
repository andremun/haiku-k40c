#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind the second-batch design to pinned sources and verified batch-1 evidence.

Generate review-inputs.json. With --check, compare without writing. This is an
offline planning check. It never builds a package, signs a grant or starts a VM.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work/S1BATCH2PLAN/review-inputs.json"
TASKS = (
    ("S1CHANCONTRACT", (), "Channel evidence and operation contract"),
    ("S1CHANMEM", ("S1CHANCONTRACT",), "Owned channel images and USERD mapping"),
    ("S1CHANSCHED", ("S1CHANMEM",), "Polling-only scheduler and routing"),
    ("S1CHANCLOSE", ("S1CHANSCHED",), "Finite detach and guest-end retention"),
    ("S1CHANSUBMIT", ("S1CHANCLOSE",), "Single host-NOP composition"),
    ("S1CHANPACKAGE", ("S1CHANSUBMIT",), "Immutable package and cardless rehearsal"),
)
NOUVEAU = "reference/nouveau/"
FIFO = NOUVEAU + "nvkm/engine/fifo/"
MMU = NOUVEAU + "nvkm/subdev/mmu/"
# Each span is checked against a literal source anchor, then hashed in full.
SPANS = (
    (
        "chip_dispatch",
        NOUVEAU + "nvkm/engine/device/base.c",
        1777,
        1805,
        "gk110_fifo_new",
    ),
    ("channel_controls", FIFO + "gk104.c", 40, 79, "0x800000"),
    ("ramfc_userd", FIFO + "gk104.c", 82, 118, "0x0000face"),
    ("channel_selection", FIFO + "gk110.c", 35, 58, "gf100_chan_preempt"),
    ("fifo_dispatch", FIFO + "gk110.c", 107, 128, "KEPLER_CHANNEL_GPFIFO_B"),
    ("userd_allocation", FIFO + "base.c", 306, 320, "fifo->chid->nr"),
    ("fifo_init_order", FIFO + "base.c", 138, 160, "init_pbdmas"),
    ("userd_clear_instance", FIFO + "gf100.c", 118, 145, "0x088"),
    ("channel_count", FIFO + "gk104.c", 801, 805, "4096"),
    ("pbdma_discovery", FIFO + "gf100.c", 927, 936, "0x000204"),
    ("routing", FIFO + "gk104.c", 756, 800, "gk104_runq_runm"),
    ("pbdma_runlist_mask", FIFO + "gk104.c", 389, 393, "0x002390"),
    ("pbdma_init", FIFO + "gk104.c", 735, 753, "0x002254"),
    ("queue_init", FIFO + "gf100.c", 351, 359, "0xfffffeff"),
    ("hce_init", FIFO + "gk104.c", 379, 386, "0x04014c"),
    ("runlist", FIFO + "gk104.c", 410, 457, "BIT(runl->id)"),
    ("preempt_remove", FIFO + "chan.c", 135, 192, "nvkm_runl_update_locked"),
    ("preempt_request", FIFO + "gf100.c", 42, 46, "0x002634"),
    ("preempt_pending", FIFO + "gf100.c", 370, 373, "0x00100000"),
    ("engine_status", FIFO + "gk104.c", 190, 267, "0x002640"),
    ("queue_idle", FIFO + "gk104.c", 288, 294, "0x0000e000"),
    ("recovery_idle_limit", FIFO + "runl.c", 86, 100, "runl->func->preempt"),
    ("channel_join", MMU + "vmmgf100.c", 337, 367, "0x0208"),
    ("pdb_invalidate", MMU + "vmmgf100.c", 188, 233, "HUB_ONLY"),
    ("gk104_geometry", MMU + "vmmgk104.c", 25, 78, "gk104_vmm_desc_17_12"),
    ("gp_put_get", NOUVEAU + "nouveau_dma.c", 74, 119, "0x8c"),
    ("channel_device_mask", NOUVEAU + "nouveau_chan.c", 302, 307, "devm = BIT(0)"),
    ("payload_get", NOUVEAU + "nouveau_chan.c", 447, 450, "0x60"),
    ("payload_reads", NOUVEAU + "nouveau_dma.c", 41, 69, "chan->user_get_hi"),
    ("nop_userd", "reference/open-gpu-doc/classes/host/cla16f.h", 42, 75, "NVA16F_NOP"),
    (
        "nop_packet",
        "reference/open-gpu-doc/classes/host/cla16f.h",
        196,
        201,
        "NVA16F_DMA_INCR_OPCODE_VALUE",
    ),
    (
        "gpfifo_fields",
        "reference/open-gpu-doc/classes/host/cla16f.h",
        150,
        165,
        "NVA16F_GP_ENTRY1_LENGTH",
    ),
)
INPUTS = (
    "AGENTS.md",
    "REVIEW.md",
    "reference/MANIFEST.md",
    "docs/S1-BATCH2-REVIEW.md",
    "docs/tasks/S1BATCH2PLAN.md",
    "docs/STATUS.md",
    "docs/S1-PLAN.md",
    "docs/PHASES.md",
    "docs/OPEN_QUESTIONS.md",
    "docs/S1-MEMORY-CONTRACT.md",
    "docs/S1-INTEGRATION-CHOICES.md",
    "docs/S1-RECIPE.md",
    "docs/S1-BATCH1-RUN-REVIEW.md",
    "docs/licensing.md",
    "work/S1BATCH1RUN/report.json",
    "work/S1BATCH1RUN/RESULT.md",
    "work/S1BATCH1RUN/consumed.json",
    "work/S1MEMCONTRACT/a7-freeze.json",
    "src/memory/VramArena.h",
    "src/memstage/Mapper.h",
    "src/memstage/Mapper.cpp",
    "src/memstage/Experiment.cpp",
    "src/memnative/NativeOwner.h",
    "src/runtime/S1Experiment.h",
    "src/runtime/S1Experiment.cpp",
    "src/fifo/PushBuffer.h",
    "src/fifo/PushBuffer.cpp",
    "tools/batch1_result.py",
    "tools/batch2_review.py",
)


def digest(path):
    """Return the SHA-256 of exact file bytes without normalization."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render():
    """Check immutable evidence and source anchors, then serialize the design inputs."""
    subprocess.run(
        [sys.executable, str(ROOT / "tools/batch1_result.py"), "--check"],
        check=True,
        cwd=ROOT,
    )
    prior = json.loads((ROOT / "work/S1BATCH1RUN/report.json").read_text())
    if prior["status"] != "PASS" or prior["bounds"]["S1_complete"]:
        raise ValueError("batch-1 scope mismatch")
    if prior["bounds"]["Q7"] != "open" or prior["bounds"]["Q11"] != "open":
        raise ValueError("unreviewed Q7/Q11 closure")
    seen = set()
    tasks = []
    for task, dependencies, purpose in TASKS:
        if any(dependency not in seen for dependency in dependencies):
            raise ValueError("task dependency order")
        path = "docs/tasks/" + task + ".md"
        text = (ROOT / path).read_text()
        if not text.startswith("# " + task + ":") or len(text.encode()) > 8192:
            raise ValueError("task header or context budget: " + task)
        tasks.append(
            dict(
                id=task,
                path=path,
                depends_on=list(dependencies),
                purpose=purpose,
                commit_policy="one task per commit",
            )
        )
        seen.add(task)
    spans = []
    for name, path, start, end, anchor in sorted(SPANS):
        lines = (ROOT / path).read_text().splitlines(keepends=True)
        if not 1 <= start <= end <= len(lines):
            raise ValueError("source bounds: " + name)
        text = "".join(lines[start - 1 : end])
        if anchor not in text:
            raise ValueError("source anchor: " + name)
        spans.append(
            dict(
                id=name,
                path=path,
                first_line=start,
                last_line=end,
                anchor=anchor,
                span_sha256=hashlib.sha256(text.encode()).hexdigest(),
                file_sha256=digest(ROOT / path),
                claim="KNOWN in pinned source",
                verification="SOURCE_ONLY",
            )
        )
    names = sorted(set(INPUTS) | {task["path"] for task in tasks})
    result_commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "bf67465^{commit}"],
        text=True,
    ).strip()
    return (
        json.dumps(
            dict(
                scope="HOST_ONLY design preparation. No runnable channel package or run approval.",
                review_entry="docs/S1-BATCH2-REVIEW.md",
                stage="S1_CHANNEL_NOP (design label only)",
                requested_verdicts=["batch-1 result evidence", "second-batch design"],
                prior_result_commit=result_commit,
                batch1=dict(
                    source_commit=prior["source_commit"],
                    package_sha256=prior["package_sha256"],
                    capture_sha256=prior["capture_sha256"],
                    bounds=prior["bounds"],
                    approval_consumed=True,
                    approval_available=False,
                ),
                source_spans=spans,
                planned_tasks=tasks,
                S1_complete=False,
                implementation_ready=False,
                hardware_authorized=False,
                proposed_success="fresh A7/memory gates, one channel GP_GET advance, fault-free finite detach and host closure",
                open_gates=[
                    "channel publication/address contract",
                    "polling interrupt deviation",
                    "GR-free scheduling",
                    "finite teardown predicates",
                    "immutable rehearsal/package",
                ],
                input_sha256={name: digest(ROOT / name) for name in names},
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main():
    """Write the review binding, or compare exact text with --check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("batch-2 review inputs differ")
    else:
        OUTPUT.write_text(text)
    print("Batch-2 design inputs and source anchors pass. No VM or card access.")


if __name__ == "__main__":
    main()
