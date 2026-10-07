#!/usr/bin/env python3
"""Generate analysis/files.json from the Nouveau chipset definition.

Reads the chipset entry from reference/nouveau/nvkm/engine/device/base.c,
resolves each constructor to its source file, then iteratively follows all
function and table references within each directory until the list is closed.

Usage:
    python3 tools/nouveau_files.py [--dry-run] [--check]

The script is deterministic: re-running produces the same output.
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


def scan_all_files():
    """Return (src, defs) where src maps rel-path -> text and defs maps
    name -> sorted list of rel-paths that define it (function or table).

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
    # Convert sets to sorted lists for determinism
    for k in defs:
        defs[k] = sorted(defs[k])
    return src, defs


def find_ctor_file(ctor_name, defs):
    """Find the single file that defines ctor_name, or None / multiple."""
    where = defs.get(ctor_name)
    if where is None:
        return None, None  # unknown
    if len(where) == 1:
        return where[0], None  # unique
    return None, sorted(where)  # ambiguous


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
    # Sort for determinism
    entries.sort()
    return entries


def collect_refs(filepath, src, defs):
    """Find all function/table names used (but not defined) in a file.

    Returns the sorted list of names that look like function/table references.
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
    refs = {r for r in refs if len(r) > 2}
    return sorted(refs)


def classify(filepath):
    """Classify a file based on chip-specific patterns in its basename.

    Matches chip identifiers as substrings (e.g. ctxgk110.c -> GK110-specific,
    vmmgk104.c -> GK104-inherited). Follows check_repo.py's b1_class() exactly.
    """
    base = os.path.basename(filepath).lower()
    if "gk110" in base:
        return "GK110-specific"
    if "gk104" in base:
        return "GK104-inherited"
    if re.search(r"gf1\d\d", base):
        return "GF100-inherited"
    if re.search(r"(nv[0-9a-f]{2}|g\d\d|gt\d{3}|mcp\d\d|gk\d|gm\d|gp\d|gv\d|tu\d|ga\d|r\d{3})", base):
        return "other-chip"
    return "generic-NVKM"


def build_role(rel_path, info, all_listed_paths, class_name):
    """Build a role string following the PHASES.md specification.

    Constructor files: "chipset constructor <name> in <subsystem> subsystem"
        (at least 6 words).
    Closure files: "<class> <noun>, used by <listed_file> (<symbol>)"
        (at least 6 words).
    """
    subsystem, field, ctor = info
    # Phase 1 entries: ctor is None, field holds the ctor name.
    # Closure entries: ctor holds the reference name that brought this file in.
    if ctor is None:
        # Constructor file — describe it as a chipset constructor
        role = f"chipset constructor {field} in {subsystem} subsystem"
    else:
        # Closure entry — describe which listed file uses it, with a prefix
        # that adds at least 2 words so the total reaches 6.
        if class_name == "GF100-inherited":
            prefix = "Fermi implementation,"
        elif class_name == "GK104-inherited":
            prefix = "Kepler inherited,"
        elif class_name == "GK110-specific":
            prefix = "Kepler+ specific,"
        elif class_name == "other-chip":
            prefix = "Legacy chip,"
        else:
            prefix = "Generic NVKM,"
        role = f"{prefix} used by {field} ({ctor})"
    return role


def main():
    dry_run = "--dry-run" in sys.argv
    check_mode = "--check" in sys.argv
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
        for filepath in sorted(listed):
            dirpath = os.path.dirname(filepath)
            subsystem = listed[filepath][0]
            refs = collect_refs(filepath, src, defs)
            for name in refs:
                where = defs.get(name)
                if where is None or len(where) != 1:
                    continue
                target = where[0]
                if target == filepath:
                    continue
                if os.path.dirname(target) != dirpath:
                    continue
                if target not in listed:
                    listed[target] = (subsystem, filepath, name)
                    changed = True

    # Phase 3: build the output
    results = []
    all_listed_paths = sorted(listed.keys())
    for rel_path in all_listed_paths:
        info = listed[rel_path]
        class_name = classify(rel_path)
        role = build_role(rel_path, info, all_listed_paths, class_name)
        entry = {
            "path": rel_path,
            "subsystem": info[0],
            "class": class_name,
            "role": role,
        }
        results.append(entry)

    # Sort: compute-path subsystems first (alphabetically), then others (alphabetically)
    order_key = lambda e: (0 if e["subsystem"] in B1_REQUIRED else 1, e["path"])
    results.sort(key=order_key)

    if check_mode:
        # Check mode: compare with the existing files.json
        if not os.path.exists(OUTPUT):
            print(f"{OUTPUT}: does not exist", file=sys.stderr)
            sys.exit(1)
        with open(OUTPUT) as f:
            existing = json.load(f)
        if existing != results:
            # Show differences
            existing_str = json.dumps(existing, indent=2)
            new_str = json.dumps(results, indent=2)
            print(f"MISMATCH: {OUTPUT} differs from tool output", file=sys.stderr)
            # Find first difference
            for i, (a, b) in enumerate(zip(existing, results)):
                if a != b:
                    print(f"  First diff at index {i}:", file=sys.stderr)
                    print(f"    existing: {json.dumps(a)}", file=sys.stderr)
                    print(f"    expected: {json.dumps(b)}", file=sys.stderr)
                    break
            if len(existing) != len(results):
                print(f"  Length: existing={len(existing)}, expected={len(results)}", file=sys.stderr)
            sys.exit(1)
        # If we get here, the file matches — write nothing and exit 0
        sys.exit(0)

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
