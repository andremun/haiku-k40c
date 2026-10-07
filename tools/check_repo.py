#!/usr/bin/env python3
"""Repository checks for `make check`.

Checks the format of the task outputs that exist (see docs/PHASES.md) and
that references point at real source lines. It does not check whether an
analysis is complete. Exit code 1 if any check fails.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
fails, notes = [], []


def fail(msg):
    fails.append(msg)


def load_json(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except ValueError as e:
        fail(f"{rel}: invalid JSON: {e}")
        return None


def src_lines(rel):
    path = os.path.join(NV, rel)
    try:
        with open(path, errors="replace") as f:
            return f.read().split("\n")
    except OSError:
        return None


def is_hex(v):
    return isinstance(v, str) and re.fullmatch(r"0x[0-9a-fA-F]+", v) is not None


# Project state -------------------------------------------------------
for rel in ("AGENTS.md", "docs/STATUS.md", "docs/PHASES.md",
            "docs/OPEN_QUESTIONS.md", "docs/REQUESTS.md", "reference/MANIFEST.md"):
    if not os.path.exists(os.path.join(ROOT, rel)):
        fail(f"{rel}: missing")
status = open(os.path.join(ROOT, "docs/STATUS.md")).read() if os.path.exists(
    os.path.join(ROOT, "docs/STATUS.md")) else ""
for key in ("Current phase:", "Current task:"):
    if key not in status:
        fail(f"docs/STATUS.md: no '{key}' line")

# Every task marked DONE in the task log needs its RESULT.md.
for m in re.finditer(r"^\|\s*([A-D]\d+)\s*\|\s*DONE\b", status, re.M):
    if not os.path.exists(os.path.join(ROOT, "work", m.group(1), "RESULT.md")):
        fail(f"docs/STATUS.md marks {m.group(1)} DONE but work/{m.group(1)}/RESULT.md is missing "
             f"(run the /handoff steps)")

# Every cited capture or reference path in the outputs must exist.
for doc in sorted(glob.glob(os.path.join(ROOT, "hardware", "*.md"))
                  + glob.glob(os.path.join(ROOT, "work", "*", "*.md"))
                  + glob.glob(os.path.join(ROOT, "analysis", "*.md"))
                  + [os.path.join(ROOT, "docs", "OPEN_QUESTIONS.md")]):
    if not os.path.exists(doc):
        continue
    for cited in sorted(set(re.findall(r"`(reference/[A-Za-z0-9_./-]+?)(?::\d+)?`", open(doc).read()))):
        if not os.path.exists(os.path.join(ROOT, cited)):
            fail(f"{os.path.relpath(doc, ROOT)}: cites {cited}, which does not exist")

# A1 hardware record --------------------------------------------------
rec = load_json("hardware/record.json")
if rec is not None:
    if not isinstance(rec, list):
        fail("hardware/record.json: must be a list (one object per K40c)")
    else:
        need = ("pci_address", "pci_id", "subsystem_id", "revision", "bars",
                "numa_node", "vbios", "vram_mib", "link", "nouveau_chipset")
        for i, r in enumerate(rec):
            missing = [k for k in need if k not in r]
            if missing:
                fail(f"hardware/record.json[{i}]: missing {missing}")
                continue
            for b in r["bars"]:
                if not (isinstance(b, dict) and "index" in b and is_hex(b.get("base"))
                        and is_hex(b.get("size"))):
                    fail(f"hardware/record.json[{i}]: bar entries need index and hex-string base/size")
                    break
            # Cross-check BARs and NUMA node against the captures.
            tag = str(r["pci_address"]).replace("0000:", "").replace(":", "_").replace(".", "_")
            cap = os.path.join(ROOT, "reference", "pci", f"resource-{tag}.txt")
            if os.path.exists(cap):
                want = {}
                for n, line in enumerate(open(cap).read().split("\n")[:6]):
                    f = line.split()
                    if len(f) == 3 and int(f[0], 16):
                        want[n] = (int(f[0], 16), int(f[1], 16) - int(f[0], 16) + 1)
                try:
                    got = {int(b["index"]): (int(b["base"], 16), int(b["size"], 16)) for b in r["bars"]}
                except (TypeError, ValueError, KeyError):
                    got = None
                if got is not None and got != want:
                    fail(f"hardware/record.json[{i}]: bars differ from reference/pci/resource-{tag}.txt "
                         f"(see reference/pci/README.md)")
            cap = os.path.join(ROOT, "reference", "pci", f"sysfs-{tag}.txt")
            if os.path.exists(cap):
                m = re.search(r"^numa_node:\s*(-?\d+)", open(cap).read(), re.M)
                if m and r["numa_node"] != int(m.group(1)):
                    fail(f"hardware/record.json[{i}]: numa_node differs from reference/pci/sysfs-{tag}.txt")
            # A2: PCI capabilities and interrupt against the root capture.
            a2_done = re.search(r"^\|\s*A2\s*\|\s*DONE\b", status, re.M) is not None
            a2_keys = ("pci_capabilities", "interrupt", "link_capability")
            if a2_done:
                missing = [k for k in a2_keys if k not in r]
                if missing:
                    fail(f"hardware/record.json[{i}]: A2 is DONE but {missing} missing")
            cap = os.path.join(ROOT, "reference", "pci", "root", f"lspci-vvv-{tag}.txt")
            if os.path.exists(cap) and "pci_capabilities" in r:
                text = open(cap).read()
                want = [int(x, 16) for x in re.findall(r"^\s*Capabilities: \[([0-9a-f]+)", text, re.M)]
                try:
                    got = [int(c["offset"], 16) for c in r["pci_capabilities"]]
                except (TypeError, ValueError, KeyError):
                    got = None
                if got != want:
                    fail(f"hardware/record.json[{i}]: pci_capabilities offsets differ from "
                         f"reference/pci/root/lspci-vvv-{tag}.txt (expected {len(want)} entries, in order)")
                m = re.search(r"routed to IRQ (\d+)", text)
                irq = r.get("interrupt", {}).get("irq") if isinstance(r.get("interrupt"), dict) else None
                if m and "interrupt" in r and irq != int(m.group(1)):
                    fail(f"hardware/record.json[{i}]: interrupt.irq differs from the capture")
            ch = r["nouveau_chipset"]
            if not isinstance(ch, dict) or ch.get("status") not in ("KNOWN", "INFERRED", "UNKNOWN"):
                fail(f"hardware/record.json[{i}]: nouveau_chipset.status must be KNOWN, INFERRED or UNKNOWN")
            if not isinstance(r["vram_mib"], int):
                fail(f"hardware/record.json[{i}]: vram_mib must be an integer")

# B1 file inventory ---------------------------------------------------
# Subdevices and engines on the compute path (docs/PHASES.md, task B1).
B1_REQUIRED = ("bar", "bus", "fb", "imem", "ltc", "mc", "mmu", "pci", "privring",
               "top", "fifo", "gr", "ce")
B1_CHIPSET = "nvf1_chipset"
B1_ROOT = "nvkm/engine/device/base.c"   # the chipset table: names every chip


def nvkm_definitions():
    """Map each function or table name to the nvkm .c files that define it.

    Nouveau puts the name of a definition at the start of a line:
    `name(args)` followed by `{` for a function, `name = {` for a table.
    """
    src, defs = {}, {}
    for path in glob.glob(os.path.join(NV, "nvkm", "**", "*.c"), recursive=True):
        rel = os.path.relpath(path, NV)
        with open(path, errors="replace") as f:
            src[rel] = f.read()
        names = re.findall(r"^(\w+)\s*\([^;{]*\)\s*\{", src[rel], re.M)
        names += re.findall(r"^(\w+)(?:\[\w*\])?\s*=\s*\{", src[rel], re.M)
        names += re.findall(r"^(?:static\s+)?(?:const\s+)?struct\s+\w+\s+\*?(\w+)(?:\[\w*\])?\s*=\s*\{",
                            src[rel], re.M)
        for n in names:
            defs.setdefault(n, set()).add(rel)
    return src, defs


def check_b1_inventory(entries):
    """The inventory must follow each constructor into the code it inherits.

    1. The file that defines the chipset constructor of every compute-path
       subdevice and engine is listed.
    2. The list is closed inside each directory: when a listed file uses a
       function or table that another file of the same directory defines,
       that file is listed too. gr/gk110b.c only calls gf100_gr_new_(), so
       gr/gf100.c and the files it uses belong to the inventory.
    Names with more than one definition are skipped. Files in other
    directories are not required by this check.
    """
    rel = "analysis/files.json"
    src, defs = nvkm_definitions()
    listed = {str(e.get("path")) for e in entries if isinstance(e, dict)}
    if B1_ROOT not in src:
        return
    m = re.search(r"\b%s\s*=\s*\{(.*?)\n\};" % B1_CHIPSET, src[B1_ROOT], re.S)
    ctors = dict(re.findall(r"\.(\w+)\s*=\s*\{[^,]*,\s*(\w+)\s*\}", m.group(1))) if m else {}
    need_dirs = set()
    for field in B1_REQUIRED:
        where = defs.get(ctors.get(field, ""), set())
        need_dirs |= {os.path.dirname(w) for w in where}
        if len(where) != 1:
            fail(f"{rel}: cannot find the {B1_CHIPSET} constructor of '{field}' in the Nouveau tree")
        elif not where <= listed:
            fail(f"{rel}: '{field}' constructor {ctors[field]} is in {min(where)}, which is not listed")
    missing = {}
    for f in sorted(listed & set(src)):
        if f == B1_ROOT:
            continue
        for name in sorted(set(re.findall(r"\b[a-z]\w+\b", src[f]))):
            where = defs.get(name, ())
            if len(where) != 1:
                continue
            g = min(where)
            if g != f and g not in listed and os.path.dirname(g) == os.path.dirname(f):
                missing.setdefault(g, (f, name))
    # Compute-path directories first.
    order = sorted(missing.items(), key=lambda kv: (os.path.dirname(kv[0]) not in need_dirs, kv[0]))
    for g, (f, name) in order[:8]:
        fail(f"{rel}: {f} uses {name} from {g}, which is not listed")
    if missing:
        fail(f"{rel}: {len(missing)} file(s) used by listed files in the same directory are not "
             f"listed (first 8 shown). Add them and run the check again: each added file can "
             f"require more. See docs/PHASES.md, task B1.")


def b1_class(path):
    """Class that the file name gives (docs/PHASES.md, task B1)."""
    base = os.path.basename(path)
    if re.search(r"gk110", base):
        return "GK110-specific"
    if re.search(r"gk104", base):
        return "GK104-inherited"
    if re.search(r"gf1\d\d", base):
        return "GF100-inherited"
    if re.search(r"(nv[0-9a-f]{2}|g\d\d|gt\d{3}|mcp\d\d|gk\d|gm\d|gp\d|gv\d|tu\d|ga\d|r\d{3})", base):
        return "other-chip"
    return "generic-NVKM"


def check_b1_fields(entries):
    """`class` follows the file name; `role` says how the path reaches the file."""
    rel = "analysis/files.json"
    paths = {str(e.get("path")) for e in entries if isinstance(e, dict)}
    badclass, badrole = [], []
    for e in entries:
        if not isinstance(e, dict):
            continue
        path, role = str(e.get("path")), str(e.get("role", ""))
        if e.get("class") != "Linux-only" and e.get("class") != b1_class(path):
            badclass.append(f"{path}: {e.get('class')}, expected {b1_class(path)}")
        m = re.search(r"used by (nvkm/[\w/]+\.c)", role)
        reached = "chipset constructor" in role or (m and m.group(1) in paths and m.group(1) != path)
        if len(role.split()) < 6 or not reached:
            badrole.append(path)
    for b in badclass[:5]:
        fail(f"{rel}: class of {b}")
    if len(badclass) > 5:
        fail(f"{rel}: {len(badclass)} entries with a class that does not follow the file name")
    if badrole:
        fail(f"{rel}: {len(badrole)} entries (first: {badrole[0]}) have a role that does not say what "
             f"the file provides and how the path reaches it. See docs/PHASES.md, task B1.")


def check_b1_tool():
    """`tools/nouveau_files.py --check` must agree with files.json, twice."""
    import subprocess
    tool = os.path.join(ROOT, "tools", "nouveau_files.py")
    if not os.path.exists(tool):
        fail("tools/nouveau_files.py: missing")
        return
    # A tool without the option would write the output file when it is run.
    if "--check" not in open(tool, errors="replace").read():
        fail("tools/nouveau_files.py: no --check option (docs/PHASES.md, task B1)")
        return
    for run in (1, 2):
        try:
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True,
                               text=True, timeout=120)
        except subprocess.TimeoutExpired:
            fail("tools/nouveau_files.py --check: no result in 120 s")
            return
        if r.returncode != 0:
            fail(f"tools/nouveau_files.py --check (run {run}): analysis/files.json is not what the "
                 f"tool generates. The tool must give the same output on every run.")
            return


files = load_json("analysis/files.json")
classes = {"GK110-specific", "GK104-inherited", "GF100-inherited", "other-chip", "generic-NVKM",
           "Linux-only"}
if files is not None:
    for i, e in enumerate(files if isinstance(files, list) else []):
        if src_lines(str(e.get("path", ""))) is None:
            fail(f"analysis/files.json[{i}]: path does not exist: {e.get('path')}")
        if e.get("class") not in classes:
            fail(f"analysis/files.json[{i}]: class must be one of {sorted(classes)}")
    if not isinstance(files, list):
        fail("analysis/files.json: must be a list")
    else:
        check_b1_inventory(files)
        check_b1_fields(files)
        check_b1_tool()

# B2 call graph -------------------------------------------------------
cg = load_json("analysis/callgraph.json")
if cg is not None:
    bad = 0
    nodes = cg.get("nodes", []) if isinstance(cg, dict) else []
    for n in nodes:
        L = src_lines(str(n.get("file", "")))
        ln = n.get("line")
        ok = L is not None and isinstance(ln, int) and 0 < ln <= len(L) and \
            re.search(r"\b%s\s*\(" % re.escape(str(n.get("name"))), "\n".join(L[max(0, ln - 2):ln + 1]))
        bad += not ok
    if not isinstance(cg, dict) or "edges" not in cg:
        fail("analysis/callgraph.json: needs 'nodes' and 'edges'")
    if bad:
        fail(f"analysis/callgraph.json: {bad} of {len(nodes)} nodes do not point at their definition")

# B3 MMIO accesses ----------------------------------------------------
mm = load_json("registers/mmio_accesses.json")
MMIO = re.compile(r"\bnvkm_(rd32|wr32|mask)\s*\(")
if mm is not None:
    bad = badop = badval = 0
    for e in mm if isinstance(mm, list) else []:
        L = src_lines(str(e.get("file", "")))
        ln = e.get("line")
        if not (L and isinstance(ln, int) and 0 < ln <= len(L) and MMIO.search(L[ln - 1])):
            bad += 1
        if e.get("op") not in ("rd32", "wr32", "mask"):
            badop += 1
        r = str(e.get("reg", "")).strip()
        if re.fullmatch(r"0x[0-9a-fA-F]+", r) and e.get("reg_value") != int(r, 16):
            badval += 1
    if bad:
        fail(f"registers/mmio_accesses.json: {bad} entries do not point at an MMIO call")
    if badop:
        fail(f"registers/mmio_accesses.json: {badop} entries with op not rd32/wr32/mask")
    if badval:
        fail(f"registers/mmio_accesses.json: {badval} constant registers without the correct reg_value")

# B4 Linux dependencies -----------------------------------------------
ld = load_json("analysis/linux_deps.json")
if ld is not None:
    cats = {"A-reimplement", "B-extract", "C-replace", "D-ignore"}
    n = sum(1 for e in (ld if isinstance(ld, list) else []) if e.get("category") not in cats)
    if n:
        fail(f"analysis/linux_deps.json: {n} entries with category not in {sorted(cats)}")

# C1 register database ------------------------------------------------
try:
    import yaml
except ImportError:
    yaml = None
for path in sorted(glob.glob(os.path.join(ROOT, "hardware/registers/*.yaml"))):
    rel = os.path.relpath(path, ROOT)
    if yaml is None:
        notes.append(f"{rel}: not checked (no PyYAML)")
        continue
    try:
        data = yaml.safe_load(open(path)) or []
    except yaml.YAMLError as e:
        fail(f"{rel}: invalid YAML: {e}")
        continue
    entries = data if isinstance(data, list) else data.get("registers", [])
    for i, e in enumerate(entries):
        miss = [k for k in ("name", "address", "source", "status") if k not in e]
        if miss:
            fail(f"{rel}[{i}]: missing {miss}")
        elif e["status"] not in ("SOURCE_ONLY", "TRACE_VERIFIED", "HARDWARE_VERIFIED", "HAIKU_VERIFIED"):
            fail(f"{rel}[{i}]: bad status {e['status']}")

# C3 hardware model documents ----------------------------------------
for path in sorted(glob.glob(os.path.join(ROOT, "docs/hardware-model/*.md"))):
    rel = os.path.relpath(path, ROOT)
    t = open(path, errors="replace").read()
    for k in ("KNOWN", "INFERRED", "UNKNOWN"):
        if not re.search(r"^#+\s.*\b%s\b" % k, t, re.M):
            fail(f"{rel}: no '{k}' section heading")
    for ref in set(re.findall(r"nvkm/[\w/]+\.[ch]", t)):
        if src_lines(ref) is None:
            fail(f"{rel}: cites a file that does not exist: {ref}")

for n in notes:
    print("note:", n)
for f in fails:
    print("FAIL:", f)
print(f"check_repo: {len(fails)} failure(s)")
sys.exit(1 if fails else 0)
