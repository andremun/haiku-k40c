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
files = load_json("analysis/files.json")
classes = {"GK110-specific", "GK104-inherited", "GF100-inherited", "generic-NVKM", "Linux-only"}
if files is not None:
    for i, e in enumerate(files if isinstance(files, list) else []):
        if src_lines(str(e.get("path", ""))) is None:
            fail(f"analysis/files.json[{i}]: path does not exist: {e.get('path')}")
        if e.get("class") not in classes:
            fail(f"analysis/files.json[{i}]: class must be one of {sorted(classes)}")
    if not isinstance(files, list):
        fail("analysis/files.json: must be a list")

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
