#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Summarize the immutable successful buffered A7 run, without hardware access.

--check compares exact text and input hashes without writes or a guest.
Linux offset-zero REPEAT markers are documented synthetic logging records.
Instruction-selection agreement does not establish MMIO or timing equivalence.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from devinit_inventory import parse_log

FOLDER = ROOT / "results/20261029-a7-069cb71b"
OUTPUT = ROOT / "work/S1A7RUN7/report.json"
LINUX = ROOT / "reference/linux-run-debug/dmesg.txt.xz"
ROM = Path.home() / "haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render():
    launch = json.loads((FOLDER / "launch.json").read_text())
    suite = launch["suite"]
    if suite != json.loads((ROOT / "work/S1A7BUFFER/package.json").read_text()):
        raise ValueError("launched package differs from approved record")
    result = json.loads((FOLDER / "result.json").read_text())
    teardown = json.loads((FOLDER / "teardown.json").read_text())
    cutoff = json.loads((FOLDER / "cutoff.json").read_text())
    if result["status"] != "pass" or (FOLDER / "job.exit").read_text().strip() != "0":
        raise ValueError("this report requires the recorded passing run")
    raw = (FOLDER / "serial.log").read_text()
    events = [
        (name, int(a, 16), int(b, 16))
        for name, a, b in re.findall(
            r"^k40_a7: (.+?) a=0x([0-9a-f]+) b=0x([0-9a-f]+)$", raw, re.M
        )
    ]

    def single(name):
        rows = [(a, b) for n, a, b in events if n == name]
        if len(rows) != 1:
            raise ValueError("missing/duplicate event: " + name)
        return rows[0]

    trace = [(a, b) for n, a, b in events if n == "TRACE_AT"]
    if [a for a, b in trace] != list(range(single("TRACE_BEGIN")[0])):
        raise ValueError("trace indexes incomplete")
    if [b for a, b in trace] != sorted(b for a, b in trace):
        raise ValueError("trace times reversed")
    if single("TRACE_END") != (0, 0) or single("POST_RESULT")[0] != 0:
        raise ValueError("diagnostic or POST failure")
    rom = ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest() != suite["rom_sha256"]:
        raise ValueError("ROM differs")
    native = [
        dict(pc=a, opcode=b, active=n == "SCRIPT_ACTIVE")
        for n, a, b in events
        if n in ("SCRIPT_ACTIVE", "SCRIPT_SKIPPED")
    ]
    if any(rom[row["pc"]] != row["opcode"] for row in native):
        raise ValueError("native opcode differs from ROM")
    linux = parse_log(lzma.open(LINUX, "rt").read())
    synthetic = [row for row in linux if int(row["offset"], 16) == 0]
    if not all(row["name"] == "REPEAT" and row["marker"].strip() for row in synthetic):
        raise ValueError("unexpected synthetic Linux marker")
    normalized = [
        (int(row["offset"], 16), bool(row["marker"].strip()))
        for row in linux
        if int(row["offset"], 16)
    ]
    if normalized != [(row["pc"], row["active"]) for row in native]:
        raise ValueError("native instruction selection differs from Linux")
    transactions = []
    audits = [event for event in events if event[0].startswith("I2C_")]
    names = [
        "I2C_REQUEST",
        "I2C_DISPOSITION",
        "I2C_RESULT",
        "I2C_PHASE",
        "I2C_TIME",
        "I2C_WORK",
    ]
    if len(audits) % len(names):
        raise ValueError("partial I2C audit")
    for start in range(0, len(audits), len(names)):
        rows = audits[start : start + len(names)]
        if [row[0] for row in rows] != names:
            raise ValueError("I2C audit order")
        request, disposition, status, phase, timing, work = rows
        transactions.append(
            dict(
                pc=hex(request[1]),
                address7=hex(request[2] >> 16),
                intended_register=hex((request[2] >> 8) & 255),
                intended_value=hex(request[2] & 255),
                attempt=disposition[1],
                disposition=disposition[2],
                primary=status[1],
                cleanup=status[2],
                phase=phase[1],
                bit=phase[2],
                transfer_us=timing[1],
                cleanup_us=timing[2],
                guard_operations=work[1],
                last_levels=hex(work[2]),
            )
        )
    polls = []
    for n, pc, count in events:
        if n != "POLL_COUNT":
            continue
        last = [(a, b) for name, a, b in events if name == "POLL_LAST" and a == pc]
        first_time = [
            (a, b) for name, a, b in events if name == "POLL_FIRST_US" and a == pc
        ]
        last_time = [
            (a, b) for name, a, b in events if name == "POLL_LAST_US" and a == pc
        ]
        if any(len(rows) != 1 for rows in (last, first_time, last_time)):
            raise ValueError("incomplete poll summary")
        polls.append(
            dict(
                pc=hex(pc),
                samples=count,
                last_value=hex(last[0][1]),
                first_us=first_time[0][1],
                last_us=last_time[0][1],
            )
        )
    before = (FOLDER / "kernel-before.log").read_bytes()
    after = (FOLDER / "kernel-after.log").read_bytes()
    if not after.startswith(before):
        raise ValueError("R5 prefix changed")
    if (
        single("ARM_BEFORE") != single("ARM_AFTER")
        or single("ARM_BEFORE")[0] != cutoff["iova"]
    ):
        raise ValueError("armed extent differs")
    if single("ARM_BEFORE")[1] != cutoff["iova"] >> 8:
        raise ValueError("arm encoding differs")
    if single("TIMER")[1] <= single("TIMER")[0]:
        raise ValueError("timer did not advance")
    if single("VRAM_BYTES")[0] != suite["physical_vram_bytes"]:
        raise ValueError("VRAM total differs")
    sources = (
        "tools/a7/result_report.py",
        "tools/devinit_inventory.py",
        "src/a7/Owner.cpp",
        "src/a7/PostDiagnostics.h",
        "src/a7/NativePlatform.cpp",
        "src/devinit/Interpreter.cpp",
        "src/devinit/BoundPost.cpp",
        "src/runtime/PreStart.cpp",
        "src/runtime/Bootstrap.cpp",
    )
    return (
        json.dumps(
            dict(
                scope="KNOWN/HARDWARE_VERIFIED reported POST/readiness on 0000:04:00.0 under Haiku only; not S1 or DMA payload visibility",
                folder=str(FOLDER.relative_to(ROOT)),
                source_commit=launch["source_commit"],
                approval="direct user go-ahead for this minor change; no independent Claude ACCEPT claimed",
                command='K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom" python3 tools/a7/run.py --run-approved-A7-once',
                suite_sha256=sha(ROOT / "work/S1A7BUFFER/package.json"),
                artifacts=suite["guest_artifacts"],
                kernel_sha256=suite["kernel_sha256"],
                rom_sha256=suite["rom_sha256"],
                result=result,
                teardown=teardown,
                instruction_selection=dict(
                    native_active=sum(row["active"] for row in native),
                    native_skipped=sum(not row["active"] for row in native),
                    linux_raw_active=sum(bool(row["marker"].strip()) for row in linux),
                    linux_raw_skipped=sum(not row["marker"].strip() for row in linux),
                    synthetic_offset_zero_repeat_markers=len(synthetic),
                    normalized_count=len(normalized),
                    exact_normalized_pc_active_sequence_match=True,
                    native_opcodes_match_rom=True,
                    normalization_source="analysis/devinit_inventory.md:60; Nouveau bios/init.c:658-677,724-733",
                    limitation="instruction selection, not MMIO value or helper timing equivalence",
                ),
                telemetry=dict(
                    identity=hex(single("IDENTITY")[0]),
                    pci_command=hex(single("PCI_COMMAND")[0]),
                    post_error=single("POST_RESULT")[0],
                    post_final_pc=hex(single("POST_RESULT")[1]),
                    post_wall_us=single("POST_WALL_US")[0],
                    requested_delay_us=single("POST_DELAY_US")[0],
                    actual_delay_us=single("POST_DELAY_US")[1],
                    delay_calls=single("POST_DELAY_COUNT")[0],
                    mmio_total_us=single("POST_MMIO_US")[0],
                    mmio_max_us=single("POST_MMIO_US")[1],
                    mmio_calls=single("POST_MMIO_COUNT")[0],
                    diagnostic_drain_us=single("TRACE_DUMP_US")[0],
                    trace_records=len(trace),
                    trace_last_us=trace[-1][1],
                ),
                i2c=transactions,
                polls=polls,
                flush=dict(
                    candidate_gpa=hex(cutoff["gpa"]),
                    candidate_iova=hex(cutoff["iova"]),
                    before_encoded_write=hex(single("ARM_BEFORE")[1]),
                    after_encoded_write=hex(single("ARM_AFTER")[1]),
                    after_post_readback=hex(single("ARM_READBACK")[0]),
                    after_rearm_readback="NOT_RECORDED",
                    programming_callback_success="INFERRED from subsequent guarded execution and PASS; no initial/final register readback",
                    mapping_scope=cutoff["claim"],
                    reason_for_zero_readback="UNKNOWN",
                ),
                readiness=dict(
                    timer_before=hex(single("TIMER")[0]),
                    timer_after=hex(single("TIMER")[1]),
                    vram_bytes=single("VRAM_BYTES")[0],
                    vram_mib=single("VRAM_BYTES")[0] // 1048576,
                    scratch_base=hex(single("SCRATCH_PASS")[0]),
                    reserved_bytes=single("SCRATCH_PASS")[1],
                    scratch_scope="three sampled dwords, pattern/complement passes and BAR flush; not entire-page coverage or DMA",
                    pending_register_value=0,
                    pending_evidence="INFERRED from Owner.cpp guarded PASS; not separately logged",
                    retained_state=single("RETAINED")[1],
                    retained_token=single("RETAINED")[0],
                ),
                kernel=dict(
                    before_bytes=len(before),
                    after_bytes=len(after),
                    unchanged=before == after,
                    delta_bytes=len(after) - len(before),
                    allowed_lines=result["allowed_kernel_lines"],
                    scope=result["kernel_scope"],
                ),
                sources_sha256={name: sha(ROOT / name) for name in sorted(sources)},
                linux_capture_sha256=sha(LINUX),
                captures_sha256={
                    path.name: sha(path)
                    for path in sorted(FOLDER.iterdir())
                    if path.is_file() and path.name != "README.md"
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
            raise ValueError("recorded A7 report differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
