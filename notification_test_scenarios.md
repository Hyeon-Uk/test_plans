# notification — Coverage-Gap Test Scenario Inventory

Generated after stripping `LCOV_EXCL` markers and running `gbs build --define "gcov 1"`. Targets every EXPORT_API / HAPI with uncovered branches in `src/notification/src/*.c`.

Coverage baseline (post-strip, 816 tests):

| File | Lines | Funcs | Status |
|---|---|---|---|
| notification.c | 75.4% | 95.2% | mostly covered |
| notification_db.c | ~75% | 100% | extended +16 tests this round |
| notification_error.c | 100% | 100% | done |
| notification_group.c | 0.0% | 0.0% | DEAD CODE (header lies, no EXPORT_API) |
| notification_internal.c | 60.0% | 90.8% | partial |
| notification_internal_tidl.c | 0.4% | 11.1% | GENERATED (skip) |
| notification_ipc.c | 74.7% | 100% | mostly covered |
| notification_list.c | 81.2% | 100% | mostly covered |
| notification_noti.c | 61.7% | 81.0% | partial |
| notification_ongoing.c | 100% | 100% | done |
| notification_setting.c | 51.3% | 89.7% | partial |
| notification_setting_service.c | 28.7% | 80.0% | gap |
| notification_shared_file.c | 11.3% | 23.3% | major gap |
| notification_status.c | 27.3% | 75.0% | gap |
| notification_tidl.c | 13.9% | 29.3% | partial |
| notification_tidl_proxy.c | 0.5% | 0.6% | GENERATED (skip) |
| notification_viewer.c | 14.7% | 54.5% | gap |

Notation: `[P]` success · `[N]` failure (one per distinct return) · `[E]` edge · `[C]` corner

---

## 1. notification_shared_file.c — 6 EXPORT_API, 32%

### `notification_remove_private_sharing_target_id` @ L623 (38%)
- [P1] target list contains matching `uid_info` → entry removed, list shortened
- [P2] target list empty → no-op, returns void
- [N1] `uid_info` NULL — guard at L637
- [E1] matching entry is head of list → list head updated
- [E2] matching entry is tail → tail updated
- [C1] multiple duplicates → only first removed (verify single-pass)

### `notification_add_private_sharing_target_id` @ L656 (72%)
- [P1] new uid_info appended; allow_to_notify, sharing_dir set
- [N1] `uid_info` NULL — early return
- [N2] `app_id` strdup OOM — return OOM
- [N3] `request_dir` strdup OOM after app_id success — partial state cleanup
- [E1] target list already has uid_info — no duplicate add (idempotency)

### `notification_validate_private_sharing` @ L763 (33%)
- [P1] image/sound/vibration paths all match sharing prefix → return TRUE
- [N1] image path doesn't start with sharing_dir → FALSE
- [N2] sound path mismatch → FALSE
- [N3] vibration path mismatch → FALSE
- [E1] image path NULL → skip image check
- [E2] sound path NULL → skip sound check
- [E3] vibration path NULL → skip vibration check
- [C1] only one type set (image only) → validate only image

### `notification_calibrate_private_sharing` @ L811 (21%)
- [P1] image path under request_dir → replaced with sharing_dir prefix
- [P2] sound path replaced
- [P3] vibration path replaced
- [N1] strdup OOM during image replace → return without crash
- [N2] strdup OOM during sound replace
- [N3] strdup OOM during vibration replace
- [E1] image NULL → skip
- [E2] no match between path and request_dir → leave path untouched
- [C1] all three paths replaced in one call

### `notification_set_private_sharing` @ L1086 (14%)
- [P1] new request: UID list empty → create new request, append
- [P2] same UID exists, new app_id → append to existing UID
- [P3] same UID + same app_id exists → idempotent
- [N1] noti handle NULL → INVALID_PARAMETER
- [N2] caller pid invalid (aul fail) → INVALID/OOM path
- [N3] `g_list_append` OOM (simulate via malloc fail) → cleanup partial state
- [N4] security_manager_create_sharing fail → return OPERATION_FAILED
- [E1] sharing_dir creation needed (first call for caller)
- [E2] file list collection: no images/sounds → request count 0, still register
- [C1] concurrent set + remove for same UID — list integrity

### `notification_remove_private_sharing` @ L1332 (38%)
- [P1] UID has request → request removed, security_manager_drop_sharing called
- [P2] UID has multiple requests → only matching one removed
- [N1] noti NULL → INVALID_PARAMETER
- [N2] UID not in list → NOT_EXIST_ID
- [N3] security_manager_drop fail → return OPERATION_FAILED
- [E1] last request for UID → UID entry removed, list shrinks
- [C1] called twice with same noti → 2nd call → NOT_EXIST_ID

---

## 2. notification_db.c — 7 EXPORT_API (post-extension ~75%)

Already added this round (16 tests). Remaining gaps:

### `notification_db_init` @ L85 (88%)
- [C1] `is_db_corrupted=TRUE` from integrity callback → `__recover_corrupted_db` runs
- [N1] `__recover_corrupted_db` itself fails (open_v2 inside recovery returns ERROR)
- [E1] errmsg non-NULL after exec failure → sqlite3_free path

### `notification_upgrade_db` @ L374 (28%)
- [P1] `__check_db_version` returns 0 (already latest) → END TRANSACTION, NONE
- [P2] version mismatch → noti_table + template upgrade + PRAGMA user_version + COMMIT
- [N1] open_v2 fail → FROM_DB (already tested)
- [N2] BEGIN TRANSACTION fail → FROM_DB (already tested)
- [N3] `__upgrade_noti_table` returns non-NONE → ROLLBACK path
- [N4] `__upgrade_noti_template_table` fail → ROLLBACK path
- [N5] `sqlite3_mprintf("PRAGMA…")` returns NULL → OUT_OF_MEMORY + ROLLBACK
- [N6] PRAGMA exec fail → FROM_DB + ROLLBACK
- [N7] END TRANSACTION fail → overrides ret to FROM_DB
- [N8] ROLLBACK fail in error path → ret = FROM_DB

---

## 3. notification_viewer.c — 3 EXPORT_API, 65%

### `notification_init_default_viewer` @ L67 (56%)
- [P1] config file present, dict load ok, viewer key present → `_default_viewer` set, returns 0
- [P2] viewer key NULL in dict → `_default_viewer` stays NULL, returns 0
- [N1] `access` to config file fails → -1 (untestable: access mock hardcoded for `notification.ini`)
- [N2] `iniparser_load` returns NULL → -1
- [E1] called twice → second call short-circuits (`_default_viewer != NULL`)
- [E2] strdup OOM on viewer → `_default_viewer` stays NULL, dict still freed

### `notification_launch_default_viewer` & `_without_candidate_process` — 100%
Done.

**Note:** `__push_delayed_noti` / `__pop_delayed_noti_cb` / `__app_control_result_cb` are tightly coupled to tizen_core and app_control — not unit-testable without mocking the whole core. **Document as integration-only.**

---

## 4. notification_status.c — 3 EXPORT_API, 32%

### `notification_status_monitor_message_cb_set` @ L74 (21%)
- [P1] first call: `g_bus_get_sync` OK, `signal_subscribe` non-zero → NONE
- [P2] second call: `md.conn` already set → skip bus_get, still subscribe if `md.message_id == 0`
- [P3] third call: both `md.conn` and `md.message_id` set → just update callback
- [N1] cb NULL → INVALID_PARAMETER
- [N2] `g_bus_get_sync` returns NULL → FROM_DBUS (`error->message` accessed)
- [N3] `signal_subscribe` returns 0 → FROM_DBUS, `g_object_unref(conn)` cleanup

### `notification_status_monitor_message_cb_unset` @ L118 (60%)
- [P1] state with `md.message_id != 0` → `g_dbus_connection_signal_unsubscribe` called, id=0
- [P2] state with `md.conn != NULL` → unref + NULL
- [C1] called twice → second call is no-op safe
- [E1] called without prior set → no crash (all branches skipped)

### `notification_status_message_post` @ L139 (29%)
- [P1] `g_bus_get_sync` OK, `emit_signal` OK, `flush_sync` OK → NONE
- [N1] message NULL → INVALID_PARAMETER (covered)
- [N2] `g_bus_get_sync` NULL → FROM_DBUS
- [N3] `emit_signal` returns FALSE → FROM_DBUS, `err->message` accessed
- [N4] `flush_sync` returns FALSE → FROM_DBUS
- [E1] err non-NULL at end → `g_error_free` cleanup
- [E2] conn non-NULL at end → `g_object_unref` cleanup

---

## 5. notification_setting_service.c — 11+ EXPORT_API, 29%

Tests already exist for null guards. Missing success/error paths for DB-backed funcs:

### `noti_setting_service_get_setting_by_app_id` @ L90
- [P1] `sqlite3_get_table` row_count=1 → setting allocated, fields populated, NONE
- [N1] app_id NULL → INVALID
- [N2] setting NULL → INVALID
- [N3] db_open fail → get_last_result error
- [N4] sqlite3_mprintf NULL → OUT_OF_MEMORY
- [N5] sqlite3_get_table fail (non-OK, non-`-1`) → FROM_DB
- [N6] row_count = 0 → NOT_EXIST_ID
- [N7] malloc setting struct fail → OUT_OF_MEMORY

### `noti_setting_get_setting_array` @ L173
- [P1] N rows returned → array filled, count=N, NONE
- [N1] setting_array NULL → INVALID
- [N2] count NULL → INVALID
- [N3] db_open fail
- [N4] mprintf NULL → OOM
- [N5] get_table fail → FROM_DB
- [N6] row_count=0 → NOT_EXIST_ID
- [N7] malloc fail → OOM

### `notification_setting_db_update` @ L348
- [P1] valid args → prepare_v2 + step success → NONE
- [N1] package_name NULL (covered)
- [N2] app_id NULL (covered)
- [N3] db_open fail
- [N4] mprintf NULL → OOM
- [N5] prepare_v2 fail → FROM_DB
- [N6] step fail → FROM_DB

### `notification_setting_db_update_system_setting` @ L392
- [P1] update ok → NONE
- [N1] db_open fail
- [N2] prepare_v2 fail → FROM_DB
- [N3] step fail → FROM_DB

### `notification_setting_db_update_do_not_disturb` @ L440
- [P1] update ok → NONE
- [N1..3] same as above

### `notification_system_setting_get_dnd_schedule_enabled_uid` @ L475
- [P1] N uids returned → array allocated, count populated
- [N1] uids NULL → INVALID
- [N2] count NULL → INVALID
- [N3..6] db_open / mprintf / get_table / malloc fails

### `notification_get_dnd_and_allow_to_notify` @ L542
- [P1] row found → dnd flag + allow_to_notify populated, NONE
- [N1] app_id NULL
- [N2..6] db_open / mprintf / get_table / 0-rows / malloc fails

### `notification_system_setting_load_dnd_allow_exception` @ L638
- [P1] N exceptions → handle array allocated
- [N1] dnd_allow_exception NULL
- [N2] count NULL
- [N3..7] db_open / mprintf / get_table / 0-rows / malloc fails

### `notification_system_setting_update_dnd_allow_exception` @ L711
- [P1] update ok → NONE
- [N1..3] db_open / prepare / step fails

### `notification_setting_db_update_app_disabled` @ L804
- [P1] update ok → NONE
- [N1] app_id NULL
- [N2..4] db_open / prepare / step fails

### `notification_setting_db_update_pkg_disabled` @ L844
- Same pattern as app_disabled.

---

## 6. notification_tidl.c — 9 EXPORT_API, 14%

All TIDL stub callbacks. Untestable without real RPC server registration. Already have compile-stubs in test_notification_tidl.cc (DPM project). Skip: requires service runtime.

---

## 7. notification_noti.c — 24 EXPORT_API, 50%

### `notification_noti_delete_by_priv_id` @ L1407 (**0% — entirely untested**)
- [P1] row exists, delete succeeds → 1+ row deleted, NONE
- [N1] app_id NULL → INVALID
- [N2] db_open fail
- [N3] mprintf NULL → OOM
- [N4] prepare_v2 fail → FROM_DB
- [N5] step fail → FROM_DB
- [E1] no matching row → 0 changes, NONE

### `notification_noti_get_count` @ L1597 (**0%**)
- [P1] vconf returns limit, query builds with type filter → count returned
- [P2] app_id filter applied → narrow count
- [P3] group_id filter applied
- [N1] count NULL → INVALID
- [N2] vconf_get_int fail → use default limit
- [N3] db_open fail
- [N4] mprintf NULL
- [N5] prepare_v2 / step fail → FROM_DB

### `notification_noti_insert` @ L1050 (75%)
- [N1] permission_check returns DENIED → PERMISSION_DENIED
- [N2] display_applist adjust → OOM on internal alloc
- [N3] prepare_v2 fail → FROM_DB
- [N4] step fail → FROM_DB

### `notification_noti_get_by_priv_id` @ L1137 (42%)
- [N1] OOM on mprintf
- [N2] `_get_notification_from_stmt` returns non-NONE → propagate
- [N3] no row found → NOT_EXIST_ID

### `notification_noti_update` @ L1193 (67%)
- [N1] permission denied
- [N2] noti not exists → NOT_EXIST_ID
- [N3] stmt prep fail
- [N4] step fail

### `notification_noti_delete_all` @ L1273 (61%)
- [P1] type filter only → list of priv_ids returned
- [P2] type + appid filter
- [N1] type invalid → INVALID
- [N2] mprintf fail in any query branch → OOM
- [N3] stmt fail at count / fetch / delete stage → FROM_DB

### `notification_noti_delete_by_display_applist` @ L1475 (69%)
- [P1] matching rows deleted, priv_id list returned
- [N1] count query fail
- [N2] fetch query fail
- [N3] delete query fail

---

## 8. notification_internal.c — 105 EXPORT_API, 60%

### `notification_resister_changed_cb_for_uid` @ L328 (15%)
- [P1] first registration: hash table created, callback list appended, monitor init, tidl call → NONE
- [N1] cb NULL → INVALID
- [N2] hash_table_new fail → OOM (untestable without g_hash_table mock)
- [N3] monitor_init fail → FROM_TIDL
- [N4] CPU inheritance setup fail
- [E1] subsequent registration: hash table exists → just append

### `notification_unresister_changed_cb_for_uid` @ L393 (22%)
- [P1] removes matching cb, list becomes empty → monitor fini called
- [P2] removes cb, list non-empty → no fini
- [N1] cb NULL → INVALID
- [N2] hash table NULL (no prior register) → INVALID
- [N3] cb not in list → INVALID
- [N4] tidl call fails

### `notification_add_deferred_task` @ L300 / `del_deferred_task` @ L313
- [N1] CPU inheritance setup fail → error path
- [N2] tidl call fail → error returned

### `notification_update_progress` @ L444 / `update_size` @ L483 / `update_content` @ L520
- [N1] caller_app_id fetch fail (aul_app_get_appid_bypid fail)
- [N2] strdup OOM on caller_app_id

### `notification_translate_localized_text` @ L580 (93%)
- [E1] bundle_create returns NULL → caller branch

### `notification_delete_group_by_group_id` @ L792 (91%)
- [N1] caller_app_id NULL (aul fail) → INVALID

### `notification_get_args` @ L746
- [E1] `*args = NULL` branch when no args bundle

### `notification_set_execute_option` @ L1036 (81%)
- [E1] each bundle type (single/multi/responding) deletion path when prior bundle present

---

## 9. notification.c — 57 EXPORT_API, 75%

Most well-covered. Top gaps:

### `notification_get_text` @ L443 (36% — largest gap)
- [P1] no variable substitution → simple dgettext lookup
- [P2] count variable %d substitution → format with int
- [P3] string variable %s substitution → format with string
- [P4] double variable substitution
- [N1] noti NULL
- [N2] text NULL out
- [N3] format string overflow → buffer truncation handling
- [E1] domain text-domain set → dgettext with domain
- [E2] localization fallback when key missing
- [C1] multiple substitution slots

### `notification_set_text` @ L230 (94%)
- [E1] each text type variant — bundle_del path when prior text exists

### `notification_set_image` @ L96 (68%)
- [P1] image_type=PRIVATE → private path bundle ops, strdup tracking
- [N1] strdup OOM on private_path → cleanup
- [E1] replace existing private image → bundle_del + add

### `notification_get_image` @ L156 (94%)
- [E1] app_icon_path key missing → NULL out param

---

## Implementation Order (priority)

1. **shared_file.c** (11% → target 60%) — biggest absolute gap, security-critical
2. **status.c** (27% → 80%) — small file, dbus mock available
3. **setting_service.c** (29% → 70%) — many similar DB patterns, batch tests
4. **noti.c** delete_by_priv_id + get_count (0% → 80%) — straightforward sqlite mock
5. **internal.c** changed_cb register/unregister (15%/22% → 60%) — needs g_hash_table behavior
6. **db.c** upgrade_db (28% → 70%) — already started, finish rollback paths
7. **notification.c** get_text (36% → 70%) — pure logic, no mocks needed
8. **viewer.c** init_default_viewer (56% → 80%) — limited by access mock

**Untestable / out of scope:**
- `notification_group.c` — header-declared but unexported, dead code
- `notification_internal_tidl.c` / `notification_tidl_proxy.c` — generated TIDL boilerplate
- `notification_tidl.c` — runtime RPC server required
- `notification_viewer.c` — `__push_delayed_noti` / `__app_control_result_cb` require tizen_core integration

## Mock Infrastructure Additions Made This Round

- `sqlite_mock.hh/cc`: added `sqlite3_prepare` (v1) and `sqlite3_errmsg`
- `LCOV_EXCL_*` markers stripped from `src/notification/src/*.c` and `src/notification-ex/*.cc` (must restore before commit)
