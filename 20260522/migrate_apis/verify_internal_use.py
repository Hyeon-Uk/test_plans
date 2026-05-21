#!/usr/bin/env python3
"""
For each candidate header to migrate, find:
  - which files inside notification/src/notification/src/ implement its functions
  - which OTHER files inside notification/src/notification/src/ call those functions
A header is "safe to move" if no other notification source file (outside the impl file)
calls its functions.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/hyeonuk/tizen/appfw")
NOTIF_SRC = ROOT / "notification/src/notification/src"
NOTIF_INC = ROOT / "notification/src/notification/include"

data = json.loads((ROOT / "analysis/by_function.json").read_text())
header_funcs = data["header_funcs"]
func_header = data["func_header"]
consumers = data["consumers"]

# Find dpm-only functions per header
dpm_only_by_header = defaultdict(list)
for fn, cons in consumers.items():
    if cons and set(cons.keys()) == {"data-provider-master"}:
        dpm_only_by_header[func_header[fn]].append(fn)

# Build map: source file -> contents
src_files = sorted(NOTIF_SRC.glob("*.c")) + sorted(NOTIF_SRC.glob("*.cc")) + sorted(NOTIF_SRC.glob("*.cpp"))
src_text = {f.name: f.read_text() for f in src_files}

# For each DPM-only function:
# - which file defines it? (heuristic: line matching /^\w+.*\bFN\s*\(/ at column 0 followed by '{')
# - which other files call it?
def defining_file(fn):
    # heuristic: search across notification source for "type FN(args) {" or "type FN(args)\n{"
    # we use a simpler signal: any source file containing both "FN(" AND "{" on consecutive lines
    candidates = []
    for fname, text in src_text.items():
        # Look for definition: starts at line beginning with possible storage class, type, then FN(
        pat = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\s\*]*?\b" + re.escape(fn) + r"\s*\(", re.MULTILINE)
        if pat.search(text):
            # additionally check there is { after the parenthesized args (definition not just declaration)
            # quick approximation
            idx = text.find(fn + "(")
            if idx >= 0:
                tail = text[idx:idx+1000]
                if "{" in tail.split(")",1)[1][:300] if ")" in tail else "":
                    candidates.append(fname)
                elif tail.split(";",1)[0].count(")") and "{" in tail[tail.find(")"):tail.find(")")+200]:
                    candidates.append(fname)
                else:
                    # fallback: any source file that contains the literal "fn(" on a definition-like line
                    if re.search(r"^[a-zA-Z_][a-zA-Z0-9_\s\*]*\b" + re.escape(fn) + r"\s*\(.*\)\s*\{?\s*$", text, re.MULTILINE):
                        candidates.append(fname)
    return candidates

def callers_of(fn):
    # Files that contain a call (not just a declaration) to fn
    callers = set()
    for fname, text in src_text.items():
        # strip block comments
        clean = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        clean = re.sub(r"//[^\n]*", "", clean)
        # look for fn( appearing as a call (preceded by space, '=', '(', '!', etc.)
        if re.search(r"[^a-zA-Z0-9_]" + re.escape(fn) + r"\s*\(", clean):
            callers.add(fname)
    return callers

# Targeted: focus on candidate headers
TARGET_HEADERS = [
    "notification_noti.h",
    "notification_setting_service.h",
    "notification_viewer.h",
    "notification_shared_file.h",
    "notification_db.h",
    "notification_list.h",
]

results = {}
for h in TARGET_HEADERS:
    fns = dpm_only_by_header.get(h, [])
    if not fns:
        # use all funcs in header
        fns = header_funcs.get(h, [])
    info = {}
    for fn in fns:
        impls = defining_file(fn)
        callrs = callers_of(fn)
        info[fn] = {
            "impl_files": impls,
            "caller_files_in_notification": sorted(callrs),
        }
    results[h] = info

(ROOT / "analysis/internal_use.json").write_text(json.dumps(results, indent=2))

# Summarize: for each candidate header, list which notification src files implement its functions,
# and whether any "other" notification src file calls them.
def basename_set(s):
    return set(s)

print("=== Files that implement DPM-only functions, and other callers within notification ===\n")
for h, info in results.items():
    impl_files_all = set()
    callers_all = set()
    for fn, d in info.items():
        impl_files_all.update(d["impl_files"])
        callers_all.update(d["caller_files_in_notification"])
    other_callers = callers_all - impl_files_all
    print(f"\n## {h}  ({len(info)} DPM-only funcs)")
    print(f"  Implementing files: {sorted(impl_files_all)}")
    print(f"  Other notification callers (must rewire if moved): {sorted(other_callers)}")
    if other_callers:
        # show which functions are called from each
        for caller in sorted(other_callers):
            called = [fn for fn, d in info.items() if caller in d["caller_files_in_notification"] and caller not in d["impl_files"]]
            print(f"    {caller} -> calls: {called}")
