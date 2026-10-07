#!/usr/bin/env python3
"""Generate analysis/files.json from the Nouveau nvf1_chipset definition.

Reads nvf1_chipset from reference/nouveau/nvkm/engine/device/base.c,
resolves each constructor to its source file, classifies the file,
and writes analysis/files.json.

Usage:
    python3 tools/nouveau_files.py [--dry-run]

The script is idempotent: re-running produces the same output.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
OUTPUT = os.path.join(ROOT, "analysis", "files.json")

# Mapping from constructor function name to file (relative to reference/nouveau/)
# and subsystem (the directory under nvkm/subdev/ or nvkm/engine/).
# These are derived from the Nouveau source tree and match the nvf1_chipset entry.
CONSTRUCTOR_MAP = {
    # Subdevices (nvkm/subdev/<name>/)
    "gf100_bar_new":       {"file": "nvkm/subdev/bar/gf100.c",      "subsystem": "bar"},
    "nvkm_bios_new":       {"file": "nvkm/subdev/bios/base.c",      "subsystem": "bios"},
    "gf100_bus_new":       {"file": "nvkm/subdev/bus/gf100.c",      "subsystem": "bus"},
    "gk104_clk_new":       {"file": "nvkm/subdev/clk/gk104.c",      "subsystem": "clk"},
    "gf100_devinit_new":   {"file": "nvkm/subdev/devinit/gf100.c",  "subsystem": "devinit"},
    "gk110_fb_new":        {"file": "nvkm/subdev/fb/gk110.c",       "subsystem": "fb"},
    "gf100_fuse_new":      {"file": "nvkm/subdev/fuse/gf100.c",     "subsystem": "fuse"},
    "gk104_gpio_new":      {"file": "nvkm/subdev/gpio/gk104.c",     "subsystem": "gpio"},
    "gk110_i2c_new":       {"file": "nvkm/subdev/i2c/gk110.c",      "subsystem": "i2c"},
    "gf100_iccsense_new":  {"file": "nvkm/subdev/iccsense/gf100.c", "subsystem": "iccsense"},
    "nv50_instmem_new":    {"file": "nvkm/subdev/instmem/nv50.c",   "subsystem": "imem"},
    "gk104_ltc_new":       {"file": "nvkm/subdev/ltc/gk104.c",      "subsystem": "ltc"},
    "gk104_mc_new":        {"file": "nvkm/subdev/mc/gk104.c",       "subsystem": "mc"},
    "gk104_mmu_new":       {"file": "nvkm/subdev/mmu/gk104.c",      "subsystem": "mmu"},
    "nv50_mxm_new":        {"file": "nvkm/subdev/mxm/nv50.c",       "subsystem": "mxm"},
    "gk104_pci_new":       {"file": "nvkm/subdev/pci/gk104.c",      "subsystem": "pci"},
    "gk110_pmu_new":       {"file": "nvkm/subdev/pmu/gk110.c",      "subsystem": "pmu"},
    "gk104_privring_new":  {"file": "nvkm/subdev/privring/gk104.c", "subsystem": "privring"},
    "gk104_therm_new":     {"file": "nvkm/subdev/therm/gk104.c",    "subsystem": "therm"},
    "nv41_timer_new":      {"file": "nvkm/subdev/timer/nv41.c",     "subsystem": "timer"},
    "gk104_top_new":       {"file": "nvkm/subdev/top/gk104.c",      "subsystem": "top"},
    "gk104_volt_new":      {"file": "nvkm/subdev/volt/gk104.c",     "subsystem": "volt"},
    # Engines (nvkm/engine/<name>/)
    "gk104_ce_new":        {"file": "nvkm/engine/ce/gk104.c",       "subsystem": "ce"},
    "gk110_disp_new":      {"file": "nvkm/engine/disp/gk110.c",     "subsystem": "disp"},
    "gf119_dma_new":       {"file": "nvkm/engine/dma/gf119.c",      "subsystem": "dma"},
    "gk110_fifo_new":      {"file": "nvkm/engine/fifo/gk110.c",     "subsystem": "fifo"},
    "gk110b_gr_new":       {"file": "nvkm/engine/gr/gk110b.c",      "subsystem": "gr"},
    "gk104_mspdec_new":    {"file": "nvkm/engine/mspdec/gk104.c",   "subsystem": "mspdec"},
    "gf100_msppp_new":     {"file": "nvkm/engine/msppp/gf100.c",    "subsystem": "msppp"},
    "gk104_msvld_new":     {"file": "nvkm/engine/msvld/gk104.c",    "subsystem": "msvld"},
    "gf100_sw_new":        {"file": "nvkm/engine/sw/gf100.c",       "subsystem": "sw"},
}

ALLOWED_CLASSES = {"GK110-specific", "GK104-inherited", "GF100-inherited", "generic-NVKM", "Linux-only"}


def classify(filepath):
    """Classify a file based on its basename prefix.

    Rules (from PHASES.md task B1):
      - GK110-specific: gk110*.c or gk110b*.c
      - GK104-inherited: gk104*.c
      - GF100-inherited: gf100*.c, gf119*.c
      - generic-NVKM: nv50*.c, nv41*.c, base.c
    """
    base = os.path.basename(filepath).lower()
    if base.startswith("gk110") or base.startswith("gk110b"):
        return "GK110-specific"
    if base.startswith("gk104"):
        return "GK104-inherited"
    if base.startswith("gf100") or base.startswith("gf119"):
        return "GF100-inherited"
    if base.startswith("nv50") or base.startswith("nv41") or base == "base.c":
        return "generic-NVKM"
    return "UNKNOWN"


def extract_chipset_entries():
    """Extract constructor entries from nvf1_chipset in base.c.

    Returns list of (field_name, constructor_func) tuples.
    """
    base_path = os.path.join(NV, "nvkm/engine/device/base.c")
    with open(base_path) as f:
        text = f.read()

    idx = text.find("nvf1_chipset")
    if idx < 0:
        print("ERROR: Could not find nvf1_chipset in base.c", file=sys.stderr)
        sys.exit(1)

    # Use balanced-brace extraction (regex [^}] breaks on nested braces)
    start = text.find("{", idx)
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = text[start + 1 : end]

    # Parse each entry: .field = { value, func_name }
    entries = []
    for m in re.finditer(r"\.(\w+)\s*=\s*[{}][^,]*,\s*(\w+)", block):
        entries.append((m.group(1), m.group(2)))
    return entries


def main():
    dry_run = "--dry-run" in sys.argv
    entries = extract_chipset_entries()

    results = []
    for field_name, func_name in entries:
        if func_name not in CONSTRUCTOR_MAP:
            print(f"WARNING: {func_name} not in CONSTRUCTOR_MAP, skipping", file=sys.stderr)
            continue
        info = CONSTRUCTOR_MAP[func_name]
        filepath = info["file"]
        full_path = os.path.join(NV, filepath)
        exists = os.path.isfile(full_path)

        if not exists:
            print(f"WARNING: {filepath} does not exist at {full_path}", file=sys.stderr)

        entry = {
            "path": filepath,
            "subsystem": info["subsystem"],
            "class": classify(filepath),
            "role": f"{func_name} — {field_name} ({info['subsystem']})",
        }
        if not exists:
            entry["exists"] = False
        results.append(entry)

    if dry_run:
        print(f"Found {len(results)} entries (dry run).")
        for e in results:
            exists_str = "✓" if e.get("exists") is not False else "?"
            print(f"  {exists_str} {e['path']:45s} {e['class']:20s} {e['subsystem']}")
        return

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    # Print summary
    classes = {}
    for e in results:
        classes[e["class"]] = classes.get(e["class"], 0) + 1
    print(f"Wrote {OUTPUT} ({len(results)} entries)")
    for cls in sorted(classes):
        print(f"  {cls}: {classes[cls]}")


if __name__ == "__main__":
    main()
