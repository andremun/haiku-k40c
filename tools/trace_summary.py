#!/usr/bin/env python3
"""Parse a mmiotrace reference-run file and produce a summary.

Outputs:
    analysis/linux_run_trace.json   – structured summary
    analysis/linux_run_trace.md     – human-readable Markdown report

Usage:
    python3 tools/trace_summary.py [--check]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rnndb


def hex_no_leading_zeros(value):
    """Convert a Python int to a hex string with 0x prefix, no leading zeros."""
    return hex(value)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace_path = os.path.join(root, "reference", "linux-run", "mmiotrace.txt.xz")
    json_out = os.path.join(root, "analysis", "linux_run_trace.json")
    md_out = os.path.join(root, "analysis", "linux_run_trace.md")

    check_mode = "--check" in sys.argv

    # ---------- pass through trace (single pass) ----------
    bars = {}          # bar_index -> (base, size)
    maps = []          # list of mapping dicts (ordered)
    by_id = {}         # map_id_str -> mapping dict
    marks = []         # list of {"line": N, "text": ...}
    phases = {k: {
        "first_line": None, "last_line": None,
        "bar0": {"reads": 0, "writes": 0},
        "bar1": {"reads": 0, "writes": 0},
        "bar3": {"reads": 0, "writes": 0},
    } for k in ("load", "job", "after")}
    cur_phase = "load"
    regs = {}          # offset -> register info for job phase
    names_cache = {}   # offset -> name (for job phase registers)
    runs = []          # list of run dicts (job phase only)
    total_lines = 0

    with __import__("lzma").open(trace_path, "rt") as f:
        for line_no, raw_line in enumerate(f, start=1):
            total_lines = line_no
            parts = raw_line.split()
            if not parts:
                continue

            # PCIDEV lines – look for K40c card
            if parts[0] == "PCIDEV" and len(parts) >= 18 and parts[2] == "10de1024":
                for i in range(7):
                    addr = int(parts[4 + i], 16)
                    size = int(parts[11 + i], 16)
                    if size:
                        base = addr & ~0xf
                        bars[i] = (base, size)
                continue

            # MAP line
            if parts[0] == "MAP":
                phys = int(parts[3], 16)
                size = int(parts[5], 16)
                # Determine which BAR contains phys
                bar_idx = None
                for idx, (b, s) in bars.items():
                    if b <= phys < b + s:
                        bar_idx = idx
                        break
                if bar_idx is not None:
                    phys_base = bars[bar_idx][0]
                    m = {
                        "id": int(parts[2]),
                        "line": line_no,
                        "phys": hex_no_leading_zeros(phys),
                        "size": hex_no_leading_zeros(size),
                        "bar": bar_idx,
                        "offset": hex_no_leading_zeros(phys - phys_base),
                        "unmap_line": None,
                    }
                    maps.append(m)
                    by_id[str(parts[2])] = m
                continue

            # UNMAP line
            if parts[0] == "UNMAP":
                mid = str(parts[2])
                if mid in by_id:
                    by_id[mid]["unmap_line"] = line_no
                continue

            # MARK line
            if parts[0] == "MARK":
                marks.append({"line": line_no, "text": " ".join(parts[2:])})
                # Advance phase: load→job, job→after
                phase_map = {"load": "job", "job": "after"}
                cur_phase = phase_map.get(cur_phase, cur_phase)
                continue

            # R / W line – register access
            if parts[0] in ("R", "W"):
                mid = parts[3]
                m = by_id.get(mid)
                if m is None:
                    continue
                bar_key = "bar%d" % m["bar"]
                k = "reads" if parts[0] == "R" else "writes"
                phases[cur_phase][bar_key][k] += 1
                if phases[cur_phase]["first_line"] is None:
                    phases[cur_phase]["first_line"] = line_no
                phases[cur_phase]["last_line"] = line_no

                # Job-phase BAR 0 accesses – collect register info
                if cur_phase == "job" and m["bar"] == 0:
                    phys = int(parts[4], 16)
                    offset = phys - bars[0][0]

                    if offset not in names_cache:
                        result = rnndb.lookup(offset)
                        names_cache[offset] = result["name"] if result else None

                    nm = names_cache[offset]
                    e = regs.setdefault(offset, {
                        "reg": "0x%06x" % offset,
                        "name": nm,
                        "reads": 0,
                        "writes": 0,
                        "first_line": line_no,
                    })
                    e[k] += 1

                    # Build runs (consecutive same-domain)
                    domain = nm.split(".")[0] if nm else "unknown"
                    if runs and runs[-1]["domain"] == domain:
                        runs[-1][k] += 1
                        runs[-1]["last_line"] = line_no
                    else:
                        runs.append({
                            "domain": domain,
                            "first_line": line_no,
                            "last_line": line_no,
                            "reads": 0,
                            "writes": 0,
                        })
                        runs[-1][k] += 1

    # ---------- assemble JSON ----------
    bars_json = {}
    for i in sorted(bars.keys()):
        base, size = bars[i]
        bars_json[str(i)] = {"base": hex_no_leading_zeros(base), "size": hex_no_leading_zeros(size)}

    job_registers = [regs[k] for k in sorted(regs.keys())]

    data = {
        "trace": "reference/linux-run/mmiotrace.txt.xz",
        "lines": total_lines,
        "bars": bars_json,
        "maps": maps,
        "marks": marks,
        "phases": phases,
        "job_registers": job_registers,
        "job_runs": runs,
    }

    if check_mode:
        # Compare existing files with what we would write
        import tempfile
        json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        md_text = build_md(data)

        # Check JSON
        if os.path.exists(json_out):
            with open(json_out) as f:
                existing = f.read()
            if existing != json_text:
                print("MISMATCH: analysis/linux_run_trace.json differs", file=sys.stderr)
                sys.exit(1)
        else:
            print("MISSING: analysis/linux_run_trace.json", file=sys.stderr)
            sys.exit(1)

        # Check MD
        if os.path.exists(md_out):
            with open(md_out) as f:
                existing = f.read()
            if existing != md_text:
                print("MISMATCH: analysis/linux_run_trace.md differs", file=sys.stderr)
                sys.exit(1)
        else:
            print("MISSING: analysis/linux_run_trace.md", file=sys.stderr)
            sys.exit(1)

        print("OK: output files match")
        sys.exit(0)
    else:
        # Write files
        with open(json_out, "w") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        with open(md_out, "w") as f:
            f.write(build_md(data))
        print("Wrote %s (%d lines), %s" % (json_out, total_lines, md_out))


def build_md(data):
    """Build the Markdown document from parsed data."""
    lines = []

    # --- Mappings ---
    lines.append("## Mappings")
    lines.append("")
    lines.append("| id | phys | size | bar | offset | unmap_line |")
    lines.append("|----|------|------|-----|--------|------------|")
    for m in data["maps"]:
        unmap = str(m["unmap_line"]) if m["unmap_line"] is not None else "null"
        lines.append("| %d | %s | %s | %d | %s | %s |" % (
            m["id"], m["phys"], m["size"], m["bar"], m["offset"], unmap))
    lines.append("")

    # --- Phases ---
    lines.append("## Phases")
    lines.append("")
    lines.append("| phase | lines | bar0 reads | bar0 writes | bar1 reads | bar1 writes | bar3 reads | bar3 writes |")
    lines.append("|-------|-------|------------|-------------|------------|-------------|------------|-------------|")
    for phn in ("load", "job", "after"):
        p = data["phases"][phn]
        first = p["first_line"] if p["first_line"] is not None else "–"
        last = p["last_line"] if p["last_line"] is not None else "–"
        span = "%d–%d" % (first, last) if first != "–" else "–"
        lines.append("| %s | %s | %d | %d | %d | %d | %d | %d |" % (
            phn, span,
            p["bar0"]["reads"], p["bar0"]["writes"],
            p["bar1"]["reads"], p["bar1"]["writes"],
            p["bar3"]["reads"], p["bar3"]["writes"],
        ))
    lines.append("")

    # --- Domains of the job ---
    lines.append("## Domains of the job")
    lines.append("")
    # Aggregate by domain across all job_registers
    domain_data = {}
    for reg in data["job_registers"]:
        d = reg["name"].split(".")[0] if reg["name"] else "unknown"
        if d not in domain_data:
            domain_data[d] = {"registers": 0, "reads": 0, "writes": 0}
        domain_data[d]["registers"] += 1
        domain_data[d]["reads"] += reg["reads"]
        domain_data[d]["writes"] += reg["writes"]
    # Sort by total accesses, largest first
    domains_sorted = sorted(domain_data.items(), key=lambda x: x[1]["reads"] + x[1]["writes"], reverse=True)

    lines.append("| domain | registers | reads | writes |")
    lines.append("|--------|-----------|-------|--------|")
    for d, info in domains_sorted:
        lines.append("| %s | %d | %d | %d |" % (d, info["registers"], info["reads"], info["writes"]))
    lines.append("")

    # --- Timeline of the job ---
    lines.append("## Timeline of the job")
    lines.append("")
    lines.append("| # | first_line | last_line | domain | reads | writes |")
    lines.append("|---|------------|-----------|--------|-------|--------|")
    for i, run in enumerate(data["job_runs"], start=1):
        lines.append("| %d | %d | %d | %s | %d | %d |" % (
            i, run["first_line"], run["last_line"], run["domain"],
            run["reads"], run["writes"]))
    lines.append("")

    # --- Registers without a name ---
    lines.append("## Registers without a name")
    lines.append("")
    unnamed = [r for r in data["job_registers"] if r["name"] is None]
    if unnamed:
        # 8 per line, as 0x...... (with prefix)
        hexes = [r["reg"] for r in unnamed]
        for i in range(0, len(hexes), 8):
            lines.append(" ".join(hexes[i:i+8]))
        lines.append("")
    else:
        lines.append("(none)")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
