#!/usr/bin/env python3
"""Copy (not move) the still-needed helper statics from notification_setting.c
into dpm_setting.c so dpm_setting compiles standalone."""
import re
from pathlib import Path

ROOT = Path("/home/hyeonuk/tizen/appfw")
NS = ROOT / "notification/src/notification/src/notification_setting.c"
DS = ROOT / "data-provider-master/src/dpm_setting.c"

ns_text = NS.read_text()

def extract_static_block(text, sig_pattern):
    m = re.search(sig_pattern, text)
    if not m:
        return None
    start = m.start()
    depth = 0
    started = False
    for j in range(start, len(text)):
        ch = text[j]
        if ch == "{":
            depth += 1
            started = True
        elif ch == "}":
            depth -= 1
            if started and depth == 0:
                return text[start:j + 1]
    return None

blk_is_package = extract_static_block(ns_text, r"static bool _is_package_in_setting_table\([^)]*\)\s*\n*\{?")
blk_foreach = extract_static_block(ns_text, r"static int _foreach_app_info_callback\([^)]*\)\s*\n*\{?")
if not blk_is_package or not blk_foreach:
    raise SystemExit("could not extract one of the helpers")

# Build a tiny header to be inserted into dpm_setting.c before the moved functions
ds_text = DS.read_text()
needle = "#define EXPORT_API __attribute__ ((visibility(\"default\")))\n#endif\n"
pre, post = ds_text.split(needle, 1)
DS.write_text(pre + needle + "\n" + blk_is_package + "\n\n" + blk_foreach + "\n\n" + post)
print("duplicated _is_package_in_setting_table + _foreach_app_info_callback into dpm_setting.c")
