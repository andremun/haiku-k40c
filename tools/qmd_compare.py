#!/usr/bin/env python3
# qmd_compare.py — compare our QMD words against the reference run.
# Distributed under the terms of the MIT License.
#
# Reads the Nouveau header at runtime, runs ref_qmd --words,
# reads the reference JSON, and writes comparison files.

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


def eval_expr(expr):
    """Evaluate an arithmetic expression that may contain (i)*n style terms.

    The expression uses only digits, parentheses, +, *, and whitespace.
    """
    # Replace any remaining (i) with nothing — by the time this is called,
    # indices should already be substituted.
    expr = expr.replace("(", " (").replace(")", ") ")
    # Clean up multiple spaces
    expr = " ".join(expr.split())
    return eval(expr)


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
    """
    if value_str.startswith("0x") or value_str.startswith("0X"):
        return int(value_str, 16)
    if value_str == "TRUE":
        return 1
    if value_str == "FALSE":
        return 0
    # Named value: look it up in the header defines
    # The value might be like "DIRECTLY_ADDRESSABLE_MEMORY_SIZE_16KB"
    # which corresponds to NVA0C0_QMDV00_06_<FIELD_NAME>_<VALUE>
    # Try exact match first
    if value_str in named:
        return named[value_str]
    # Try matching as a suffix of a named value
    for name, val in named.items():
        if name.endswith("_" + value_str) or name == value_str:
            return val
    # Fallback: try to parse as hex without prefix
    try:
        return int(value_str, 16)
    except ValueError:
        return 0


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


def main():
    check_mode = "--check" in sys.argv

    # Step 1: Parse the header
    fields, named = parse_header(HEADER_PATH)
    print(f"Parsed {len(fields)} fields, {len(named)} named values", file=sys.stderr)

    # Step 2: Run ref_qmd --words
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

    words = []
    for line in result.stdout.strip().split("\n"):
        words.append(int(line.strip(), 16))

    # Step 3: Read the reference JSON
    with open(REFERENCE_JSON, "r") as f:
        ref_data = json.load(f)

    qmd_entries = ref_data.get("qmd", [])

    # Step 4: Compute comparison rows
    rows = []
    equal_count = 0
    diff_count = 0

    for entry in qmd_entries:
        ref_name = entry["name"]
        ref_value_str = entry["value"]
        ref_value = parse_value(ref_value_str, ref_name, named)

        # Resolve field name and index
        header_name = resolve_field_name(ref_name)
        index = get_index(ref_name)

        if header_name not in fields:
            # Skip fields not found in header (shouldn't happen for V00_06)
            continue

        hi_lo_text = fields[header_name]

        # Substitute index if present
        if index is not None:
            hi_lo_text = substitute_index(hi_lo_text, index)

        # Parse HI:LO
        parts = hi_lo_text.split(":")
        if len(parts) != 2:
            continue
        hi = eval_expr(parts[0])
        lo = eval_expr(parts[1])

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

    # Step 5: Write JSON output
    json_output = {
        "words": [f"0x{w:08x}" for w in words],
        "fields": rows,
        "equal": equal_count,
        "different": diff_count,
    }

    json_path = os.path.join(ANALYSIS_DIR, "qmd_compare.json")
    md_path = os.path.join(ANALYSIS_DIR, "qmd_compare.md")

    if check_mode:
        # Read existing files and compare
        try:
            with open(json_path, "r") as f:
                existing_json = json.load(f)
            with open(md_path, "r") as f:
                existing_md = f.read()
            if json.dumps(json_output, sort_keys=True) == json.dumps(
                existing_json, sort_keys=True
            ):
                sys.exit(0)
            else:
                sys.exit(1)
        except (FileNotFoundError, json.JSONDecodeError):
            sys.exit(1)

    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2)
        f.write("\n")

    # Step 6: Write markdown output
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

    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))

    print(f"qmd_compare: {equal_count} match, {diff_count} differ", file=sys.stderr)


if __name__ == "__main__":
    main()
