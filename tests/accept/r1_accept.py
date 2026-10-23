#!/usr/bin/env python3
"""Acceptance test for task R1, part F4, written by the scaffold. Do not edit:
`make check` compares this file with a recorded hash.

F4 of the external review (docs/external/2026-10-13-review-outcome-package-b.md):
tools/qmd_compare.py skipped unknown fields, turned unknown named values into
zero, accepted a short word list, did not fail on differences, and did not
check its Markdown output. This test runs the tool on modified inputs in a
temporary directory and checks that each of these now fails.

Interface required by docs/tasks/R1.md:
  tools/qmd_compare.py [--reference F] [--words F] [--header F]
                       [--out-json F] [--out-md F] [--verify]
Without --verify the tool writes the two output files; it exits 1 (and
writes nothing) when an input is invalid. With --verify it writes nothing
and exits 0 only when the inputs are valid, every field is equal, and both
output files are exactly what it would write.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "qmd_compare.py")
HEADER = os.path.join(ROOT, "reference", "mesa", "src", "gallium", "drivers", "nouveau", "nvc0", "cla0c0qmd.h")
REF = os.path.join(ROOT, "analysis", "linux_run_shader.json")

checks = 0
failures = 0


def check(cond, what):
    global checks, failures
    checks += 1
    if not cond:
        failures += 1
        print("FAIL:", what)


def run(tmp, ref, words, verify=False):
    args = [sys.executable, TOOL, "--reference", ref, "--words", words, "--header", HEADER,
            "--out-json", os.path.join(tmp, "out.json"), "--out-md", os.path.join(tmp, "out.md")]
    if verify:
        args.append("--verify")
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120).returncode


def main():
    words = subprocess.run([os.path.join(ROOT, "build", "tests", "ref_qmd"), "--words"],
                           capture_output=True, text=True, timeout=60).stdout.split()
    check(len(words) == 64, "build/tests/ref_qmd --words prints 64 words (run make -s -C tests first)")
    ref = json.load(open(REF))
    tmp = tempfile.mkdtemp(prefix="r1_accept_")
    try:
        wfile = os.path.join(tmp, "words.txt")
        open(wfile, "w").write("\n".join(words) + "\n")

        def write_ref(name, qmd):
            p = os.path.join(tmp, name)
            r = dict(ref)
            r["qmd"] = qmd
            json.dump(r, open(p, "w"))
            return p

        good = write_ref("good.json", ref["qmd"])
        # 1. Valid inputs: generate, then verify passes.
        check(run(tmp, good, wfile) == 0, "generation with valid inputs exits 0")
        check(run(tmp, good, wfile, verify=True) == 0, "--verify passes after generation")
        out_md = os.path.join(tmp, "out.md")

        # 2. The Markdown output is checked: a changed file fails --verify.
        open(out_md, "a").write("\nchanged by hand\n")
        check(run(tmp, good, wfile, verify=True) == 1, "--verify fails when out.md was changed")
        run(tmp, good, wfile)

        # 3. A field value that differs: generation may write it, --verify fails.
        q = [dict(e) for e in ref["qmd"]]
        i = next(n for n, e in enumerate(q) if e["name"] == "PROGRAM_OFFSET")
        q[i]["value"] = "0x7f200"
        diff = write_ref("diff.json", q)
        run(tmp, diff, wfile)
        check(run(tmp, diff, wfile, verify=True) == 1, "--verify fails when one field differs")

        # 4. An unknown field name: the tool refuses the input.
        q = [dict(e) for e in ref["qmd"]] + [{"name": "NO_SUCH_FIELD", "value": "0x0"}]
        bad = write_ref("unknown-field.json", q)
        check(run(tmp, bad, wfile) == 1, "an unknown field name is refused")

        # 5. An unknown named value: the tool refuses the input (not zero).
        q = [dict(e) for e in ref["qmd"]]
        i = next(n for n, e in enumerate(q) if e["name"] == "SAMPLER_INDEX")
        q[i]["value"] = "NOT_A_VALUE"
        bad = write_ref("unknown-value.json", q)
        check(run(tmp, bad, wfile) == 1, "an unknown named value is refused")

        # 6. A field listed twice: refused.
        q = [dict(e) for e in ref["qmd"]] + [dict(ref["qmd"][0])]
        bad = write_ref("duplicate.json", q)
        check(run(tmp, bad, wfile) == 1, "a duplicate field is refused")

        # 7. 63 words instead of 64: refused.
        short = os.path.join(tmp, "short.txt")
        open(short, "w").write("\n".join(words[:63]) + "\n")
        check(run(tmp, good, short) == 1, "a list of 63 words is refused")

        # 8. A word that is not 32-bit hex: refused.
        badw = os.path.join(tmp, "badword.txt")
        open(badw, "w").write("\n".join(words[:63] + ["1ffffffff"]) + "\n")
        check(run(tmp, good, badw) == 1, "a word of more than 32 bits is refused")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    src = open(TOOL).read()
    check("eval(" not in src, "the tool does not use eval() to read the header")

    print(f"r1_accept.py: {checks} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
