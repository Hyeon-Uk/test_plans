#!/usr/bin/env python3
"""Phase 3b: extract DPM-only functions from notification_internal.c,
notification_setting.c, notification_db.c. Move them to new dpm_*.c files
in data-provider-master.
"""
from pathlib import Path
from extract_function import extract_blocks

ROOT = Path("/home/hyeonuk/tizen/appfw")
NOTIF_SRC = ROOT / "notification/src/notification/src"
DPM_SRC = ROOT / "data-provider-master/src"
DPM_INC = ROOT / "data-provider-master/include"

# Map: source file -> (list of DPM-only function names, new DPM file basename, includes-block)
JOBS = {
    "notification_internal.c": {
        "fns": [
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
        "dpm_basename": "dpm_internal",
        "dpm_header_decls": """\
int notification_get_uid(notification_h noti, uid_t *uid);
int notification_set_uid(notification_h noti, uid_t uid);
int notification_get_event_flag(notification_h noti, bool *event_flag);
int notification_get_pairing_type(notification_h noti, int *type);
int notification_get_channel_name(notification_h noti, char **name);
int notification_get_extension_data(notification_h noti, const char *key, bundle **value);
int notification_channel_get_name(notification_channel_h handle, char **name);
int notification_channel_get_block(notification_channel_h handle, bool *is_blocked);
int notification_channel_get_blockable(notification_channel_h handle, bool *blockable);
int notification_channel_free(notification_channel_h handle);
""",
        "includes": """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

#include <bundle.h>
#include <bundle_internal.h>

#include <notification.h>
#include <notification_internal.h>
#include <notification_error.h>

#include "debug.h"
#include "dpm_internal.h"
#include "notification_private.h"

#ifndef EXPORT_API
#define EXPORT_API __attribute__ ((visibility("default")))
#endif
""",
    },
    "notification_setting.c": {
        "fns": [
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
        "dpm_basename": "dpm_setting",
        "dpm_header_decls": """\
int notification_setting_get_allow_to_notify(notification_setting_h setting, bool *value);
int notification_setting_get_do_not_disturb_except(notification_setting_h setting, bool *value);
int notification_setting_get_pop_up_notification(notification_setting_h setting, bool *value);
int notification_setting_get_app_disabled(notification_setting_h setting, bool *value);
int notification_setting_insert_package_for_uid(const char *pkgname, uid_t uid);
int notification_setting_delete_package_for_uid(const char *pkgname, uid_t uid);
int notification_system_setting_get_do_not_disturb(notification_system_setting_h system_setting, bool *value);
int notification_system_setting_free_system_setting(notification_system_setting_h system_setting);
int notification_system_setting_dnd_schedule_get_enabled(notification_system_setting_h system_setting, bool *value);
int notification_system_setting_dnd_schedule_get_day(notification_system_setting_h system_setting, int *value);
int notification_system_setting_dnd_schedule_get_start_time(notification_system_setting_h system_setting, int *hour, int *min);
int notification_system_setting_dnd_schedule_get_end_time(notification_system_setting_h system_setting, int *hour, int *min);
""",
        "includes": """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <notification.h>
#include <notification_internal.h>
#include <notification_error.h>
#include <notification_setting.h>
#include <notification_setting_internal.h>

#include "debug.h"
#include "dpm_setting.h"
#include "notification_private.h"

#ifndef EXPORT_API
#define EXPORT_API __attribute__ ((visibility("default")))
#endif
""",
    },
    "notification_db.c": {
        "fns": ["notification_db_init", "notification_upgrade_db"],
        "dpm_basename": "dpm_db",
        "dpm_header_decls": """\
int notification_db_init(void);
int notification_upgrade_db(void);
""",
        "includes": """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sqlite3.h>
#include <db-util.h>
#include <tzplatform_config.h>

#include <notification.h>
#include <notification_db.h>
#include <notification_error.h>
#include <notification_internal.h>

#include "debug.h"
#include "dpm_db.h"
#include "notification_private.h"
#include "notification_db_query.h"

#ifndef EXPORT_API
#define EXPORT_API __attribute__ ((visibility("default")))
#endif
""",
    },
}

# Process each
for src_name, job in JOBS.items():
    src_path = NOTIF_SRC / src_name
    extracted, remaining = extract_blocks(src_path, job["fns"])
    missing = [fn for fn, b in extracted.items() if b is None]
    if missing:
        print(f"!! Missing functions in {src_name}: {missing}")
        continue
    # Write remaining (notification side, minus extracted)
    src_path.write_text(remaining)
    # Build DPM .c
    dpm_c = DPM_SRC / f"{job['dpm_basename']}.c"
    header_comment = """/*
 * Copyright (c) 2000 - 2017 Samsung Electronics Co., Ltd. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
"""
    body = "\n".join(extracted[fn] for fn in job["fns"])
    dpm_c.write_text(header_comment + "\n" + job["includes"] + "\n" + body)
    # Build DPM .h
    dpm_h = DPM_INC / f"{job['dpm_basename']}.h"
    guard = job["dpm_basename"].upper()
    header_text = f"""{header_comment}

#ifndef __{guard}_H__
#define __{guard}_H__

#include <stdbool.h>
#include <sys/types.h>

#include "notification.h"

#ifdef __cplusplus
extern "C" {{
#endif

{job['dpm_header_decls']}
#ifdef __cplusplus
}}
#endif

#endif /* __{guard}_H__ */
"""
    dpm_h.write_text(header_text)
    print(f"OK {src_name}: extracted {len(job['fns'])} fns → {dpm_c.name} + {dpm_h.name}")

print("Phase 3b extraction complete.")
