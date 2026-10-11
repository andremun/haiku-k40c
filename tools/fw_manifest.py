#!/usr/bin/env python3
"""Generate the firmware manifest for task C2.

Reads the Nouveau .fuc3 headers and gf100.c to build a manifest
of built-in firmware arrays, external firmware files, and the
load sequence.

Usage:
    python3 tools/fw_manifest.py             # write firmware/manifest.yaml
    python3 tools/fw_manifest.py --check     # verify manifest matches, exit 0
    python3 tools/fw_manifest.py --extract   # write firmware/*.bin to build/
"""
import hashlib
import os
import re
import struct
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
MANIFEST = os.path.join(ROOT, "firmware", "manifest.yaml")
BUILD = os.path.join(ROOT, "build", "firmware")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def src_lines(path):
    """Return lines of a Nouveau source file, or None if not found."""
    full = os.path.join(NV, path)
    if os.path.exists(full):
        with open(full) as f:
            return f.read().splitlines()
    return None


def extract_arrays(hdr_path, asm_path, engine):
    """Parse a .fuc3.h header for uint32_t array definitions.

    Returns a list of dicts with name, first/last_line, words (count), etc.
    Also returns the raw word lists as a parallel list and the sorted set of
    #include directives from the asm source.
    """
    lines = src_lines(hdr_path)
    if not lines:
        return [], [], []

    license_line = lines[0] if lines else ""
    is_mit = "SPDX-License-Identifier: MIT" in license_line

    # Extract includes from assembly source
    asm_lines = src_lines(asm_path) or []
    includes = sorted(set(re.findall(r'#include "([\w.]+)"', "\n".join(asm_lines))))

    arrays = []
    raw_words_list = []
    cur = None
    for i, text in enumerate(lines, 1):
        m = re.match(r"static uint32_t (\w+)\[\] = \{", text)
        if m:
            name = m.group(1)
            kind = name.rsplit("_", 1)[1]
            cur = {
                "name": name,
                "engine": engine,
                "kind": kind,
                "first_line": i,
                "words": [],
            }
            raw_words_list.append(cur["words"])
        elif cur and text.startswith("};"):
            cur["last_line"] = i
            words = cur["words"]
            blob = struct.pack("<%dI" % len(words), *words)
            cur.update(
                words=len(words),
                size_bytes=len(blob),
                sha256=hashlib.sha256(blob).hexdigest(),
                source="built-in",
                file=hdr_path,
                asm_source=asm_path,
                asm_includes=includes,
                license="MIT" if is_mit else None,
            )
            arrays.append(cur)
            cur = None
        elif cur:
            # Drop C-style comments before extracting hex values
            text_no_comment = text.split("/*")[0]
            for w in re.findall(r"\b0x[0-9a-fA-F]{8}\b", text_no_comment):
                cur["words"].append(int(w, 16))

    return arrays, raw_words_list, includes


def extract_external(gf100_lines):
    """Parse gf100.c for gf100_gr_load_fw() calls.

    Returns a list of dicts with filename, engine, kind, requested_at, etc.
    """
    entries = []
    for i, text in enumerate(gf100_lines, 1):
        m = re.search(
            r'gf100_gr_load_fw\(gr, "(\w+)", &gr->(\w+)\.(\w+)\)', text
        )
        if m:
            filename = m.group(1)
            engine = m.group(2)
            field = m.group(3)
            kind = "code" if field == "inst" else "data"
            entries.append({
                "filename": filename,
                "engine": engine,
                "kind": kind,
                "requested_at": "nvkm/engine/gr/gf100.c:%d" % i,
                "source": "external-file",
                "distribution": "do-not-distribute",
                "needed": False,
            })
    return entries


def extract_load_sequence(gf100_lines):
    """Parse body of gf100_gr_init_ctxctl_int for function calls.

    Returns a list of (line, call_name) tuples.
    """
    seq = []
    inside = False
    for i, text in enumerate(gf100_lines, 1):
        if text.startswith("gf100_gr_init_ctxctl_int("):
            inside = True
        elif inside and text.startswith("}"):
            break
        elif inside:
            for m in re.finditer(r"\b(nvkm_\w+|gf100_gr_\w+)\(", text):
                seq.append((i, m.group(1)))
    return seq


# ---------------------------------------------------------------------------
# What-text table for load_sequence entries
# ---------------------------------------------------------------------------

WHAT_TEXTS = {
    1842: "Write 0 to master control register 0x000260 before the microcode upload (purpose not known)",
    1843: "Load FECS Falcon data memory from firmware blob at offset zero",
    1846: "Load FECS Falcon instruction memory from firmware blob",
    1851: "Load GPCCS Falcon data memory from firmware blob at offset zero",
    1854: "Load GPCCS Falcon instruction memory from firmware blob",
    1857: "Write 1 to master control register 0x000260 after both microcode uploads (purpose not known)",
    1860: "Initialize HUB context register data with base address",
    1861: "Initialize GPC 0 context register data with base address",
    1862: "Initialize GPC 1 context register data with base address",
    1863: "Initialize TPC context register data with base address",
    1864: "Initialize PPC context register data with base address",
    1867: "Write HUB control register to clear configuration bits",
    1868: "Start HUB ucode execution by writing control register",
    1869: "Wait up to two seconds (2000 ms) for HUB ucode to become ready",
    1870: "Read HUB status register to check execution progress",
    1873: "Debug context control registers on timeout failure path",
    1877: "Read GR context size from hardware status register",
}


def build_manifest():
    """Build and return the full manifest dictionary."""
    # Built-in arrays
    hdr_pairs = [
        ("nvkm/engine/gr/fuc/hubgk110.fuc3.h",
         "nvkm/engine/gr/fuc/hubgk110.fuc3", "fecs"),
        ("nvkm/engine/gr/fuc/gpcgk110.fuc3.h",
         "nvkm/engine/gr/fuc/gpcgk110.fuc3", "gpccs"),
    ]
    all_arrays = []
    for hdr, asm, engine in hdr_pairs:
        arrays, _, _ = extract_arrays(hdr, asm, engine)
        all_arrays.extend(arrays)

    # External firmware
    gf100_lines = src_lines("nvkm/engine/gr/gf100.c") or []
    external = extract_external(gf100_lines)

    # Load sequence
    seq_tuples = extract_load_sequence(gf100_lines)
    load_sequence = []
    for line, call in seq_tuples:
        what = WHAT_TEXTS.get(line, "Query hardware state at unknown register")
        load_sequence.append({
            "line": line,
            "call": call,
            "what": what,
        })

    return {
        "built_in": all_arrays,
        "external": external,
        "load_sequence": load_sequence,
    }


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def mode_generate():
    """Generate the manifest YAML file."""
    data = build_manifest()
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def mode_check():
    """Verify the manifest matches what the tool generates."""
    data = build_manifest()
    expected = yaml.safe_dump(data, sort_keys=False)
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            actual = f.read()
        if actual != expected:
            print("ERROR: manifest.yaml differs from tool output", file=sys.stderr)
            # Show diff
            import difflib
            diff = difflib.unified_diff(
                actual.splitlines(), expected.splitlines(),
                lineterm="", fromfile="manifest.yaml", tofile="tool output",
            )
            for line in diff:
                print(line)
            sys.exit(1)
    else:
        print("ERROR: manifest.yaml does not exist", file=sys.stderr)
        sys.exit(1)


def mode_extract():
    """Write firmware arrays as binary files for testing."""
    os.makedirs(BUILD, exist_ok=True)
    hdr_pairs = [
        ("nvkm/engine/gr/fuc/hubgk110.fuc3.h",
         "nvkm/engine/gr/fuc/hubgk110.fuc3", "fecs"),
        ("nvkm/engine/gr/fuc/gpcgk110.fuc3.h",
         "nvkm/engine/gr/fuc/gpcgk110.fuc3", "gpccs"),
    ]
    for hdr, asm, engine in hdr_pairs:
        arrays, raw_words, _ = extract_arrays(hdr, asm, engine)
        for arr, words in zip(arrays, raw_words):
            blob = struct.pack("<%dI" % len(words), *words)
            path = os.path.join(BUILD, arr["name"] + ".bin")
            with open(path, "wb") as f:
                f.write(blob)
            print(f"Wrote {path} ({arr['size_bytes']} bytes, {arr['sha256']})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        mode_generate()
    elif sys.argv[1] == "--check":
        mode_check()
    elif sys.argv[1] == "--extract":
        mode_extract()
    else:
        print(f"Unknown option: {sys.argv[1]}", file=sys.stderr)
        print("Usage: fw_manifest.py [--check | --extract]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
