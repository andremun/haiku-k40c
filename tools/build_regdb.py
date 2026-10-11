#!/usr/bin/env python3
"""Build the register database YAML files for task C1.

Reads registers/mmio_accesses.json, groups entries by subsystem,
looks up each register in the envytools rnndb, and writes
hardware/registers/<group>.yaml files.

Usage:
    python3 tools/build_regdb.py            # write all files
    python3 tools/build_regdb.py --check    # verify files match, exit 0 if ok
"""
import copy
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import rnndb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_accesses():
    """Load and return the mmio_accesses.json entries."""
    with open(os.path.join(ROOT, "registers", "mmio_accesses.json")) as f:
        return json.load(f)


def parse_macros():
    """Parse gk100.h macro definitions for address calculation."""
    header = os.path.join(ROOT, "reference", "nouveau", "nvkm", "engine", "gr", "gf100.h")
    macros = {}
    for line in open(header):
        m = re.match(r"#define\s+(\w+)\(([\w, ]+)\)\s+(\(.*\))\s*$", line)
        if m:
            names = [a.strip() for a in m.group(2).split(",")]
            macros[m.group(1)] = (names, m.group(3))
    return macros


def calc_address(reg_text, macros):
    """Extract a numeric address from a reg string.

    Rules (from C1.md):
    1. Starts with hex number: return that number.
    2. Is a macro call (GPC_UNIT, ROP_BCAST, etc.): evaluate with all vars=0.
    3. Everything else: return None.
    """
    # Rule 1: starts with hex
    m = re.match(r"0x[0-9a-fA-F]+", reg_text)
    if m:
        return int(m.group(0), 16)

    # Rule 2: macro call
    m = re.fullmatch(r"(\w+)\((.*)\)", reg_text)
    if m and m.group(1) in macros:
        names, body = macros[m.group(1)]
        args = [a.strip() for a in m.group(2).split(",")]
        if len(args) != len(names):
            return None
        # Step 1: substitute macro parameter names in body with their args
        for n, a in zip(names, args):
            body = re.sub(r"\(%s\)" % n, "(" + a + ")", body)
        # Step 2: replace all remaining variable names with 0
        body = re.sub(
            r"\b[A-Za-z_]\w*(->\w+)*", "0",
            body,
        )
        # Step 3: convert hex literals to decimal for eval
        body = re.sub(
            r"0x[0-9a-fA-F]+",
            lambda h: str(int(h.group(0), 16)),
            body,
        )
        try:
            return int(eval(body, {"__builtins__": {}}))
        except Exception:
            return None

    return None


def group_key(entry, addr):
    """Determine the group key for an entry.

    FIFO entries with address in 0x40000..0x5FFFF go to 'pbdma'.
    """
    if entry["subsystem"] == "fifo" and addr is not None and 0x40000 <= addr < 0x60000:
        return "pbdma"
    return entry["subsystem"]


def build_entries(accesses, macros):
    """Build grouped entries. Returns {group: {reg: entry_dict}}."""
    groups = {}
    for entry in accesses:
        addr = calc_address(entry["reg"], macros)
        grp = group_key(entry, addr)

        reg = entry["reg"]
        if grp not in groups:
            groups[grp] = {}
        if reg not in groups[grp]:
            look = rnndb.lookup(addr) if addr is not None else None
            groups[grp][reg] = {
                "reg": reg,
                "address": "0x%06x" % addr if addr is not None else None,
                "name": look["name"] if look else None,
                "name_source": "rnndb:" + look["file"] if look else "none",
                "width": 32,
                "readable": False,
                "writable": False,
                "fields": look["fields"] if look else [],
                "source": [],
                "status": "SOURCE_ONLY",
            }
        groups[grp][reg]["source"].append(
            "%s:%d" % (entry["file"], entry["line"])
        )
        if entry["op"] in ("rd32", "mask"):
            groups[grp][reg]["readable"] = True
        if entry["op"] in ("wr32", "mask"):
            groups[grp][reg]["writable"] = True

    # Deduplicate and sort sources for each entry
    for grp in groups:
        for reg in groups[grp]:
            groups[grp][reg]["source"] = sorted(
                set(groups[grp][reg]["source"])
            )

    return groups


def write_yaml(entries, path):
    """Write a YAML file from a dict of entries, sorted by reg."""
    import yaml
    sorted_entries = sorted(entries.values(), key=lambda e: e["reg"])
    # Use a custom representer for None → null, and preserve insertion order
    doc = []
    for e in sorted_entries:
        doc.append({
            "reg": e["reg"],
            "address": e["address"],
            "name": e["name"],
            "name_source": e["name_source"],
            "width": e["width"],
            "readable": e["readable"],
            "writable": e["writable"],
            "fields": e["fields"],
            "source": e["source"],
            "status": e["status"],
        })
    with open(path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)


def write_readme(groups, accesses):
    """Write the README.md for the register database."""
    import yaml
    lines = []
    lines.append("# Register Database\n")
    lines.append("One YAML file per subsystem, one entry per distinct register.\n")
    lines.append("All registers have status `SOURCE_ONLY` — traced to Nouveau source\n")
    lines.append("but not yet verified against hardware captures.\n")
    lines.append("## Summary\n")
    lines.append("| File | Entries | Named | No address |\n")
    lines.append("|---|---|---|---|\n")
    total_entries = 0
    total_named = 0
    total_no_addr = 0
    for grp in sorted(groups):
        ents = groups[grp]
        n_named = sum(1 for e in ents.values() if e["name"] is not None)
        n_no_addr = sum(1 for e in ents.values() if e["address"] is None)
        lines.append(
            "| %s.yaml | %d | %d | %d |\n"
            % (grp, len(ents), n_named, n_no_addr)
        )
        total_entries += len(ents)
        total_named += n_named
        total_no_addr += n_no_addr
    lines.append(
        "| **Total** | **%d** | **%d** | **%d** |\n"
        % (total_entries, total_named, total_no_addr)
    )
    lines.append("")
    # "Not named" section for mc, fb, fifo, pbdma
    for grp in ("mc", "fb", "fifo", "pbdma"):
        if grp not in groups:
            continue
        not_named = [
            e for e in groups[grp].values() if e["name"] is None
        ]
        if not not_named:
            continue
        lines.append("## Not named — %s\n" % grp)
        # Build a lookup of which functions use which regs from the raw accesses
        reg_func = {}
        for a in accesses:
            addr = calc_address(a["reg"], parse_macros())
            g = group_key(a, addr)
            if g == grp:
                reg_func.setdefault(a["reg"], set()).add(a["function"])
        lines.append("| Address | Function(s) |\n")
        lines.append("|---|---|\n")
        for e in sorted(not_named, key=lambda x: x["reg"]):
            funcs = sorted(reg_func.get(e["reg"], set()))
            addr_str = e["address"] or "(variable)"
            lines.append("| %s | %s |\n" % (addr_str, ", ".join(funcs)))
        lines.append("")

    return lines


def do_check(groups):
    """Check that existing files match what the tool would generate. Exit 0 if ok."""
    import yaml

    errors = []
    # Check file list
    expected_files = sorted(g + ".yaml" for g in groups)
    reg_dir = os.path.join(ROOT, "hardware", "registers")
    actual_files = sorted(
        f for f in os.listdir(reg_dir) if f.endswith(".yaml")
    )
    if actual_files != expected_files:
        errors.append(
            "File mismatch: expected %s, got %s"
            % (expected_files, actual_files)
        )

    for grp, grp_entries in sorted(groups.items()):
        path = os.path.join(ROOT, "hardware", "registers", grp + ".yaml")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            existing = yaml.safe_load(f) or []
        # Compare
        new_path = os.path.join(ROOT, "hardware", "registers", grp + ".yaml")
        # We write to a temp and compare
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            write_yaml(grp_entries, tmp.name)
            with open(tmp.name) as tf:
                new_content = tf.read()
            with open(path) as fp:
                old_content = fp.read()
            if new_content != old_content:
                diff = difflib.unified_diff(
                    old_content.splitlines(),
                    new_content.splitlines(),
                    fromfile=grp + ".yaml (on disk)",
                    tofile=grp + ".yaml (generated)",
                    lineterm="",
                )
                errors.append("Differences in %s.yaml:" % grp)
                errors.append("\n".join(list(diff)[:30]))
        os.unlink(tmp.name)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return False
    return True


def do_write(groups):
    """Write all YAML files and the README."""
    import yaml

    reg_dir = os.path.join(ROOT, "hardware", "registers")
    os.makedirs(reg_dir, exist_ok=True)

    for grp, grp_entries in sorted(groups.items()):
        write_yaml(grp_entries, os.path.join(reg_dir, grp + ".yaml"))

    accesses = load_accesses()
    macros = parse_macros()
    readme_path = os.path.join(reg_dir, "README.md")
    readme_text = "".join(write_readme(groups, accesses))
    with open(readme_path, "w") as f:
        f.write(readme_text)

    print("Wrote %d YAML files and README.md in hardware/registers/" % len(groups))


def main():
    check_mode = "--check" in sys.argv

    accesses = load_accesses()
    macros = parse_macros()
    groups = build_entries(accesses, macros)

    if check_mode:
        ok = do_check(groups)
        sys.exit(0 if ok else 1)
    else:
        do_write(groups)


if __name__ == "__main__":
    main()
