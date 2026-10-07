#!/usr/bin/env python3
"""B6 tool: extract the compute launch path from Mesa's Nouveau driver.

Reads pinned source in reference/mesa/ and produces:
  - analysis/compute_launch.json
  - analysis/compute_launch.md

Usage:
  python3 tools/compute_launch.py           # generate
  python3 tools/compute_launch.py --check   # verify output matches tool
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESA = os.path.join(ROOT, "reference", "mesa",
                    "src", "gallium", "drivers", "nouveau")
NVE4_COMPUTE_C = os.path.join(MESA, "nvc0", "nve4_compute.c")
NVE4_COMPUTE_XML = os.path.join(MESA, "nvc0", "nve4_compute.xml.h")
CLA0C0_QMD_H = os.path.join(MESA, "nvc0", "cla0c0qmd.h")
NV_OBJECT_XML_H = os.path.join(MESA, "nv_object.xml.h")
OUT_JSON = os.path.join(ROOT, "analysis", "compute_launch.json")
OUT_MD = os.path.join(ROOT, "analysis", "compute_launch.md")

# ---------------------------------------------------------------------------
# Compute class constants for GK110 branch resolution
# ---------------------------------------------------------------------------
GK110_COMPUTE_CLASS = 0x0000a1c0  # NVF0_COMPUTE_CLASS
GV100_COMPUTE_CLASS = 0x0000c3c0
GP100_COMPUTE_CLASS = 0x0000c0c0
GA102_COMPUTE_CLASS = 0x0000d1c0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_file(path):
    with open(path, errors="replace") as fh:
        return fh.read()


def find_function(source, func_name):
    """Return (start_line, end_line, body_text) for *func_name*."""
    lines = source.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.search(r'\b' + re.escape(func_name) + r'\s*\(', line):
            start = i + 1  # 1-based
            break
    if start is None:
        return 0, 0, ""
    depth = 0
    brace_start = None
    for i in range(start - 1, len(lines)):
        for ch in lines[i]:
            if ch == '{':
                depth += 1
                if brace_start is None:
                    brace_start = i + 1
            elif ch == '}':
                depth -= 1
        if depth == 0 and brace_start is not None:
            end = i + 1  # 1-based inclusive
            body = "\n".join(lines[start - 1:end])
            return start, end, body
    return start, len(lines), "\n".join(lines[start - 1:])


def resolve_method_name(raw):
    """Strip SUBC_CP(), NVE4_CP() etc. to get the bare method name.

    Returns (name, param_or_None).
    Hex literals (0x...) are returned as-is (lowercase).
    Named values are uppercased.
    """
    raw = raw.strip()

    # Handle SUBC_CP(hex_value) — return hex as-is (lowercase)
    m = re.match(r'^SUBC_CP\s*\(\s*(0x[0-9a-fA-F]+)\s*\)$', raw, re.I)
    if m:
        return m.group(1).lower(), None

    # Handle SUBC_CP(NAME) — uppercase the name
    m = re.match(r'^SUBC_CP\s*\(\s*(\w+)\s*\)$', raw, re.I)
    if m:
        return m.group(1).upper(), None

    # Handle NVE4_CP(NAME)  or  NVE4_CP(NAME(i))
    m = re.match(r'^NVE4_CP\s*\(\s*(\w+)(?:\(([^)]*)\))?\s*\)$', raw, re.I)
    if m:
        return m.group(1).upper(), m.group(2)

    # Bare name
    m = re.match(r'^(\w+)$', raw.strip(), re.I)
    if m:
        return m.group(1).upper(), None

    return raw, None


def lookup_offset(method_name, param):
    """Look up NVE4_COMPUTE_XXX offset from xml.h.

    Returns (hex_str, None|formula).  Hex.h uses tabs not '='.
    """
    src = read_file(NVE4_COMPUTE_XML)
    lines = src.split("\n")
    for line in lines:
        line = line.strip()
        m = re.match(
            r'#define\s+NVE4_COMPUTE_' + re.escape(method_name) + r'\b', line)
        if m:
            # Value is a hex literal after whitespace (tabs/spaces, no '=')
            val_m = re.search(r'(0x[0-9a-fA-F]+)', line)
            if val_m:
                return val_m.group(1).lower(), None
            # Parameterized formula: NVE4_CP(FIELD(i0)) -> (0x... + ...)
            formula_m = re.search(r'\(\s*([^)]+)\s*\)', line)
            if formula_m and param:
                formula = formula_m.group(1)
                expr = formula.replace('i0', param)
                try:
                    val = int(expr, 16)
                    return "0x{:08x}".format(val), formula
                except ValueError:
                    pass
    return None, None


def lookup_qmd_bits(field_name):
    """Look up NVA0C0_QMDV00_06_FIELDNAME MW(hi:lo) from cla0c0qmd.h."""
    src = read_file(CLA0C0_QMD_H)
    m = re.search(
        r'#define\s+NVA0C0_QMDV00_06_' + re.escape(field_name) +
        r'\s+MW\((\d+):(\d+)\)',
        src
    )
    if m:
        return m.group(1), m.group(2)
    return None, None


def check_gk110_branch(var, op, val):
    """Check if a conditional branch is taken when oclass == GK110 (NVF0)."""
    if op == "<":
        if "GV100" in val:
            return True   # GK110 < GV100
        if "GA102" in val:
            return True   # GK110 < GA102
    if op == ">=":
        if "NVF0" in val:
            return True   # GK110 >= NVF0
        if "GP100" in val:
            return False  # GK110 < GP100
        if "GV100" in val:
            return False  # GK110 < GV100
    if op == "==":
        if "NVF0" in val:
            return True
    return False


# ---------------------------------------------------------------------------
# Condition / preprocessor stack helpers
# ---------------------------------------------------------------------------

METHOD_MACROS = ("BEGIN_NVC0", "BEGIN_1IC0", "BEGIN_NIC0", "IMMED_NVC0")
COND_PAT = re.compile(
    r'if\s*\(\s*(\w+(?:[-.]\w+)*)\s*(<|>|==|!=|>=|<=)\s*(\w+(?:_\w+)?)')


def extract_methods_with_branch_filter(lines, abs_start, abs_end):
    """Extract method calls from a range of source lines, GK110-filtered.

    Tracks:
      - if / else / else-if blocks with brace guards
      - #if / #endif preprocessor blocks
      - /* ... */ comment blocks

    Returns list of dicts with method, offset, formula, count, file, line, macro.
    """
    full_src = read_file(NVE4_COMPUTE_C)
    abs_lines = full_src.split("\n")

    methods = []
    in_block_comment = False
    in_preprocessor = False       # inside #if … #endif
    if_depth = 0                   # number of open if-else blocks (brace-gated)
    cond_stack = []               # GK110-taken status per open block

    for abs_line in range(abs_start, abs_end + 1):
        raw_line = abs_lines[abs_line - 1]
        stripped = raw_line.strip()

        # ---- preprocessor directives ----
        if re.match(r'#\s*(ifdef|ifndef|if)\b', stripped):
            in_preprocessor = True
            continue
        if re.match(r'#\s*endif\b', stripped):
            in_preprocessor = False
            continue
        if in_preprocessor:
            continue

        # ---- block comments ----
        if '/*' in stripped and '*/' not in stripped:
            in_block_comment = True
            continue
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue
        if '/*' in stripped and '*/' in stripped:
            after = stripped[stripped.index('*/') + 2:].strip()
            if not after:
                continue
            stripped = after

        if not stripped:
            continue

        # ---- if / else / else-if tracking (only brace-gated) ----
        m_if = COND_PAT.search(stripped)
        if m_if and re.search(r'\{', stripped) and not re.search(r'BEGIN_', stripped):
            var, op, val = m_if.group(1), m_if.group(2), m_if.group(3)
            gk110 = check_gk110_branch(var, op, val)
            cond_stack.append(gk110)
            if_depth += 1
            continue

        m_else = re.match(r'\}\s*else\s*\{', stripped)
        if m_else and if_depth > 0:
            cond_stack[-1] = not cond_stack[-1]
            # if_depth stays (else replaces the if's block)
            continue

        m_else_if = re.match(r'\}\s*else\s*if\s*\(', stripped)
        if m_else_if and if_depth > 0:
            cond_stack[-1] = not cond_stack[-1]
            m2 = COND_PAT.search(stripped[m_else_if.end():])
            if m2:
                gk110 = check_gk110_branch(m2.group(1), m2.group(2),
                                           m2.group(3))
                cond_stack.append(gk110)
                if_depth += 1
            continue

        # Standalone } that closes an if-else block
        if stripped == '}' and if_depth > 0:
            cond_stack.pop()
            if_depth -= 1
            continue

        # ---- extract method calls ----
        gk110_active = all(cond_stack) if cond_stack else True

        for macro_name in METHOD_MACROS:
            pat = (macro_name +
                   r'\s*\(\s*push\s*,\s*([^,]+)\s*,\s*(\d+)\s*\)')
            m = re.search(pat, stripped)
            if m:
                raw_method = m.group(1)
                count = int(m.group(2))
                method_name, param = resolve_method_name(raw_method)
                offset, formula = lookup_offset(method_name, param)
                methods.append({
                    "method": method_name,
                    "offset": offset,
                    "formula": formula,
                    "count": count,
                    "file": ("reference/mesa/src/gallium/drivers/nouveau/"
                             "nvc0/nve4_compute.c"),
                    "line": abs_line,
                    "macro": macro_name,
                })
                break  # only one method per macro call

    return methods


# ---------------------------------------------------------------------------
# Extract: nve4_screen_compute_setup (GK110 path)
# ---------------------------------------------------------------------------

def extract_compute_setup():
    """Extract method calls from nve4_screen_compute_setup, GK110 path only."""
    full_src = read_file(NVE4_COMPUTE_C)
    abs_start, abs_end, _ = find_function(full_src,
                                          "nve4_screen_compute_setup")
    return extract_methods_with_branch_filter(full_src, abs_start, abs_end)


# ---------------------------------------------------------------------------
# Extract: nve4_compute_setup_launch_desc (descriptor fields)
# ---------------------------------------------------------------------------

def extract_descriptor_fields():
    """Extract QMD field definitions from nve4_compute_setup_launch_desc."""
    full_src = read_file(NVE4_COMPUTE_C)
    abs_start, abs_end, _ = find_function(
        full_src, "nve4_compute_setup_launch_desc")
    abs_lines = full_src.split("\n")
    fields = []

    for abs_line in range(abs_start, abs_end + 1):
        raw_line = abs_lines[abs_line - 1]
        stripped = raw_line.strip()
        if not stripped:
            continue

        # DEF_SET: NVA0C0_QMDV00_06_DEF_SET(qmd, FIELD, VALUE)
        m = re.search(
            r'NVA0C0_QMDV00_06_DEF_SET\s*\(\s*qmd\s*,\s*(\w+)\s*,\s*(\w+)\s*\)',
            stripped)
        if m:
            field_name = m.group(1)
            value = m.group(2)
            hi, lo = lookup_qmd_bits(field_name)
            fields.append({
                "field": field_name,
                "bits": hi + ":" + lo if hi and lo else None,
                "value": value,
                "type": "DEF_SET",
                "file": ("reference/mesa/src/gallium/drivers/nouveau/"
                         "nvc0/nve4_compute.c"),
                "line": abs_line,
            })
            continue

        # VAL_SET: NVA0C0_QMDV00_06_VAL_SET(qmd, FIELD, VALUE)
        m = re.search(
            r'NVA0C0_QMDV00_06_VAL_SET\s*\(\s*qmd\s*,\s*(\w+)\s*,\s*'
            r'([^)]+)\s*\)',
            stripped)
        if m:
            field_name = m.group(1)
            value = m.group(2).strip()
            hi, lo = lookup_qmd_bits(field_name)
            fields.append({
                "field": field_name,
                "bits": hi + ":" + lo if hi and lo else None,
                "value": value,
                "type": "VAL_SET",
                "file": ("reference/mesa/src/gallium/drivers/nouveau/"
                         "nvc0/nve4_compute.c"),
                "line": abs_line,
            })

    return fields


# ---------------------------------------------------------------------------
# Extract: nve4_launch_grid (GK110 path)
# ---------------------------------------------------------------------------

def extract_launch_grid():
    """Extract the GK110 launch sequence from nve4_launch_grid.

    GK110 path:
      - oclass < GA102_COMPUTE_CLASS → True: LAUNCH with 0x3
      - else (GP100+/GA102+) branch is NOT taken.
    """
    full_src = read_file(NVE4_COMPUTE_C)
    abs_start, abs_end, _ = find_function(full_src, "nve4_launch_grid")
    return extract_methods_with_branch_filter(full_src, abs_start, abs_end)


# ---------------------------------------------------------------------------
# Extract compute class
# ---------------------------------------------------------------------------

def extract_compute_class():
    src = read_file(NV_OBJECT_XML_H)
    m = re.search(r'#define\s+NVF0_COMPUTE_CLASS\s+(0x[0-9a-fA-F]+)', src)
    if m:
        return m.group(1).lower()
    return None


# ---------------------------------------------------------------------------
# Kernel needs (derived from analysis)
# ---------------------------------------------------------------------------

def kernel_needs():
    return [
        "SASS version 0x30 (GK110 compute shader ISA)",
        "QMD v0.0.6 format (a0c0 class)",
        "512-byte launch descriptor buffer (256-word QMD)",
        "MP temporary memory per-SM (screen->tls)",
        "TIC (texture instruction cache) table",
        "TSC (texture sampler cache) table",
        "Unified constant buffer for compute",
        "Text section (code) with GPU-addressable offset",
    ]


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def build_json():
    compute_class = extract_compute_class()
    setup = extract_compute_setup()
    launch = extract_launch_grid()
    descriptor_fields = extract_descriptor_fields()

    def clean_method(m):
        out = {
            "method": m["method"],
            "file": m["file"],
            "line": m["line"],
            "macro": m["macro"],
            "count": m["count"],
        }
        if m["offset"] is not None:
            out["offset"] = m["offset"]
        else:
            out["offset"] = None
        if m.get("formula"):
            out["formula"] = m["formula"]
        return out

    def clean_field(f):
        out = {
            "field": f["field"],
            "file": f["file"],
            "line": f["line"],
            "type": f["type"],
            "value": f["value"],
        }
        if f["bits"]:
            out["bits"] = f["bits"]
        return out

    result = {
        "compute_class": compute_class,
        "class_source": ("reference/mesa/src/gallium/drivers/nouveau/"
                         "nv_object.xml.h"),
        "setup": [clean_method(m) for m in setup],
        "launch": [clean_method(m) for m in launch],
        "descriptor_fields": [clean_field(f) for f in descriptor_fields],
        "kernel_needs": kernel_needs(),
    }
    return result


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def build_md(data):
    lines = []
    lines.append("# Compute Launch Path (GK110 / K40c)")
    lines.append("")
    lines.append("Source: Mesa Nouveau driver, pinned in `reference/mesa/`.")
    lines.append("")

    # Class
    lines.append("## Compute Class")
    lines.append("")
    lines.append(f"- Class: `{data['compute_class']}` (`NVF0_COMPUTE_CLASS`)")
    lines.append(f"- Source: `{data['class_source']}`")
    lines.append("")

    # Setup methods
    lines.append("## Setup Methods (`nve4_screen_compute_setup`)")
    lines.append("")
    lines.append("| # | Method | Offset | Macro | Count | Line |")
    lines.append("|---|--------|--------|-------|-------|------|")
    for i, m in enumerate(data["setup"], 1):
        off = m.get("offset") or "N/A"
        lines.append(
            f"| {i} | `{m['method']}` | `{off}` | `{m['macro']}`"
            f" | {m['count']} | {m['file']}:{m['line']} |")
    lines.append("")

    # Descriptor fields
    lines.append(
        "## Launch Descriptor Fields (`nve4_compute_setup_launch_desc`)")
    lines.append("")
    lines.append("| # | Field | Bits | Type | Value | Line |")
    lines.append("|---|-------|------|------|-------|------|")
    for i, f in enumerate(data["descriptor_fields"], 1):
        bits = f.get("bits") or "N/A"
        lines.append(
            f"| {i} | `{f['field']}` | {bits} | `{f['type']}`"
            f" | `{f['value']}` | {f['file']}:{f['line']} |")
    lines.append("")

    # Launch methods
    lines.append(
        "## Launch Methods (`nve4_launch_grid`, GK110 path)")
    lines.append("")
    lines.append("| # | Method | Offset | Macro | Count | Line |")
    lines.append("|---|--------|--------|-------|-------|------|")
    for i, m in enumerate(data["launch"], 1):
        off = m.get("offset") or "N/A"
        lines.append(
            f"| {i} | `{m['method']}` | `{off}` | `{m['macro']}`"
            f" | {m['count']} | {m['file']}:{m['line']} |")
    lines.append("")

    # Kernel needs
    lines.append("## Kernel Requirements")
    lines.append("")
    for need in data["kernel_needs"]:
        lines.append(f"- {need}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Check mode
# ---------------------------------------------------------------------------

def check_mode():
    """Regenerate JSON and compare with existing file."""
    existing = None
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON) as fh:
            existing = fh.read()

    data = build_json()
    regenerated = json.dumps(data, indent=2) + "\n"

    if existing != regenerated:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        with open(OUT_JSON, "w") as fh:
            fh.write(regenerated)
        print("compute_launch.py --check: regenerated analysis/compute_launch.json")
        return 1
    else:
        print("compute_launch.py --check: OK — output matches")
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="B6: Compute launch path extraction")
    parser.add_argument("--check", action="store_true",
                        help="Verify output matches tool generation")
    args = parser.parse_args()

    if args.check:
        sys.exit(check_mode())

    data = build_json()
    md = build_md(data)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)

    with open(OUT_JSON, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    with open(OUT_MD, "w") as fh:
        fh.write(md)

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
