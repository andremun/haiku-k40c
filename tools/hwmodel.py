#!/usr/bin/env python3
"""Generate hardware model JSON and Markdown for subsystem models (task C3a).

Reads the Nouveau source to extract function tables and their members for
each of the six subsystems, then writes analysis/hwmodel/<sub>.json and
docs/hardware-model/<sub>.md.

Usage:
    python3 tools/hwmodel.py              # write all JSON + Markdown
    python3 tools/hwmodel.py --check      # verify output matches, exit 0
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
HWMODEL_DIR = os.path.join(ROOT, "analysis", "hwmodel")
DOCS_DIR = os.path.join(ROOT, "docs", "hardware-model")

# The six subsystems for task C3a
C3A_SUBSYSTEMS = ["mc", "bar", "imem", "mmu", "fb", "top",
                  "privring", "ltc", "timer",  # C3b
                  "fifo",  # C3c
                  "chan"]  # C3d

# A model of a table that is not a chipset member: name -> (owning
# subsystem, table). Added by the scaffold for task C3d.
EXTRA = {"chan": ("fifo", "gk110_chan")}

# Constructor function names and their table names (from nvf1_chipset in base.c)
# These are looked up dynamically from the chipset table.


def src_lines(rel):
    """Return lines of a Nouveau source file, or None if not found."""
    path = os.path.join(NV, rel)
    try:
        with open(path, errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return None


def nvkm_definitions():
    """Map each function/table name to its (file, line) definition.

    Definitions in nvkm source:
    - Function: line starting with `name(` (possibly with static/const)
    - Table: line starting with `name = {`
    Returns (src_map, def_map) where src_map maps relative path to content
    and def_map maps ("F", name) or ("T", name) to (rel, line).
    """
    src, defs = {}, {}
    for path in glob.glob(os.path.join(NV, "nvkm", "**", "*.c"), recursive=True):
        rel = os.path.relpath(path, NV)
        content = open(path, errors="replace").read()
        src[rel] = content
        for i, line in enumerate(content.splitlines(), 1):
            # Function definition: name(args)
            m = re.match(r"^(?:static\s+)?(?:const\s+)?(\w+)\s*\(", line)
            if m:
                defs.setdefault(("F", m.group(1)), (rel, i))
            # Table definition: name = {  (matches check_repo.py's regex exactly)
            m = re.match(r"^(\w+)\s*=\s*\{", line)
            if m:
                defs.setdefault(("T", m.group(1)), (rel, i))
    return src, defs


def chipset_table():
    """Parse nvf1_chipset from base.c and return {subsystem: (ctor_name, line)}.

    Also return the constructor body text for each subsystem.
    """
    lines = src_lines("nvkm/engine/device/base.c") or []
    result, inside, ctor_bodies = {}, False, {}
    for i, line in enumerate(lines, 1):
        if line.startswith("nvf1_chipset"):
            inside = True
        elif inside and line.startswith("};"):
            break
        elif inside:
            m = re.match(r"\s*\.(\w+)\s*=\s*\{\s*0x[0-9a-f]+,\s*(\w+)\s*\}", line)
            if m:
                result[m.group(1)] = m.group(2)
                # Capture the constructor body for finding the table reference
    # Now parse constructor bodies
    for sub, ctor in result.items():
        info = defs.get(("F", ctor))
        if info:
            cf, cl = info
            L = src_lines(cf) or []
            a = cl
            while a <= len(L) and not L[a - 1].startswith("}"):
                a += 1
            ctor_bodies[sub] = (cf, cl, a)
    return result, ctor_bodies


def find_table_ref(ctor_body):
    """Find the first &NAME reference in a constructor body where NAME is a table.

    Returns (table_name, file, line) or None.
    """
    cf, cl, end = ctor_body
    L = src_lines(cf) or []
    body_text = "\n".join(L[cl - 1:end])
    # Find &NAME where NAME is a known table
    for m in re.finditer(r"&(\w+)", body_text):
        name = m.group(1)
        if ("T", name) in defs:
            tf, tl = defs[("T", name)]
            return name, tf, tl
    return None


def extract_table_members(table_name, parent=None):
    """Extract members of a function table.

    For each line matching `.member = &?value`, record member and value.
    If value is a defined function, kind="function" and look up its definition.
    If value is a defined table, kind="table" and recurse (only if parent is None).
    Returns list of member dicts.
    """
    f, ln = defs[("T", table_name)]
    L = src_lines(f) or []
    # Body runs from ln to the next line starting with }
    a = ln
    while a <= len(L) and not L[a - 1].startswith("}"):
        a += 1

    members = []
    for i in range(a - ln):
        line = L[ln - 1 + i]
        m = re.match(r"\s*\.([\w.]+)\s*=\s*&?(\w+)", line)
        if not m:
            continue
        member_name, value = m.group(1), m.group(2)

        if ("F", value) in defs:
            kind = "function"
            vf, vl = defs[("F", value)]
        elif ("T", value) in defs:
            kind = "table"
            vf, vl = defs[("T", value)]
        else:
            kind = "value"
            vf, vl = None, None

        # Look up accesses for function members
        accesses = []
        if kind == "function":
            accesses = sorted(
                c3_acc.get((value, vf), []), key=lambda x: x["line"]
            )

        entry = {
            "member": member_name,
            "value": value,
            "kind": kind,
            "file": vf,
            "line": vl,
            "parent": parent,
            "accesses": accesses,
        }
        members.append(entry)

        # If it's a table and parent is None (top-level member), recurse
        if kind == "table" and parent is None:
            members += extract_table_members(value, member_name)

    return members


# Globals populated at load time
defs = {}
src_map = {}
c3_acc = {}
chip_map = {}


def build_accesses_map():
    """Build { (function_name, file) : [access dicts] } from mmio_accesses.json."""
    acc_path = os.path.join(ROOT, "registers", "mmio_accesses.json")
    if not os.path.exists(acc_path):
        return {}
    with open(acc_path) as f:
        accesses = json.load(f)
    result = {}
    for a in accesses:
        key = (a["function"], a["file"])
        result.setdefault(key, []).append({
            "file": a["file"],
            "line": a["line"],
            "op": a["op"],
            "reg": a["reg"],
        })
    return result


def generate_json(subsystem, ctor_name, ctor_info, table_name, table_info, members):
    """Generate the full JSON object for a subsystem.

    ctor_name/ctor_info: the chipset constructor function (e.g., gk104_mc_new).
    table_name/table_info: the function table referenced by &NAME in the ctor.
    """
    return {
        "subsystem": subsystem,
        "constructor": {"name": ctor_name, "file": ctor_info[0], "line": ctor_info[1]},
        "table": {"name": table_name, "file": table_info[0], "line": table_info[1]},
        "members": members,
        "depends_on": [],  # Placeholder - filled by the author
        "summary": "",     # Placeholder - filled by the author
    }


def generate_markdown(hw):
    """Generate Markdown from a subsystem JSON object."""
    lines = []
    lines.append(f"# {hw['subsystem']}: Hardware Model")
    lines.append("")
    lines.append("## Purpose")
    lines.append(hw.get("summary", "(not written)"))
    lines.append("")
    lines.append("## Nouveau files")
    lines.append("")
    ctor = hw["constructor"]
    tbl = hw["table"]
    lines.append(f"- Constructor: **{ctor['name']}** (`{ctor['file']}:{ctor['line']}`)")
    lines.append(f"- Function table: **{tbl['name']}** (`{tbl['file']}:{tbl['line']}`)")
    lines.append("")
    lines.append("## Members")
    lines.append("")
    lines.append("| Member | Function | Role | Needed | Registers |")
    lines.append("|--------|----------|------|--------|-----------|")
    for m in hw["members"]:
        fn = m.get("value", "-")
        role = m.get("role", "")
        needed = str(m.get("needed_for_compute", ""))
        nregs = len(m.get("accesses", []))
        lines.append(f"| {m['member']} | {fn} | {role} | {needed} | {nregs} |")
    lines.append("")
    lines.append("## Dependencies")
    deps = hw.get("depends_on", [])
    if deps:
        lines.append(", ".join(deps))
    else:
        lines.append("(none identified)")
    lines.append("")

    # Certainty sections
    for certainty in ("KNOWN", "INFERRED", "UNKNOWN"):
        entries = [m for m in hw["members"] if m.get("certainty") == certainty]
        lines.append(f"## {certainty}")
        lines.append("")
        if entries:
            for e in entries:
                what = e.get("what", "(no description)")
                src = ""
                if e.get("file"):
                    src = f" (`{e['file']}:{e['line']}`)"
                lines.append(f"- **{e['member']}**: {what}{src}")
        else:
            lines.append("(none)")
        lines.append("")

    return "\n".join(lines)


def apply_decisions(hw):
    """Merge the hand-written decisions into the generated structure.

    analysis/hwmodel/decisions/<subsystem>.json is written by hand and this
    tool never writes it:
        {"summary": "...", "depends_on": ["top"],
         "members": {"init": {"role": ..., "needed_for_compute": ..., "what": ...,
                              "certainty": ..., "evidence": {"line": ..., "quote": ...}},
                     "intr.pending": {...}}}
    The key of a nested member is "<parent>.<member>". (Added by the scaffold.)
    """
    path = os.path.join(ROOT, "analysis", "hwmodel", "decisions", hw["subsystem"] + ".json")
    dec = {}
    if os.path.exists(path):
        with open(path) as f:
            dec = json.load(f)
    hw["summary"] = dec.get("summary", "")
    hw["depends_on"] = dec.get("depends_on", [])
    for m in hw["members"]:
        key = (m["parent"] + "." if m.get("parent") else "") + m["member"]
        d = dec.get("members", {}).get(key, {})
        for k in ("role", "needed_for_compute", "what", "certainty"):
            m[k] = d.get(k)
        if "evidence" in d:
            m["evidence"] = d["evidence"]


def generate_all():
    """Generate all JSON and Markdown files."""
    global defs, src_map, c3_acc, chip_map

    # Load definitions
    src_map, defs = nvkm_definitions()
    c3_acc = build_accesses_map()
    chip_map, ctor_bodies = chipset_table()

    results = {}

    for sub in C3A_SUBSYSTEMS:
        owner = EXTRA[sub][0] if sub in EXTRA else sub
        ctor = chip_map.get(owner)
        if not ctor:
            print(f"warning: no chipset entry for '{sub}'", file=sys.stderr)
            continue
        info = defs.get(("F", ctor))
        if not info:
            print(f"warning: no definition for constructor '{ctor}'", file=sys.stderr)
            continue
        cf, cl = info

        # Find the table reference in the constructor
        table_ref_info = find_table_ref(ctor_bodies.get(owner, (cf, cl, cl + 1)))
        if sub in EXTRA:
            table_ref_info = (EXTRA[sub][1],) + tuple(defs[("T", EXTRA[sub][1])])
        if not table_ref_info:
            print(f"warning: no function table found in {ctor}", file=sys.stderr)
            continue
        table_name, tf, tl = table_ref_info

        # Extract members
        members = extract_table_members(table_name)

        # Generate JSON (without decisions)
        # ctor_info and table_info are (file, line) tuples
        ctor_info = (cf, cl)
        table_info = (tf, tl)
        hw = generate_json(sub, ctor, ctor_info, table_name, table_info, members)
        apply_decisions(hw)

        # Generate Markdown
        md = generate_markdown(hw)

        results[sub] = (hw, md)

    return results


def write_output():
    """Write JSON and Markdown files."""
    os.makedirs(HWMODEL_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    results = generate_all()

    for sub, (hw, md) in sorted(results.items()):
        json_path = os.path.join(HWMODEL_DIR, f"{sub}.json")
        md_path = os.path.join(DOCS_DIR, f"{sub}.md")

        with open(json_path, "w") as f:
            json.dump(hw, f, indent=2)
            f.write("\n")

        with open(md_path, "w") as f:
            f.write(md)

    return results


def check_output():
    """Verify output matches what the tool generates."""
    # First, save current output
    os.makedirs(HWMODEL_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    results = generate_all()

    failures = []
    for sub, (hw, md) in sorted(results.items()):
        json_path = os.path.join(HWMODEL_DIR, f"{sub}.json")
        md_path = os.path.join(DOCS_DIR, f"{sub}.md")

        # Compare JSON
        if os.path.exists(json_path):
            with open(json_path) as f:
                existing = f.read()
            expected = json.dumps(hw, indent=2) + "\n"
            if existing != expected:
                failures.append(f"{sub}.json: content mismatch")
        else:
            failures.append(f"{sub}.json: missing")

        # Compare Markdown
        if os.path.exists(md_path):
            with open(md_path) as f:
                existing = f.read()
            if existing != md:
                failures.append(f"{sub}.md: content mismatch")
        else:
            failures.append(f"{sub}.md: missing")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    if "--check" in sys.argv:
        ok = check_output()
        sys.exit(0 if ok else 1)
    else:
        write_output()
        print("Generated hwmodel JSON and Markdown for subsystems.")
