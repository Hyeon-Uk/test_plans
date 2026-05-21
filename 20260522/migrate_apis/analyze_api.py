#!/usr/bin/env python3
"""
For each function declared in notification's public devel headers,
find which packages (across the 65 cloned repos) reference it.

Output:
  analysis/api_per_consumer.tsv  -> (function, header, consumer_package, count)
  analysis/dpm_exclusive.tsv     -> functions consumed ONLY by data-provider-master
  analysis/by_function.json
"""
import json
import os
import re
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/hyeonuk/tizen/appfw")
NOTIF_INC = ROOT / "notification/src/notification/include"
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(exist_ok=True)

PUBLIC_HEADERS = [
    "notification.h",
    "notification_db.h",
    "notification_internal.h",
    "notification_error.h",
    "notification_type.h",
    "notification_list.h",
    "notification_ongoing.h",
    "notification_ongoing_flag.h",
    "notification_text_domain.h",
    "notification_status.h",
    "notification_status_internal.h",
    "notification_setting.h",
    "notification_setting_internal.h",
    "notification_ipc.h",
    "notification_noti.h",
    "notification_setting_service.h",
    "notification_viewer.h",
    "notification_shared_file.h",
    "notification_type_internal.h",
]

# Regex: capture function name in a declaration like:
#   int notification_xxx(args);
#   void notification_xxx (args);
#   notification_h notification_create(args);
FN_RE = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_\s\*]*?\b(notification[a-zA-Z0-9_]+|noti_[a-zA-Z0-9_]+)\s*\([^;]*?\)\s*;",
    re.MULTILINE,
)

# Extract functions per header
header_funcs = {}        # header -> set(funcs)
func_header = {}         # func -> header (first occurrence)
all_funcs = set()

for h in PUBLIC_HEADERS:
    hf = NOTIF_INC / h
    if not hf.exists():
        continue
    text = hf.read_text()
    # Strip block comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Strip line comments
    text = re.sub(r"//[^\n]*", "", text)
    funcs = set()
    for m in FN_RE.finditer(text):
        fn = m.group(1)
        # Filter obvious non-functions / macros
        if fn.startswith("notification_") or fn.startswith("noti_"):
            funcs.add(fn)
    header_funcs[h] = funcs
    for f in funcs:
        if f not in func_header:
            func_header[f] = h
        all_funcs.add(f)

print(f"Headers: {len(header_funcs)}, unique functions: {len(all_funcs)}")

# Build list of all packages (directories under ROOT)
pkgs = sorted([
    p.name for p in ROOT.iterdir()
    if p.is_dir() and (p / ".git").is_dir()
])
print(f"Packages: {len(pkgs)}")

# Build single grep across all packages except notification itself
# Use ripgrep if available
def have(cmd):
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
USE_RG = have("rg")
print("Using ripgrep" if USE_RG else "Using grep -F per package")

# Search each function symbol across all packages (excluding notification's own source)
# To make this efficient, do one big rg with -f patterns file.
patterns_file = ANALYSIS / "patterns.txt"
patterns_file.write_text("\n".join(rf"\b{re.escape(f)}\b" for f in sorted(all_funcs)))

# Run rg with regex patterns across the corpus, excluding the notification repo
# Output: file:line:matched_function
results = defaultdict(lambda: defaultdict(int))  # func -> pkg -> count
if USE_RG:
    # rg -o emits only matched portion; with -H -n we get file
    # Use a single regex pattern file
    cmd = [
        "rg", "--no-heading", "-o", "--with-filename", "-n",
        "-tcpp", "-tc", "-tcmake",
        "-f", str(patterns_file),
        "-g", "!notification/**",
        ".",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=600)
        out = proc.stdout
    except subprocess.TimeoutExpired:
        print("rg timed out")
        out = ""
    for line in out.splitlines():
        # format: ./<pkg>/path:line:match
        if not line.startswith("./"):
            continue
        rest = line[2:]
        try:
            path_part, _, match = rest.split(":", 2)
        except ValueError:
            continue
        pkg = path_part.split("/", 1)[0]
        # match is the matched substring (the function name)
        fn = match.strip()
        if fn in all_funcs:
            results[fn][pkg] += 1
else:
    # Use grep -F (fixed strings) per package -- much faster than per-symbol search
    sym_file = ANALYSIS / "syms.txt"
    sym_file.write_text("\n".join(sorted(all_funcs)))
    for pkg in pkgs:
        if pkg == "notification":
            continue
        pkg_dir = ROOT / pkg
        # search only source-like files
        cmd = [
            "grep", "-rwoF", "-f", str(sym_file),
            "--include=*.c", "--include=*.cc", "--include=*.cpp",
            "--include=*.h", "--include=*.hh", "--include=*.hpp",
            "--include=*.cxx",
            str(pkg_dir),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT: {pkg}")
            continue
        for line in proc.stdout.splitlines():
            # format: path:match
            if ":" not in line:
                continue
            _, _, match = line.partition(":")
            fn = match.strip()
            if fn in all_funcs:
                results[fn][pkg] += 1
        print(f"  {pkg}: done")

# For each function, list consumers (excluding "notification" package itself)
api_rows = []
dpm_exclusive = []
no_consumer = []
for fn in sorted(all_funcs):
    consumers = {pkg: cnt for pkg, cnt in results.get(fn, {}).items() if pkg != "notification"}
    header = func_header[fn]
    for pkg, cnt in sorted(consumers.items()):
        api_rows.append((fn, header, pkg, cnt))
    if not consumers:
        no_consumer.append((fn, header))
    elif set(consumers.keys()) == {"data-provider-master"}:
        dpm_exclusive.append((fn, header, consumers["data-provider-master"]))

# Write outputs
with open(ANALYSIS / "api_per_consumer.tsv", "w") as f:
    f.write("function\theader\tconsumer\tcount\n")
    for r in api_rows:
        f.write("\t".join(map(str, r)) + "\n")

with open(ANALYSIS / "dpm_exclusive.tsv", "w") as f:
    f.write("function\theader\tdpm_count\n")
    for r in dpm_exclusive:
        f.write("\t".join(map(str, r)) + "\n")

with open(ANALYSIS / "no_consumer.tsv", "w") as f:
    f.write("function\theader\n")
    for r in no_consumer:
        f.write("\t".join(map(str, r)) + "\n")

# Per-header summary
hdr_summary = defaultdict(lambda: {"total": 0, "dpm_excl": 0, "no_consumer": 0, "shared": 0})
for fn in all_funcs:
    h = func_header[fn]
    hdr_summary[h]["total"] += 1
    consumers = {pkg: cnt for pkg, cnt in results.get(fn, {}).items() if pkg != "notification"}
    if not consumers:
        hdr_summary[h]["no_consumer"] += 1
    elif set(consumers.keys()) == {"data-provider-master"}:
        hdr_summary[h]["dpm_excl"] += 1
    else:
        hdr_summary[h]["shared"] += 1

with open(ANALYSIS / "header_summary.tsv", "w") as f:
    f.write("header\ttotal\tdpm_excl\tshared\tno_consumer\n")
    for h, s in sorted(hdr_summary.items()):
        f.write(f"{h}\t{s['total']}\t{s['dpm_excl']}\t{s['shared']}\t{s['no_consumer']}\n")

# Persist full per-function consumer map for downstream tools
by_func = {fn: {pkg: cnt for pkg, cnt in results.get(fn, {}).items() if pkg != "notification"} for fn in all_funcs}
(ANALYSIS / "by_function.json").write_text(json.dumps({
    "header_funcs": {h: sorted(list(funcs)) for h, funcs in header_funcs.items()},
    "func_header": func_header,
    "consumers": by_func,
}, indent=2))

print("--- per-header summary ---")
for h, s in sorted(hdr_summary.items()):
    print(f"{h:42s} total={s['total']:4d}  DPM-only={s['dpm_excl']:4d}  shared={s['shared']:4d}  unused={s['no_consumer']:4d}")
print(f"--- DPM-exclusive functions: {len(dpm_exclusive)} ---")
for fn, h, cnt in dpm_exclusive[:50]:
    print(f"  {h:42s}  {fn}  ({cnt} refs)")
