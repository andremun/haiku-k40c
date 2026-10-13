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


# A worktree for one task may skip the checks of a task that another
# worktree is reworking: put the task ID in the untracked file .check-skip.
SKIP = set()
if os.path.exists(os.path.join(ROOT, ".check-skip")):
    SKIP = set(open(os.path.join(ROOT, ".check-skip")).read().split())
    notes.append(f"checks skipped by .check-skip: {sorted(SKIP)}")


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
# Subdevices and engines on the compute path (docs/tasks/B1.md).
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
             f"require more. See docs/tasks/B1.md.")


def b1_class(path):
    """Class that the file name gives (docs/tasks/B1.md)."""
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
             f"the file provides and how the path reaches it. See docs/tasks/B1.md.")


def check_b1_tool():
    """`tools/nouveau_files.py --check` must agree with files.json, twice."""
    import subprocess
    tool = os.path.join(ROOT, "tools", "nouveau_files.py")
    if not os.path.exists(tool):
        fail("tools/nouveau_files.py: missing")
        return
    # A tool without the option would write the output file when it is run.
    if "--check" not in open(tool, errors="replace").read():
        fail("tools/nouveau_files.py: no --check option (docs/tasks/B1.md)")
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
# Roots: the chipset constructors of fb, mmu, fifo and gr (docs/tasks/B2.md).
B2_ROOTS = ("gk110_fb_new", "gk104_mmu_new", "gk110_fifo_new", "gk110b_gr_new")
cg = load_json("analysis/callgraph.json") if "B2" not in SKIP else None
if cg is not None:
    rel = "analysis/callgraph.json"
    nodes = cg.get("nodes", []) if isinstance(cg, dict) else []
    edges = cg.get("edges", []) if isinstance(cg, dict) else []
    if not isinstance(cg, dict) or "edges" not in cg:
        fail(f"{rel}: needs 'nodes' and 'edges'")
    # A node is a function (`name(args)` then `{`) or a function table
    # (`name = {`). Its body runs to the next line that starts with `}`.
    bad, body = 0, {}
    for n in nodes:
        name, L, ln = str(n.get("name")), src_lines(str(n.get("file", ""))), n.get("line")
        ok = L is not None and isinstance(ln, int) and 0 < ln <= len(L) and \
            re.search(r"\b%s(\s*\(|(\[\w*\])?\s*=)" % re.escape(name), "\n".join(L[max(0, ln - 2):ln + 1]))
        bad += not ok
        if ok:
            end = next((i for i in range(ln, len(L)) if L[i].startswith("}")), len(L) - 1)
            body[name] = "\n".join(L[ln - 1:end + 1])
    if bad:
        fail(f"{rel}: {bad} of {len(nodes)} nodes do not point at their definition")
    names = {str(n.get("name")) for n in nodes}
    for r in B2_ROOTS:
        if r not in names:
            fail(f"{rel}: root {r} is not a node")
    pairs = [e for e in edges if isinstance(e, list) and len(e) == 2]
    if len(pairs) != len(edges):
        fail(f"{rel}: every edge must be [caller, callee]")
    loose = [e for e in pairs if e[0] not in names or e[1] not in names]
    if loose:
        fail(f"{rel}: {len(loose)} edges name a function that is not a node (first: {loose[0]})")
    unreal = [e for e in pairs if e[0] in body and not re.search(r"\b%s\b" % re.escape(str(e[1])),
                                                                 body[e[0]].split("\n", 1)[-1])]
    if unreal:
        fail(f"{rel}: {len(unreal)} edges where the caller's body does not use the callee "
             f"(first: {unreal[0]})")
    # Every node is reached from a root.
    out = {}
    for c, d in pairs:
        out.setdefault(c, set()).add(d)
    seen, todo = set(), [r for r in B2_ROOTS if r in names]
    while todo:
        x = todo.pop()
        if x not in seen:
            seen.add(x)
            todo.extend(out.get(x, ()))
    lost = sorted(names - seen)
    if lost:
        fail(f"{rel}: {len(lost)} nodes are not reached from a root (first: {lost[0]})")
    # The tool must reproduce the file, on every run.
    tool = os.path.join(ROOT, "tools", "callgraph.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/callgraph.py: missing, or no --check option (docs/tasks/B2.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/callgraph.py --check (run {run}): {rel} is not what the tool generates. "
                     f"The tool must give the same output on every run.")
                break
    # Nouveau reaches its init code through function tables, not calls.
    for need in ("gf100_gr_init", "gf100_fb_init", "gk104_fifo_init"):
        if need not in names:
            fail(f"{rel}: {need} is not a node. It is reached through a function table "
                 f"(`.init = ...`): see docs/tasks/B2.md.")

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
    # Complete: one entry for each call in each file of the B1 inventory.
    rel = "registers/mmio_accesses.json"
    have, badfn, badreg = {}, 0, 0
    for e in mm if isinstance(mm, list) else []:
        key = (str(e.get("file")), e.get("line"))
        have[key] = have.get(key, 0) + 1
    want, func_at = {}, {}
    for f in sorted({str(x.get("path")) for x in (files or []) if isinstance(x, dict)}):
        cur = None
        for i, text in enumerate(src_lines(f) or [], 1):
            m = re.match(r"^(\w+)\s*\(", text)
            if m:
                cur = m.group(1)
            n = len(MMIO.findall(text))
            if n:
                want[(f, i)] = n
                func_at[(f, i)] = cur
    if files is not None and have != want:
        short = sorted(k for k in want if have.get(k, 0) < want[k])
        extra = sorted(k for k in have if have[k] > want.get(k, 0))
        fail(f"{rel}: {sum(have.values())} entries, but the files of analysis/files.json have "
             f"{sum(want.values())} calls (a line with two calls needs two entries). "
             f"Missing at {len(short)} lines"
             + (f" (first: {short[0][0]}:{short[0][1]})" if short else "")
             + f", too many at {len(extra)} lines"
             + (f" (first: {extra[0][0]}:{extra[0][1]})" if extra else "") + ".")
    for e in mm if isinstance(mm, list) else []:
        key = (str(e.get("file")), e.get("line"))
        L = src_lines(key[0])
        if key in func_at and e.get("function") != func_at[key]:
            badfn += 1
        r = str(e.get("reg", "")).strip()
        if L and isinstance(key[1], int) and 0 < key[1] <= len(L) and (
                not r or r.replace(" ", "") not in L[key[1] - 1].replace(" ", "")):
            badreg += 1
    if badfn:
        fail(f"{rel}: {badfn} entries where 'function' is not the function that contains the line")
    if badreg:
        fail(f"{rel}: {badreg} entries where 'reg' is not the register expression written on the line")
    tool = os.path.join(ROOT, "tools", "extract_mmio.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/extract_mmio.py: missing, or no --check option (docs/tasks/B3.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/extract_mmio.py --check (run {run}): {rel} is not what the tool generates")
                break

# B6 compute launch path ----------------------------------------------
cl = load_json("analysis/compute_launch.json")
if cl is not None:
    rel = "analysis/compute_launch.json"
    MESA = os.path.join(ROOT, "reference", "mesa")

    def mesa_line(f, ln):
        try:
            with open(os.path.join(MESA, str(f)), errors="replace") as fh:
                L = fh.read().split("\n")
        except OSError:
            return None
        return L[ln - 1] if isinstance(ln, int) and 0 < ln <= len(L) else None

    if not isinstance(cl, dict):
        fail(f"{rel}: must be an object")
        cl = {}
    want = None
    try:
        with open(os.path.join(MESA, "src/gallium/drivers/nouveau/nv_object.xml.h")) as fh:
            m = re.search(r"#define NVF0_COMPUTE_CLASS\s+(0x[0-9a-fA-F]+)", fh.read())
            want = int(m.group(1), 16) if m else None
    except OSError:
        pass
    try:
        got = int(str(cl.get("compute_class")), 16)
    except ValueError:
        got = None
    if want is not None and got != want:
        fail(f"{rel}: compute_class must be NVF0_COMPUTE_CLASS from nv_object.xml.h")
    for key, name in (("setup", "method"), ("launch", "method"), ("descriptor_fields", "field")):
        rows = cl.get(key)
        if not isinstance(rows, list) or not rows:
            fail(f"{rel}: '{key}' must be a list with entries")
            continue
        bad = 0
        for r in rows:
            text = mesa_line(r.get("file"), r.get("line")) if isinstance(r, dict) else None
            word = str(r.get(name, "")) if isinstance(r, dict) else ""
            bad += not (text is not None and word and word.lower() in text.lower())
        if bad:
            fail(f"{rel}: {bad} of {len(rows)} '{key}' entries do not point at a line that has "
                 f"the {name} name (paths are relative to reference/mesa/)")
    order = [str(r.get("method")) for r in cl.get("launch", []) if isinstance(r, dict)]
    if not ("LAUNCH_DESC_ADDRESS" in order and "LAUNCH" in order
            and order.index("LAUNCH_DESC_ADDRESS") < order.index("LAUNCH")):
        fail(f"{rel}: 'launch' must have LAUNCH_DESC_ADDRESS and then LAUNCH")
    if not cl.get("kernel_needs"):
        fail(f"{rel}: 'kernel_needs' is empty")
    # Which methods the GK110 card receives (second review of B6).
    flags = {(k, r.get("line")): r.get("gk110") for k in ("setup", "launch")
             for r in cl.get(k, []) if isinstance(r, dict)}
    if any(v not in (True, False) for v in flags.values()):
        fail(f"{rel}: every 'setup' and 'launch' entry needs \"gk110\": true or false")
    else:
        other = sorted(k for k, v in flags.items() if v is False)
        want_other = [("launch", 878), ("setup", 87), ("setup", 90)]
        if other != want_other:
            fail(f"{rel}: entries with gk110 false are {other}; the branches for other chips "
                 f"are {want_other} (work/B6/REVIEW.md)")
    tool = os.path.join(ROOT, "tools", "compute_launch.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/compute_launch.py: missing, or no --check option (docs/tasks/B6.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/compute_launch.py --check (run {run}): {rel} is not what the tool generates")
                break

# B5 minimum chain ----------------------------------------------------
mc = load_json("analysis/min_chain.json")
if mc is not None and "B5" not in SKIP:
    rel = "analysis/min_chain.json"
    MESA5 = os.path.join(ROOT, "reference", "mesa")
    if not isinstance(mc, dict):
        fail(f"{rel}: must be an object")
        mc = {}

    def b5_line(tree, f, ln):
        base = MESA5 if tree == "mesa" else NV
        try:
            with open(os.path.join(base, str(f)), errors="replace") as fh:
                L = fh.read().split("\n")
        except OSError:
            return None
        return L[ln - 1] if isinstance(ln, int) and 0 < ln <= len(L) else None

    def b5_words(v, n=5):
        return isinstance(v, str) and len(v.split()) >= n

    def b5_rows(key):
        rows = mc.get(key)
        if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
            fail(f"{rel}: '{key}' must be a list of objects with entries")
            return []
        return rows

    # (1) every subsystem of the card's chipset table is classified
    base_c = src_lines("nvkm/engine/device/base.c") or []
    want_sub, inside = {}, False
    for i, text in enumerate(base_c, 1):
        if text.startswith("nvf1_chipset"):
            inside = True
        elif inside and text.startswith("};"):
            break
        elif inside:
            m = re.match(r"\s*\.(\w+)\s*=\s*\{\s*0x[0-9a-f]+,\s*(\w+)\s*\}", text)
            if m:
                want_sub[m.group(1)] = (m.group(2), i)
    subs = b5_rows("subsystems")
    got_sub = {str(r.get("name")): r for r in subs}
    if sorted(got_sub) != sorted(want_sub) or len(subs) != len(want_sub):
        fail(f"{rel}: 'subsystems' must have one entry for each of the {len(want_sub)} members of "
             f"nvf1_chipset in nvkm/engine/device/base.c; missing {sorted(set(want_sub) - set(got_sub))}, "
             f"extra {sorted(set(got_sub) - set(want_sub))}")
    STAT = {"needed", "optional", "not-needed"}
    bad = [n for n, r in got_sub.items() if n in want_sub and
           (r.get("constructor"), r.get("line")) != want_sub[n]]
    if bad:
        fail(f"{rel}: subsystems with a constructor or line that is not the nvf1_chipset line: {bad}")
    bad = [n for n, r in got_sub.items() if r.get("status") not in STAT or not b5_words(r.get("reason"))]
    if bad:
        fail(f"{rel}: subsystems need \"status\" in {sorted(STAT)} and a \"reason\" of 5 words or more: {bad}")
    for n in ("bar", "fb", "imem", "mmu", "mc", "fifo", "gr"):
        if n in got_sub and got_sub[n].get("status") in STAT - {"needed"}:
            fail(f"{rel}: subsystem '{n}' must be \"needed\": a compute job cannot run without it")
    for n in ("disp", "mspdec", "msppp", "msvld"):
        if n in got_sub and got_sub[n].get("status") == "needed":
            fail(f"{rel}: subsystem '{n}' is display or video decoding and cannot be \"needed\"")

    # (2) ordered steps with real functions and the registers of B3
    steps = b5_rows("steps")
    if [r.get("step") for r in steps] != list(range(1, len(steps) + 1)):
        fail(f"{rel}: 'steps' must be numbered 1, 2, 3, ... in order")
    if steps and len(steps) < 8:
        fail(f"{rel}: {len(steps)} steps; the chain from PCI to a finished job has 8 or more")
    mm = load_json("registers/mmio_accesses.json") or []
    by_fn = {}
    for a in mm if isinstance(mm, list) else []:
        by_fn.setdefault(a.get("function"), set()).add((a.get("file"), a.get("line"), a.get("reg")))
    where, bad_fn, bad_reg, bad_txt = {}, [], [], []
    for r in steps:
        n = r.get("step")
        if r.get("subsystem") not in set(want_sub) | {"host", "channel", "mesa"}:
            fail(f"{rel}: step {n}: 'subsystem' must be a subsystems name, \"host\", \"channel\" or \"mesa\"")
        if r.get("status") not in ("known", "partly-known", "unknown") or not b5_words(r.get("what")):
            bad_txt.append(n)
        fns = r.get("functions") if isinstance(r.get("functions"), list) else []
        want_reg = set()
        for f in fns:
            if not isinstance(f, dict):
                bad_fn.append((n, str(f)))
                continue
            text = b5_line(f.get("tree"), f.get("file"), f.get("line"))
            name = str(f.get("name", ""))
            if f.get("tree") not in ("nouveau", "mesa") or text is None or not name or name not in text:
                bad_fn.append((n, name))
            where.setdefault(name, n)
            if f.get("tree") == "nouveau":
                want_reg |= by_fn.get(name, set())
        regs = r.get("registers") if isinstance(r.get("registers"), list) else None
        got_reg = {(x.get("file"), x.get("line"), x.get("reg")) for x in regs or [] if isinstance(x, dict)}
        if regs is None or got_reg != want_reg:
            bad_reg.append(n)
    if bad_txt:
        fail(f"{rel}: steps {bad_txt} need \"status\" known, partly-known or unknown and a \"what\" "
             f"of 5 words or more")
    if bad_fn:
        fail(f"{rel}: {len(bad_fn)} functions do not point at a line that has the name "
             f"(\"tree\" is \"nouveau\" or \"mesa\"): {bad_fn[:6]}")
    if bad_reg:
        fail(f"{rel}: steps {bad_reg}: 'registers' must be exactly the entries of "
             f"registers/mmio_accesses.json for the step's nouveau functions (file, line, reg)")
    chain = ["gf100_fb_init", "gk104_fifo_init", "gf100_gr_init",
             "nve4_screen_compute_setup", "nve4_launch_grid"]
    miss = [f for f in chain if f not in where]
    if miss:
        fail(f"{rel}: no step has the function {miss}")
    elif [where[f] for f in chain] != sorted(where[f] for f in chain) or \
            where["gf100_gr_init"] >= where["nve4_screen_compute_setup"] or \
            where["nve4_screen_compute_setup"] >= where["nve4_launch_grid"]:
        fail(f"{rel}: the steps must have these functions in this order: {chain}")
    # First review of B5 (work/B5/REVIEW.md).
    for n, why in (("top", "gk104_fifo_init reads device->top (fifo/gk104.c:764)"),
                   ("ltc", "the GR engine calls nvkm_ltc_* (gr/gf100.c:94)"),
                   ("timer", "every nvkm_msec wait uses it (gr/gf100.c:758)"),
                   ("privring", "it is the register bus to the GR units")):
        if n in got_sub and got_sub[n].get("status") != "needed":
            fail(f"{rel}: subsystem '{n}' must be \"needed\": {why}")
    mid = ["gf100_gr_init_ctxctl_int", "gk104_chan_ramfc_write", "gk104_runl_commit",
           "gf100_gr_chan_new", "gf100_grctx_generate"]
    miss = [f for f in mid if f not in where]
    if miss:
        fail(f"{rel}: no step has the function {miss} (firmware start, channel, GR context)")
    elif not miss and all(f in where for f in chain):
        late = [f for f in mid[1:] if not where["gf100_gr_init"] < where[f] < where["nve4_screen_compute_setup"]]
        if late:
            fail(f"{rel}: {late} must be in steps after gf100_gr_init and before "
                 f"nve4_screen_compute_setup: the channel and its GR context exist before Mesa "
                 f"sends methods")
        if steps and where["nve4_launch_grid"] == len(steps):
            fail(f"{rel}: the chain ends at the launch; add the steps after it (wait for the job, "
                 f"read the result buffer)")
    shallow = [r.get("step") for r in steps if r.get("status") == "known" and r.get("subsystem") in want_sub
               and all(str(f.get("name", "")).endswith("_new") for f in r.get("functions") or [{}]
                       if isinstance(f, dict))]
    if shallow:
        fail(f"{rel}: steps {shallow} have status known but only a constructor (*_new allocates, it "
             f"does not start hardware): add the init function or use partly-known")
    wrong = {"memory controller": "mc is the master control: engine enable bits and interrupts",
             "ring buffer": "privring is the PRI ring, the register bus to the engines",
             "multi-gpu": "top is the device topology table that lists engines and runlists",
             "workqueue": "HWW is a hardware warning (error report)",
             "instantiated": "imem is instance memory: GPU objects such as page tables and RAMFC"}
    texts = " ".join(str(r.get(k, "")) for rows in (subs, steps, [h for h in mc.get("gr_hooks") or [] if isinstance(h, dict)])
                     for r in rows
                     for k in ("reason", "what", "notes")).lower()
    for w, right in wrong.items():
        if w in texts:
            fail(f"{rel}: the text says \"{w}\". {right}. Read the source before you write a reason")

    used = {r.get("subsystem") for r in steps}
    idle = sorted(n for n, r in got_sub.items() if r.get("status") == "needed" and n not in used)
    if idle:
        fail(f"{rel}: subsystems marked needed that no step uses: {idle}")

    # (3) every init hook of the GR function table is classified
    gr_c = src_lines("nvkm/engine/gr/gk110b.c") or []
    want_hook, inside = {}, False
    for text in gr_c:
        if text.startswith("gk110b_gr = {"):
            inside = True
        elif inside and text.startswith("};"):
            break
        elif inside:
            m = re.match(r"\s*\.((?:one)?init\w*)\s*=\s*(\w+),", text)
            if m:
                want_hook[m.group(1)] = m.group(2)
    hooks = b5_rows("gr_hooks")
    got_hook = {str(r.get("hook")): r for r in hooks}
    if {k: v.get("function") for k, v in got_hook.items()} != want_hook:
        fail(f"{rel}: 'gr_hooks' must have each .init* and .oneinit* member of gk110b_gr "
             f"(nvkm/engine/gr/gk110b.c) with its function: {len(want_hook)} entries; missing or wrong "
             f"{sorted(k for k in want_hook if got_hook.get(k, {}).get('function') != want_hook[k])}, "
             f"extra {sorted(set(got_hook) - set(want_hook))}")
    USE = {"compute", "graphics-only", "both"}
    bad = []
    for k, r in got_hook.items():
        text = b5_line("nouveau", r.get("file"), r.get("line"))
        if r.get("use") not in USE or not b5_words(r.get("reason")) or text is None \
                or str(r.get("function")) not in text:
            bad.append(k)
    if bad:
        fail(f"{rel}: gr_hooks need \"use\" in {sorted(USE)}, a \"reason\" of 5 words or more and the "
             f"file and line of the function definition: {bad}")
    if "init_zcull" in got_hook and got_hook["init_zcull"].get("use") != "graphics-only":
        fail(f"{rel}: gr_hooks init_zcull sets up depth culling: it is \"graphics-only\"")
    if "init" in got_hook and got_hook["init"].get("use") != "both":
        fail(f"{rel}: gr_hooks init is gf100_gr_init, which calls all the other hooks: \"both\"")
    if hooks and not any(r.get("use") in ("compute", "both") for r in hooks):
        fail(f"{rel}: no gr_hooks entry has use compute or both")

    # (4) firmware
    fw = {str(r.get("name")): r for r in b5_rows("firmware")}
    for name, hdr in (("fecs", "nvkm/engine/gr/fuc/hubgk110.fuc3.h"),
                      ("gpccs", "nvkm/engine/gr/fuc/gpcgk110.fuc3.h")):
        r = fw.get(name)
        if r is None:
            fail(f"{rel}: 'firmware' has no entry named \"{name}\"")
        elif r.get("source") != "built-in" or r.get("file") != hdr:
            fail(f"{rel}: firmware '{name}': Nouveau has this code in its own source. \"source\" must "
                 f"be \"built-in\" and \"file\" the header that gk110.c includes for it")
    for name, r in fw.items():
        if r.get("source") not in ("built-in", "external-file", "vbios") or not b5_words(r.get("note")):
            fail(f"{rel}: firmware '{name}' needs \"source\" built-in, external-file or vbios and a "
                 f"\"note\" of 5 words or more")

    md = os.path.join(ROOT, "analysis", "min_chain.md")
    if not os.path.exists(md) or len(open(md, errors="replace").read().split("\n")) < 40:
        fail("analysis/min_chain.md: missing or under 40 lines")
    tool = os.path.join(ROOT, "tools", "min_chain.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/min_chain.py: missing, or no --check option (docs/tasks/B5.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/min_chain.py --check (run {run}): {rel} is not what the tool generates")
                break

# B4 Linux dependencies -----------------------------------------------
ld = load_json("analysis/linux_deps.json")
if ld is not None and "B4" not in SKIP:
    rel = "analysis/linux_deps.json"
    HK = os.path.join(ROOT, "reference", "haiku")
    if not isinstance(ld, list) or not all(isinstance(e, dict) for e in ld):
        fail(f"{rel}: must be a list of objects")
        ld = []
    # The rule of docs/tasks/B4.md, computed here.
    B4_KW = set("if for while switch return sizeof defined do else case typeof __typeof__ offsetof".split())
    b4_defined = set()
    for d, _, fs in os.walk(NV, followlinks=True):
        for f in fs:
            if f.endswith((".c", ".h")):
                t = open(os.path.join(d, f), errors="replace").read()
                b4_defined |= set(re.findall(r"^(\w+)\s*\(", t, re.M))
                b4_defined |= set(re.findall(r"^#\s*define\s+(\w+)", t, re.M))
    b4_count, b4_lines = {}, {}
    for e in load_json("analysis/files.json") or []:
        if e.get("class") == "other-chip":
            continue
        try:
            t = open(os.path.join(NV, e["path"]), errors="replace").read()
        except OSError:
            continue
        t = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
        for m in re.finditer(r"(?<![\w.>])([A-Za-z_]\w*)\s*\(", t):
            n = m.group(1)
            if n not in B4_KW and n not in b4_defined:
                b4_count[n] = b4_count.get(n, 0) + 1
                b4_lines.setdefault(n, set()).add((e["path"], t.count("\n", 0, m.start()) + 1))
    got = {str(e.get("symbol")): e for e in ld}
    if sorted(got) != sorted(b4_count) or len(ld) != len(b4_count):
        fail(f"{rel}: {len(ld)} symbols, the rule of docs/tasks/B4.md gives {len(b4_count)}; missing "
             f"{sorted(set(b4_count) - set(got))[:8]}, extra {sorted(set(got) - set(b4_count))[:8]}")
    if [e.get("symbol") for e in ld] != sorted(got):
        fail(f"{rel}: entries must be sorted by symbol")
    CATS = {"A-reimplement", "B-extract", "C-replace", "D-ignore", "X-not-linux"}
    STDC = {"malloc", "calloc", "free", "realloc", "memcpy", "memset", "memcmp", "memmove", "snprintf",
            "sprintf", "strlcpy", "strlen"}
    bad = {}
    for n, e in got.items():
        if n not in b4_count:
            continue
        ex = e.get("example") if isinstance(e.get("example"), dict) else {}
        if e.get("count") != b4_count[n]:
            bad.setdefault("count", []).append(n)
        if (ex.get("file"), ex.get("line")) not in b4_lines[n]:
            bad.setdefault("example (a file and line with a call of the symbol)", []).append(n)
        if e.get("category") not in CATS:
            bad.setdefault(f"category (one of {sorted(CATS)})", []).append(n)
        if not isinstance(e.get("note"), str) or len(e["note"].split()) < 4:
            bad.setdefault("note (4 words or more)", []).append(n)
        api = e.get("haiku_api")
        if e.get("category") == "C-replace":
            if not isinstance(api, list) or not api:
                bad.setdefault("haiku_api (a list with one name or more for C-replace)", []).append(n)
                continue
            hdr = e.get("header")
            if hdr is None:
                if not set(api) <= STDC:
                    bad.setdefault("header (null is only for standard C functions)", []).append(n)
            else:
                try:
                    text = open(os.path.join(HK, str(hdr)), errors="replace").read()
                except OSError:
                    text = None
                if text is None or not str(hdr).startswith("headers/") or \
                        not all(re.search(r"\b%s\b" % re.escape(str(a)), text) for a in api):
                    bad.setdefault("header (a file under reference/haiku/headers that has every "
                                   "haiku_api name)", []).append(n)
    for k, names in sorted(bad.items()):
        fail(f"{rel}: wrong {k} in {len(names)} entries: {names[:6]}")
    # Decisions that the check knows.
    for n in ("kzalloc", "kfree", "kmalloc", "mutex_lock", "mutex_unlock", "mutex_init", "spin_lock",
              "spin_unlock", "spin_lock_irqsave", "spin_unlock_irqrestore", "list_add_tail", "list_del",
              "dma_map_page", "msleep", "usleep_range"):
        if n in got and got[n].get("category") != "C-replace":
            fail(f"{rel}: '{n}' is Linux infrastructure with a Haiku equivalent: C-replace")
    for n, apis in (("mutex_lock", ["mutex_lock"]), ("spin_lock_irqsave", ["acquire_spinlock", "disable_interrupts"]),
                    ("msleep", ["snooze"]), ("usleep_range", ["snooze"])):
        if n in got and not set(apis) <= set(got[n].get("haiku_api") or []):
            fail(f"{rel}: haiku_api of '{n}' must have {apis}")
    # First review of B4 (work/B4/REVIEW.md).
    for n, any_of in (("list_del", ["list_remove_item", "list_remove_link"]),
                      ("list_del_init", ["list_remove_item", "list_remove_link"]),
                      ("list_empty", ["list_is_empty"]), ("INIT_LIST_HEAD", ["list_init"]),
                      ("atomic_inc", ["atomic_add"]), ("atomic_dec", ["atomic_add"]),
                      ("atomic_dec_and_test", ["atomic_add"]), ("atomic_inc_return", ["atomic_add"]),
                      ("kref_get", ["atomic_add"]), ("refcount_inc", ["atomic_add"]),
                      ("refcount_dec_and_test", ["atomic_add"]),
                      ("spin_lock_init", ["B_INITIALIZE_SPINLOCK", "B_SPINLOCK_INITIALIZER"]),
                      ("dma_map_page", ["get_memory_map"]), ("printk", ["dprintf"])):
        if n in got and (got[n].get("category") != "C-replace"
                         or not set(any_of) & set(got[n].get("haiku_api") or [])):
            fail(f"{rel}: '{n}' is C-replace and its haiku_api has one of {any_of}")
    for n in ("request_firmware", "release_firmware"):
        if n in got and got[n].get("category") != "D-ignore":
            fail(f"{rel}: '{n}' is D-ignore: only gf100_gr_load_fw calls it, for the external firmware "
                 f"files that the driver does not use (firmware/README.md)")
    for n in ("set_bit", "clear_bit", "__set_bit", "__mutex_init"):
        if n in got and got[n].get("category") == "X-not-linux":
            fail(f"{rel}: '{n}' is a Linux kernel symbol, not X-not-linux")
    for n, e in got.items():
        if n.startswith("dma_") and set(e.get("haiku_api") or []) & {"malloc", "free", "calloc"}:
            fail(f"{rel}: '{n}' is about physical addresses for the device; malloc and free do not replace it")
    for n in ("agp_enable", "agp_backend_acquire", "pci_enable_msi"):
        if n in got and got[n].get("category") in ("A-reimplement", "B-extract"):
            fail(f"{rel}: '{n}' is not a hardware algorithm or hardware data of the GPU")
    md = os.path.join(ROOT, "analysis", "linux_deps.md")
    if not os.path.exists(md) or len(open(md, errors="replace").read().split("\n")) < 30:
        fail("analysis/linux_deps.md: missing or under 30 lines")
    else:
        # Second review of B4: the tables of the document come from the JSON.
        mdt = open(md, errors="replace").read()
        rows = {m.group(1): int(m.group(2))
                for m in re.finditer(r"^\|\s*`(\w+)`\s*\|\s*(\d+)\s*\|", mdt, re.M)}
        wrong = sorted(n for n in b4_count if rows.get(n) != b4_count[n])
        if wrong:
            fail(f"analysis/linux_deps.md: {len(wrong)} symbols have no table row `| \`symbol\` | count | ...` "
                 f"with the count of the JSON file, for example {wrong[:5]}. Let the tool write the tables")
    tool = os.path.join(ROOT, "tools", "linux_deps.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/linux_deps.py: missing, or no --check option (docs/tasks/B4.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/linux_deps.py --check (run {run}): {rel} is not what the tool generates")
                break

# C1 register database ------------------------------------------------
try:
    import yaml
except ImportError:
    yaml = None
reg_files = sorted(glob.glob(os.path.join(ROOT, "hardware/registers/*.yaml")))
if reg_files and yaml is None:
    notes.append("hardware/registers: not checked (no PyYAML)")
elif reg_files and "C1" not in SKIP:
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import rnndb
    macros = {}
    for text in src_lines("nvkm/engine/gr/gf100.h") or []:
        m = re.match(r"#define (\w+)\(([\w, ]+)\)\s+(\(.*\))\s*$", text)
        if m:
            macros[m.group(1)] = ([a.strip() for a in m.group(2).split(",")], m.group(3))

    def c1_address(reg):
        m = re.match(r"0x[0-9a-fA-F]+\b", reg)
        if m:
            return int(m.group(0), 16)
        m = re.fullmatch(r"(\w+)\((.*)\)", reg)
        if m and m.group(1) in macros:
            names, body = macros[m.group(1)]
            args = [a.strip() for a in m.group(2).split(",")]
            if len(args) != len(names):
                return None
            for n, a in zip(names, args):
                body = re.sub(r"\(%s\)" % n, "(" + a + ")", body)
            body = re.sub(r"\b[A-Za-z_]\w*(->\w+)*", "0", re.sub(r"0x[0-9a-fA-F]+", lambda h: str(int(h.group(0), 16)), body))
            try:
                return int(eval(body, {"__builtins__": {}}))
            except Exception:
                return None
        return None

    want = {}
    for a in load_json("registers/mmio_accesses.json") or []:
        addr = c1_address(a["reg"])
        grp = "pbdma" if a["subsystem"] == "fifo" and addr is not None and 0x40000 <= addr < 0x60000 \
            else a["subsystem"]
        w = want.setdefault(grp, {}).setdefault(a["reg"], {"address": addr, "source": set(), "r": False, "w": False})
        w["source"].add(f"{a['file']}:{a['line']}")
        w["r"] |= a["op"] in ("rd32", "mask")
        w["w"] |= a["op"] in ("wr32", "mask")
    have = {os.path.basename(p)[:-5]: p for p in reg_files}
    if sorted(have) != sorted(want):
        fail(f"hardware/registers: the files must be {sorted(g + '.yaml' for g in want)}; missing "
             f"{sorted(set(want) - set(have))}, extra {sorted(set(have) - set(want))}")
    for grp, path in sorted(have.items()):
        rel = os.path.relpath(path, ROOT)
        try:
            entries = yaml.safe_load(open(path)) or []
        except yaml.YAMLError as e:
            fail(f"{rel}: invalid YAML: {e}")
            continue
        if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
            fail(f"{rel}: must be a list of entries")
            continue
        got = {str(e.get("reg")): e for e in entries}
        exp = want.get(grp, {})
        if sorted(got) != sorted(exp) or len(entries) != len(exp):
            fail(f"{rel}: {len(entries)} entries, B3 has {len(exp)} distinct 'reg' texts for this file; "
                 f"missing {sorted(set(exp) - set(got))[:5]}, extra {sorted(set(got) - set(exp))[:5]}")
        bad = {}
        for reg, e in got.items():
            w = exp.get(reg)
            if w is None:
                continue
            addr = w["address"]
            look = rnndb.lookup(addr) if addr is not None else None
            checks = {
                "address": e.get("address") == (None if addr is None else "0x%06x" % addr),
                "name": e.get("name") == (look["name"] if look else None),
                "name_source": e.get("name_source") == ("rnndb:" + look["file"] if look else "none"),
                "fields": [(f.get("name"), f.get("shift"), f.get("width")) for f in e.get("fields") or []]
                == [(f["name"], f["shift"], f["width"]) for f in (look["fields"] if look else [])],
                "source": e.get("source") == sorted(w["source"]),
                "readable": e.get("readable") is w["r"],
                "writable": e.get("writable") is w["w"],
                "status": e.get("status") == "SOURCE_ONLY",
                "width": e.get("width") == 32,
            }
            for k, ok in checks.items():
                if not ok:
                    bad.setdefault(k, []).append(reg)
        for k, regs in sorted(bad.items()):
            fail(f"{rel}: '{k}' is wrong in {len(regs)} entries, for example reg {regs[0]!r} "
                 f"(rules: docs/tasks/C1.md)")
    readme = os.path.join(ROOT, "hardware/registers/README.md")
    text = open(readme, errors="replace").read() if os.path.exists(readme) else ""
    miss = [g for g in sorted(want) if g + ".yaml" not in text]
    if miss:
        fail(f"hardware/registers/README.md: missing, or no line for {miss}")
    tool = os.path.join(ROOT, "tools", "build_regdb.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/build_regdb.py: missing, or no --check option (docs/tasks/C1.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/build_regdb.py --check (run {run}): hardware/registers is not what the tool generates")
                break

# C2 firmware ---------------------------------------------------------
fw_path = os.path.join(ROOT, "firmware", "manifest.yaml")
if os.path.exists(fw_path) and yaml is not None and "C2" not in SKIP:
    import hashlib
    import struct
    rel = "firmware/manifest.yaml"
    try:
        man = yaml.safe_load(open(fw_path)) or {}
    except yaml.YAMLError as e:
        fail(f"{rel}: invalid YAML: {e}")
        man = {}
    if not isinstance(man, dict):
        fail(f"{rel}: must be a mapping with built_in, external and load_sequence")
        man = {}
    FUC = "nvkm/engine/gr/fuc/"
    want_bi = {}
    for hdr, asm, engine in ((FUC + "hubgk110.fuc3.h", FUC + "hubgk110.fuc3", "fecs"),
                             (FUC + "gpcgk110.fuc3.h", FUC + "gpcgk110.fuc3", "gpccs")):
        L = src_lines(hdr) or []
        inc = sorted(set(re.findall(r'#include "([\w.]+)"', "\n".join(src_lines(asm) or []))))
        cur = None
        for i, text in enumerate(L, 1):
            m = re.match(r"static uint32_t (\w+)\[\] = \{", text)
            if m:
                cur = {"name": m.group(1), "engine": engine, "kind": m.group(1).rsplit("_", 1)[1],
                       "file": hdr, "first_line": i, "words": [], "asm_source": asm, "asm_includes": inc,
                       "license": "MIT" if "SPDX-License-Identifier: MIT" in L[0] else None}
            elif cur and text.startswith("};"):
                cur["last_line"] = i
                blob = struct.pack("<%dI" % len(cur["words"]), *cur["words"])
                cur.update(words=len(cur["words"]), size_bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())
                want_bi[cur["name"]] = cur
                cur = None
            elif cur:
                cur["words"] += [int(w, 16) for w in re.findall(r"\b0x[0-9a-fA-F]{8}\b", text.split("/*")[0])]
    got_bi = {str(e.get("name")): e for e in man.get("built_in") or [] if isinstance(e, dict)}
    if sorted(got_bi) != sorted(want_bi):
        fail(f"{rel}: 'built_in' must have the arrays {sorted(want_bi)}")
    bad = {}
    for n, w in want_bi.items():
        for k, v in w.items():
            if n in got_bi and got_bi[n].get(k) != v:
                bad.setdefault(k, []).append(n)
        if n in got_bi and got_bi[n].get("source") != "built-in":
            bad.setdefault("source", []).append(n)
    for k, names in sorted(bad.items()):
        fail(f"{rel}: built_in '{k}' is wrong for {names} (rules: docs/tasks/C2.md)")
    gf = src_lines("nvkm/engine/gr/gf100.c") or []
    want_ex = {}
    for i, text in enumerate(gf, 1):
        m = re.search(r'gf100_gr_load_fw\(gr, "(\w+)", &gr->(\w+)\.(\w+)\)', text)
        if m:
            want_ex[m.group(1)] = {"filename": m.group(1), "engine": m.group(2),
                                   "kind": "code" if m.group(3) == "inst" else "data",
                                   "requested_at": f"nvkm/engine/gr/gf100.c:{i}"}
    got_ex = {str(e.get("filename")): e for e in man.get("external") or [] if isinstance(e, dict)}
    if sorted(got_ex) != sorted(want_ex):
        fail(f"{rel}: 'external' must have the files {sorted(want_ex)}")
    for n, w in want_ex.items():
        e = got_ex.get(n, {})
        if any(e.get(k) != v for k, v in w.items()) or e.get("source") != "external-file" \
                or e.get("distribution") != "do-not-distribute" or e.get("needed") is not False:
            fail(f"{rel}: external '{n}': engine, kind and requested_at come from the gf100_gr_load_fw "
                 f"line; source external-file, distribution do-not-distribute, needed false")
    want_seq, inside = [], False
    for i, text in enumerate(gf, 1):
        if text.startswith("gf100_gr_init_ctxctl_int("):
            inside = True
        elif inside and text.startswith("}"):
            break
        elif inside:
            for m in re.finditer(r"\b(nvkm_\w+|gf100_gr_\w+)\(", text):
                want_seq.append((i, m.group(1)))
    got_seq = [(e.get("line"), e.get("call")) for e in man.get("load_sequence") or [] if isinstance(e, dict)]
    if got_seq != want_seq:
        fail(f"{rel}: 'load_sequence' must have the {len(want_seq)} calls of gf100_gr_init_ctxctl_int in "
             f"order (line, call); first difference at entry "
             f"{next((k for k, (a, b) in enumerate(zip(got_seq, want_seq)) if a != b), min(len(got_seq), len(want_seq))) + 1}")
    if any(not isinstance(e.get("what"), str) or len(e["what"].split()) < 4
           for e in man.get("load_sequence") or [] if isinstance(e, dict)):
        fail(f"{rel}: every load_sequence entry needs a 'what' of 4 words or more")
    readme = os.path.join(ROOT, "firmware", "README.md")
    text = open(readme, errors="replace").read() if os.path.exists(readme) else ""
    if len(text.split("\n")) < 50:
        fail("firmware/README.md: missing or under 50 lines")
    for word in ("NvGrUseFW", "gf100_gr_load", "gf100_gr_nofw", "gf100_gr_init_ctxctl_int", "MIT",
                 "Not known"):
        if word not in text:
            fail(f"firmware/README.md: does not mention {word}")
    for f, ln in set(re.findall(r"(nvkm/[\w/.]+\.[ch]):(\d+)", text)):
        L = src_lines(f)
        if L is None or int(ln) > len(L):
            fail(f"firmware/README.md: cites {f}:{ln}, which does not exist")
    # The shader of the reference run (task C5a) is the one exception: it
    # is 160 bytes that Mesa generated from this project's own source.
    if [f for f in glob.glob(os.path.join(ROOT, "firmware", "*.bin"))
            if os.path.basename(f) != "compute_add1.bin"]:
        fail("firmware/: no binary files in the repository (write them under build/)")
    tool = os.path.join(ROOT, "tools", "fw_manifest.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/fw_manifest.py: missing, or no --check option (docs/tasks/C2.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/fw_manifest.py --check (run {run}): {rel} is not what the tool generates")
                break

# C3 subsystem models (analysis/hwmodel/<subsystem>.json) ---------------
C3_TASKS = {"C3a": ["mc", "bar", "imem", "mmu", "fb", "top"],
            "C3b": ["privring", "ltc", "timer"],
            "C3c": ["fifo"], "C3d": ["chan"], "C3e": ["gr"]}
# Models of a table that is not a chipset member: name -> (owning subsystem, table).
C3_EXTRA = {"chan": ("fifo", "gk110_chan"),
            # gk110b_gr_new passes a firmware-interface list, not the table
            "gr": ("gr", "gk110b_gr")}
hw_files = sorted(glob.glob(os.path.join(ROOT, "analysis/hwmodel/*.json")))
for task, names in C3_TASKS.items():
    if re.search(r"^\|\s*%s\s*\|\s*DONE\b" % task, status, re.M):
        for n in names:
            for rel in (f"analysis/hwmodel/{n}.json", f"docs/hardware-model/{n}.md"):
                if not os.path.exists(os.path.join(ROOT, rel)):
                    fail(f"{rel}: missing, and docs/STATUS.md marks {task} DONE")
if hw_files and "C3" not in SKIP:
    c3_defs = {}
    for d, _, fs in os.walk(os.path.join(NV, "nvkm"), followlinks=True):
        for f in fs:
            if f.endswith(".c"):
                path = os.path.join(d, f)
                relp = os.path.relpath(path, NV)
                for i, text in enumerate(open(path, errors="replace").read().split("\n"), 1):
                    m = re.match(r"^(\w+)\(", text)
                    if m:
                        c3_defs.setdefault(("F", m.group(1)), (relp, i))
                    m = re.match(r"^(\w+) = \{", text)
                    if m:
                        c3_defs.setdefault(("T", m.group(1)), (relp, i))
    c3_chip, inside = {}, False
    for i, text in enumerate(src_lines("nvkm/engine/device/base.c") or [], 1):
        if text.startswith("nvf1_chipset"):
            inside = True
        elif inside and text.startswith("};"):
            break
        elif inside:
            m = re.match(r"\s*\.(\w+)\s*=\s*\{\s*0x[0-9a-f]+,\s*(\w+)\s*\}", text)
            if m:
                c3_chip[m.group(1)] = m.group(2)
    c3_acc = {}
    for a in load_json("registers/mmio_accesses.json") or []:
        c3_acc.setdefault((a["function"], a["file"]), []).append(
            {"file": a["file"], "line": a["line"], "op": a["op"], "reg": a["reg"]})

    def c3_body(f, ln):
        L = src_lines(f) or []
        j = ln
        while j <= len(L) and not L[j - 1].startswith("}"):
            j += 1
        return L, ln, j

    def c3_table(name, parent):
        f, ln = c3_defs[("T", name)]
        L, a, b = c3_body(f, ln)
        out = []
        for text in L[a:b - 1]:
            m = re.match(r"\s*\.([\w.]+)\s*=\s*&?(\w+)", text)
            if not m:
                continue
            member, value = m.group(1), m.group(2)
            if ("F", value) in c3_defs:
                kind, (vf, vl) = "function", c3_defs[("F", value)]
            elif ("T", value) in c3_defs:
                kind, (vf, vl) = "table", c3_defs[("T", value)]
            else:
                kind, vf, vl = "value", None, None
            out.append({"member": member, "value": value, "kind": kind, "file": vf, "line": vl,
                        "parent": parent,
                        "accesses": sorted(c3_acc.get((value, vf), []), key=lambda x: x["line"])
                        if kind == "function" else []})
            if kind == "table" and parent is None:
                out += c3_table(value, member)
        return out

    C3_ROLE = {"init", "interrupt", "teardown", "runtime", "data"}
    C3_BAD = {"memory controller": "mc is the master control", "instantiated": "imem is instance memory",
              "multi-gpu": "top is the device topology table", "workqueue": "HWW is a hardware warning"}
    for path in hw_files:
        rel = os.path.relpath(path, ROOT)
        name = os.path.basename(path)[:-5]
        hw = load_json(rel)
        if not isinstance(hw, dict):
            fail(f"{rel}: must be an object")
            continue
        ctor = c3_chip.get(C3_EXTRA[name][0] if name in C3_EXTRA else name)
        if ctor is None or ("F", ctor) not in c3_defs:
            fail(f"{rel}: '{name}' is not a member of nvf1_chipset")
            continue
        cf, cl = c3_defs[("F", ctor)]
        L, a, b = c3_body(cf, cl)
        tabs = [t for t in re.findall(r"&(\w+)", "\n".join(L[a - 1:b])) if ("T", t) in c3_defs]
        if name in C3_EXTRA:
            tabs = [C3_EXTRA[name][1]]
        if not tabs:
            fail(f"{rel}: the checker finds no function table in {ctor}; ask the scaffold")
            continue
        tf, tl = c3_defs[("T", tabs[0])]
        if hw.get("subsystem") != name or hw.get("constructor") != {"name": ctor, "file": cf, "line": cl} \
                or hw.get("table") != {"name": tabs[0], "file": tf, "line": tl}:
            fail(f"{rel}: 'subsystem', 'constructor' or 'table' is wrong; the constructor is {ctor} "
                 f"({cf}:{cl}) and its function table is {tabs[0]} ({tf}:{tl})")
        want = c3_table(tabs[0], None)
        got = hw.get("members") if isinstance(hw.get("members"), list) else []
        key = lambda e: (e.get("parent"), e.get("member"), e.get("value"))
        if [key(e) for e in got if isinstance(e, dict)] != [key(e) for e in want]:
            fail(f"{rel}: 'members' must be the {len(want)} members of {tabs[0]} in source order, each "
                 f"nested table followed by its own members (parent = the member name); got {len(got)}")
            continue
        bad = {}
        for e, w in zip(got, want):
            tag = (w["parent"] + "." if w["parent"] else "") + w["member"]
            for k in ("kind", "file", "line", "accesses"):
                if e.get(k) != w[k]:
                    bad.setdefault(k, []).append(tag)
            if e.get("role") not in C3_ROLE or not isinstance(e.get("needed_for_compute"), bool):
                bad.setdefault("role or needed_for_compute", []).append(tag)
            if not isinstance(e.get("what"), str) or len(e["what"].split()) < 6:
                bad.setdefault("what (6 words or more)", []).append(tag)
            if e.get("certainty") not in ("KNOWN", "INFERRED", "UNKNOWN"):
                bad.setdefault("certainty", []).append(tag)
            elif w["kind"] == "function" and e["certainty"] != "UNKNOWN":
                ev = e.get("evidence") if isinstance(e.get("evidence"), dict) else {}
                FL, fa, fb = c3_body(w["file"], w["line"])
                ln, quote = ev.get("line"), str(ev.get("quote", "")).strip()
                if not (isinstance(ln, int) and fa <= ln <= fb and len(quote) >= 10 and quote in FL[ln - 1]):
                    bad.setdefault("evidence (a line inside the function and a quote of 10 characters or "
                                   "more from that line)", []).append(tag)
            m = w["member"].split(".")[-1]
            if w["kind"] == "function" and m.startswith("intr") and e.get("role") != "interrupt":
                bad.setdefault("role (a member named intr... is interrupt)", []).append(tag)
            if w["kind"] == "function" and m in ("dtor", "fini") and e.get("role") != "teardown":
                bad.setdefault("role (dtor and fini are teardown)", []).append(tag)
        for k, tags in sorted(bad.items()):
            fail(f"{rel}: wrong {k} in {len(tags)} members: {tags[:6]}")
        deps = hw.get("depends_on")
        if not isinstance(deps, list) or any(d not in c3_chip or d == name for d in deps):
            fail(f"{rel}: 'depends_on' must be a list of other nvf1_chipset member names")
        if not isinstance(hw.get("summary"), str) or len(hw["summary"].split()) < 30:
            fail(f"{rel}: 'summary' needs 30 words or more")
        texts = " ".join([str(hw.get("summary", ""))] + [str(e.get("what", "")) for e in got]).lower()
        for w_, right in C3_BAD.items():
            if w_ in texts:
                fail(f"{rel}: the text says \"{w_}\". {right}")
        if not os.path.exists(os.path.join(ROOT, "docs/hardware-model", name + ".md")):
            fail(f"docs/hardware-model/{name}.md: missing (the tool writes it from {rel})")
    tool = os.path.join(ROOT, "tools", "hwmodel.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/hwmodel.py: missing, or no --check option (docs/tasks/C3a.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/hwmodel.py --check (run {run}): analysis/hwmodel or docs/hardware-model is "
                     f"not what the tool generates")
                break

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

# Phase D: scaffold acceptance tests ---------------------------------
# name: (trigger file, recorded sha256 of the test, source files to compile with it)
ACCEPT = {
    "d1_accept": ("src/hw/RegisterIO.h",
                  "afbe40a9bfc487e23210f17e0acf171bec6ec120c332027a79135a5cfefee2bf", "src/hw/*.cpp"),
    "d2_accept": ("src/mmu/PageTable.h", "dd82a560200b061908c8e37964a67941cb855b8b872a5bb444618dfc3448ed03", "src/mmu/*.cpp"),
    "d3_accept": ("src/fifo/PushBuffer.h", "20a7e97b35b82552d6d3797aa8a87afd2a3f2ae60f9b2724e658dcea164a0344", "src/fifo/*.cpp"),
    "d5_accept": ("src/compute/LaunchDesc.h", "1c87c1e7e58221aeaf545996263b07fadd8d92baea83d935b4714aa590635881", "src/compute/*.cpp src/fifo/*.cpp"),
}
for name, (trigger, sha, sources) in ACCEPT.items():
    test = os.path.join(ROOT, "tests", "accept", name + ".cpp")
    if os.path.exists(test):
        import hashlib
        if hashlib.sha256(open(test, "rb").read()).hexdigest() != sha:
            fail(f"tests/accept/{name}.cpp was changed. It is the scaffold's test: restore it with "
                 f"`git checkout main -- tests/accept/{name}.cpp`")
    if not os.path.exists(os.path.join(ROOT, trigger)) or name.split("_")[0].upper() in SKIP:
        continue
    import subprocess
    out = os.path.join(ROOT, "build", "accept")
    os.makedirs(out, exist_ok=True)
    srcs = sorted(f for g in sources.split() for f in glob.glob(os.path.join(ROOT, g)))
    r = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I" + os.path.join(ROOT, "src"),
                        test] + srcs + ["-o", os.path.join(out, name)], capture_output=True, text=True)
    if r.returncode != 0:
        first = [ln for ln in r.stderr.split("\n") if "error" in ln][:3]
        fail(f"tests/accept/{name}.cpp does not compile with -Wall -Wextra -Werror: {first}")
        continue
    try:
        r = subprocess.run([os.path.join(out, name)], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        fail(f"tests/accept/{name}: no result after 60 s")
        continue
    if r.returncode != 0:
        lines = [ln for ln in r.stdout.split("\n") if ln.startswith("FAIL")]
        fail(f"tests/accept/{name}: {len(lines)} checks fail, first: {lines[:3]}")
    for src in srcs + sorted(glob.glob(os.path.join(ROOT, os.path.dirname(sources.split()[0]), "*.h"))):
        text = open(src, errors="replace").read()
        if re.search(r"#include\s*<(linux|drm|asm|sys)/", text) or "KernelExport.h" in text:
            fail(f"{os.path.relpath(src, ROOT)}: phase D code is plain C++17 with standard headers only")
    own = os.path.join(ROOT, "tests", "test_" + trigger.split("/")[-1].replace(".h", "").lower() + ".cpp")
    n = len(re.findall(r"\bCHECK\(", open(own, errors="replace").read())) if os.path.exists(own) else 0
    if n < 15:
        fail(f"{os.path.relpath(own, ROOT)}: your own tests, 15 CHECK(...) lines or more; found {n}")
    r = subprocess.run(["make", "-s", "-C", os.path.join(ROOT, "tests")], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"make -C tests fails: {(r.stdout + r.stderr).strip().splitlines()[-2:]}")

# D4 trace comparison tool (Python acceptance test) -----------------------
d4_test = os.path.join(ROOT, "tests", "accept", "d4_accept.py")
if os.path.exists(d4_test):
    import hashlib
    if hashlib.sha256(open(d4_test, "rb").read()).hexdigest() != "b3d3fa90e1437d05f79866749e0da8ca0b86f7edaaa8d20a50aeba4827091729":
        fail("tests/accept/d4_accept.py was changed. It is the scaffold's test: restore it with "
             "`git checkout main -- tests/accept/d4_accept.py`")
d4_tool = os.path.join(ROOT, "tools", "compare_register_traces.py")
if os.path.exists(d4_tool) and "D4" not in SKIP:
    import subprocess
    try:
        r = subprocess.run([sys.executable, d4_test], cwd=ROOT, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            lines = [ln for ln in r.stdout.split("\n") if ln.startswith("FAIL")]
            last = (r.stderr.strip().splitlines() or [""])[-1]
            fail(f"tests/accept/d4_accept.py: {len(lines)} checks fail, first: {lines[:3]} {last[:160]}")
    except subprocess.TimeoutExpired:
        fail("tests/accept/d4_accept.py: no result after 120 s")
    own = os.path.join(ROOT, "tests", "test_compare_traces.py")
    n = len(re.findall(r"\bcheck\(", open(own, errors="replace").read())) if os.path.exists(own) else 0
    if n < 15:
        fail(f"tests/test_compare_traces.py: your own tests, 15 check(...) lines or more; found {n}")
    else:
        r = subprocess.run([sys.executable, own], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"tests/test_compare_traces.py fails: {(r.stdout + r.stderr).strip().splitlines()[-1:]}")
    if not os.path.exists(os.path.join(ROOT, "docs", "register-traces.md")):
        fail("docs/register-traces.md: missing (docs/tasks/D4.md)")

# C4a source provenance of the constants in src/ --------------------------
prov_md = os.path.join(ROOT, "docs", "register-provenance.md")
if os.path.exists(prov_md) and "C4a" not in SKIP:
    C4_CIT = re.compile(r"([\w./-]*\w\.(?:c|h)):(\d+)")
    c4_index = {}
    for base, tree in ((NV, "nouveau"), (os.path.join(ROOT, "reference", "mesa"), "mesa")):
        for d, _, fs in os.walk(base, followlinks=True):
            for f in fs:
                if f.endswith((".c", ".h")):
                    c4_index.setdefault(f, []).append((tree, os.path.relpath(os.path.join(d, f), base)))
    uncited, unresolved, n_const = [], [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "src", "*", "*.h")) +
                       glob.glob(os.path.join(ROOT, "src", "*", "*.cpp"))):
        rel = os.path.relpath(path, ROOT)
        if rel.startswith("src/hw/"):
            continue  # the register access layer has no hardware constants
        L = open(path, errors="replace").read().split("\n")
        for i, line in enumerate(L):
            code = re.sub(r'"[^"]*"', '""', line.split("//")[0])
            if not re.search(r"0x[0-9a-fA-F]{2,}|\bconstexpr\b", code):
                continue
            n_const += 1
            com = line.split("//", 1)[1] if "//" in line else ""
            j = i - 1
            while j >= 0 and L[j].strip().startswith("//"):
                com += " " + L[j]
                j -= 1
            cits = C4_CIT.findall(com)
            if not cits and "no source:" not in com:
                uncited.append(f"{rel}:{i + 1}")
            for f, ln in cits:
                cand = [c for c in c4_index.get(os.path.basename(f), []) if c[1].endswith(f)]
                ok = False
                if len(cand) == 1:
                    base = NV if cand[0][0] == "nouveau" else os.path.join(ROOT, "reference", "mesa")
                    n_lines = len(open(os.path.join(base, cand[0][1]), errors="replace").read().split("\n"))
                    ok = 0 < int(ln) <= n_lines
                if not ok:
                    unresolved.append(f"{rel}:{i + 1} ({f}:{ln})")
    if uncited:
        fail(f"src/: {len(uncited)} of {n_const} lines with a hardware constant have no source: add "
             f"`// path/file.c:LINE` on the line or in the comment above it, or `// no source: reason` "
             f"for plain arithmetic. First: {uncited[:6]}")
    if unresolved:
        fail(f"src/: {len(unresolved)} citations do not name exactly one file under reference/nouveau or "
             f"reference/mesa with that line (write enough of the path to be unique): {unresolved[:6]}")
    tool = os.path.join(ROOT, "tools", "provenance.py")
    if not os.path.exists(tool) or "--check" not in open(tool, errors="replace").read():
        fail("tools/provenance.py: missing, or no --check option (docs/tasks/C4a.md)")
    else:
        import subprocess
        for run in (1, 2):
            r = subprocess.run([sys.executable, tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/provenance.py --check (run {run}): docs/register-provenance.md is not what the "
                     f"tool generates")
                break
    text = open(prov_md, errors="replace").read()
    rows = len(re.findall(r"^\|\s*`src/", text, re.M))
    if rows < n_const - len(uncited):
        fail(f"docs/register-provenance.md: {rows} table rows that start with `src/...`; src/ has {n_const} "
             f"constant lines")
    if "SOURCE_ONLY" not in text:
        fail("docs/register-provenance.md: no status column with SOURCE_ONLY")

# C4b design documents ---------------------------------------------------
C4B_DOCS = ["04-mmu-design.md", "05-fifo-design.md", "06-gr-design.md", "07-firmware-analysis.md"]
C4B_SECTIONS = ["Goal", "What Nouveau does", "Haiku driver design", "Haiku interfaces", "Host tests",
                "Not known"]
c4b_present = [d for d in C4B_DOCS if os.path.exists(os.path.join(ROOT, "docs", d))]
if re.search(r"^\|\s*C4b\s*\|\s*DONE\b", status, re.M):
    for d in C4B_DOCS:
        if d not in c4b_present:
            fail(f"docs/{d}: missing, and docs/STATUS.md marks C4b DONE")
if c4b_present and "C4b" not in SKIP:
    c4b_regs = set()
    for path in glob.glob(os.path.join(ROOT, "hardware/registers/*.yaml")):
        for m in re.finditer(r"^\s*address: '(0x[0-9a-f]{6})'", open(path).read(), re.M):
            c4b_regs.add(m.group(1))
    c4b_words = set()
    for sub in ("os", "private/kernel", "private/drivers"):
        for d, _, fs in os.walk(os.path.join(ROOT, "reference", "haiku", "headers", sub), followlinks=True):
            for f in fs:
                if f.endswith(".h"):
                    c4b_words |= set(re.findall(r"[A-Za-z_]\w+", open(os.path.join(d, f), errors="replace").read()))
    MESA4 = os.path.join(ROOT, "reference", "mesa")
    for doc in c4b_present:
        rel = "docs/" + doc
        text = open(os.path.join(ROOT, rel), errors="replace").read()
        if len(text.split("\n")) < 70:
            fail(f"{rel}: under 70 lines")
        heads = re.findall(r"^## (.+?)\s*$", text, re.M)
        if [h for h in heads if h in C4B_SECTIONS] != C4B_SECTIONS:
            fail(f"{rel}: needs the sections {C4B_SECTIONS} as `## ` headings, in this order")
            continue
        sec = {h: text.split("## " + h, 1)[1].split("\n## ", 1)[0] for h in C4B_SECTIONS}
        cites, bad = set(), []
        for f, ln in re.findall(r"((?:nvkm|src/gallium)/[\w/.-]+\.[ch]):(\d+)", text):
            base = MESA4 if f.startswith("src/gallium") else NV
            cites.add((f, ln))
            try:
                n = len(open(os.path.join(base, f), errors="replace").read().split("\n"))
            except OSError:
                n = 0
            if int(ln) > n or int(ln) < 1:
                bad.append(f"{f}:{ln}")
        if bad:
            fail(f"{rel}: cites lines that do not exist: {sorted(set(bad))[:5]}")
        n_nv = len(set(re.findall(r"((?:nvkm|src/gallium)/[\w/.-]+\.[ch]):(\d+)", sec["What Nouveau does"])))
        if n_nv < 8:
            fail(f"{rel}: 'What Nouveau does' has {n_nv} source citations (file:line); 8 or more")
        unknown = sorted(set(re.findall(r"\b0x[0-9a-f]{6}\b", text)) - c4b_regs)
        if unknown:
            fail(f"{rel}: register addresses that are not in hardware/registers/*.yaml: {unknown[:6]}. "
                 f"Use only registers of the database (6 hex digits), or write the value another way "
                 f"if it is not a register")
        apis = re.findall(r"`([A-Za-z_]\w+)\(\)`", sec["Haiku interfaces"])
        missing = sorted(a for a in set(apis) if a not in c4b_words)
        if len(set(apis)) < 3:
            fail(f"{rel}: 'Haiku interfaces' names {len(set(apis))} functions as `name()`; 3 or more")
        if missing:
            fail(f"{rel}: 'Haiku interfaces' names functions that are not in reference/haiku/headers: "
                 f"{missing[:6]}")
        paths = re.findall(r"`((?:src|tests|tools|analysis|hardware|docs|firmware)/[\w./-]+)`", text)
        gone = sorted(p for p in set(paths) if not os.path.exists(os.path.join(ROOT, p)))
        if gone:
            fail(f"{rel}: names files that do not exist: {gone[:6]}")
        if not re.search(r"`tests/[\w./-]+`", sec["Host tests"]):
            fail(f"{rel}: 'Host tests' names no file under tests/ (write \"none yet\" items in 'Not known')"
                 if doc != "07-firmware-analysis.md" and doc != "06-gr-design.md" else
                 f"{rel}: 'Host tests' must name the test files that exist, or `tests/` and what is missing")
        if len(re.findall(r"^\s*[-*] ", sec["Not known"], re.M)) < 3:
            fail(f"{rel}: 'Not known' needs 3 list items or more")
        for w_, right in {"memory controller": "mc is the master control",
                          "front end command scheduler": "FECS is not expanded in the source",
                          "pixel pipeline": "PPC is not expanded in the source"}.items():
            if w_ in text.lower():
                fail(f"{rel}: the text says \"{w_}\". {right}")

# C5a shader binary and launch descriptor of the reference run ------------
c5a_tool = os.path.join(ROOT, "tools", "shader_extract.py")
c5a_log = os.path.join(ROOT, "reference", "linux-run", "compute_test.log")
c5a_done = re.search(r"^\| C5a \| DONE", open(os.path.join(ROOT, "docs", "STATUS.md")).read(), re.M)
if (os.path.exists(c5a_tool) or c5a_done) and "C5a" not in SKIP:
    import hashlib, struct, subprocess
    res_txt = open(os.path.join(ROOT, "reference", "linux-run", "RESULT.txt")).read().split("\n")
    if "PASS" not in res_txt:
        fail("reference/linux-run/RESULT.txt: no line PASS")
    L = open(c5a_log).read().split("\n")
    i = max(k for k, l in enumerate(L) if l.startswith("shader binary code"))
    size = int(re.search(r"0x([0-9a-f]+) bytes", L[i]).group(1), 16)
    words, k = [], i + 1
    while len(words) < size // 4:
        words += L[k].split(); k += 1
    blob = struct.pack("<%dI" % len(words), *[int(w, 16) for w in words])
    q = L.index("Queue Meta Data:")
    qmd = []
    for l in L[q + 1:]:
        m = re.match(r"^   (\S+)\s*: (.*\S)\s*$", l)
        if not m:
            break
        qmd.append((m.group(1), m.group(2)))
    binp = os.path.join(ROOT, "firmware", "compute_add1.bin")
    if not os.path.exists(binp):
        fail("firmware/compute_add1.bin: missing (docs/tasks/C5a.md)")
    elif open(binp, "rb").read() != blob:
        got = open(binp, "rb").read()
        fail(f"firmware/compute_add1.bin: {len(got)} bytes, first word {got[:4].hex()}; it must be the "
             f"{size} bytes of the last code dump of the log (line {i + 1}), each word little-endian: "
             f"the first 4 bytes are {blob[:4].hex()}")
    rel = "analysis/linux_run_shader.json"
    j = load_json(rel) if os.path.exists(os.path.join(ROOT, rel)) else None
    if not isinstance(j, dict):
        fail(f"{rel}: missing or not an object (docs/tasks/C5a.md)")
    else:
        if j.get("log_line") != i + 1 or j.get("size_bytes") != size:
            fail(f"{rel}: log_line and size_bytes must be {i + 1} and {size} (the last code dump)")
        if [str(w).lower() for w in j.get("words", [])] != ["0x" + w for w in words]:
            fail(f"{rel}: 'words' must be the {len(words)} words of the log as \"0x........\", in order")
        if j.get("sha256") != hashlib.sha256(blob).hexdigest():
            fail(f"{rel}: 'sha256' is not the sha256 of the correct binary")
        got = [(e.get("name"), e.get("value")) for e in j.get("qmd", []) if isinstance(e, dict)]
        if got != qmd:
            diff = next((n for n, (a, b) in enumerate(zip(got, qmd)) if a != b), min(len(got), len(qmd)))
            fail(f"{rel}: 'qmd' has {len(got)} entries, the log has {len(qmd)} fields; first difference at "
                 f"entry {diff}: expected {qmd[diff] if diff < len(qmd) else 'nothing'}")
        if "NVF1" not in str(j.get("renderer")) or "25.2.8" not in str(j.get("version")):
            fail(f"{rel}: 'renderer' and 'version' must be the text of the log")
        csrc = open(os.path.join(ROOT, "tools", "guest", "files", "compute_test.c")).read()
        want_src = re.findall(r'^\t"(.*)\\n"', csrc[csrc.index("kSource"):csrc.index("int\nmain")], re.M)
        want_src = [x.replace("\\t", "\t") for x in want_src]
        if j.get("source") != want_src:
            fail(f"{rel}: 'source' must be the {len(want_src)} lines of kSource in "
                 f"tools/guest/files/compute_test.c (first: {want_src[0]!r}; a tab is a real tab)")
    rel = "firmware/compute_add1.md"
    if not os.path.exists(os.path.join(ROOT, rel)):
        fail(f"{rel}: missing (docs/tasks/C5a.md)")
    else:
        md = open(os.path.join(ROOT, rel)).read()
        secs = dict((h, b) for h, b in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", md, re.M | re.S))
        need = ["Source", "How it was made", "Code", "Launch descriptor", "Not known"]
        if [h.strip() for h in secs] != need:
            fail(f"{rel}: the '## ' sections must be {need}, in this order")
        else:
            if hashlib.sha256(blob).hexdigest() not in secs["Code"]:
                fail(f"{rel}: 'Code' does not have the sha256 of the binary")
            if [w.lower().replace("0x", "") for w in re.findall(r"\b(?:0x)?[0-9a-f]{8}\b", secs["Code"])
                    if w.lower().replace("0x", "") in words][:len(words)] != words:
                fail(f"{rel}: 'Code' must list the {len(words)} words in order")
            rows = [tuple(c.strip().strip("`") for c in r.strip().strip("|").split("|"))
                    for r in secs["Launch descriptor"].split("\n") if r.startswith("|")][2:]
            want = [x for x in qmd if x[1] not in ("0x0", "FALSE")]
            if rows != want:
                fail(f"{rel}: the table of 'Launch descriptor' has {len(rows)} rows; it must have the "
                     f"{len(want)} fields that are not 0x0 or FALSE, in the order of the log "
                     f"(first: {want[0]})")
            for word in ("NV50_PROG_DEBUG", "NV50_PROG_CHIPSET", "25.2.8", "compute_test.log"):
                if word not in secs["How it was made"]:
                    fail(f"{rel}: 'How it was made' does not name {word}")
            if len(re.findall(r"^\s*[-*] ", secs["Not known"], re.M)) < 2:
                fail(f"{rel}: 'Not known' needs 2 list items or more")
    if not os.path.exists(c5a_tool) or "--check" not in open(c5a_tool, errors="replace").read():
        fail("tools/shader_extract.py: missing, or no --check option (docs/tasks/C5a.md)")
    else:
        for run in (1, 2):
            r = subprocess.run([sys.executable, c5a_tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/shader_extract.py --check (run {run}): the output files are not what the tool "
                     f"generates")
                break

# C5b summary of the register trace of the reference run ------------------
C5_JOB = {}
def c5b_build(T, rnndb):
    bars={};maps=[];byid={};marks=[];n=0
    ph={k:{'first_line':None,'last_line':None,'bar0':{'reads':0,'writes':0},'bar1':{'reads':0,'writes':0},'bar3':{'reads':0,'writes':0}} for k in('load','job','after')}
    cur='load';regs={};runs=[];names={}
    for l in lzma.open(os.path.join(ROOT, T),'rt'):
        n+=1;p=l.split()
        if not p: continue
        if p[0]=='PCIDEV' and p[2]=='10de1024':
            for i in range(7):
                a=int(p[4+i],16);s=int(p[11+i],16)
                if s: bars[i]=(a&~0xf,s)
        elif p[0]=='MAP':
            ph_=int(p[3],16);b=[i for i,(a,s) in bars.items() if a<=ph_<a+s][0]
            m={'id':int(p[2]),'line':n,'phys':hex(ph_),'size':hex(int(p[5],16)),'bar':b,'offset':hex(ph_-bars[b][0]),'unmap_line':None}
            maps.append(m);byid[p[2]]=m
        elif p[0]=='UNMAP': byid[p[2]]['unmap_line']=n
        elif p[0]=='MARK':
            marks.append({'line':n,'text':' '.join(p[2:])})
            cur={'load':'job','job':'after'}[cur]; continue
        elif p[0] in('R','W'):
            m=byid[p[3]];k='reads' if p[0]=='R' else 'writes'
            ph[cur]['bar%d'%m['bar']][k]+=1
            if ph[cur]['first_line'] is None: ph[cur]['first_line']=n
            ph[cur]['last_line']=n
            if cur=='job' and m['bar']==0:
                off=int(p[4],16)-bars[0][0]
                if off not in names:
                    r=rnndb.lookup(off); names[off]=r['name'] if r else None
                nm=names[off]
                C5_JOB[n]=(p[0],off,int(p[5],16),nm)
                e=regs.setdefault(off,{'reg':'0x%06x'%off,'name':nm,'reads':0,'writes':0,'first_line':n})
                e[k]+=1
                d=nm.split('.')[0] if nm else 'unknown'
                if runs and runs[-1]['domain']==d: runs[-1][k]+=1; runs[-1]['last_line']=n
                else: runs.append({'domain':d,'first_line':n,'last_line':n,'reads':0,'writes':0}); runs[-1][k]+=1
    return {'trace':'reference/linux-run/mmiotrace.txt.xz','lines':n,'bars':{str(i):{'base':hex(a),'size':hex(s)} for i,(a,s) in sorted(bars.items())},'maps':maps,'marks':marks,'phases':ph,'job_registers':[regs[k] for k in sorted(regs)],'job_runs':runs}

c5b_tool = os.path.join(ROOT, "tools", "trace_summary.py")
if (os.path.exists(c5b_tool) or re.search(r"^\| C5b \| DONE", open(os.path.join(ROOT, "docs", "STATUS.md")).read(), re.M)) \
        and "C5b" not in SKIP:
    import lzma, subprocess
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import rnndb as c5b_rnndb
    want = c5b_build("reference/linux-run/mmiotrace.txt.xz", c5b_rnndb)
    rel = "analysis/linux_run_trace.json"
    j = load_json(rel) if os.path.exists(os.path.join(ROOT, rel)) else None
    if not isinstance(j, dict):
        fail(f"{rel}: missing or not an object (docs/tasks/C5b.md)")
    else:
        for key in ("lines", "bars", "marks"):
            if j.get(key) != want[key]:
                fail(f"{rel}: '{key}' is {json.dumps(j.get(key))[:120]}; expected {json.dumps(want[key])[:200]}")
        for key in ("maps", "job_registers", "job_runs"):
            got = j.get(key)
            if not isinstance(got, list):
                fail(f"{rel}: '{key}' must be a list"); continue
            if got != want[key]:
                d = next((n for n, (a, b) in enumerate(zip(got, want[key])) if a != b), min(len(got), len(want[key])))
                fail(f"{rel}: '{key}' has {len(got)} entries, expected {len(want[key])}; first difference at "
                     f"entry {d}: yours {json.dumps(got[d]) if d < len(got) else 'nothing'}, expected "
                     f"{json.dumps(want[key][d]) if d < len(want[key]) else 'nothing'}")
        for phn in ("load", "job", "after"):
            got = (j.get("phases") or {}).get(phn)
            if got != want["phases"][phn]:
                fail(f"{rel}: phases.{phn} is {json.dumps(got)[:200]}; expected {json.dumps(want['phases'][phn])}")
    rel = "analysis/linux_run_trace.md"
    if not os.path.exists(os.path.join(ROOT, rel)):
        fail(f"{rel}: missing (docs/tasks/C5b.md)")
    else:
        md = open(os.path.join(ROOT, rel)).read()
        secs = dict((h.strip(), b) for h, b in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", md, re.M | re.S))
        need = ["Mappings", "Phases", "Domains of the job", "Timeline of the job", "Registers without a name"]
        if list(secs) != need:
            fail(f"{rel}: the '## ' sections must be {need}, in this order")
        else:
            rows = lambda t: len([r for r in t.split("\n") if r.startswith("|")]) - 2
            doms = len(set(r["domain"] for r in want["job_runs"]))
            for sec, n in (("Mappings", len(want["maps"])), ("Phases", 3), ("Domains of the job", doms),
                           ("Timeline of the job", len(want["job_runs"]))):
                if rows(secs[sec]) != n:
                    fail(f"{rel}: the table of '{sec}' has {rows(secs[sec])} rows; expected {n}")
            noname = ["0x%s" % r["reg"][2:] for r in want["job_registers"] if r["name"] is None]
            if re.findall(r"0x[0-9a-f]{6}\b", secs["Registers without a name"]) != noname:
                fail(f"{rel}: 'Registers without a name' must list the {len(noname)} registers with name null, "
                     f"in order (first: {noname[0]})")
    if not os.path.exists(c5b_tool) or "--check" not in open(c5b_tool, errors="replace").read():
        fail("tools/trace_summary.py: missing, or no --check option (docs/tasks/C5b.md)")
    else:
        for run in (1, 2):
            try:
                r = subprocess.run([sys.executable, c5b_tool, "--check"], cwd=ROOT, capture_output=True,
                                   text=True, timeout=60)
            except subprocess.TimeoutExpired:
                fail("tools/trace_summary.py --check: no result in 60 s (read the trace one time)"); break
            if r.returncode != 0:
                fail(f"tools/trace_summary.py --check (run {run}): the output files are not what the tool generates")
                break

# C5c document about the job in the trace ---------------------------------
c5c_doc = os.path.join(ROOT, "docs", "08-compute-launch.md")
if (os.path.exists(c5c_doc) or re.search(r"^\| C5c \| DONE", open(os.path.join(ROOT, "docs", "STATUS.md")).read(), re.M)) \
        and "C5c" not in SKIP:
    rel = "docs/08-compute-launch.md"
    if not os.path.exists(c5c_doc):
        fail(f"{rel}: missing (docs/tasks/C5c.md)")
    else:
        if not C5_JOB:
            import lzma
            sys.path.insert(0, os.path.join(ROOT, "tools"))
            import rnndb as c5c_rnndb
            c5b_build("reference/linux-run/mmiotrace.txt.xz", c5c_rnndb)
        j0, j1 = min(C5_JOB), max(C5_JOB)
        md = open(c5c_doc).read()
        secs = dict((h.strip(), b) for h, b in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", md, re.M | re.S))
        need = ["What ran", "Phases of the trace", "Steps of the job", "Verified values",
                "What the trace does not show", "Consequences for the Haiku driver", "Not known"]
        if list(secs) != need:
            fail(f"{rel}: the '## ' sections must be {need}, in this order")
        else:
            cells = lambda t: [[c.strip().strip("`") for c in r.strip().strip("|").split("|")]
                               for r in t.split("\n") if r.startswith("|")][2:]
            steps = cells(secs["Steps of the job"])
            C5C_PARTS = [(573421, 615162), (615163, 615167), (615168, 615176), (615177, 615190),
                         (615191, 616553), (616554, 618713), (618714, 726184), (726185, 726188),
                         (726189, 730273), (730274, 892358), (892359, 892368), (892369, 900526),
                         (900527, 900552), (900553, 901167)]
            got_ranges = []
            for r in steps:
                m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", r[1]) if len(r) == 5 else None
                got_ranges.append((int(m.group(1)), int(m.group(2))) if m else None)
            if got_ranges != C5C_PARTS:
                fail(f"{rel}: 'Steps of the job' must have the 14 rows of the task text (5 cells, the same "
                     f"'Lines' as FIRST-LAST); it has {len(steps)} rows")
            else:
                covered = {}
                for r, (a, b) in zip(steps, C5C_PARTS):
                    inrange = set(v[1] for k, v in C5_JOB.items() if a <= k <= b)
                    regs = [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]{6}\b", r[3])]
                    if not 1 <= len(regs) <= 6:
                        fail(f"{rel}: step {r[0]}: 'Registers' needs 1 to 6 registers as 0x...... (6 hex digits)")
                    bad = [f"0x{x:06x}" for x in regs if x not in inrange]
                    if bad:
                        fail(f"{rel}: step {r[0]}: registers {bad[:6]} are not accessed in lines {a}-{b} "
                             f"(run tools/trace_lines.py --regs {a} {b})")
                    for x in regs:
                        covered.setdefault(x, []).append(int(r[0]) if r[0].isdigit() else 0)
                    if len(r[2].split()) < 6:
                        fail(f"{rel}: step {r[0]}: 'What' must be a sentence")
                for x, st in ((0x800010, 2), (0x800014, 2), (0x002270, 3), (0x409500, 8), (0x409504, 8),
                              (0x800014, 11), (0x800010, 13)):
                    if st not in covered.get(x, []):
                        fail(f"{rel}: 'Steps of the job': step {st} must list 0x{x:06x}")
            vals = cells(secs["Verified values"])
            if len(vals) < 12 or any(len(r) != 6 for r in vals):
                fail(f"{rel}: 'Verified values' needs 12 rows or more with 6 cells (it has {len(vals)} rows)")
            else:
                seen = set()
                for r in vals:
                    try:
                        ln, reg, val = int(r[0]), int(r[2], 16), int(r[4], 16)
                    except ValueError:
                        fail(f"{rel}: 'Verified values': row '{' | '.join(r[:5])}' is not LINE, R/W, 0x......, "
                             f"name, 0x value"); continue
                    t = C5_JOB.get(ln)
                    if t is None:
                        fail(f"{rel}: 'Verified values': line {ln} is not a BAR 0 access of the job phase (copy the line number from tools/trace_lines.py)"); continue
                    want_row = (t[0], t[1], t[2], t[3] or "-")
                    if (r[1], reg, val, r[3]) != want_row:
                        fail(f"{rel}: 'Verified values': line {ln} is '{t[0]} 0x{t[1]:06x} {t[3] or '-'} "
                             f"0x{t[2]:x}' in the trace, the row says '{r[1]} {r[2]} {r[3]} {r[4]}'")
                    seen.add(reg)
                    if len(r[5].split()) < 2:
                        fail(f"{rel}: 'Verified values': line {ln}: 'Meaning' is empty (write 'not known')")
                miss = [f"0x{x:06x}" for x in (0x800010, 0x800014, 0x002270, 0x002274, 0x409500, 0x409504)
                        if x not in seen]
                if miss:
                    fail(f"{rel}: 'Verified values' has no row for {miss}")
            bad = []
            for f, ln in set(re.findall(r"((?:nvkm|nvif|dispnv50)?/?[\w/.-]*\w\.[ch]):(\d+)", md)):
                hits = [d for d in glob.glob(os.path.join(NV, "**", os.path.basename(f)), recursive=True)
                        if d.endswith(f)]
                hits += [d for d in glob.glob(os.path.join(ROOT, "reference", "mesa", "**", os.path.basename(f)),
                                              recursive=True) if d.endswith(f)]
                if len(hits) != 1 or int(ln) > sum(1 for _ in open(hits[0], errors="replace")):
                    bad.append(f"{f}:{ln}")
            if bad:
                fail(f"{rel}: source citations that do not name exactly one file and an existing line "
                     f"(write enough of the path): {sorted(bad)[:6]}")
            if len(set(re.findall(r"[\w/.-]+\.[ch]:\d+", secs["Steps of the job"] + secs["Verified values"]))) < 6:
                fail(f"{rel}: 'Steps of the job' and 'Verified values' need 6 different source citations "
                     f"(file.c:LINE) or more")
            low = secs["What the trace does not show"].lower()
            for word in ("pushbuffer", "launch", "user space"):
                if word not in low:
                    fail(f"{rel}: 'What the trace does not show' does not mention \"{word}\"")
            cons = [l for l in re.split(r"\n(?=\s*[-*] )", secs["Consequences for the Haiku driver"]) if re.match(r"\s*[-*] ", l)]
            if len(cons) < 4:
                fail(f"{rel}: 'Consequences for the Haiku driver' needs 4 list items or more")
            for it in cons:
                if not re.search(r"`(?:src|docs|tests|tools|firmware|hardware|analysis)/[\w./-]+`", it):
                    fail(f"{rel}: a consequence names no file of the repository: '{it.strip()[:70]}'")
            paths = re.findall(r"`((?:src|tests|tools|analysis|hardware|docs|firmware|reference)/[\w./-]+)`", md)
            gone = sorted(p_ for p_ in set(paths) if not os.path.exists(os.path.join(ROOT, p_)))
            if gone:
                fail(f"{rel}: names files that do not exist: {gone[:6]}")
            if len(re.findall(r"^\s*[-*] ", secs["Not known"], re.M)) < 3:
                fail(f"{rel}: 'Not known' needs 3 list items or more")

# D6 launch descriptor against the reference run ---------------------------
D6_WORDS = "2e98b7c2dce9c380e787f6cc3c1f1e33b3e1302a866eaab7a28051d0bb3aa331"
D6_ROWS = ["18977836c4", "4d31bb04e6", "3395ac23fa", "aff4b739b3", "c331136fd1", "b23bee6f71", "1a07f9e434", "89075d34b0", "7f7c327ef8", "615eeff9e2", "dbc9472b14", "e3ce1cc1c7", "46245d6e5c", "1db11ac449", "ca8bf2ec1f", "44fcabb331", "7c4fc5542d", "66ac241b08", "fa8634758e", "a108ff9e24", "9c5ba9798b", "0c24a10a4b", "53c1db2d20", "20aa2633f2", "7e2c330cfe", "72f5a0e1cc", "2b20d958ec", "cb548fd308", "fc987b6f5d", "7ad8f1e88c", "e6bbcfdd49", "45370e45f0", "f2cebf122d", "a0afa8bf22", "ab0cd87cd9", "9deb625da6", "b6b17c32ce", "25a193e95d", "9ad41915c6", "bbe9ff45ff", "f93967b93f", "b3540633aa", "b09ec2370d", "16f789899d", "004ac1849f", "905add2760", "1e40b49b36", "23c0deee8f", "51572486de", "805d9c43c4", "0ce498bd15", "3ab5153aca", "1a7c6902b2", "acbc2bd180", "b1981dd8ee", "335d3acabb", "df59acdc3b", "aa366dbcb5", "d8878aeebf", "32d6e22a97", "94a734cdf6", "d68db94499", "3370ae78ae", "c8d02100a8", "0591a7d861", "05391a1c9d", "19dd509a17", "84dc707c90", "19e8e50fa5", "0d2384e16a", "0303f1dd25", "6dd676ddca", "da187dda6b", "9fd5d10aa6", "48d5bd1185", "ceb424080e", "9fbc10cecb", "84fd17491b", "341e6ce601", "707112c889", "ce222b313f", "bac603e03a", "0f9ae92ecd", "1f8f08c96d", "1997040dcc", "709a66b8da", "af94e34b32", "5ef4344699", "6c07758740", "dcbb049db2", "5d7157d8db", "7974f1668e", "7a21f70b4a", "0023ebe4e6", "ae80ef12c0", "739c68a271", "531fa0dc15", "931dcf5749", "bd4acf007c", "4bc6713c45", "b6a0811056", "4bed36ebec", "e21bdf4304", "04943b288e", "638b13fc50", "2411d42e02", "4e4b98a6c8", "2219a1704a", "3c96e5c47f", "788ffd5f13", "2648b081e4", "9de4ed93df", "9fd0087dc7", "b0c03f7898", "84dacb2446", "aaa91ae028", "02b2b701b2", "abd9e6886c", "91a0c93dbd", "2741e798c2", "ede583e40f", "029e2a5010", "dadba237e2", "77aeabebb0", "c5170d2dee", "331fd1452e", "684af846b1", "2be52fce75", "e3c3b6c552", "a92ac0c86f", "fe68ac8287", "43293a6ad7", "6deb4361d1", "b6fcce354f", "76b6c82518", "6b76584e00", "ae95ee24b2", "967972c99f", "57f51d1ecb", "fd43b32064", "715d644dbc", "4f1ec8382f", "75268ee69d", "c0edd1b43f", "1fbb06532a", "b41c4e68ca", "3fa4cafe44", "0ea635f14a", "3fa80e2105", "f2b5d959db", "95f278fe91", "ba6c641e91", "a608e0f4a3", "43f562a816", "2076a2d3bc"]
d6_tool = os.path.join(ROOT, "tools", "qmd_compare.py")
if (os.path.exists(d6_tool) or re.search(r"^\| D6 \| DONE", open(os.path.join(ROOT, "docs", "STATUS.md")).read(), re.M)) \
        and "D6" not in SKIP:
    import hashlib, subprocess
    rel = "analysis/qmd_compare.json"
    j = load_json(rel) if os.path.exists(os.path.join(ROOT, rel)) else None
    if not isinstance(j, dict) or not isinstance(j.get("fields"), list) or not isinstance(j.get("words"), list):
        fail(f"{rel}: missing, or no 'words' and 'fields' lists (docs/tasks/D6.md)")
    else:
        ws = " ".join(str(x).lower().replace("0x", "") for x in j["words"])
        if hashlib.sha256(ws.encode()).hexdigest() != D6_WORDS:
            fail(f"{rel}: 'words' are not the 64 words that src/compute builds for the job of the task text "
                 f"(8 hex digits each; word 8 is 0007f100)")
        rows = j["fields"]
        if len(rows) != len(D6_ROWS):
            fail(f"{rel}: 'fields' has {len(rows)} entries; the reference has {len(D6_ROWS)}")
        else:
            for n, (r_, h) in enumerate(zip(rows, D6_ROWS)):
                keys = {"name", "hi", "lo", "reference", "reference_value", "ours", "equal"}
                if not isinstance(r_, dict) or set(r_) != keys:
                    fail(f"{rel}: fields[{n}] must have exactly the keys {sorted(keys)}"); break
                if hashlib.sha256(json.dumps(r_, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:10] != h:
                    fail(f"{rel}: fields[{n}] ({r_.get('name')}) is not what the reviewer's program computes: "
                         f"yours has hi {r_.get('hi')}, lo {r_.get('lo')}, reference_value "
                         f"{r_.get('reference_value')}, ours {r_.get('ours')}, equal {r_.get('equal')}. Check the "
                         f"bits in cla0c0qmd.h, the index, and the number of a named value"); break
            eq = sum(1 for r_ in rows if isinstance(r_, dict) and r_.get("equal") is True)
            if j.get("equal") != eq or j.get("different") != len(rows) - eq:
                fail(f"{rel}: 'equal' and 'different' must be the counts of the rows ({eq} and {len(rows) - eq})")
            rel2 = "analysis/qmd_compare.md"
            if not os.path.exists(os.path.join(ROOT, rel2)):
                fail(f"{rel2}: missing (docs/tasks/D6.md)")
            else:
                md = open(os.path.join(ROOT, rel2)).read()
                secs = dict((h_.strip(), b) for h_, b in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", md, re.M | re.S))
                if list(secs) != ["Result", "Fields that are not zero", "Differences"]:
                    fail(f"{rel2}: the '## ' sections must be Result, Fields that are not zero, Differences")
                else:
                    nz = sum(1 for r_ in rows if isinstance(r_, dict) and (r_.get("reference_value") or r_.get("ours")))
                    got = len([l for l in secs["Fields that are not zero"].split("\n") if l.startswith("|")]) - 2
                    if got != nz:
                        fail(f"{rel2}: the table of 'Fields that are not zero' has {got} rows; expected {nz}")
                    nd = len(rows) - eq
                    gd = max(0, len([l for l in secs["Differences"].split("\n") if l.startswith("|")]) - 2)
                    if gd != nd or (nd == 0 and "None." not in secs["Differences"]):
                        fail(f"{rel2}: 'Differences' must have {nd} table rows (or the sentence 'None.')")
    mk = open(os.path.join(ROOT, "tests", "Makefile")).read()
    if "ref_qmd:compute+fifo" not in mk or not os.path.exists(os.path.join(ROOT, "tests", "ref_qmd.cpp")):
        fail("tests/ref_qmd.cpp or its entry ref_qmd:compute+fifo in CXX_TESTS of tests/Makefile is missing")
    if not os.path.exists(d6_tool) or "--check" not in open(d6_tool, errors="replace").read():
        fail("tools/qmd_compare.py: missing, or no --check option (docs/tasks/D6.md)")
    else:
        for run in (1, 2):
            r = subprocess.run([sys.executable, d6_tool, "--check"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"tools/qmd_compare.py --check (run {run}): the output files are not what the tool generates")
                break

for n in notes:
    print("note:", n)
for f in fails:
    print("FAIL:", f)
print(f"check_repo: {len(fails)} failure(s)")
sys.exit(1 if fails else 0)
