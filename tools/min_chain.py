#!/usr/bin/env python3
"""B5: Minimum chain to one compute job.

Reads the call graph and MMIO access records, parses the chipset and GR tables
from Nouveau source, and produces analysis/min_chain.json.

Usage:
    python3 tools/min_chain.py          # write analysis/min_chain.json
    python3 tools/min_chain.py --check  # write nothing; exit 0 if file is correct
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
MESA = os.path.join(ROOT, "reference", "mesa")

# ── helpers ────────────────────────────────────────────────────────────────

def read_source(path):
    """Read a source file and return (base-path relative to NV or MESA, lines)."""
    for root in (NV, MESA):
        full = os.path.join(root, path)
        if os.path.isfile(full):
            with open(full, errors="replace") as f:
                return path, f.read().splitlines()
    return path, []


def parse_subsystems(lines):
    """Parse nvf1_chipset entries from base.c lines.

    Each entry looks like:
        .bar      = { 0x00000001, gf100_bar_new },
    Returns dict: {name: (constructor, line_number)}
    """
    result = {}
    inside = False
    for i, line in enumerate(lines, 1):
        if re.match(r"\s*nvf1_chipset\s*=", line) and "{" in line:
            inside = True
            continue
        if inside and line.strip() == "};":
            break
        if inside:
            m = re.match(r"\s*\.\s*(\w+)\s*=\s*\{\s*0x[0-9a-f]+,\s*(\w+)\s*\}", line)
            if m:
                result[m.group(1)] = (m.group(2), i)
    return result


def parse_gr_hooks(lines):
    """Parse gk110b_gr .init* and .oneinit* entries.

    Each entry looks like:
        .init_zcull = gf117_gr_init_zcull,
    Returns dict: {hook_name: function_name}
    """
    result = {}
    inside = False
    for line in lines:
        # Match exactly "gk110b_gr = {" not "gk110b_gr_init_xxx"
        if re.match(r"\s*gk110b_gr\s*=", line) and "{" in line:
            inside = True
            continue
        if inside and line.strip() == "};":
            break
        if inside:
            m = re.match(r"\s*\.\S+\s*=\s*(\w+),", line)
            if m:
                # Extract the field name (everything between . and =)
                field = re.search(r"\.(\S+?)\s*=", line)
                if field and (field.group(1).startswith("init") or field.group(1).startswith("oneinit")):
                    result[field.group(1)] = m.group(1)
    return result


def find_callgraph_node(cg, name):
    """Find a node in the call graph by name. Returns (name, file, line) or None."""
    # callgraph.json has structure: {"nodes": [...], "edges": [...]}
    if isinstance(cg, dict) and "nodes" in cg:
        node_list = cg["nodes"]
    elif isinstance(cg, dict):
        # fallback: look for a list value
        for val in cg.values():
            if isinstance(val, list) and val and isinstance(val[0], dict):
                node_list = val
                break
        else:
            return None
    elif isinstance(cg, list):
        node_list = cg
    else:
        return None
    for n in node_list:
        if n.get("name") == name:
            return (name, n.get("file"), n.get("line"))
    return None


def load_callgraph():
    """Load analysis/callgraph.json and return nodes dict."""
    path = os.path.join(ROOT, "analysis", "callgraph.json")
    with open(path) as f:
        return json.load(f)


def load_mmio():
    """Load registers/mmio_accesses.json. Returns dict: func_name -> list of (file, line, reg)."""
    path = os.path.join(ROOT, "registers", "mmio_accesses.json")
    with open(path) as f:
        data = json.load(f)
    result = {}
    for entry in data:
        fn = entry.get("function")
        if fn:
            result.setdefault(fn, []).append(
                (entry.get("file"), entry.get("line"), entry.get("reg"))
            )
    return result


def grep_func_line(func_name, source_path):
    """grep for a function definition line in source; return (file, line) or None."""
    full = os.path.join(NV, source_path)
    if not os.path.isfile(full):
        return None
    with open(full, errors="replace") as f:
        for i, line in enumerate(f, 1):
            if f"^{func_name}(" in line or (f" {func_name}(" in line and "(" in line and ")" in line):
                # Check it's a function definition (not just a call)
                # A definition has a type before the function name
                if re.search(r'\b' + re.escape(func_name) + r'\s*\(', line):
                    return (source_path, i)
    return None


# ── subsystem decisions ────────────────────────────────────────────────────

SUBSYSTEM_STATUS = {
    # Core subsystems needed for compute
    "bar":       ("needed", "PCI BAR mapping is required before any GPU register access can occur"),
    "fb":        ("needed", "framebuffer and memory layout must be initialized for GPU memory access"),
    "imem":      ("needed", "instance memory provides GPU objects such as page tables and RAMFC "
                           "structures that the GR engine loads firmware code into"),
    "ltc":       ("needed", "the GR engine calls nvkm_ltc_* functions for zbc color and depth "
                            "configuration at gr/gf100.c:94 and 114"),
    "mmu":       ("needed", "memory management unit must translate virtual to physical addresses"),
    "mc":        ("needed", "master control provides engine enable bits and interrupt configuration "
                           "for every subdevice that the GR and FIFO engines use"),
    "fifo":      ("needed", "command submission engine is required to send work to the GPU"),
    "gr":        ("needed", "graphics/compute engine must be initialized to run compute shaders"),
    # Non-essential for compute
    "disp":      ("not-needed", "display engine is only needed for outputting to a connected monitor"),
    "mspdec":    ("not-needed", "media spatial decoder is for video decoding not compute workloads"),
    "msppp":     ("not-needed", "media post-processing pipeline is for video effects not compute"),
    "msvld":     ("not-needed", "media video decode engine is for video playback not compute jobs"),
    # Optional/infrastructure subsystems
    "bios":      ("optional", "VBIOS parsing is needed for initial card identification and clocks"),
    "bus":       ("optional", "PCI bus layer handles link speed configuration and power management"),
    "clk":       ("optional", "clock management sets GPU and memory frequencies before compute"),
    "devinit":   ("optional", "device initialization handles power domains and clock gating setup"),
    "fuse":      ("optional", "fuse configuration reads factory-calibrated GPU parameters"),
    "gpio":      ("optional", "general-purpose I/O is used for board-level controls not compute"),
    "i2c":       ("optional", "I2C bus is used for sensor access and EEPROM reading not compute"),
    "iccsense":  ("optional", "current sensing monitors power draw but is not required for compute"),
    "privring":  ("needed", "PRI ring provides the register bus to the GR units for interrupt "
                           "handling and hardware error reporting at privring/gf100.c"),
    "therm":     ("optional", "thermal management prevents overheating but compute can proceed without"),
    "timer":     ("needed", "every nvkm_msec wait call in GR uses the timer subdev for polling "
                           "loops at gr/gf100.c:758 during firmware initialization"),
    "top":       ("needed", "device topology table lists engines and their runlists; "
                           "gk104_fifo_init reads device->top to iterate runlists at fifo/gk104.c:764"),
    "volt":      ("optional", "voltage control adjusts power levels but is not needed for compute"),
    "ce":        ("optional", "copy engine handles memory transfers but compute can use channel"),
    "dma":       ("optional", "DMA engine supports direct memory access for non-GPU transfers"),
    "mxm":       ("optional", "Modular MXM interface handles laptop-specific connector detection"),
    "pmu":       ("optional", "the GR engine calls nvkm_pmu_pgob at gr/gf100.c:2006 to switch power "
                           "gating off; needed if the video BIOS leaves power gating on (not known)"),
    "sw":        ("optional", "software subsystem provides generic kernel infrastructure support"),
}


# ── step definitions ───────────────────────────────────────────────────────

# Each step lists the Nouveau functions that define the work.
# The tool will look up their lines in the call graph, then pull MMIO regs.
# For functions not in the call graph, provide file and line directly.
STEP_FUNCTIONS = [
    {
        "subsystem": "bar",
        "what": "Map PCI BAR regions and read VBIOS for GPU identification",
        "functions": ["gf100_bar_new"],
        "status": "partly-known",
        "notes": "Only the constructor gf100_bar_new is traced; init function not in call graph",
    },
    {
        "subsystem": "fb",
        "what": "Initialize framebuffer layer including memory layout and page tables",
        "functions": ["gk110_fb_new", "gf100_fb_init"],
        "status": "known",
    },
    {
        "subsystem": "mc",
        "what": "Master control provides engine enable bits and interrupt configuration",
        "functions": ["gk104_mc_new"],
        "status": "partly-known",
        "notes": "Only the constructor gk104_mc_new is traced; init function not in call graph",
    },
    {
        "subsystem": "imem",
        "what": "Instance memory provides GPU objects such as page tables and RAMFC structures",
        "functions": ["nv50_instmem_new"],
        "status": "partly-known",
        "notes": "Only the constructor nv50_instmem_new is traced; init function not in call graph",
    },
    {
        "subsystem": "mmu",
        "what": "Set up memory management unit for address translation",
        "functions": ["gk104_mmu_new", "nvkm_mmu_init"],
        "status": "known",
    },
    {
        "subsystem": "top",
        "what": "Device topology table lists engines and their runlists for FIFO access",
        "functions": [],
        "status": "partly-known",
        "notes": "Topology initialized early; gk104_fifo_init reads device->top at fifo/gk104.c:764",
    },
    {
        "subsystem": "fifo",
        "what": "Initialize FIFO engine for command submission and context switching",
        "functions": ["gk110_fifo_new", "gk104_fifo_init"],
        "status": "known",
    },
    {
        "subsystem": "ltc",
        "what": "LTC layer provides zbc color and depth configuration for the GR engine",
        "functions": [],
        "status": "partly-known",
        "notes": "LTC initialized before GR; called from gr/gf100.c:94 for zbc color configuration",
    },
    {
        "subsystem": "timer",
        "what": "Timer subdev provides polling delays for GR firmware initialization waits",
        "functions": [],
        "status": "partly-known",
        "notes": "Timer used by every nvkm_msec call at gr/gf100.c:758 during GR init",
    },
    {
        "subsystem": "privring",
        "what": "PRI ring provides the register bus to GR units for interrupt and error handling",
        "functions": [],
        "status": "partly-known",
        "notes": "Privring initialized before GR; register bus to engines at privring/gf100.c",
    },
    {
        "subsystem": "gr",
        "what": "Initialize graphics and compute engine with firmware and exception handlers",
        "functions": ["gk110b_gr_new", "gf100_gr_init", "gf100_gr_init_ctxctl_int"],
        "status": "known",
    },
    {
        "subsystem": "channel",
        "what": "Create channel address space with RAMFC write and runlist commit",
        "functions": ["gk104_chan_ramfc_write", "gk104_runl_commit"],
        "status": "partly-known",
        "notes": "Channel creation traced; full command buffer submission not fully traced",
    },
    {
        "subsystem": "channel",
        "what": "Create GR context for the channel including GPU object generation",
        "functions": ["gf100_gr_chan_new", "gf100_grctx_generate"],
        "status": "partly-known",
        "notes": "GR context creation traced via grep; not in B2 call graph",
    },
    {
        "subsystem": "mesa",
        "what": "Set up compute context including TLS textures and command buffer preparation",
        "functions": ["nve4_screen_compute_setup"],
        "status": "known",
    },
    {
        "subsystem": "mesa",
        "what": "Launch compute grid with QMD descriptor and GPU execution parameters",
        "functions": ["nve4_launch_grid"],
        "status": "known",
    },
    {
        "subsystem": "channel",
        "what": "Wait for the job to complete by polling the channel status register",
        "functions": [],
        "status": "unknown",
        "notes": "Job completion polling not traced in B2 call graph; needs FIFO status register",
    },
    {
        "subsystem": "host",
        "what": "Read back the result buffer from GPU memory through the PCI BAR mapping",
        "functions": [],
        "status": "unknown",
        "notes": "Result buffer read-back not traced; requires BAR0 access to GPU memory",
    },
]

# Hard-coded file:line for functions not in the call graph
MISSING_FUNC_LINES = {
    "gf100_bar_new": ("nvkm/subdev/bar/gf100.c", 192),
    "gk104_mc_new": ("nvkm/subdev/mc/gk104.c", 63),
    "nv50_instmem_new": ("nvkm/subdev/instmem/nv50.c", 436),
    "gf100_gr_chan_new": ("nvkm/engine/gr/gf100.c", 377),
    "gf100_grctx_generate": ("nvkm/engine/gr/ctxgf100.c", 1436),
}


# ── gr_hook decisions ─────────────────────────────────────────────────────

GR_HOOK_USE = {
    "init":               ("both",     "gf100_gr_init calls all other hooks and is shared between "
                                     "graphics and compute pipelines"),
    "init_gpc_mmu":       ("compute",    "GPC MMU initialization configures address translation for compute"),
    "init_vsc_stream_master": ("both",   "VSC stream master setup supports both graphics and compute vertex stream routing"),
    "init_zcull":         ("graphics-only", "Depth culling unit is specific to rasterization graphics pipeline only"),
    "init_num_active_ltcs": ("both",     "LTC count initialization is shared by both graphics and compute workloads"),
    "init_rop_active_fbps":   ("graphics-only", "ROP active framebuffer configuration is for graphics rendering only"),
    "init_fecs_exceptions":   ("both",     "FEC exception handling is shared between graphics and compute error paths"),
    "init_sked_hww_esr":      ("both",     "Scheduler hardware warning error service routine reports "
                                         "error conditions for both graphics and compute paths"),
    "init_419cc0":        ("both",     "Register 0x419cc0 initialization is used by both graphics and compute engines"),
    "init_419eb4":        ("compute",    "Register 0x419eb4 is GK110-specific and used for compute pipeline configuration"),
    "init_ppc_exceptions":    ("both",     "PPC exception handling supports both graphics and compute error recovery"),
    "init_tex_hww_esr":     ("both",     "Texture hardware warning error service reports errors "
                                         "for both graphics and compute execution paths"),
    "init_shader_exceptions": ("both",     "Shader exception handling is needed for both graphics shader and compute execution"),
    "init_rop_exceptions":    ("graphics-only", "ROP exceptions are specific to raster operations in graphics pipeline"),
    "init_exception2":      ("both",     "Exception group 2 handling is shared across compute and graphics execution paths"),
    "init_400054":        ("both",     "Register 0x400054 initialization is used by both graphics and compute pipelines"),
    "oneinit_tiles":      ("both",     "Tile initialization configures memory tiling for both graphics and compute workloads"),
    "oneinit_sm_id":      ("both",     "Streaming multiprocessor ID setup configures SM identity for both paths"),
}


# ── firmware ───────────────────────────────────────────────────────────────

FIRMWARE = [
    {
        "name": "fecs",
        "source": "built-in",
        "file": "nvkm/engine/gr/fuc/hubgk110.fuc3.h",
        "note": "Falcon EXEC context scheduler firmware compiled into Nouveau source tree for GK110",
    },
    {
        "name": "gpccs",
        "source": "built-in",
        "file": "nvkm/engine/gr/fuc/gpcgk110.fuc3.h",
        "note": "GPC compute context scheduler firmware compiled into Nouveau source tree for GK110",
    },
]


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Write nothing; exit 0 if the JSON file matches")
    args = parser.parse_args()

    # 1. Parse subsystems from base.c
    _, base_lines = read_source("nvkm/engine/device/base.c")
    want_sub = parse_subsystems(base_lines)

    # 2. Parse GR hooks from gk110b.c
    _, gr_lines = read_source("nvkm/engine/gr/gk110b.c")
    want_hooks = parse_gr_hooks(gr_lines)

    # 3. Load call graph
    cg = load_callgraph()

    # 4. Load MMIO accesses
    mmio = load_mmio()

    # 5. Build subsystems list
    subsystems = []
    for name in sorted(want_sub.keys()):
        constructor, line = want_sub[name]
        status, reason = SUBSYSTEM_STATUS.get(name, ("optional",
            f"Subsystem {name} is not required for a minimal compute workload"))
        # Try to find constructor line in call graph
        cg_node = find_callgraph_node(cg, constructor)
        file_path = "nvkm/engine/device/base.c"
        if cg_node:
            file_path = cg_node[1]
        subsystems.append({
            "name": name,
            "constructor": constructor,
            "file": file_path,
            "line": line,
            "status": status,
            "reason": reason,
        })

    # 6. Build GR hooks list
    gr_hooks = []
    for hook_name in sorted(want_hooks.keys()):
        func_name = want_hooks[hook_name]
        use, reason = GR_HOOK_USE.get(hook_name,
            ("both", f"GR hook {hook_name} supports compute workloads"))
        # Find function definition line
        cg_node = find_callgraph_node(cg, func_name)
        if cg_node:
            file_path, line_num = cg_node[1], cg_node[2]
        else:
            # grep fallback
            gf = grep_func_line(func_name, f"nvkm/engine/gr/{func_name[:4]}.c")
            if gf:
                file_path, line_num = gf
            else:
                # Try broader search
                file_path, line_num = None, None
        gr_hooks.append({
            "hook": hook_name,
            "function": func_name,
            "file": file_path or "",
            "line": line_num or 0,
            "use": use,
            "reason": reason,
        })

    # 7. Build firmware list
    firmware = list(FIRMWARE)

    # 8. Build steps
    steps = []
    for idx, step_def in enumerate(STEP_FUNCTIONS, 1):
        # Look up each function's file and line
        functions = []
        for func_name in step_def["functions"]:
            cg_node = find_callgraph_node(cg, func_name)
            if cg_node:
                functions.append({
                    "name": func_name,
                    "tree": "nouveau",
                    "file": cg_node[1],
                    "line": cg_node[2],
                })
            elif func_name in MISSING_FUNC_LINES:
                fpath, fline = MISSING_FUNC_LINES[func_name]
                functions.append({
                    "name": func_name,
                    "tree": "nouveau",
                    "file": fpath,
                    "line": fline,
                })
            else:
                # grep fallback
                gf = grep_func_line(func_name, "nvkm/engine/device/base.c")
                if gf:
                    functions.append({
                        "name": func_name,
                        "tree": "nouveau",
                        "file": gf[0],
                        "line": gf[1],
                    })
                else:
                    functions.append({
                        "name": func_name,
                        "tree": "nouveau",
                        "file": "",
                        "line": 0,
                    })

        # For mesa functions, use tree="mesa"
        for f in functions:
            if f["name"] in ("nve4_screen_compute_setup", "nve4_launch_grid"):
                f["tree"] = "mesa"
                f["file"] = f"src/gallium/drivers/nouveau/nvc0/nve4_compute.c"
                # Mesa function lines
                mesa_lines = {"nve4_screen_compute_setup": 44, "nve4_launch_grid": 785}
                f["line"] = mesa_lines.get(f["name"], 0)

        # Collect registers from MMIO accesses
        regs = []
        seen = set()
        for f in functions:
            if f["tree"] == "nouveau" and f["name"] in mmio:
                for (rfile, rline, rreg) in sorted(mmio[f["name"]]):
                    key = (rfile, rline, rreg)
                    if key not in seen:
                        seen.add(key)
                        regs.append({"reg": rreg, "file": rfile, "line": rline})
        regs.sort(key=lambda x: (x["file"], x["line"], x["reg"]))

        step = {
            "step": idx,
            "subsystem": step_def["subsystem"],
            "what": step_def["what"],
            "functions": functions,
            "registers": regs,
            "status": step_def["status"],
            "notes": step_def.get("notes", ""),
        }
        steps.append(step)

    # 9. Assemble result
    result = {
        "subsystems": subsystems,
        "steps": steps,
        "gr_hooks": gr_hooks,
        "firmware": firmware,
    }

    if args.check:
        # Compare with existing file
        out_path = os.path.join(ROOT, "analysis", "min_chain.json")
        if not os.path.isfile(out_path):
            print(f"FAIL: {out_path} does not exist", file=sys.stderr)
            sys.exit(1)
        with open(out_path) as f:
            existing = json.load(f)
        if json.dumps(result, sort_keys=True) != json.dumps(existing, sort_keys=True):
            print(f"FAIL: {out_path} differs from tool output", file=sys.stderr)
            sys.exit(1)
        print("OK: min_chain.json matches tool output")
        sys.exit(0)
    else:
        out_path = os.path.join(ROOT, "analysis", "min_chain.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, sort_keys=False)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
