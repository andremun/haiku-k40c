#!/usr/bin/env python3
# provenance.py — Source provenance of driver constants.
# Reads constant lines from src/*.h and src/*.cpp, extracts citations,
# and writes docs/register-provenance.md.
#
# Usage:
#   python3 tools/provenance.py          # generate the document
#   python3 tools/provenance.py --check  # verify document matches tool output
#   python3 tools/provenance.py --missing  # list lines missing citations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
MESABASE = os.path.join(ROOT, "reference", "mesa")

# Regex for citations like path/file.c:LINE or file.h:LINE
CIT_RE = re.compile(r"([\w./-]*\w\.(?:c|h)):(\d+)")
# Regex for "no source:" in comments
NOSRC_RE = re.compile(r"no source:")
# Regex for constant lines: hex ≥2 digits or constexpr
CONST_RE = re.compile(r'0x[0-9a-fA-F]{2,}|\bconstexpr\b')


def build_index():
    """Build a map from basename to (tree, relpath) pairs for all .c/.h files."""
    index = {}
    for base, tree in ((NV, "nouveau"), (MESABASE, "mesa")):
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base, followlinks=True):
            for f in files:
                if f.endswith((".c", ".h")):
                    relpath = os.path.relpath(os.path.join(dirpath, f), base)
                    index.setdefault(f, []).append((tree, relpath))
    return index


def find_citation(comment_text, index):
    """Find all citations in comment text and resolve them.
    Returns (resolved_citation_or_none, reason_if_no_source)."""
    cits = CIT_RE.findall(comment_text)
    if cits:
        for fname, lineno in cits:
            # Resolve by basename
            basenames = [os.path.basename(f) for f, _ in cits]
            # Find the matching file
            cand = []
            for cited_file, cited_line in cits:
                bname = os.path.basename(cited_file)
                matches = [c for c in index.get(bname, []) if c[1].endswith(bname)]
                if len(matches) == 1:
                    tree, relpath = matches[0]
                    base = NV if tree == "nouveau" else MESABASE
                    fullpath = os.path.join(base, relpath)
                    n_lines = len(open(fullpath, errors="replace").read().split("\n"))
                    if 0 < int(cited_line) <= n_lines:
                        cand.append((cited_file, cited_line, relpath))
                        break
            if cand:
                return cand[0][2] + ":" + cand[0][1]
        # Multiple ambiguous matches or resolution failed
        return "no source: ambiguous citation"
    if NOSRC_RE.search(comment_text):
        m = NOSRC_RE.search(comment_text)
        rest = comment_text[m.end():].strip()
        return "no source: " + rest if rest else "no source: not found"
    return None  # truly uncited


def scan_file(path, index):
    """Scan a file for constant lines with citations.
    Returns list of (rel_path, line_num, code, citation, cited_line_text, status)."""
    rel = os.path.relpath(path, ROOT)
    if rel.startswith("src/hw/"):
        return []

    lines = open(path, errors="replace").read().split("\n")
    results = []

    for i, line in enumerate(lines):
        code = re.sub(r'"[^"]*"', '""', line.split("//")[0])
        if not CONST_RE.search(code):
            continue

        # Gather comment text: current line + preceding comment lines
        full_code = re.sub(r'"[^"]*"', '""', line)
        com = ""
        if "//" in full_code:
            com = full_code.split("//", 1)[1]
        j = i - 1
        while j >= 0 and lines[j].strip().startswith("//"):
            line_text = lines[j]
            if "//" in line_text:
                com = " " + line_text.split("//", 1)[1] + com
            j -= 1

        citation = find_citation(com, index)
        status = "SOURCE_ONLY"

        if citation and citation.startswith("no source:"):
            # It has a "no source" annotation
            status = "SOURCE_ONLY"
        elif citation is None:
            # Uncited
            citation = "UNCITED"
        else:
            # Resolved citation
            status = "SOURCE_ONLY"

        results.append((rel, i + 1, code.strip(), citation, status))

    return results


def write_document(all_results):
    """Write docs/register-provenance.md."""
    # Group by source file
    by_file = {}
    for rel, linenum, code, citation, status in all_results:
        by_file.setdefault(rel, []).append((linenum, code, citation, status))

    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    md = os.path.join(ROOT, "docs", "register-provenance.md")

    lines = []
    lines.append("# Register Provenance")
    lines.append("")
    lines.append("Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`")
    lines.append("(excluding `src/hw/`) is listed below with its source citation.")
    lines.append("")
    lines.append("Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).")
    lines.append("")

    uncited = []

    for rel in sorted(by_file.keys()):
        lines.append(f"## {rel}")
        lines.append("")
        lines.append("| Line | Code | Source | Status |")
        lines.append("|------|------|--------|--------|")
        for linenum, code, citation, status in sorted(by_file[rel]):
            # Escape pipes in cells
            code_escaped = code.replace("|", "\\|")
            citation_escaped = citation.replace("|", "\\|")
            lines.append(f"| `{rel}:{linenum}` | `{code_escaped}` | {citation_escaped} | {status} |")
        lines.append("")

    # Open section
    for rel, entries in sorted(by_file.items()):
        for linenum, code, citation, status in entries:
            if citation == "UNCITED":
                uncited.append(f"{rel}:{linenum}")
            elif citation.startswith("no source:"):
                uncited.append(f"{rel}:{linenum} ({citation})")

    lines.append("## Open")
    lines.append("")
    if uncited:
        lines.append("The following constant lines have no source citation:")
        lines.append("")
        for u in uncited:
            lines.append(f"- {u}")
        lines.append("")
        lines.append("These constants may be verified by a mmiotrace in task C5.")
    else:
        lines.append("All constant lines have citations or `no source:` annotations.")
        lines.append("")
        lines.append("A mmiotrace in task C5 can verify which of these are actually used.")

    lines.append("")

    with open(md, "w") as f:
        f.write("\n".join(lines))

    return md


def main():
    mode = "--missing" if len(sys.argv) > 1 and sys.argv[1] == "--missing" else "generate"
    check = len(sys.argv) > 1 and sys.argv[1] == "--check"

    index = build_index()

    # Scan all source files
    all_results = []
    for ext in ("*.h", "*.cpp"):
        for path in sorted(glob.glob(os.path.join(ROOT, "src", "*", ext))):
            all_results.extend(scan_file(path, index))

    if check:
        # Read existing document and compare
        md = os.path.join(ROOT, "docs", "register-provenance.md")
        if not os.path.exists(md):
            print(f"FAIL: {md} does not exist", file=sys.stderr)
            sys.exit(1)
        existing = open(md, errors="replace").read()

        # Generate expected
        import io
        import contextlib
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            # Re-generate to compare
            by_file = {}
            for rel, linenum, code, citation, status in all_results:
                by_file.setdefault(rel, []).append((linenum, code, citation, status))

            exp_lines = []
            exp_lines.append("# Register Provenance")
            exp_lines.append("")
            exp_lines.append("Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`")
            exp_lines.append("(excluding `src/hw/`) is listed below with its source citation.")
            exp_lines.append("")
            exp_lines.append("Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).")
            exp_lines.append("")

            for rel in sorted(by_file.keys()):
                exp_lines.append(f"## {rel}")
                exp_lines.append("")
                exp_lines.append("| Line | Code | Source | Status |")
                exp_lines.append("|------|------|--------|--------|")
                for linenum, code, citation, status in sorted(by_file[rel]):
                    code_escaped = code.replace("|", "\\|")
                    citation_escaped = citation.replace("|", "\\|")
                    exp_lines.append(f"| `{rel}:{linenum}` | `{code_escaped}` | {citation_escaped} | {status} |")
                exp_lines.append("")

            uncited = []
            for rel, entries in sorted(by_file.items()):
                for linenum, code, citation, status in entries:
                    if citation == "UNCITED":
                        uncited.append(f"{rel}:{linenum}")
                    elif citation.startswith("no source:"):
                        uncited.append(f"{rel}:{linenum} ({citation})")

            exp_lines.append("## Open")
            exp_lines.append("")
            if uncited:
                exp_lines.append("The following constant lines have no source citation:")
                exp_lines.append("")
                for u in uncited:
                    exp_lines.append(f"- {u}")
                exp_lines.append("")
                exp_lines.append("These constants may be verified by a mmiotrace in task C5.")
            else:
                exp_lines.append("All constant lines have citations or `no source:` annotations.")
                exp_lines.append("")
                exp_lines.append("A mmiotrace in task C5 can verify which of these are actually used.")

            exp_lines.append("")
            expected = "\n".join(exp_lines)

        if existing != expected:
            print("FAIL: docs/register-provenance.md does not match tool output", file=sys.stderr)
            # Show diff
            import difflib
            diff = difflib.unified_diff(
                existing.splitlines(keepends=True),
                expected.splitlines(keepends=True),
                fromfile="existing",
                tofile="expected",
            )
            print("".join(diff), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if mode == "--missing":
        uncited = []
        for rel, linenum, code, citation, status in all_results:
            if citation == "UNCITED":
                uncited.append(f"{rel}:{linenum}")
        if uncited:
            print(f"{len(uncited)} uncited constant line(s):")
            for u in uncited:
                print(f"  {u}")
        else:
            print("All constant lines have citations or `no source:` annotations.")
        sys.exit(0)

    # Generate mode
    write_document(all_results)
    md = os.path.join(ROOT, "docs", "register-provenance.md")
    print(f"Generated {md}")


if __name__ == "__main__":
    main()
