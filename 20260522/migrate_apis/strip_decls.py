#!/usr/bin/env python3
"""Remove the C declarations for a list of functions from the named headers,
plus the contiguous /** ... */ doxygen block immediately preceding the
declaration if it's solely about that function.
"""
import re
from pathlib import Path

JOBS = {
    "notification/src/notification/include/notification_internal.h": [
        "notification_channel_free",
        "notification_channel_get_block",
        "notification_channel_get_blockable",
        "notification_channel_get_name",
        "notification_get_channel_name",
        "notification_get_event_flag",
        "notification_get_extension_data",
        "notification_get_pairing_type",
        "notification_get_uid",
        "notification_set_uid",
    ],
    "notification/src/notification/include/notification_setting_internal.h": [
        "notification_setting_delete_package_for_uid",
        "notification_setting_get_allow_to_notify",
        "notification_setting_get_app_disabled",
        "notification_setting_get_do_not_disturb_except",
        "notification_setting_get_pop_up_notification",
        "notification_setting_insert_package_for_uid",
        "notification_system_setting_dnd_schedule_get_day",
        "notification_system_setting_dnd_schedule_get_enabled",
        "notification_system_setting_dnd_schedule_get_end_time",
        "notification_system_setting_dnd_schedule_get_start_time",
        "notification_system_setting_free_system_setting",
        "notification_system_setting_get_do_not_disturb",
    ],
    "notification/src/notification/include/notification_db.h": [
        "notification_db_init",
        "notification_upgrade_db",
    ],
}

ROOT = Path("/home/hyeonuk/tizen/appfw")


def remove_decl(text, fn_name):
    """Find a `<type> fn_name(args);` line, remove that line and any
    contiguous preceding doxygen `/** ... */` block."""
    lines = text.splitlines(keepends=True)
    # Find declaration line: starts with type tokens, contains fn_name(, ends with `;`
    decl_pat = re.compile(rf"^[^/].*\b{re.escape(fn_name)}\s*\(.*\)\s*;\s*$")
    # Some declarations span multiple lines. Use a multi-line scan.
    i = 0
    while i < len(lines):
        if fn_name + "(" in lines[i] and not lines[i].strip().startswith("*") and not lines[i].strip().startswith("//"):
            # check if this is a declaration (ends with ; on same or subsequent line, no '{' before ';')
            j = i
            decl_text = ""
            while j < len(lines):
                decl_text += lines[j]
                if "{" in lines[j]:
                    decl_text = None
                    break
                if ";" in lines[j]:
                    break
                j += 1
            if decl_text is None:
                # this is a definition, not a decl - skip
                i += 1
                continue
            # found decl from line i..j inclusive
            # Look upward for doxygen block to remove
            start = i
            k = i - 1
            # skip a single blank line
            while k >= 0 and lines[k].strip() == "":
                k -= 1
            if k >= 0 and lines[k].strip().endswith("*/"):
                # walk back to /**
                while k >= 0:
                    if lines[k].strip().startswith("/**") or lines[k].strip().startswith("/*"):
                        start = k
                        break
                    k -= 1
            del lines[start:j + 1]
            # also delete one trailing blank line
            if start < len(lines) and lines[start].strip() == "":
                del lines[start]
            return "".join(lines), True
        i += 1
    return text, False


for rel, fns in JOBS.items():
    path = ROOT / rel
    text = path.read_text()
    changed = []
    for fn in fns:
        text, ok = remove_decl(text, fn)
        if ok:
            changed.append(fn)
    path.write_text(text)
    print(f"{rel}: removed {len(changed)} / {len(fns)}")
    if len(changed) < len(fns):
        missing = set(fns) - set(changed)
        print(f"  MISSING: {missing}")
