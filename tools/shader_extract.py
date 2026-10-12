#!/usr/bin/env python3
"""Extract the shader binary and launch descriptor from the reference run log.

Reads reference/linux-run/compute_test.log and tools/guest/files/compute_test.c.
Writes:
  firmware/compute_add1.bin
  analysis/linux_run_shader.json
  firmware/compute_add1.md

Usage:
  python3 tools/shader_extract.py
  python3 tools/shader_extract.py --check
"""
import os
import re
import sys
import json
import hashlib
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "reference", "linux-run", "compute_test.log")
SRC = os.path.join(ROOT, "tools", "guest", "files", "compute_test.c")
BIN = os.path.join(ROOT, "firmware", "compute_add1.bin")
JSON_OUT = os.path.join(ROOT, "analysis", "linux_run_shader.json")
MD_OUT = os.path.join(ROOT, "firmware", "compute_add1.md")


def parse_log():
    L = open(LOG).read().split("\n")

    # Find the last "shader binary code" line
    i = max(k for k, l in enumerate(L) if l.startswith("shader binary code"))
    size = int(re.search(r"0x([0-9a-f]+) bytes", L[i]).group(1), 16)

    # Parse words
    words, k = [], i + 1
    while len(words) < size // 4:
        words += L[k].split()
        k += 1

    # Build binary blob (little-endian)
    blob = struct.pack("<%dI" % len(words), *[int(w, 16) for w in words])

    # Parse Queue Meta Data
    q = L.index("Queue Meta Data:")
    qmd = []
    for l in L[q + 1:]:
        m = re.match(r"^   (\S+)\s*: (.*\S)\s*$", l)
        if not m:
            break
        qmd.append({"name": m.group(1), "value": m.group(2)})

    # Renderer and version from RESULT.txt (or from log header)
    res = open(os.path.join(ROOT, "reference", "linux-run", "RESULT.txt")).read().split("\n")
    renderer = ""
    version = ""
    for line in res:
        if line.startswith("renderer: "):
            renderer = line[len("renderer: "):]
        if line.startswith("version: "):
            version = line[len("version: "):]

    # Shader source from compute_test.c
    csrc = open(SRC).read()
    start = csrc.index("kSource")
    end = csrc.index("int\nmain")
    csrc_section = csrc[start:end]
    want_src = re.findall(r'^\t"(.*)\\n"', csrc_section, re.M)
    want_src = [x.replace("\\t", "\t") for x in want_src]

    return {
        "log_line": i + 1,
        "size_bytes": size,
        "words": words,
        "blob": blob,
        "qmd": qmd,
        "renderer": renderer,
        "version": version,
        "source": want_src,
    }


def extract_shader_source():
    """Extract the kSource lines from compute_test.c."""
    csrc = open(SRC).read()
    start = csrc.index("kSource")
    end = csrc.index("int\nmain")
    csrc_section = csrc[start:end]
    lines = re.findall(r'^\t"(.*)\\n"', csrc_section, re.M)
    lines = [x.replace("\\t", "\t") for x in lines]
    return lines


def write_bin(blob):
    os.makedirs(os.path.dirname(BIN), exist_ok=True)
    open(BIN, "wb").write(blob)


def write_json(data):
    os.makedirs(os.path.dirname(JSON_OUT), exist_ok=True)
    sha = hashlib.sha256(data["blob"]).hexdigest()
    obj = {
        "log": "reference/linux-run/compute_test.log",
        "log_line": data["log_line"],
        "size_bytes": data["size_bytes"],
        "words": ["0x" + w.lower() for w in data["words"]],
        "sha256": sha,
        "renderer": data["renderer"],
        "version": data["version"],
        "source": data["source"],
        "qmd": data["qmd"],
    }
    with open(JSON_OUT, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def write_md(data):
    os.makedirs(os.path.dirname(MD_OUT), exist_ok=True)
    sha = hashlib.sha256(data["blob"]).hexdigest()
    lines = []

    # Source section
    lines.append("## Source\n")
    lines.append("```glsl\n")
    for line in data["source"]:
        lines.append(line + "\n")
    lines.append("```\n")
    lines.append("\n")
    lines.append("Source file: `tools/guest/files/compute_test.c` (variable `kSource`).\n")

    # How it was made section
    lines.append("\n## How it was made\n")
    lines.append("\n")
    lines.append("- **Renderer:** " + data["renderer"] + "\n")
    lines.append("- **Mesa version:** " + data["version"] + "\n")
    lines.append("- **Command:** `./compute_test`\n")
    lines.append("- **Environment:** `NV50_PROG_DEBUG=1` and `NV50_PROG_CHIPSET=0xf1`\n")
    lines.append("- **Log:** `reference/linux-run/compute_test.log` line " + str(data["log_line"]) + "\n")

    # Code section
    lines.append("\n## Code\n")
    lines.append("\n")
    lines.append("Size: " + str(data["size_bytes"]) + " bytes\n")
    lines.append("SHA-256: " + sha + "\n")
    lines.append("\n")
    lines.append("```\n")
    for idx in range(0, len(data["words"]), 8):
        chunk = data["words"][idx:idx + 8]
        lines.append(" ".join(chunk) + "\n")
    lines.append("```\n")

    # Launch descriptor section (only non-0x0 and non-FALSE fields)
    lines.append("\n## Launch descriptor\n")
    lines.append("\n")
    lines.append("| Field | Value |\n")
    lines.append("|-------|-------|\n")
    for entry in data["qmd"]:
        if entry["value"] not in ("0x0", "FALSE"):
            lines.append("| " + entry["name"] + " | " + entry["value"] + " |\n")

    # Not known section
    lines.append("\n## Not known\n")
    lines.append("\n")
    lines.append("- What each instruction word in the shader binary means (opcode, operands).\n")
    lines.append("- The meaning of the QMD field sizes and layout in memory.\n")
    lines.append("- How the constant buffer at address 0x510000 is laid out.\n")

    with open(MD_OUT, "w") as f:
        f.write("".join(lines))


def main():
    if "--check" in sys.argv:
        # Re-parse and compare against existing files
        data = parse_log()
        sha = hashlib.sha256(data["blob"]).hexdigest()

        # Check binary
        if not os.path.exists(BIN):
            sys.exit(1)
        if open(BIN, "rb").read() != data["blob"]:
            sys.exit(1)

        # Check JSON
        if not os.path.exists(JSON_OUT):
            sys.exit(1)
        j = json.load(open(JSON_OUT))
        if j.get("log_line") != data["log_line"]:
            sys.exit(1)
        if j.get("size_bytes") != data["size_bytes"]:
            sys.exit(1)
        if [str(w).lower() for w in j.get("words", [])] != ["0x" + w for w in data["words"]]:
            sys.exit(1)
        if j.get("sha256") != sha:
            sys.exit(1)
        got_qmd = [(e.get("name"), e.get("value")) for e in j.get("qmd", []) if isinstance(e, dict)]
        want_qmd = [(e["name"], e["value"]) for e in data["qmd"]]
        if got_qmd != want_qmd:
            sys.exit(1)

        # Check MD
        if not os.path.exists(MD_OUT):
            sys.exit(1)
        md = open(MD_OUT).read()
        if sha not in md:
            sys.exit(1)

        sys.exit(0)
    else:
        data = parse_log()
        write_bin(data["blob"])
        write_json(data)
        write_md(data)
        print("Wrote " + BIN)
        print("Wrote " + JSON_OUT)
        print("Wrote " + MD_OUT)


if __name__ == "__main__":
    main()
