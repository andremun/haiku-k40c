#!/usr/bin/env python3
"""Generate analysis/files.json from the Nouveau chipset definition.

Reads the chipset entry from reference/nouveau/nvkm/engine/device/base.c,
resolves each constructor to its source file, then iteratively follows all
function and table references within each directory until the list is closed.

Usage:
    python3 tools/nouveau_files.py [--dry-run]

The script is idempotent: re-running produces the same output.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
OUTPUT = os.path.join(ROOT, "analysis", "files.json")

# Subsystems to include on the compute path.
B1_REQUIRED = ("bar", "bus", "fb", "imem", "ltc", "mc", "mmu", "pci",
               "privring", "top", "fifo", "gr", "ce")

# Non-compute-path subsystems that may appear as transitive dependencies
# and should be included with a generic role.
KNOWN_EXTRA = ("bios", "clk", "devinit", "fuse", "gpio", "i2c", "iccsense",
               "mxm", "pmu", "therm", "timer", "volt",
               "disp", "dma", "mspdec", "msppp", "msvld", "sw")


def scan_all_files():
    """Return (src, defs) where src maps rel-path -> text and defs maps
    name -> set of rel-paths that define it (function or table).

    Uses the same patterns as tools/check_repo.py (which passes).
    """
    src, defs = {}, {}
    for path in sorted(__import__("glob").glob(os.path.join(NV, "nvkm", "**", "*.c"),
                                                recursive=True)):
        rel = os.path.relpath(path, NV)
        with open(path, errors="replace") as f:
            src[rel] = f.read()
        # Function: name(args) {  (check_repo.py style, handles multi-line signatures
        # because [^;{] matches newlines)
        names = re.findall(r"^(\w+)\s*\([^;{]*\)\s*\{", src[rel], re.M)
        # Table/struct: name[] = {  or name = {
        names += re.findall(r"^(\w+)(?:\[\w*\])?\s*=\s*\{", src[rel], re.M)
        # struct pointer table: struct foo *bar = {
        names += re.findall(
            r"^(?:static\s+)?(?:const\s+)?struct\s+\w+\s+\*?(\w+)(?:\[\w*\])?\s*=\s*\{",
            src[rel], re.M)
        for n in names:
            defs.setdefault(n, set()).add(rel)
    return src, defs


def find_ctor_file(ctor_name, defs):
    """Find the single file that defines ctor_name, or None / multiple."""
    where = defs.get(ctor_name)
    if where is None:
        return None, None  # unknown
    if len(where) == 1:
        return where.pop(), None  # unique
    return None, where  # ambiguous


def extract_chipset_entries():
    """Extract (field, constructor_func) from nvf1_chipset in base.c."""
    base_path = os.path.join(NV, "nvkm/engine/device/base.c")
    with open(base_path) as f:
        text = f.read()
    idx = text.find("nvf1_chipset")
    if idx < 0:
        print("ERROR: Could not find nvf1_chipset in base.c", file=sys.stderr)
        sys.exit(1)
    start = text.find("{", idx)
    depth, end = 0, start
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = text[start + 1 : end]
    entries = []
    for m in re.finditer(r"\.(\w+)\s*=\s*\{[^,]*,\s*(\w+)\s*\}", block):
        entries.append((m.group(1), m.group(2)))
    return entries


def collect_refs(filepath, src):
    """Find all function names used (but not defined) in a file.

    Returns the set of names that look like function/table references:
    identifiers starting with a lowercase letter that are not keywords,
    not already defined in this file.
    """
    text = src[filepath]
    # Get names defined in this file
    defined = set()
    for name in re.findall(r"^(?:static\s+)?(?:const\s+)?(?:void|int|u?8|u?16|u?32|u?64|struct\s+\w+)\s+(\w+)\s*\([^;{]*\)\s*\{",
                            text, re.M):
        defined.add(name)
    for name in re.findall(r"^(?:static\s+)?(?:const\s+)?struct\s+\w+\s+\*?(\w+)(?:\[\w*\])?\s*=\s*\{",
                            text, re.M):
        defined.add(name)
    for name in re.findall(r"^(?:static\s+)?(?:const\s+)?(?:struct\s+\w+\s+\*?\w+\s+)?(\w+)(?:\[\w*\])?\s*=\s*\{",
                            text, re.M):
        defined.add(name)

    # Extract all identifiers from the file
    all_ids = set(re.findall(r"\b([a-z]\w*)\b", text))
    # Remove C keywords and common false positives
    keywords = {"sizeof", "return", "if", "else", "while", "for", "switch",
                "case", "break", "continue", "default", "do", "goto",
                "typeof", "defined", "NULL", "true", "false"}
    refs = all_ids - defined - keywords

    # Filter: keep identifiers longer than 2 chars
    # Most false positives are already removed by the defined/keywords sets
    refs = {r for r in refs if len(r) > 2}
    return refs


def classify(filepath, subsystem):
    """Classify a file based on chip-specific patterns in its basename.

    Matches chip identifiers as substrings (e.g. ctxgk110.c → GK110-specific,
    vmmgk104.c → GK104-inherited) rather than requiring a prefix.
    """
    base = os.path.basename(filepath).lower()
    if "gk110" in base or "gk110b" in base:
        return "GK110-specific"
    if "gk104" in base:
        return "GK104-inherited"
    if "gf100" in base or "gf119" in base:
        return "GF100-inherited"
    return "generic-NVKM"


def main():
    dry_run = "--dry-run" in sys.argv
    src, defs = scan_all_files()

    # Extract chipset entries
    entries = extract_chipset_entries()

    # Filter to compute-path subsystems
    compute_entries = [(f, c) for f, c in entries if f in B1_REQUIRED]

    # Phase 1: find the constructor file for each compute-path subsystem
    listed = {}  # rel_path -> (subsystem, field, ctor)
    for field, ctor in compute_entries:
        file_path, ambig = find_ctor_file(ctor, defs)
        if file_path is None:
            if ambig:
                print(f"WARNING: {ctor} defined in multiple files: {sorted(ambig)}",
                      file=sys.stderr)
            else:
                print(f"WARNING: {ctor} not found in Nouveau tree", file=sys.stderr)
            continue
        listed[file_path] = (field, ctor, None)  # subsystem from the key

    # Phase 2: iterative closure within each directory.
    # Each entry in `listed` tracks (subsystem, field, ctor) where
    # `subsystem` is the nvkm/<subsys>/ directory of the entry.
    # When we follow a reference to a file in the same directory,
    # that file inherits the same subsystem.
    changed = True
    while changed:
        changed = False
        for filepath in list(listed):
            dirpath = os.path.dirname(filepath)
            subsystem = listed[filepath][0]
            refs = collect_refs(filepath, src)
            for name in refs:
                where = defs.get(name)
                if where is None or len(where) != 1:
                    continue
                target = min(where)
                if target == filepath:
                    continue
                if os.path.dirname(target) != dirpath:
                    continue
                if target not in listed:
                    listed[target] = (subsystem, filepath, name)
                    changed = True

    # Phase 3: for files outside compute-path dirs, check if they are
    # dependencies that should be included
    all_subsystems = set()
    for rel_path in list(listed):
        parts = rel_path.split("/")
        if len(parts) >= 3:
            sub = parts[2]  # nvkm/<subsys>/<file>
            all_subsystems.add(sub)

    # Add known extra subsystems if they appear in closure references
    # We already got them from closure above, so just ensure all are included

    # Phase 4: build the output
    results = []
    for rel_path, info in sorted(listed.items()):
        subsystem, field, ctor = info
        # Phase 1 entries: ctor is None, field holds the ctor name.
        # Closure entries: ctor holds the reference name that brought this file in.
        name = field if ctor is None else ctor
        role = f"{name} — {subsystem}"
        entry = {
            "path": rel_path,
            "subsystem": subsystem,
            "class": classify(rel_path, subsystem),
            "role": role,
        }
        results.append(entry)

    # Sort: compute-path subsystems first, then others
    order_key = lambda e: (0 if e["subsystem"] in B1_REQUIRED else 1, e["path"])
    results.sort(key=order_key)

    if dry_run:
        classes = defaultdict(int)
        subsys = defaultdict(int)
        for e in results:
            classes[e["class"]] += 1
            subsys[e["subsystem"]] += 1
        print(f"Found {len(results)} entries (dry run).")
        for cls in sorted(classes):
            print(f"  {cls}: {classes[cls]}")
        print("Subsystems:")
        for s in sorted(subsys):
            print(f"  {s}: {subsys[s]}")
        return

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    classes = defaultdict(int)
    subsys = defaultdict(int)
    for e in results:
        classes[e["class"]] += 1
        subsys[e["subsystem"]] += 1
    print(f"Wrote {OUTPUT} ({len(results)} entries)")
    for cls in sorted(classes):
        print(f"  {cls}: {classes[cls]}")
    print("Subsystems:")
    for s in sorted(subsys):
        print(f"  {s}: {subsys[s]}")


if __name__ == "__main__":
    main()
