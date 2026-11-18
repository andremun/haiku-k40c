#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Compare a printed golden image with the image of the Linux reference run.

The reference trace holds the context of the job channel: Linux writes a copy of
its golden image into the channel context (engine/gr/gf100.c:330-338), which the
trace shows as writes to MAP 26. A stage in print mode (s3g, gr::Compute) prints
our golden image in `k40_mem: IMG` lines. This tool compares the two word by
word (work/S3DIAG/REPORT.md, approach A).

The image is not the same in two Linux runs: about half of its words differ
(saved hardware state that the generation does not set). The tool therefore reads
the image of both reference traces and judges only the words that agree in both.

--check writes nothing and exits 0 when both reference images have their known form.
--serial FILE compares and lists the words that differ where both Linux runs agree;
exit 0 means none. Words that hold run data (addresses of our own records) and
state bits that change from run to run can differ: review the list. A log of a run
that stopped during the print is compared up to its last line. HOST_ONLY: the
comparison is not card evidence; the serial log of the run is.
"""
import argparse
import lzma
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "memstage"))
import oracle

IMAGE_BYTES = 0x4EA00  # tools/gr/program.py KNOWN[0x409804], trace 616433.
CONTEXT_BYTES = 0x4F000  # engine/gr/gf100.c:330-338: the channel context record of the reference runs.
# Reference traces and the count of image words that are not zero (KNOWN, from the traces).
TRACES = (("linux-run", oracle.TRACE, 56574),
          ("linux-run-ladder", oracle.ROOT / "reference/linux-run-ladder/mmiotrace.txt.xz", 56850))


def reference(path):
    """The Linux image of one trace as a list of words: the first IMAGE_BYTES / 4 writes
    to the first map of CONTEXT_BYTES. The two list words that follow are left out."""
    words, seen, base, ident = [0] * (IMAGE_BYTES // 4), 0, None, None
    with lzma.open(path, "rt") as trace:
        for number, line in enumerate(trace, 1):
            part = line.split()
            if len(part) < 6:
                continue
            if ident is None:
                if part[0] == "MAP" and int(part[5], 16) == CONTEXT_BYTES:
                    ident, base = part[2], int(part[3], 16)
                continue
            if part[0] == "W" and part[3] == ident:
                offset = int(part[4], 16) - base
                if part[1] != "4" or offset != seen * 4:
                    raise ValueError(f"trace line {number}: not the next word of the image")
                words[seen] = int(part[5], 16)
                seen += 1
                if seen == len(words):
                    return words
    raise ValueError(f"reference image: {seen} writes, expected {len(words)}")


def printed(serial):
    """Our image from the IMG lines of a serial log: (words, lines, bytes covered).
    A run that stopped during the print covers the image up to its last line."""
    import evidence

    lines = evidence.image_lines(serial)
    words = [0] * (IMAGE_BYTES // 4)
    for offset, row in lines.items():
        words[offset // 4: offset // 4 + 8] = row
    complete = "k40_mem: GR step=15 error=0" in serial
    return words, len(lines), IMAGE_BYTES if complete else (max(lines) + 32 if lines else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--serial", type=Path)
    parser.add_argument("--limit", type=int, default=64, help="differences to print")
    args = parser.parse_args()
    images = []
    for name, path, known in TRACES:
        words = reference(path)
        if sum(1 for word in words if word) != known or any(words[:64]) or words[64] != 0x0905090A:
            raise SystemExit(f"reference image of {name} differs from its known form")
        images.append(words)
    total = len(images[0])
    stable = [index for index in range(total) if images[0][index] == images[1][index]]
    print(f"reference golden images: {total} words; the two Linux runs differ in {total - len(stable)} words "
          f"and agree in {len(stable)}; HOST_ONLY")
    if not args.serial:
        return 0
    ours, lines, covered = printed(args.serial.read_text(errors="replace"))
    span = covered // 4
    print(f"printed image: {lines} lines, {covered} of {IMAGE_BYTES} bytes covered, {sum(1 for word in ours[:span] if word)} words not zero")
    for (name, _, _), words in zip(TRACES, images):
        print(f"words that differ from {name}: {sum(1 for index in range(span) if ours[index] != words[index])} of {span}")
    print(f"the two Linux runs differ from each other in {sum(1 for index in range(span) if images[0][index] != images[1][index])} of {span}")
    differ = [index for index in stable if index < span and ours[index] != images[0][index]]
    print(f"words equal in both Linux runs: {sum(1 for index in stable if index < span)}; ours differs in {len(differ)}")
    for index in differ[: args.limit]:
        print(f"  +{index * 4:05x} ours {ours[index]:08x} linux {images[0][index]:08x}")
    if len(differ) > args.limit:
        print(f"  ... {len(differ) - args.limit} more (--limit)")
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
