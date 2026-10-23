#!/usr/bin/env python3
"""Extract MMIO accesses from Nouveau source files listed in analysis/files.json.

Outputs registers/mmio_accesses.json: a list of
{"file", "line", "function", "op", "reg", "reg_value", "value", "mask",
"subsystem"}.

--check  writes nothing and exits 0 when the JSON file is exactly what
the tool generates, else 1.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
OUTPUT = os.path.join(ROOT, "registers", "mmio_accesses.json")

# Regex for nvkm_rd32, nvkm_wr32, nvkm_mask calls (the op name)
MMIO_RE = re.compile(r"\bnvkm_(rd32|wr32|mask)\s*\(")
# C keywords that look like function calls but aren't definitions
C_KEYWORDS = frozenset({
    "if", "else", "for", "while", "do", "switch", "case", "return",
    "break", "continue", "goto", "sizeof", "typedef", "struct", "union",
    "enum", "defined", "asm", "__asm", "__asm__",
})
# Regex to find function definitions (single line):
# optional modifiers, type, name(args)
FUNC_RE = re.compile(
    r"^(?:\s*static\s+|const\s+|inline\s+|volatile\s+|unsigned\s+|struct\s+\w+\s+)*"
    r"(?:[\w\s\*]+\b)?(\w+)\s*\((.+)\)\s*$"
)
# Return type on one line, function name on the next: "type name(args)"
FUNC_RE_MULTI = re.compile(r"^(\w+)\s+(\w+)\s*\((.+)\)\s*$")
# Comment lines to skip
COMMENT_RE = re.compile(r"^\s*(//|/\*|\*)")
# Hex constant
HEX_RE = re.compile(r"0x[0-9a-fA-F]+")


def find_function(lines, start_line):
    """Return the last function-like identifier seen on any line from
    0..start_line, matching the same logic as check_repo.py:
    the first word before '(' at the start of the line."""
    result = ""
    for i in range(start_line + 1):
        line = lines[i].rstrip()
        m = re.match(r"^(\w+)\s*\(", line)
        if m:
            name = m.group(1)
            if name not in C_KEYWORDS:
                result = name
    return result


def find_matching_paren(text, start):
    """Find the position of the closing paren matching the one at `start`.

    `start` is the index of the opening '(' after the function name.
    """
    depth = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return len(text) - 1


def split_args(text):
    """Split comma-separated arguments, respecting nested parens and brackets.

    Returns a list of argument strings (stripped).
    """
    args = []
    depth = 0
    bracket_depth = 0
    current = []
    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "[":
            bracket_depth += 1
            current.append(ch)
        elif ch == "]":
            bracket_depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0 and bracket_depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    remaining = "".join(current).strip()
    if remaining:
        args.append(remaining)
    return args


def extract_mmio_accesses():
    """Extract all MMIO calls from the files in analysis/files.json."""
    files_data = json.load(open(os.path.join(ROOT, "analysis", "files.json")))
    path_to_sub = {}
    for e in files_data:
        if isinstance(e, dict):
            path_to_sub[e["path"]] = e.get("subsystem", "unknown")

    results = []
    for path in sorted(path_to_sub.keys()):
        full_path = os.path.join(NV, path)
        try:
            with open(full_path, errors="replace") as fh:
                raw_lines = fh.readlines()
        except OSError:
            continue

        # Build a list of (line_number_1based, joined_text) for lines containing MMIO
        i = 0
        while i < len(raw_lines):
            line_idx = i  # 0-based index of the first line of this call
            line_text = raw_lines[i].rstrip("\n")

            # Check if this line (or continued lines) contains an MMIO call
            # First, try the single line
            mmio_match = MMIO_RE.search(line_text)
            if mmio_match:
                # Single-line call: extract it and any remaining calls on the line
                # We may have multiple calls on one line (e.g., nvkm_wr32(..., nvkm_rd32(...)))
                # Find all top-level nvkm_rd32/wr32/mask calls on this line
                end = _extract_from_line(results, path, path_to_sub, line_idx, line_text,
                                         raw_lines, i, len(raw_lines))
                i = max(i + 1, end + 1)  # end=-1 means i+=1; end=N means skip to N+1
            else:
                # Check if the line starts a multi-line MMIO call.
                # Only join if parens are unbalanced on this line.
                is_multi = line_text.count("(") > line_text.count(")")
                if is_multi:
                    # Multi-line call: join lines until parens balance
                    joined = line_text
                    end_line = i
                    while end_line + 1 < len(raw_lines) and joined.count("(") > joined.count(")"):
                        end_line += 1
                        joined += raw_lines[end_line].rstrip("\n")
                    # Now joined is the complete call
                    # Find MMIO calls within the joined text
                    line_map = _build_line_map(joined, raw_lines, i, end_line)
                    _extract_from_joined(results, path, path_to_sub, line_idx, joined,
                                         line_map, end_line, raw_lines)
                    i = end_line + 1
                else:
                    i += 1

    # Sort by file, then line
    results.sort(key=lambda e: (e["file"], e["line"]))
    return results


def _extract_all_mmio_positions(text):
    """Find all MMIO calls in text, including nested ones.

    Returns a list of (start, end, op) tuples for each call.
    We collect them from inside-out: first find all call positions,
    then extract arguments for each.
    """
    calls = []
    pos = 0
    while True:
        mmio_match = MMIO_RE.search(text, pos)
        if not mmio_match:
            break
        op = mmio_match.group(1)
        paren_open = mmio_match.end() - 1
        close_paren = find_matching_paren(text, paren_open)
        calls.append((mmio_match.start(), close_paren, op))
        pos = mmio_match.start() + 1  # Move forward by 1 char to catch nested calls
    return calls


def _build_line_map(joined_text, raw_lines, start_idx, end_line):
    """Build an offset map: line_map[j] = 0-based line index in raw_lines
    for the character at position j in joined_text.

    joined_text is formed by concatenating raw_lines[start_idx]..raw_lines[end_line]
    (each stripped of trailing newline).
    """
    line_map = []
    for li in range(start_idx, end_line + 1):
        chunk = raw_lines[li].rstrip("\n")
        for _ in chunk:
            line_map.append(li)
    return line_map


def _extract_from_line(results, path, path_to_sub, line_idx, line_text,
                       raw_lines, i, total_lines):
    """Extract MMIO calls from a line. Handles multi-call lines and
    calls that span multiple lines."""
    # Find all MMIO calls on this line (including nested)
    calls = _extract_all_mmio_positions(line_text)

    if not calls:
        return -1

    # Check if parens are unbalanced (call spans multiple lines)
    if line_text.count("(") > line_text.count(")"):
        # The call spans multiple lines -- join and use multi-line logic
        joined = line_text
        end_line = i
        while end_line + 1 < total_lines and joined.count("(") > joined.count(")"):
            end_line += 1
            joined += raw_lines[end_line].rstrip("\n")
        line_map = _build_line_map(joined, raw_lines, i, end_line)
        _extract_from_joined(results, path, path_to_sub, line_idx, joined,
                             line_map, end_line, raw_lines)
        return end_line  # signal main loop to skip past joined lines

    # All calls are on this single line
    func_name = find_function(raw_lines, line_idx)

    for start, close_paren, op in calls:
        mmio_match = MMIO_RE.search(line_text, start)
        paren_open = mmio_match.end() - 1

        # Extract the argument text (everything between ( and ))
        args_text = line_text[paren_open + 1:close_paren]

        # Split into arguments
        args = split_args(args_text)

        # Determine reg, value, mask based on op
        reg = value = mask = None
        if op == "rd32":
            # nvkm_rd32(device, reg)
            if len(args) >= 2:
                reg = args[1]
        elif op == "wr32":
            # nvkm_wr32(device, reg, value)
            if len(args) >= 3:
                reg = args[1]
                value = args[2]
        elif op == "mask":
            # nvkm_mask(device, reg, mask, value)
            if len(args) >= 4:
                reg = args[1]
                mask = args[2]
                value = args[3]

        # Determine if reg is a constant
        reg_value = None
        if reg is not None and HEX_RE.fullmatch(reg.strip()):
            reg_value = int(reg.strip(), 16)

        entry = {
            "file": path,
            "line": line_idx + 1,  # 1-based
            "function": func_name,
            "op": op,
            "reg": reg,
            "reg_value": reg_value,
            "value": value,
            "mask": mask,
            "subsystem": path_to_sub.get(path, "unknown"),
        }
        results.append(entry)

    return -1  # single-line: main loop should advance by 1


def _extract_from_joined(results, path, path_to_sub, line_idx, joined_text,
                         line_map, end_line, raw_lines):
    """Extract MMIO calls from a multi-line joined text.

    `line_map` maps each character position in `joined_text` to the
    0-based index into `raw_lines`, so each extracted call can be
    assigned to its actual source line.
    """
    # Same logic as single-line, but using joined_text
    calls = _extract_all_mmio_positions(joined_text)
    func_name = find_function(raw_lines, line_idx)

    for start, close_paren, op in calls:
        mmio_match = MMIO_RE.search(joined_text, start)
        paren_open = mmio_match.end() - 1
        args_text = joined_text[paren_open + 1:close_paren]
        args = split_args(args_text)

        reg = value = mask = None
        if op == "rd32":
            if len(args) >= 2:
                reg = args[1]
        elif op == "wr32":
            if len(args) >= 3:
                reg = args[1]
                value = args[2]
        elif op == "mask":
            if len(args) >= 4:
                reg = args[1]
                mask = args[2]
                value = args[3]

        reg_value = None
        if reg is not None and HEX_RE.fullmatch(reg.strip()):
            reg_value = int(reg.strip(), 16)

        # Assign the call to the line where its function name starts
        call_line = line_map[start] + 1  # 1-based

        entry = {
            "file": path,
            "line": call_line,
            "function": func_name,
            "op": op,
            "reg": reg,
            "reg_value": reg_value,
            "value": value,
            "mask": mask,
            "subsystem": path_to_sub.get(path, "unknown"),
        }
        results.append(entry)


def generate_output():
    """Generate the JSON output."""
    data = extract_mmio_accesses()
    return data


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Compare existing file against what the tool generates
        existing = None
        if os.path.exists(OUTPUT):
            try:
                with open(OUTPUT) as f:
                    existing = json.load(f)
            except ValueError:
                print(f"{OUTPUT}: invalid JSON", file=sys.stderr)
                sys.exit(1)
        generated = generate_output()

        if existing != generated:
            print("FAIL: registers/mmio_accesses.json is not what the tool generates",
                  file=sys.stderr)
            sys.exit(1)
        print("OK")
    else:
        data = generate_output()
        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
        with open(OUTPUT, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {len(data)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()
