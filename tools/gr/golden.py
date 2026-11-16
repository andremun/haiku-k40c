#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Compare a printed golden image with the image of the Linux reference run.

The reference trace holds the context of the job channel: Linux writes a copy of
its golden image into the channel context (engine/gr/gf100.c:330-338), which the
trace shows as writes to MAP 26. A stage in print mode (s3g, gr::Compute) prints
our golden image in `k40_mem: IMG` lines. This tool compares the two word by
word (work/S3DIAG/REPORT.md, approach A).

--check writes nothing and exits 0 when the reference image has its known form.
--serial FILE compares and lists the words that differ; exit 0 means that no
word differs. Words that hold run data (addresses of our own records) can differ:
review the list. HOST_ONLY: the comparison is not card evidence; the serial log
of the run is.
"""
import argparse
import lzma
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "memstage"))
import oracle

IMAGE_BYTES = 0x4EA00  # tools/gr/program.py KNOWN[0x409804], trace 616433.
MAP, BASE = "26", 0x8103A5000  # trace line 811577: MAP 26, 0x4f000 bytes.
FIRST, LAST = 811578, 892190  # The image copy. Lines 892191-892192 are the two list words.
NOT_ZERO = 56574  # KNOWN: words of the reference image that are not zero.


def reference():
    """The Linux image as a list of words."""
    words, seen = [0] * (IMAGE_BYTES // 4), 0
    with lzma.open(oracle.TRACE, "rt") as trace:
        for number, line in enumerate(trace, 1):
            if number < FIRST:
                continue
            if number > LAST:
                break
            part = line.split()
            if len(part) >= 6 and part[0] == "W" and part[3] == MAP:
                offset = int(part[4], 16) - BASE
                if part[1] != "4" or offset % 4 or not 0 <= offset < IMAGE_BYTES:
                    raise ValueError(f"trace line {number}: not a word of the image")
                words[offset // 4] = int(part[5], 16)
                seen += 1
    if seen != IMAGE_BYTES // 4:
        raise ValueError(f"reference image: {seen} writes, expected {IMAGE_BYTES // 4}")
    return words


def printed(serial):
    """Our image from the IMG lines of a serial log, checked against its summary line."""
    import evidence

    lines = evidence.image_lines(serial)
    words = [0] * (IMAGE_BYTES // 4)
    for offset, row in lines.items():
        words[offset // 4: offset // 4 + 8] = row
    return words, len(lines)


def compare(ours, linux):
    """Offsets (bytes) of the words that differ, in order."""
    return [index * 4 for index, (a, b) in enumerate(zip(ours, linux)) if a != b]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--serial", type=Path)
    parser.add_argument("--limit", type=int, default=64, help="differences to print")
    args = parser.parse_args()
    linux = reference()
    count = sum(1 for word in linux if word)
    if count != NOT_ZERO or any(linux[:64]) or linux[64] != 0x0905090A:
        raise SystemExit("reference image differs from its known form")
    if not args.serial:
        print(f"reference golden image: {len(linux)} words, {count} not zero, sum {sum(linux) & 0xFFFFFFFF:08x}; "
              "trace MAP 26; HOST_ONLY")
        return 0
    ours, lines = printed(args.serial.read_text(errors="replace"))
    differ = compare(ours, linux)
    print(f"printed image: {lines} lines, {sum(1 for word in ours if word)} words not zero, sum {sum(ours) & 0xFFFFFFFF:08x}")
    print(f"reference image: {count} words not zero, sum {sum(linux) & 0xFFFFFFFF:08x}")
    print(f"words that differ: {len(differ)} of {len(linux)}")
    for offset in differ[: args.limit]:
        print(f"  +{offset:05x} ours {ours[offset // 4]:08x} linux {linux[offset // 4]:08x}")
    if len(differ) > args.limit:
        print(f"  ... {len(differ) - args.limit} more (--limit)")
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
