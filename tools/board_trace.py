#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Compare host board-helper accesses with the pinned Linux IO trace window.

Reads the private ROM, ADR 004, compiled host probe, and compressed capture.
Writes aggregate provenance and comparison results, never firmware bytes.
With --check, compares exact generated text without writing. No hardware access.
"""

import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "reference/linux-run-debug/mmiotrace.txt.xz"
ADR = ROOT / "docs/decisions/004-board-operations-and-review.md"
PROBE = ROOT / "build/tests/board_probe"
SOURCES = (
    "src/devinit/Board.h", "src/devinit/Board.cpp", "src/devinit/Interpreter.cpp",
    "src/devinit/Interpreter.h", "src/devinit/Sha256.h", "src/devinit/Sha256.cpp",
    "tests/board_fake.h", "tests/board_probe.cpp", "tools/board_trace.py",
)


def read_policy(text):
    """Parse the six user-approved instruction rows, not an independent policy copy."""
    hashes = re.findall(r"\b[a-f0-9]{64}\b", text)
    if len(set(hashes)) != 1:
        raise ValueError("ADR 004 must name one ROM SHA-256")
    # Opcode dispatch: pinned nvkm/subdev/bios/init.c:2246,2252,2269,2297.
    codes = {"IO": 0x69, "ZM_CR": 0x53, "ZM_I2C_BYTE": 0x4d, "GPIO_NE": 0xa9}
    rows = re.findall(r"\|\s*`(0x[0-9a-f]+)`\s*\|\s*`([A-Z0-9_]+)`\s*\|", text)
    if len(rows) != 6 or len({offset for offset, _ in rows}) != 6:
        raise ValueError("ADR 004 must contain exactly six distinct instruction rows")
    try:
        return sorted((hashes[0], int(offset, 16), codes[name]) for offset, name in rows)
    except KeyError as error:
        raise ValueError("unreviewed board opcode in ADR 004") from error


def capture_window(lines, first=45579, last=45598):
    """Read both byte and dword accesses using the existing mmiotrace format.

    Format: tools/compare_register_traces.py:69-108 and tools/load_trace.py:24-38.
    BAR0 comes from PCIDEV metadata, so relocation cannot become a register offset.
    The last two accesses are the following ZM_CR, not part of INIT_IO itself.
    """
    base = None
    size = 0
    events = []
    for number, line in enumerate(lines, 1):
        fields = line.split()
        if fields and fields[0] == "PCIDEV" and len(fields) >= 18 and fields[2] == "10de1024":
            base, size = int(fields[4], 16) & ~15, int(fields[11], 16)
        if first <= number <= last:
            if len(fields) < 8 or fields[0] not in ("R", "W") or fields[1] not in ("1", "4"):
                raise ValueError("unexpected access in the fixed comparison window")
            address, value = int(fields[4], 16), int(fields[5], 16)
            width = int(fields[1])
            if base is None or not base <= address < base + size or value >= 1 << (8 * width):
                raise ValueError("capture access is outside BAR0 or its width")
            events.append((fields[0], width, address - base, value))
        if number >= last:
            break
    if len(events) != last - first + 1:
        raise ValueError("capture window is incomplete")
    return events


def probe(*args, input_text=None):
    """Run only the compiled host recorder. It has no device APIs."""
    return subprocess.check_output([str(PROBE), *map(str, args)], text=True, input=input_text)


def run_events(rom, initial, skipped=False):
    text = "".join(f"{at:x} {value:x}\n" for at, value in sorted(initial.items()))
    rows = probe("--io", rom, *(["--skip"] if skipped else []), input_text=text)
    events = []
    for line in rows.splitlines():
        kind, width, address, value = line.split()
        events.append((kind, int(width), int(address, 16), int(value, 16)))
    return events


def compare_io(rom, trace=TRACE):
    """Recompute policy, IO/CRTC trace equality, and skipped-IO waits."""
    approved = read_policy(ADR.read_text())
    emitted = []
    for row in probe("--rules").splitlines():
        digest, offset, opcode = row.split()
        emitted.append((digest, int(offset, 16), int(opcode, 16)))
    if sorted(emitted) != approved:
        raise ValueError("compiled board policy differs from ADR 004")
    digest = hashlib.sha256(rom.read_bytes()).hexdigest()
    if digest != approved[0][0] or probe("--sha", rom).strip() != digest:
        raise ValueError("ROM hash is not approved or the C++ hash differs")
    accepted = int(probe("--policy", rom).strip())
    with lzma.open(trace, "rt") as stream:
        expected = capture_window(stream)
    initial = {}
    for kind, _, address, value in expected:
        if kind == "R":
            initial.setdefault(address, value)
    observed = run_events(rom, initial)
    accesses = [event for event in observed if event[0] != "D"]
    if accesses != expected:
        raise ValueError("host helper accesses differ from trace lines 45579-45598")
    waits = [event[3] for event in observed if event[0] == "D"]
    skipped = run_events(rom, initial, skipped=True)
    if waits != [10000, 10000] or skipped != [("D", 0, 0, 10000)] * 2:
        raise ValueError("IO does not preserve both unconditional waits")
    return {
        "scope": "HOST_ONLY helpers; IO and following ZM_CR access facts TRACE_VERIFIED",
        "rom_sha256": digest,
        "approved_policy_rows": accepted,
        "trace": str(trace.relative_to(ROOT)),
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "trace_lines": [45579, 45598],
        "matched_accesses": len(accesses),
        "reads": sum(event[0] == "R" for event in accesses),
        "writes": sum(event[0] == "W" for event in accesses),
        "active_waits_us": waits,
        "skipped_waits_us": [event[3] for event in skipped],
        "real_rom_policy_and_failure_exercise": "pass",
        "inputs_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in sorted((*SOURCES, str(ADR.relative_to(ROOT))))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=Path(os.environ.get(
        "K40_VBIOS", Path.home() / "haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
    )).expanduser())
    parser.add_argument("--output", type=Path, default=ROOT / "work/S1BOARD/trace-check.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(compare_io(args.rom), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text() != text:
            raise SystemExit("board trace report differs")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print("board trace: 20 accesses match; both skipped IO waits preserved (HOST_ONLY)")


if __name__ == "__main__":
    main()
