#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Offline inventory of observed devinit instructions; never executes firmware."""
import argparse
from collections import Counter
import json
import lzma
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "reference/linux-run-debug/dmesg.txt.xz"
INSTRUCTION = re.compile(r"devinit: (0x[0-9a-fA-F]{8})\[([^]]*)\]: (.*)")
TIMESTAMP = re.compile(r"^\[\s*\d+(?:\.\d+)?\]\s?")
BOARD = set("ZM_I2C_BYTE I2C_BYTE ZM_I2C I2C_IF GPIO GPIO_NE IO IO_MASK IO_OR IO_AND ZM_CR CR TIME CONDITION_TIME INDEX_IO ZM_INDEX_IO".split())


def parse_log(text):
    lines = text.splitlines()
    instructions = []
    for index, line in enumerate(lines):
        match = INSTRUCTION.search(line)
        if not match or match[3].startswith("\t"):
            continue
        offset, marker, payload = match.groups()
        if not payload.split():
            raise ValueError(f"empty instruction at line {index + 1}")
        instructions.append(dict(line=index + 1, offset=offset.lower(), marker=marker,
                                 name=payload.split()[0], text=payload.strip()))
    for index, instruction in enumerate(instructions):
        stop = instructions[index + 1]["line"] - 1 if index + 1 < len(instructions) else len(lines)
        instruction["details"] = [value for line in lines[instruction["line"]:stop]
                                  if (value := TIMESTAMP.sub("", line).rstrip()).strip()]
    return instructions


def log_summary(instructions):
    executed = Counter(i["name"] for i in instructions if i["marker"].strip())
    skipped = Counter(i["name"] for i in instructions if not i["marker"].strip())
    return dict(log_instructions=len(instructions), executed=sum(executed.values()),
                skipped=sum(skipped.values()),
                opcodes=[dict(name=name, executed=executed[name], skipped=skipped[name])
                         for name in sorted(executed.keys() | skipped.keys())])


LISTING = re.compile(r"^0x([0-9a-fA-F]{8}):((?: [0-9a-f]{2})+)\s{2,}(\S.*?)\s*$")
SCRIPT = re.compile(r"^Init script (\d+) at (0x[0-9a-fA-F]+):$")


def parse_listing(text):
    scripts, instructions, seen = [], [], {}
    started = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("Init script table at "):
            started = True
        if not started:
            continue
        script = SCRIPT.match(line)
        if script:
            scripts.append(dict(index=int(script[1]), offset=script[2].lower()))
        match = LISTING.match(line)
        if not match:
            continue
        payload = match[3]
        # Match the task's listing-row definition: exclude empty first
        # lines and explicit R[...] continuations. Numeric table rows stay
        # in this presentation inventory; this is NOT a bytecode decoder.
        if not payload or payload.startswith("R["):
            continue
        offset = int(match[1], 16)
        item = dict(offset=f"0x{offset:08x}", line=number,
                    name=payload.split()[0], bytes=match[2].split(), text=payload)
        if offset in seen and seen[offset] != item:
            # The listing can print one script from more than one root. Lines
            # differ; bytes and instruction spelling must agree.
            old = seen[offset]
            if (old["bytes"], old["name"]) != (item["bytes"], item["name"]):
                raise ValueError(f"conflicting decode at {offset:#x}")
        seen[offset] = item
        instructions.append(item)
    return scripts, instructions



def inventory(decoded, log_text):
    instructions = parse_log(log_text)
    scripts, listing = parse_listing(decoded)
    log_offsets = {i["offset"] for i in instructions}
    listing_offsets = {i["offset"] for i in listing}
    return dict(**log_summary(instructions), scripts=scripts,
                static_instructions=len(listing),
                log_offsets_not_in_listing=sorted(log_offsets - listing_offsets),
                listing_offsets_not_in_log=len(listing_offsets - log_offsets),
                board_operations=[{key: value for key, value in i.items()}
                                  for i in instructions if i["name"] in BOARD])



def markdown(report):
    def escape(value):
        return str(value).replace("|", "&#124;").replace("\t", " ")
    lines = ["# Observed devinit inventory", "", "## Summary", "",
             "This is observed execution/listing agreement, not a reachability proof.", "",
             f"Log instructions: {report['log_instructions']}; executed: {report['executed']}; skipped: {report['skipped']}.",
             f"Listing rows (task definition): {report['static_instructions']}; listing offsets absent from log: {report['listing_offsets_not_in_log']}.",
             "", "| Script | Offset |", "|---|---|"]
    lines += [f"| {item['index']} | {item['offset']} |" for item in report["scripts"]]
    lines += ["", "## Instructions", "", "| Name | Executed | Skipped |", "|---|---|---|"]
    lines += [f"| {item['name']} | {item['executed']} | {item['skipped']} |" for item in report["opcodes"]]
    lines += ["", "## Not in the listing", ""]
    lines += [f"- `{offset}`" for offset in report["log_offsets_not_in_listing"]]
    lines += ["", "Offset zero is a synthetic REPEAT trace after END_REPEAT sets the interpreter offset to zero; it is not a ROM instruction at zero (Nouveau bios/init.c:658-677,724-733).",
              "The seven COPY_NV_REG starts are present as byte-only lines; nvbios prints their names at start+16 on the second line of each 22-byte instruction (nvbios/nvbios.c:469-476). They follow RESUME or the preceding register/copy instruction in the log, not a hidden branch or missing script.",
              "The listing-offset count follows the task definition, including numeric table rows and a repeated DONE at 0x657f. It is not a count of reachable bytecode instructions.",
              "", "## Board operations", "", "| Log line | Offset | Marker | Name | Text | Detail lines |", "|---|---|---|---|---|---|"]
    lines += [f"| {i['line']} | {i['offset']} | `{i['marker']}` | {i['name']} | {escape(i['text'])} | {len(i['details'])} |" for i in report["board_operations"]]
    lines += ["", "Board-operation occurrence or script origin is not authorization to execute it. See docs/BOARD-OPERATIONS.md.", ""]
    return "\n".join(lines)


def default_decoded():
    if os.environ.get('K40_DECODED'):return Path(os.environ['K40_DECODED']).expanduser()
    original = Path.home() / "haiku-cross/vbios/decoded/all.txt"
    return original if original.is_file() else Path.home() / "mediaflux/vbios/decoded/all.txt"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoded", type=lambda s: Path(s).expanduser(), default=default_decoded())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = inventory(args.decoded.read_text(), lzma.open(LOG, "rt").read())
    outputs = {ROOT / "analysis/devinit_inventory.json": json.dumps(report, indent=2) + "\n",
               ROOT / "analysis/devinit_inventory.md": markdown(report)}
    if args.check:
        return 0 if all(path.is_file() and path.read_text() == text for path, text in outputs.items()) else 1
    for path, text in outputs.items():
        path.write_text(text)
    print(f"devinit inventory: {report['log_instructions']} observed, {report['static_instructions']} listing rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
