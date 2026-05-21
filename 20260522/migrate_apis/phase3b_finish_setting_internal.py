#!/usr/bin/env python3
"""Final cleanup pass:
  - Move orphan statics from notification_setting.c (after Phase 3b extraction)
    into dpm_setting.c.
  - Inject a private static copy of `_create_bundle_from_bundle_raw`
    into dpm_internal.c (it remains in notification_ipc.c as a different
    static — symbol is file-local so two copies coexist).
"""
from pathlib import Path
from extract_function import extract_blocks

ROOT = Path("/home/hyeonuk/tizen/appfw")
NS = ROOT / "notification/src/notification/src/notification_setting.c"
NI = ROOT / "notification/src/notification/src/notification_internal.c"
DS = ROOT / "data-provider-master/src/dpm_setting.c"
DI = ROOT / "data-provider-master/src/dpm_internal.c"

# === notification_setting.c orphan statics ===
statics = ["_install_and_update_package", "_delete_package_from_setting_db"]
extracted, remaining = extract_blocks(NS, statics)
NS.write_text(remaining)
needle = "#define EXPORT_API __attribute__ ((visibility(\"default\")))\n#endif\n"
ds_text = DS.read_text()
if needle in ds_text:
    pre, post = ds_text.split(needle, 1)
    blocks = "\n".join(extracted[fn] for fn in statics)
    DS.write_text(pre + needle + "\n" + blocks + "\n" + post)
print(f"moved {statics} into dpm_setting.c")

# === _create_bundle_from_bundle_raw : take a private copy ===
ni_text = NI.read_text()
# Find the static definition in notification_internal.c
import re
m = re.search(r"static bundle \*_create_bundle_from_bundle_raw\(bundle_raw \*string\)\s*\{",
              ni_text)
if not m:
    raise SystemExit("definition not found")
start = m.start()
# Walk braces to find end
depth = 0
started = False
end = None
for j in range(start, len(ni_text)):
    ch = ni_text[j]
    if ch == "{":
        depth += 1
        started = True
    elif ch == "}":
        depth -= 1
        if started and depth == 0:
            end = j + 1
            break
block = ni_text[start:end] + "\n"
di_text = DI.read_text()
if needle in di_text:
    pre, post = di_text.split(needle, 1)
    DI.write_text(pre + needle + "\n" + block + "\n" + post)
    print("injected _create_bundle_from_bundle_raw into dpm_internal.c")
else:
    print("could not find injection point in dpm_internal.c")
