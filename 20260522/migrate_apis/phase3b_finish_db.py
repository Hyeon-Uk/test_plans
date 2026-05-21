#!/usr/bin/env python3
"""Move the orphaned static helpers in notification_db.c into dpm_db.c
so the moved functions resolve cleanly."""
from pathlib import Path
from extract_function import extract_blocks

ROOT = Path("/home/hyeonuk/tizen/appfw")
SRC = ROOT / "notification/src/notification/src/notification_db.c"
DPM_DB = ROOT / "data-provider-master/src/dpm_db.c"

statics = [
    "__check_integrity_cb",
    "__recover_corrupted_db",
    "__check_db_version",
    "__upgrade_noti_table",
    "__upgrade_noti_template_table",
]
extracted, remaining = extract_blocks(SRC, statics)
SRC.write_text(remaining)

# Read existing dpm_db.c
dpm_text = DPM_DB.read_text()
# Find a place to inject (right after the #ifndef EXPORT_API ... #endif block or after the includes)
inject_marker = "#endif\n"
idx = dpm_text.find("#endif", dpm_text.find("EXPORT_API"))
# Just split at the include/EXPORT block end and inject before the body
parts = dpm_text.split("#endif\n", 1)
head = "#endif\n".join([dpm_text.split("\n", 0)[0], ""])
# simpler: append statics right after the EXPORT_API ifndef block
needle = "#define EXPORT_API __attribute__ ((visibility(\"default\")))\n#endif\n"
if needle in dpm_text:
    pre, post = dpm_text.split(needle, 1)
    blocks = "\n".join(extracted[fn] for fn in statics)
    new_dpm = pre + needle + "\n" + blocks + "\n" + post
else:
    blocks = "\n".join(extracted[fn] for fn in statics)
    new_dpm = dpm_text + "\n" + blocks
DPM_DB.write_text(new_dpm)
print(f"Moved {len(statics)} statics into dpm_db.c")
