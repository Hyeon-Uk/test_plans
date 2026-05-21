#!/usr/bin/env python3
"""
Surgical helper: locate a function definition by name in a C source file,
return its (start_line, end_line) inclusive 1-based, including any
immediately preceding /* LCOV_EXCL_START */ comment line and any
immediately following /* LCOV_EXCL_STOP */ comment line.

Usage:
  from extract_function import find_function_range, remove_range, get_block
"""
import re
from pathlib import Path

def find_function_range(text_lines, fn_name):
    """Return (start, end) inclusive 1-based for the function body, or None."""
    # Find the line that begins the definition: starts with type then has `<name>(`
    # ignoring forward declarations (which end with ;)
    name_pat = re.compile(rf"\b{re.escape(fn_name)}\s*\(")
    type_prefix_pat = re.compile(r"^(EXPORT_API\s+|static\s+|inline\s+|extern\s+)*[a-zA-Z_][a-zA-Z0-9_\s\*]*\s+" + re.escape(fn_name) + r"\s*\(")
    for i, line in enumerate(text_lines):
        if not name_pat.search(line):
            continue
        if not type_prefix_pat.match(line):
            continue
        # Found candidate def. Confirm by scanning forward: find matching ')' then '{'
        depth = 0
        end_paren = None
        for j in range(i, min(i + 30, len(text_lines))):
            for ch in text_lines[j]:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end_paren = j
                        break
            if end_paren is not None:
                break
        if end_paren is None:
            continue
        # After ')': look for '{' before ';' on same/next lines
        post = "\n".join(text_lines[end_paren:end_paren + 4])
        # Remove the matched ')' and everything before it
        post = post.split(")", 1)[1] if ")" in post else post
        if "{" not in post:
            continue
        # Walk to closing brace
        brace_depth = 0
        started = False
        end_line = None
        for j in range(end_paren, len(text_lines)):
            for ch in text_lines[j]:
                if ch == "{":
                    brace_depth += 1
                    started = True
                elif ch == "}":
                    brace_depth -= 1
                    if started and brace_depth == 0:
                        end_line = j
                        break
            if end_line is not None:
                break
        if end_line is None:
            continue
        s, e = i, end_line
        # Expand to include LCOV markers
        if s > 0 and "LCOV_EXCL_START" in text_lines[s - 1]:
            s -= 1
        # Look at next non-empty line for LCOV_EXCL_STOP
        k = e + 1
        while k < len(text_lines) and text_lines[k].strip() == "":
            k += 1
        if k < len(text_lines) and "LCOV_EXCL_STOP" in text_lines[k]:
            e = k
        # Include a trailing blank line for cleanliness
        if e + 1 < len(text_lines) and text_lines[e + 1].strip() == "":
            e += 1
        return s + 1, e + 1  # 1-based inclusive
    return None


def extract_blocks(src_path, fn_names):
    """Extract the source code blocks for each function, return
    {fn: block_str, ...} and the remaining text (with blocks removed).
    Functions are removed in reverse-line order to keep line numbers stable."""
    text = Path(src_path).read_text()
    lines = text.splitlines(keepends=True)
    ranges = []
    extracted = {}
    for fn in fn_names:
        r = find_function_range(lines, fn)
        if r is None:
            extracted[fn] = None
            continue
        s, e = r
        ranges.append((s, e, fn))
    # remove ranges from highest start to lowest
    ranges_sorted = sorted(ranges, key=lambda x: x[0], reverse=True)
    new_lines = list(lines)
    for s, e, fn in ranges_sorted:
        extracted[fn] = "".join(lines[s - 1:e])
        del new_lines[s - 1:e]
    return extracted, "".join(new_lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: extract_function.py <src> <fn1> [<fn2> ...]")
        sys.exit(1)
    src = sys.argv[1]
    fns = sys.argv[2:]
    extracted, remaining = extract_blocks(src, fns)
    for fn, block in extracted.items():
        print(f"=== {fn} ===")
        if block is None:
            print("  NOT FOUND")
        else:
            print(f"  {len(block.splitlines())} lines")
