#!/usr/bin/env python3
"""Split notification_shared_file.c into:
   - notification's slim client-side notification_shared_file.c (kept)
   - DPM's new dpm_shared_file.c with all server-only code

Approach:
   - Read the full source.
   - Identify exact byte ranges for each piece (client-keep vs DPM-move).
   - Build the two new files string-by-string.
"""
from pathlib import Path

SRC = Path("/home/hyeonuk/tizen/appfw/notification/src/notification/src/notification_shared_file.c")
text = SRC.read_text()
lines = text.splitlines(keepends=True)
def block(start, end):  # inclusive 1-based
    return "".join(lines[start-1:end])

# 1) Identify line ranges via grep
def find(needle, after=0):
    for i, l in enumerate(lines, 1):
        if i > after and needle in l:
            return i
    raise ValueError(needle)

# Top boilerplate up to the first include block
end_of_includes_n  = 0
for i, l in enumerate(lines, 1):
    if l.startswith("#include"):
        end_of_includes_n = i
# Find the line where typedef/macros end (just before "static const char *__last_index_of(const char *path, const char *search);" forward decl at 91)
fwd_decl = find("static const char *__last_index_of(const char *path, const char *search);")
make_sharing_dir_start = find("static bool __make_sharing_dir(", after=fwd_decl)
last_index_of_def = find("static const char *__last_index_of(const char *path, const char *search)\n", after=fwd_decl)
is_res_file = find("static bool __is_res_file(", after=fwd_decl)
is_shared_file = find("static bool __is_shared_file(", after=fwd_decl)
is_RO_file = find("static bool __is_RO_file(", after=fwd_decl)
copy_private_file = find("int notification_copy_private_file(", after=fwd_decl)
free_file_info = find("static void __free_file_info(", after=fwd_decl)
free_req_info = find("static void __free_req_info(", after=fwd_decl)
comp_str = find("static gint __comp_str(", after=fwd_decl)
comp_file_info = find("static gint __comp_file_info(", after=fwd_decl)
comp_dst_path = find("static gint __comp_dst_path(", after=fwd_decl)
make_file_info = find("static void __make_file_info(", after=fwd_decl)
comp_sharing_req = find("static gint __comp_sharing_req_list(", after=fwd_decl)
comp_uid_info = find("static gint __comp_uid_info_list(", after=fwd_decl)
comp_priv_id = find("static gint __comp_priv_id(", after=fwd_decl)
comp_target_app = find("static gint __comp_target_app(", after=fwd_decl)
convert_list_to_array = find("static char **__convert_list_to_array(", after=fwd_decl)
dup_file_info = find("static sharing_file_info_s *__dup_file_info(", after=fwd_decl)
get_new_file_list = find("static GList *__get_new_file_list(", after=fwd_decl)
get_shared_dir = find("static char *__get_shared_dir(", after=fwd_decl)
remove_target_id = find("notification_remove_private_sharing_target_id(", after=fwd_decl)
add_target_id = find("notification_add_private_sharing_target_id(", after=fwd_decl)
check_file_path = find("char *notification_check_file_path_is_private(", after=fwd_decl)
validate_sharing = find("notification_validate_private_sharing(", after=fwd_decl)
calibrate_sharing = find("notification_calibrate_private_sharing(", after=fwd_decl)
set_sharing_new_target = find("int __set_sharing_for_new_target(", after=fwd_decl)
set_sharing_new_file = find("int __set_sharing_for_new_file(", after=fwd_decl)
set_private_sharing = find("notification_set_private_sharing(", after=fwd_decl)
timeout_handler = find("static bool __timeout_handler(", after=fwd_decl)
remove_sharing = find("notification_remove_private_sharing(", after=fwd_decl)

# We need to find each function end (line of closing '}') by scanning braces
def fn_range(start):
    # Find first '{' at or after start (definition body start)
    depth = 0
    started = False
    for j in range(start - 1, len(lines)):
        for ch in lines[j]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
                if started and depth == 0:
                    return (start, j + 1)
    raise ValueError(f"no close for {start}")

# Helper: include any leading LCOV_EXCL_START line right above the function
def with_lcov(start):
    while start > 1 and ("LCOV_EXCL_START" in lines[start-2] or lines[start-2].strip().startswith("/*")):
        # only step back if it's the LCOV start comment immediately before
        if "LCOV_EXCL_START" in lines[start-2]:
            start -= 1
            continue
        break
    return start

# Helper: include trailing LCOV_EXCL_STOP comment right after function
def end_with_lcov(end):
    while end < len(lines) and "LCOV_EXCL_STOP" in (lines[end] if end < len(lines) else ""):
        end += 1
    # also absorb blank line below
    while end < len(lines) and lines[end].strip() == "":
        end += 1
        break
    return end

# Define moves and keeps
# (each: name, start line of definition)
all_fns = [
    ("__make_sharing_dir", make_sharing_dir_start),
    ("__last_index_of_def", last_index_of_def),
    ("__is_res_file", is_res_file),
    ("__is_shared_file", is_shared_file),
    ("__is_RO_file", is_RO_file),
    ("notification_copy_private_file", copy_private_file),
    ("__free_file_info", free_file_info),
    ("__free_req_info", free_req_info),
    ("__convert_list_to_array", convert_list_to_array),
    ("__comp_str", comp_str),
    ("__comp_file_info", comp_file_info),
    ("__comp_dst_path", comp_dst_path),
    ("__dup_file_info", dup_file_info),
    ("__make_file_info", make_file_info),
    ("__get_new_file_list", get_new_file_list),
    ("__get_shared_dir", get_shared_dir),
    ("__comp_sharing_req_list", comp_sharing_req),
    ("__comp_uid_info_list", comp_uid_info),
    ("__comp_priv_id", comp_priv_id),
    ("__comp_target_app", comp_target_app),
    ("notification_remove_private_sharing_target_id", remove_target_id),
    ("notification_add_private_sharing_target_id", add_target_id),
    ("notification_check_file_path_is_private", check_file_path),
    ("notification_validate_private_sharing", validate_sharing),
    ("notification_calibrate_private_sharing", calibrate_sharing),
    ("__set_sharing_for_new_target", set_sharing_new_target),
    ("__set_sharing_for_new_file", set_sharing_new_file),
    ("notification_set_private_sharing", set_private_sharing),
    ("__timeout_handler", timeout_handler),
    ("notification_remove_private_sharing", remove_sharing),
]

# Compute concrete ranges
def_ranges = {}
for name, start in all_fns:
    s, e = fn_range(start)
    s_with = with_lcov(s)
    e_with = end_with_lcov(e)
    def_ranges[name] = (s_with, e_with)

KEEP_IN_NOTIFICATION = {
    "__last_index_of_def",
    "__is_res_file",
    "__is_shared_file",
    "__is_RO_file",
    "notification_copy_private_file",
    "notification_check_file_path_is_private",
}
MOVE_TO_DPM = {n for n, _ in all_fns} - KEEP_IN_NOTIFICATION

# Build new notification's notification_shared_file.c (slim client-side version)
HEADER = '''/*
 * Copyright (c) 2017 Samsung Electronics Co., Ltd. All rights reserved.
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

#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include <gio/gio.h>
#include <glib/gstdio.h>

#include <sys/stat.h>
#include <sys/types.h>
#include <utime.h>
#include <sys/time.h>

#include "notification.h"
#include "notification_debug.h"
#include "notification_shared_file.h"
#include <notification_private.h>
#include "notification_internal.h"

#define NOTI_PRIV_DATA_DIR "data/.notification"

'''

# Sorted ranges to keep, by start line
keep_blocks = sorted([def_ranges[n] for n in KEEP_IN_NOTIFICATION], key=lambda x: x[0])
notif_body = "".join(block(s, e) for s, e in keep_blocks)
new_notif_src = HEADER + notif_body
Path("/home/hyeonuk/tizen/appfw/notification/src/notification/src/notification_shared_file.c").write_text(new_notif_src)

# Build DPM's dpm_shared_file.c (everything else, plus types/macros/global state)
DPM_HEADER = '''/*
 * Copyright (c) 2017 Samsung Electronics Co., Ltd. All rights reserved.
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
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <aul.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include <gio/gio.h>
#include <glib/gstdio.h>

#include <tizen_core.h>
#include <tzplatform_config.h>
#include <security-manager.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <linux/xattr.h>
#include <sys/types.h>
#include <utime.h>
#include <sys/time.h>
#include <package_manager.h>

#include <notification.h>
#include <notification_internal.h>
#include <notification_shared_file.h>

#include "debug.h"
#include "dpm_shared_file.h"
#include "notification_private.h"

#ifndef EXPORT_API
#define EXPORT_API __attribute__ ((visibility("default")))
#endif

#define NOTI_PRIV_DATA_DIR "data/.notification"
#define MAX_TIMEOUT 5000
#define MAX_RETRY_CNT 3
#define ERR_BUFFER_SIZE 1024

#define DUMMY_PARAM
#define __OOM_CHECK(value, ret_value, free_fun) \\
do { \\
\tif (value == NULL) { \\
\t\tERR("out of memory"); \\
\t\tfree_fun; \\
\t\treturn ret_value; \\
\t} \\
} while (0)

static GList *__uid_list;
typedef struct uid_info {
\tuid_t uid;
\tGList *sharing_req_list;
\tGList *target_app_list;
} uid_info_s;

typedef struct sharing_req_data {
\tchar *app_id;
\tchar *dir;
\ttizen_core_source_h timer;
\tint drop_retry_count;
\tuid_t uid;
\tGList *priv_id_list;
\tGList *shared_file_list;
\tGList *target_app_table;
} sharing_req_data_s;

typedef struct sharing_file_info {
\tchar *src_path;
\tchar *dst_path;
\ttime_t modification_time;
} sharing_file_info_s;

typedef struct target_app_info {
\tchar *app_id;
\tchar *tidl_sender_name;
} target_app_info_s;

/* Local copy of helper from notification_shared_file.c — DPM needs it for __make_file_info. */
static const char *__last_index_of(const char *path, const char *search)
{
\tconst char *p = path;
\tconst char *last = NULL;
\tsize_t slen = strlen(search);

\twhile ((p = strstr(p, search)) != NULL) {
\t\tlast = p;
\t\tp += slen;
\t}
\treturn last;
}

'''

# Forward decl of __set_sharing_for_new_target / _new_file — they are non-static in original.
# In the moved file they're only used internally; declare static.
# We'll keep them as `int` returning to avoid changing their signature/use sites — but mark static.
move_blocks = sorted([def_ranges[n] for n in MOVE_TO_DPM], key=lambda x: x[0])
move_body = "".join(block(s, e) for s, e in move_blocks)
# Replace the two non-static definitions with static
move_body = move_body.replace(
    "int __set_sharing_for_new_target(sharing_req_data_s",
    "static int __set_sharing_for_new_target(sharing_req_data_s",
)
move_body = move_body.replace(
    "int __set_sharing_for_new_file(sharing_req_data_s",
    "static int __set_sharing_for_new_file(sharing_req_data_s",
)
# Need forward declarations for static helpers used before defined
# __timeout_handler is defined late but referenced earlier? actually all references are inside set_private_sharing which is defined after.
# We need fwd decls of __set_sharing_for_new_target/_new_file because they're used from notification_set_private_sharing
fwd_decls = """\
static int __set_sharing_for_new_target(sharing_req_data_s *req_data, GList *target_list);
static int __set_sharing_for_new_file(sharing_req_data_s *req_data, GList *new_file_list, gboolean is_overlapping);
static bool __timeout_handler(void *data);

"""
dpm_src = DPM_HEADER + fwd_decls + move_body
Path("/home/hyeonuk/tizen/appfw/data-provider-master/src/dpm_shared_file.c").write_text(dpm_src)

# Build dpm_shared_file.h
DPM_HDR = """/*
 * Copyright (c) 2017 Samsung Electronics Co., Ltd. All rights reserved.
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

#ifndef __DPM_SHARED_FILE_H__
#define __DPM_SHARED_FILE_H__

#include <sys/types.h>
#include <stdbool.h>

#include "notification.h"

#ifdef __cplusplus
extern "C" {
#endif

int notification_set_private_sharing(notification_h noti, uid_t uid);
void notification_remove_private_sharing(const char *src_app_id, int priv_id, uid_t uid);
void notification_add_private_sharing_target_id(pid_t pid, const char *sender, uid_t uid);
void notification_remove_private_sharing_target_id(const char *sender, uid_t uid);
void notification_calibrate_private_sharing(notification_h updated_noti, notification_h source_noti);
bool notification_validate_private_sharing(notification_h updated_noti);

#ifdef __cplusplus
}
#endif

#endif /* __DPM_SHARED_FILE_H__ */
"""
Path("/home/hyeonuk/tizen/appfw/data-provider-master/include/dpm_shared_file.h").write_text(DPM_HDR)

# Build slim notification_shared_file.h with only surviving functions
NOTIF_HDR = """/*
 * Copyright (c) 2017 Samsung Electronics Co., Ltd. All rights reserved.
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

#ifndef __NOTIFICATION_SHARED_FILE_H__
#define __NOTIFICATION_SHARED_FILE_H__

#include "notification.h"

#ifdef __cplusplus
extern "C" {
#endif

int notification_copy_private_file(const char* src_path, const char* dst_path);
char *notification_check_file_path_is_private(const char *pkg_id, const char *file_path);

#ifdef __cplusplus
}
#endif
#endif /* __NOTIFICATION_SHARED_FILE_H__ */
"""
Path("/home/hyeonuk/tizen/appfw/notification/src/notification/include/notification_shared_file.h").write_text(NOTIF_HDR)

print("Phase 3a split complete.")
print(f"  KEEP in notification: {sorted(KEEP_IN_NOTIFICATION)}")
print(f"  MOVE to DPM: {sorted(MOVE_TO_DPM)}")
