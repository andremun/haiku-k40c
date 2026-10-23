#!/usr/bin/env python3
"""B2: Call graph from chipset constructors through init paths.

Outputs analysis/callgraph.json and analysis/callgraph.md.
When run with --check, writes nothing and exits 0 if analysis/callgraph.json
matches what the tool would generate, else exits 1.

Scope: all .c files listed in analysis/files.json.
Roots: gk110_fb_new, gk104_mmu_new, gk110_fifo_new, gk110b_gr_new.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
FILES_JSON = os.path.join(ROOT, "analysis", "files.json")
CG_JSON = os.path.join(ROOT, "analysis", "callgraph.json")
CG_MD = os.path.join(ROOT, "analysis", "callgraph.md")

B2_ROOTS = ("gk110_fb_new", "gk104_mmu_new", "gk110_fifo_new", "gk110b_gr_new")


def load_files():
    """Load analysis/files.json and return the list."""
    with open(FILES_JSON) as f:
        return json.load(f)


def scope_dirs(entries):
    """Return the sorted list of nvkm/... subdirectories for the four scope subsystems."""
    subsystems = {"fb", "mmu", "fifo", "gr"}
    dirs = set()
    for e in entries:
        path = e.get("path", "")
        subsystem = e.get("subsystem", "")
        if subsystem in subsystems:
            dirs.add(os.path.dirname(path))
    return sorted(dirs)


def read_source(rel):
    """Read a source file relative to the Nouveau tree root."""
    path = os.path.join(NV, rel)
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return None


def extract_definitions(source, rel):
    """Extract (name, line_number, kind) from a .c file.

    Kind is 'function' or 'table'.
    """
    lines = source.split("\n")
    defs = []
    keywords = {"struct", "typedef", "enum", "union", "return",
                "if", "else", "for", "while", "do", "switch",
                "case", "default", "sizeof", "typeof", "__", "no",
                "static_assert", "_Static_assert", "asm", "__asm",
                "goto", "break", "continue", "register", "volatile",
                "extern", "auto", "signed", "unsigned", "short",
                "long", "const", "inline", "static", "void"}

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- Table definition ---
        # static const struct foo bar = {  or  bar = {  (simple form)
        m = re.match(
            r"^\s*(?:static\s+)?(?:const\s+)?"
            r"(struct\s+\w+\s+)"
            r"(\w+)(?:\[[^\]]*\])?\s*=\s*\{", line
        )
        if not m:
            # Simple form: just name[] = { or name = { at start of line
            m = re.match(r"^\s*(\w+)(?:\[[^\]]*\])?\s*=\s*\{", line)
        if m:
            # Struct-based: group(1) is the type, group(2) is the name
            # Simple form: group(1) is the name
            name = m.group(2) if m.lastindex >= 2 else m.group(1)
            if name and name[0].islower() and name not in keywords:
                defs.append((name, i + 1, "table"))
                i += 1
                continue

        # --- Function definition ---
        # Can be: name(args) { or type name(args) { or static/const/type name(args) {
        # The { may be on the next line
        # Must be at file scope (no leading whitespace/tabs) to avoid matching
        # function calls inside other functions.
        m = re.match(
            r"^(?:static\s+|const\s+|inline\s+)*"
            r"(?:[\w*]+\s+)*"
            r"(\w+)\s*\(", line
        )
        if m:
            name = m.group(1)
            if name not in keywords and name[0].islower():
                # Check: is this a struct/enum/typedef/union declaration?
                # Look backwards for type keywords
                before = line[:m.start()]
                if re.search(r'\b(struct|enum|typedef|union)\s*$', before):
                    i += 1
                    continue
                # Verify the line (or next 2 lines) has a {
                brace_found = False
                for j in range(i, min(i + 3, len(lines))):
                    if "{" in lines[j]:
                        brace_found = True
                        break
                if brace_found:
                    defs.append((name, i + 1, "function"))
                    i += 1
                    continue

        i += 1
    return defs


def extract_body(lines, start_line, kind):
    """Extract the body of a function or table.

    start_line is 1-based line number of the definition.
    For functions: body is from the opening { to the matching }.
    For tables: body is from the = { line to matching }.
    """
    start = start_line - 1  # 0-based
    brace_depth = 0
    found_open = False

    for i in range(start, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                brace_depth += 1
                found_open = True
            elif ch == "}":
                brace_depth -= 1
        if found_open and brace_depth == 0:
            return "\n".join(lines[start:i + 1])

    return "\n".join(lines[start:])


def find_edges_in_body(body, node_names):
    """Find edges within a body text.

    Optimized: extract words from body, intersect with node_names set (O(1)).
    Patterns: function calls, address-of, struct field names, struct field
    values, and function call arguments.
    """
    name_set = set(node_names)
    edges = set()

    for line in body.split("\n"):
        # Remove comments and preprocessor directives
        line = re.sub(r"//.*$", "", line)
        line = re.sub(r"/\*.*?\*/", "", line)
        line = re.sub(r"#.*$", "", line)

        # Pattern 1: function call -- name(  or name (
        for m in re.finditer(r'\b(\w+)\s*\(', line):
            name = m.group(1)
            if name in name_set:
                edges.add(name)

        # Pattern 2: address-of -- &name
        for m in re.finditer(r'\&(\w+)\b', line):
            name = m.group(1)
            if name in name_set:
                edges.add(name)

        # Pattern 3: struct field -- .name =  (extracts field name)
        for m in re.finditer(r'\.(\w+)\s*=', line):
            name = m.group(1)
            if name in name_set:
                edges.add(name)

        # Pattern 4: struct field value -- .name = value  (extracts value)
        for m in re.finditer(r'\.\w+\s*=\s*(?:&|)(\w+)\b', line):
            name = m.group(1)
            if name in name_set:
                edges.add(name)

        # Pattern 5: function call arguments -- inside ( ... )
        for m in re.finditer(r'\(\s*([^)]*)\s*\)', line):
            args = m.group(1)
            for arg in args.split(','):
                arg = arg.strip()
                # Handle pointer dereference: *name
                arg = re.sub(r'^\s*\*\s*', '', arg)
                m2 = re.match(r'(\w+)', arg)
                if m2:
                    name = m2.group(1)
                    if name in name_set:
                        edges.add(name)

    return edges


def build_graph():
    """Build the call graph from files.json scope."""
    entries = load_files()
    scope_dirs_list = scope_dirs(entries)
    inventory = {e["path"] for e in entries}

    # Read all source files in scope and extract definitions
    all_defs = {}  # name -> (file, line, kind)
    node_names = set()

    for rel in scope_dirs_list:
        src_dir = os.path.join(NV, rel)
        if not os.path.isdir(src_dir):
            continue
        for fname in sorted(os.listdir(src_dir)):
            if not fname.endswith(".c"):
                continue
            # Only files of the B1 inventory (docs/tasks/B2.md). Other files
            # of the directory belong to chips that are not on this path.
            if os.path.join(rel, fname) not in inventory:
                continue
            source = read_source(os.path.join(rel, fname))
            if source is None:
                continue
            defs = extract_definitions(source, os.path.join(rel, fname))
            for name, line, kind in defs:
                if name not in all_defs:
                    all_defs[name] = (os.path.join(rel, fname), line, kind)
                    node_names.add(name)

    # Build edges: for each function/table, find references to other node names
    edges = set()
    node_bodies = {}

    for name, (f, l, kind) in sorted(all_defs.items()):
        source = read_source(f)
        if source is None:
            continue
        body = extract_body(source.split("\n"), l, kind)
        node_bodies[name] = body
        # Find references to other node names in this body (optimized)
        referenced = find_edges_in_body(body, node_names)
        for target in referenced:
            if target != name:
                edges.add((name, target))

    # Build nodes list
    all_nodes = []
    for name, (f, l, kind) in sorted(all_defs.items()):
        node = {"name": name, "file": f, "line": l}
        if kind:
            node["kind"] = kind
        all_nodes.append(node)
    all_names = {n["name"] for n in all_nodes}

    # Filter: only keep nodes reachable from roots via BFS
    out = {}
    for c, d in edges:
        out.setdefault(c, set()).add(d)
    seen, todo = set(), [r for r in B2_ROOTS if r in all_names]
    while todo:
        x = todo.pop()
        if x not in seen:
            seen.add(x)
            todo.extend(sorted(out.get(x, ())))
    reachable = seen & all_names  # only keep if the node exists in all_nodes

    # Filter nodes
    nodes = [n for n in all_nodes if n["name"] in reachable]

    # Filter edges: both caller and callee must be reachable
    edges = sorted((c, d) for c, d in edges if c in reachable and d in reachable)

    return {"nodes": nodes, "edges": edges}, all_defs, edges


def render(graph):
    """Return the text of callgraph.json and of callgraph.md."""
    nodes = graph["nodes"]
    edges = graph["edges"]
    json_text = json.dumps(graph, indent=2) + "\n"

    # Build adjacency for markdown
    out = {}  # caller -> set of callees
    for c, d in edges:
        out.setdefault(c, set()).add(d)

    # Group nodes by file
    by_file = {}
    for n in nodes:
        by_file.setdefault(n["file"], []).append(n)

    # Group by subsystem
    subsystems = {}
    for n in nodes:
        f = n["file"]
        m = re.search(r"nvkm/(\w+)/", f)
        if m:
            subsystems.setdefault(m.group(1), []).append(n)

    md_lines = []
    md_lines.append("# Call Graph\n")
    md_lines.append(f"Generated from {len(nodes)} nodes and {len(edges)} edges.\n")
    md_lines.append("## Nodes by subsystem\n")
    for sub in sorted(subsystems):
        md_lines.append(f"### {sub}\n")
        md_lines.append(f"- **{len(subsystems[sub])}** nodes\n")
        md_lines.append("| Function/Table | File | Line | Kind |\n")
        md_lines.append("|---|---|---|---|\n")
        for n in sorted(subsystems[sub], key=lambda x: (x["file"], x["line"])):
            md_lines.append(
                f"| `{n['name']}` | `{n['file']}` | {n['line']} | {n.get('kind', 'function')} |\n"
            )

    md_lines.append("\n## Paths from roots\n")
    for root in B2_ROOTS:
        md_lines.append(f"### {root}\n")
        if root not in out:
            md_lines.append(f"- Root `{root}` has no outgoing edges\n")
            continue
        # BFS to find paths
        visited = set()
        todo = [(root, [root])]
        while todo:
            current, path = todo.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for callee in sorted(out.get(current, set())):
                if callee not in visited:
                    new_path = path + [callee]
                    md_lines.append(
                        f"- {' → '.join(new_path)}\n"
                    )
                    if any(x not in visited for x in out.get(callee, set())):
                        todo.append((callee, new_path))

    md_lines.append("\n## Top-level callers\n")
    callees = {e[1] for e in edges}
    callers = {e[0] for e in edges}
    leaves = sorted(callees - callers)
    md_lines.append(f"- **{len(leaves)}** leaf nodes (no outgoing edges in scope):\n")
    for l in leaves[:30]:
        md_lines.append(f"  - `{l}`\n")
    if len(leaves) > 30:
        md_lines.append(f"  - … and {len(leaves) - 30} more\n")

    # Which nodes are in files named for another chip. The class of each
    # file comes from analysis/files.json (task B1).
    with open(FILES_JSON) as f:
        file_class = {e["path"]: e["class"] for e in json.load(f)}
    md_lines.append("\n## Code for other chips\n")
    md_lines.append(
        "A graph of names cannot tell which of these nodes the GK110B card "
        "runs. A node is in the graph when a reachable function or table "
        "uses its name. Shared tables name functions for several chips, and "
        "a branch on the chipset is not visible here. Nodes in `GK110-specific` "
        "and `GK104-inherited` files are on the card's own path. Nodes in "
        "`other-chip` files are reached by name only, until a trace or a "
        "reading of the branch shows that the card uses them (UNKNOWN).\n")
    md_lines.append("| Subsystem | Class of the file | Nodes |")
    md_lines.append("|---|---|---|")
    counts = {}
    for n in nodes:
        m = re.search(r"nvkm/\w+/(\w+)/", n["file"])
        key = (m.group(1) if m else "?", file_class.get(n["file"], "not in files.json"))
        counts[key] = counts.get(key, 0) + 1
    for (sub, cls), c in sorted(counts.items()):
        md_lines.append(f"| {sub} | {cls} | {c} |")

    return json_text, "\n".join(md_lines)


def write_outputs(graph):
    """Write callgraph.json and callgraph.md."""
    json_text, md_text = render(graph)
    with open(CG_JSON, "w") as f:
        f.write(json_text)
    with open(CG_MD, "w") as f:
        f.write(md_text)


def main():
    check = "--check" in sys.argv
    graph, all_defs, edges = build_graph()

    if check:
        # Compare text with text. A loaded JSON file has lists where the
        # graph in memory has tuples, so a comparison of objects always fails.
        json_text, md_text = render(graph)
        for path, text in ((CG_JSON, json_text), (CG_MD, md_text)):
            if not os.path.exists(path) or open(path).read() != text:
                print(
                    f"FAIL: {os.path.relpath(path, ROOT)} is not what the tool "
                    "generates. Run without --check to update it.",
                    file=sys.stderr
                )
                sys.exit(1)
    else:
        write_outputs(graph)
        print(f"Call graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
        print(f"  → {CG_JSON}")
        print(f"  → {CG_MD}")


if __name__ == "__main__":
    main()
