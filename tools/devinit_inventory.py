#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
"""Offline inventory of observed devinit instructions; never executes firmware."""
import argparse
from collections import Counter
import json
import lzma
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


if __name__ == "__main__":
    instructions = parse_log(lzma.open(LOG, "rt").read())
    print(json.dumps(log_summary(instructions), indent=2))
