#!/usr/bin/env python3
"""Map every function in notification_shared_file.c with its line range and which
functions it calls. Output a function inventory used to split the file."""
import re
from pathlib import Path

SRC = Path("/home/hyeonuk/tizen/appfw/notification/src/notification/src/notification_shared_file.c")
text = SRC.read_text()
lines = text.splitlines()

# function definition regex: a line that starts with type and ends with "(" or "{ /args/ }"
# we recognize "<type> <name>(" at column 0 followed by a function body until matching "}".
fn_def_re = re.compile(
    r"^(static\s+)?([a-zA-Z_][a-zA-Z0-9_\s\*]*?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
)

fns = []
i = 0
while i < len(lines):
    line = lines[i]
    m = fn_def_re.match(line)
    if not m and not line.startswith("static"):
        # also consider non-static raw function defs that start at col 0
        # try simple "type name(" pattern at column 0
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_\s\*]*?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line)
    if m:
        # check that this is a *definition*: the args list ends with ")" then "{" eventually
        # find matching close paren on this or subsequent lines, then look for { after
        depth = 0
        end_paren_line = None
        for j in range(i, min(i + 30, len(lines))):
            l = lines[j]
            for ch in l:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end_paren_line = j
                        break
            if end_paren_line is not None:
                break
        if end_paren_line is None:
            i += 1
            continue
        # Look at the rest of the line / next few lines for '{' (definition) or ';' (declaration)
        post = "".join(lines[end_paren_line:end_paren_line + 4])
        post = post.split(")", 1)[1] if ")" in post else post
        if "{" not in post:
            i += 1
            continue
        # Walk forward to find the matching closing brace
        brace_depth = 0
        started = False
        end_line = None
        for j in range(end_paren_line, len(lines)):
            l = lines[j]
            for ch in l:
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
            i += 1
            continue
        fn_name = m.group(3) if m.lastindex == 3 else m.group(2)
        is_static = bool(m.group(1)) if m.lastindex == 3 else False
        fns.append({
            "name": fn_name,
            "static": is_static,
            "start": i,
            "end": end_line,
        })
        i = end_line + 1
        continue
    i += 1

# Compute call graph: function -> set(calls to other functions in this file)
names = {f["name"] for f in fns}
call_re = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
for f in fns:
    body = "\n".join(lines[f["start"]:f["end"]+1])
    # strip strings/comments roughly
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r'"[^"\n]*"', '""', body)
    calls = set()
    for cm in call_re.finditer(body):
        name = cm.group(1)
        if name in names and name != f["name"]:
            calls.add(name)
    f["calls"] = calls

# Classify
PUBLIC_DPM = {
    "notification_set_private_sharing",
    "notification_remove_private_sharing",
    "notification_add_private_sharing_target_id",
    "notification_remove_private_sharing_target_id",
    "notification_calibrate_private_sharing",
    "notification_validate_private_sharing",
}
PUBLIC_CLIENT = {
    "notification_copy_private_file",
    "notification_check_file_path_is_private",
}

# Iteratively compute transitive closure of helpers needed by DPM-only and client respectively
def closure(seed):
    """Return all helper static functions reachable from seed via calls."""
    needed = set(seed)
    changed = True
    while changed:
        changed = False
        for f in fns:
            if f["name"] in needed:
                for callee in f["calls"]:
                    callee_fn = next((g for g in fns if g["name"] == callee), None)
                    if callee_fn and callee not in needed:
                        # only include statics/helpers in closure (public funcs already classified)
                        if callee not in PUBLIC_DPM and callee not in PUBLIC_CLIENT:
                            needed.add(callee)
                            changed = True
    return needed

dpm_reach = closure(PUBLIC_DPM)
client_reach = closure(PUBLIC_CLIENT)

both = (dpm_reach & client_reach) - PUBLIC_DPM - PUBLIC_CLIENT
only_dpm = dpm_reach - client_reach - PUBLIC_DPM - PUBLIC_CLIENT
only_client = client_reach - dpm_reach - PUBLIC_DPM - PUBLIC_CLIENT
unreachable = {f["name"] for f in fns} - dpm_reach - client_reach

print("== DPM-only helpers ==")
for n in sorted(only_dpm):
    print(" ", n)
print("\n== Client-only helpers ==")
for n in sorted(only_client):
    print(" ", n)
print("\n== Shared helpers (used by both — must duplicate or keep in libnotification) ==")
for n in sorted(both):
    print(" ", n)
print("\n== Unreachable (orphan) functions ==")
for n in sorted(unreachable):
    print(" ", n)

# Save inventory
import json
inv = {
    "functions": [{"name": f["name"], "static": f["static"], "start": f["start"], "end": f["end"], "calls": sorted(list(f["calls"]))} for f in fns],
    "dpm_only_helpers": sorted(only_dpm),
    "client_only_helpers": sorted(only_client),
    "shared_helpers": sorted(both),
    "unreachable": sorted(unreachable),
}
Path("/home/hyeonuk/tizen/appfw/analysis/shared_file_inventory.json").write_text(json.dumps(inv, indent=2))
print(f"\nTotal functions parsed: {len(fns)}")
