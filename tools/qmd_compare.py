#!/usr/bin/env python3
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# qmd_compare.py -- compare our QMD words against the reference run.
# Distributed under the terms of the MIT License.
#
# Reads the Nouveau header at runtime, runs ref_qmd --words,
# reads the reference JSON, and writes comparison files.

import argparse
import json
import os
import re
import subprocess
import sys

HEADER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reference", "mesa", "src", "gallium", "drivers", "nouveau", "nvc0",
    "cla0c0qmd.h",
)

ANALYSIS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"
)

REFERENCE_JSON = os.path.join(ANALYSIS_DIR, "linux_run_shader.json")


def parse_header(path):
    """Parse cla0c0qmd.h for NVA0C0_QMDV00_06_ defines.

    Returns:
        fields: dict of name -> "HI:LO" text (lines with MW(...))
        named:  dict of name -> int value (lines without MW)
    """
    fields = {}
    named = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#define NVA0C0_QMDV00_06_"):
                continue
            # Split into name and value parts
            m = re.match(
                r"#define\s+(NVA0C0_QMDV00_06_\w+(?:\([^)]*\))?)\s+(.+)", line
            )
            if not m:
                continue
            raw_name = m.group(1)
            value_text = m.group(2).strip()

            # Strip trailing backslash continuation
            value_text = value_text.rstrip("\\")

            if "MW(" in value_text:
                # Field definition: strip the NVA0C0_QMDV00_06_ prefix and
                # any trailing (i) index to get the canonical name.
                # Also strip the MW( and ) wrapper from the value text.
                field_name = raw_name
                field_name = re.sub(r"^NVA0C0_QMDV00_06_", "", field_name)
                field_name = re.sub(r"\(.*\)$", "", field_name)
                # Strip MW( prefix and ) suffix
                inner = value_text[3:]  # remove "MW("
                if inner.endswith(")"):
                    inner = inner[:-1]
                fields[field_name] = inner
            else:
                # Named value: parse the integer
                try:
                    int_val = int(value_text, 16)
                except ValueError:
                    continue
                named[raw_name] = int_val

    return fields, named


def compute_expr(expr):
    """Compute an arithmetic expression containing only digits, +, *, (, ).

    Replaces (i) with the substituted index value first.
    Uses a simple recursive descent parser, no eval.
    """
    expr = expr.replace(" ", "")
    pos = [0]

    def parse_expr():
        """expr -> term (('+' | '-') term)*"""
        left = parse_term()
        while pos[0] < len(expr) and expr[pos[0]] in ('+', '-'):
            op = expr[pos[0]]
            pos[0] += 1
            right = parse_term()
            if op == '+':
                left = left + right
            else:
                left = left - right
        return left

    def parse_term():
        """term -> factor ('*' factor)*"""
        left = parse_factor()
        while pos[0] < len(expr) and expr[pos[0]] == '*':
            pos[0] += 1
            right = parse_factor()
            left = left * right
        return left

    def parse_factor():
        """factor -> '(' expr ')' | number"""
        if pos[0] < len(expr) and expr[pos[0]] == '(':
            pos[0] += 1
            val = parse_expr()
            if pos[0] < len(expr) and expr[pos[0]] == ')':
                pos[0] += 1
            return val
        # number
        start = pos[0]
        while pos[0] < len(expr) and expr[pos[0]].isdigit():
            pos[0] += 1
        if start == pos[0]:
            raise ValueError(f"unexpected character in expression: {expr[pos[0]]}")
        return int(expr[start:pos[0]])

    return parse_expr()


def substitute_index(hi_lo_text, index):
    """Replace (i) in the MW text with the actual index value."""
    return hi_lo_text.replace("(i)", str(index))


def extract_bits(words, hi, lo):
    """Extract bits hi:lo from the 64-word QMD array.

    Bit B of the descriptor is bit (B % 32) of word (B // 32).
    Returns the value as an integer.
    """
    val = 0
    for b in range(lo, hi + 1):
        word_idx = b // 32
        bit_idx = b % 32
        if word_idx < len(words):
            if words[word_idx] & (1 << bit_idx):
                val |= 1 << (b - lo)
    return val


def parse_value(value_str, field_name, named):
    """Parse a reference value string into an integer.

    Handles: hex (0x...), TRUE, FALSE, and named values from the header.
    Rejects unknown named values (F4).
    """
    if value_str.startswith("0x") or value_str.startswith("0X"):
        return int(value_str, 16)
    if value_str == "TRUE":
        return 1
    if value_str == "FALSE":
        return 0
    # Named value: look it up in the header defines
    if value_str in named:
        return named[value_str]
    # Try matching as a suffix of a named value
    for name, val in named.items():
        if name.endswith("_" + value_str) or name == value_str:
            return val
    # F4: unknown named value -- refuse instead of zeroing
    raise ValueError(f"Unknown named value '{value_str}' for field '{field_name}'")


def resolve_field_name(ref_name):
    """Resolve a reference field name to a header field name.

    Reference names like CONSTANT_BUFFER_VALID(7) need the index stripped
    to match the header name CONSTANT_BUFFER_VALID.
    """
    return re.sub(r"\(.*\)$", "", ref_name)


def get_index(ref_name):
    """Extract the index from a reference field name like CONSTANT_BUFFER_VALID(7)."""
    m = re.search(r"\((\d+)\)$", ref_name)
    if m:
        return int(m.group(1))
    return None


def generate_outputs(words, rows, equal_count, diff_count):
    """Generate JSON and markdown output strings."""
    json_output = {
        "words": [f"0x{w:08x}" for w in words],
        "fields": rows,
        "equal": equal_count,
        "different": diff_count,
    }

    md_lines = []
    md_lines.append("# QMD Comparison: Our words vs Reference run\n")
    md_lines.append("## Result\n")
    md_lines.append(
        f"{equal_count} fields match, {diff_count} differ.\n"
    )

    md_lines.append("## Fields that are not zero\n")
    md_lines.append("| Field | Bits | Reference | Ours | Equal |")
    md_lines.append("|-------|------|-----------|------|-------|")
    for row in rows:
        if row["reference_value"] != 0 or row["ours"] != 0:
            ref_hex = f"0x{row['reference_value']:x}"
            ours_hex = f"0x{row['ours']:x}"
            eq = "yes" if row["equal"] else "NO"
            md_lines.append(
                f"| {row['name']} | [{row['hi']}:{row['lo']}] | {ref_hex} | {ours_hex} | {eq} |"
            )

    md_lines.append("")
    md_lines.append("## Differences\n")
    diffs = [r for r in rows if not r["equal"]]
    if diffs:
        md_lines.append("| Field | Bits | Reference | Ours |")
        md_lines.append("|-------|------|-----------|------|")
        for row in diffs:
            ref_hex = f"0x{row['reference_value']:x}"
            ours_hex = f"0x{row['ours']:x}"
            md_lines.append(
                f"| {row['name']} | [{row['hi']}:{row['lo']}] | {ref_hex} | {ours_hex} |"
            )
    else:
        md_lines.append("None.")

    md_lines.append("")

    return json_output, "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(description="Compare QMD words")
    parser.add_argument("--reference", default=REFERENCE_JSON,
                        help="Reference JSON file")
    parser.add_argument("--words", help="Words file (default: run ref_qmd --words)")
    parser.add_argument("--header", default=HEADER_PATH,
                        help="Header file path")
    parser.add_argument("--out-json", default=os.path.join(ANALYSIS_DIR, "qmd_compare.json"),
                        help="JSON output path")
    parser.add_argument("--out-md", default=os.path.join(ANALYSIS_DIR, "qmd_compare.md"),
                        help="Markdown output path")
    parser.add_argument("--verify", action="store_true",
                        help="Verify mode: exit 0 only if inputs valid and files match")
    parser.add_argument("--check", action="store_true",
                        help="Check mode: same as --verify with default paths")

    args = parser.parse_args()

    verify_mode = args.verify or args.check

    # Step 1: Parse the header
    fields, named = parse_header(args.header)
    print(f"Parsed {len(fields)} fields, {len(named)} named values", file=sys.stderr)

    # Step 2: Read words
    if args.words:
        try:
            with open(args.words, "r") as f:
                word_lines = f.read().strip().split("\n")
        except FileNotFoundError:
            print(f"Words file not found: {args.words}", file=sys.stderr)
            sys.exit(1)
    else:
        # Run ref_qmd --words
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_bin = os.path.join(repo_root, "build", "tests", "ref_qmd")

        if not os.path.exists(test_bin):
            subprocess.run(["make", "-s", "-C", "tests"], cwd=repo_root, check=True)

        result = subprocess.run(
            [test_bin, "--words"], capture_output=True, text=True, cwd=repo_root
        )
        if result.returncode != 0:
            print(f"ref_qmd failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        word_lines = result.stdout.strip().split("\n")

    # Validate word count and format (F4)
    words = []
    for wline in word_lines:
        wline = wline.strip()
        if not wline:
            continue
        try:
            w = int(wline, 16)
        except ValueError:
            print(f"Invalid hex word: {wline}", file=sys.stderr)
            sys.exit(1)
        if w > 0xffffffff:
            print(f"Word exceeds 32 bits: {wline}", file=sys.stderr)
            sys.exit(1)
        words.append(w)

    if len(words) != 64:
        print(f"Expected 64 words, got {len(words)}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Read the reference JSON
    try:
        with open(args.reference, "r") as f:
            ref_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Cannot read reference JSON: {e}", file=sys.stderr)
        sys.exit(1)

    qmd_entries = ref_data.get("qmd", [])

    # Check for duplicate field names (F4)
    seen_names = set()
    for entry in qmd_entries:
        ref_name = entry["name"]
        if ref_name in seen_names:
            print(f"Duplicate field name: {ref_name}", file=sys.stderr)
            sys.exit(1)
        seen_names.add(ref_name)

    # Step 4: Compute comparison rows
    rows = []
    equal_count = 0
    diff_count = 0

    for entry in qmd_entries:
        ref_name = entry["name"]
        ref_value_str = entry["value"]

        # Resolve field name and index
        header_name = resolve_field_name(ref_name)
        index = get_index(ref_name)

        # F4: refuse unknown field names
        if header_name not in fields:
            print(f"Unknown field name: {header_name}", file=sys.stderr)
            sys.exit(1)

        hi_lo_text = fields[header_name]

        # Substitute index if present
        if index is not None:
            hi_lo_text = substitute_index(hi_lo_text, index)

        # Parse HI:LO
        parts = hi_lo_text.split(":")
        if len(parts) != 2:
            print(f"Invalid HI:LO format: {hi_lo_text}", file=sys.stderr)
            sys.exit(1)

        try:
            hi = compute_expr(parts[0])
            lo = compute_expr(parts[1])
        except (ValueError, IndexError) as e:
            print(f"Error evaluating HI:LO: {e}", file=sys.stderr)
            sys.exit(1)

        # Parse reference value (F4: refuse unknown named values)
        try:
            ref_value = parse_value(ref_value_str, ref_name, named)
        except ValueError as e:
            print(f"{e}", file=sys.stderr)
            sys.exit(1)

        # Extract our value
        ours = extract_bits(words, hi, lo)

        is_equal = (ours == ref_value)
        if is_equal:
            equal_count += 1
        else:
            diff_count += 1

        rows.append(
            {
                "name": ref_name,
                "hi": hi,
                "lo": lo,
                "reference": ref_value_str,
                "reference_value": ref_value,
                "ours": ours,
                "equal": is_equal,
            }
        )

    # Generate outputs
    json_output, md_output = generate_outputs(words, rows, equal_count, diff_count)

    # Step 5: Handle verify vs generate mode
    if verify_mode:
        # Read existing files and compare
        try:
            with open(args.out_json, "r") as f:
                existing_json = json.load(f)
            with open(args.out_md, "r") as f:
                existing_md = f.read()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Cannot read output files for verification: {e}", file=sys.stderr)
            sys.exit(1)

        # Verify all fields match and output files are correct
        if diff_count != 0:
            print(f"Verification failed: {diff_count} fields differ", file=sys.stderr)
            sys.exit(1)

        # Compare JSON
        if json.dumps(json_output, sort_keys=True) != json.dumps(
            existing_json, sort_keys=True
        ):
            print("Verification failed: JSON output differs", file=sys.stderr)
            sys.exit(1)

        # Compare Markdown
        if md_output != existing_md:
            print("Verification failed: Markdown output differs", file=sys.stderr)
            sys.exit(1)

        print(f"Verification passed: {equal_count} fields match", file=sys.stderr)
        sys.exit(0)

    # Generate mode: write files
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(json_output, f, indent=2)
        f.write("\n")

    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write(md_output)

    print(f"qmd_compare: {equal_count} match, {diff_count} differ", file=sys.stderr)


if __name__ == "__main__":
    main()
