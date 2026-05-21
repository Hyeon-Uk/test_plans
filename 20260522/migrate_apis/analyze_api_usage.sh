#!/bin/bash
# For each function declared in notification's public headers,
# list which packages (other than notification itself) call it.
set -u
ROOT=/home/hyeonuk/tizen/appfw
cd "$ROOT"
mkdir -p analysis

HEADERS=(
  notification.h
  notification_db.h
  notification_internal.h
  notification_error.h
  notification_type.h
  notification_list.h
  notification_ongoing.h
  notification_ongoing_flag.h
  notification_text_domain.h
  notification_status.h
  notification_status_internal.h
  notification_setting.h
  notification_setting_internal.h
  notification_ipc.h
  notification_noti.h
  notification_setting_service.h
  notification_viewer.h
  notification_shared_file.h
  notification_type_internal.h
)

# Extract function names from each header
> analysis/all_functions.tsv
for h in "${HEADERS[@]}"; do
  hf="notification/src/notification/include/$h"
  [ -f "$hf" ] || continue
  # match "type name(" patterns; capture function name
  # Be conservative: lines like "int notification_xxx(" or "void notification_xxx ("
  grep -E '^[a-zA-Z_][a-zA-Z0-9_ \*]*\b(notification[a-zA-Z0-9_]*|noti_[a-zA-Z0-9_]*)\s*\(' "$hf" \
    | grep -v -E '^\s*//' \
    | sed -E 's|^[^(]*\b((notification|noti)_[a-zA-Z0-9_]+)\s*\(.*$|\1|' \
    | sort -u \
    | while read -r fn; do
        # validate
        [[ "$fn" =~ ^(notification|noti)_[a-zA-Z0-9_]+$ ]] && echo -e "$h\t$fn"
      done >> analysis/all_functions.tsv
done

# Also use ctags-like nm extraction approach via grep + post-filter
echo "Functions extracted: $(wc -l < analysis/all_functions.tsv)"

# Build list of unique function names
awk -F'\t' '{print $2}' analysis/all_functions.tsv | sort -u > analysis/funcs.txt
echo "Unique functions: $(wc -l < analysis/funcs.txt)"
