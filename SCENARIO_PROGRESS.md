# Scenario Progress — notification package
Updated: 2026-05-15 | Batch: 2 functions per iteration | Tests: 761 (commit pending)

## Status legend
- `[D]` DONE — positive + null/error paths covered
- `[P]` PARTIAL — null/error only; positive path missing
- `[IPC]` IPC path needs rpc-port mock (rpc_port_mock.hh/cc ready, not yet committed)
- `[ ]` TODO — no tests at all

## ▶ NEXT BATCH (iteration current)
**Commit infra first**: `tests/mock/rpc_port_mock.{hh,cc}` + `test_notification_internal.cc` pending changes  
**Batch 1** ✅ DONE (696 tests): `notification_post` + `notification_update` — type/null validation + IPC connect-fail path
**Batch 2**: `notification_delete_all` + `notification_delete` (both [IPC])

---

## notification.c — notification_set/get/post/delete (scenario lines 36–634)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | notification_set_image | [D] | 9 tests |
| 2 | notification_get_image | [D] | 4 tests |
| 3 | notification_set_time | [D] | 3 tests |
| 4 | notification_get_time | [D] | 2 tests |
| 5 | notification_get_insert_time | [D] | 2 tests |
| 6 | notification_set_text | [D] | 15+ tests |
| 7 | notification_get_text | [D] | 4 tests |
| 8 | notification_set_text_domain | [D] | 3 tests |
| 9 | notification_get_text_domain | [D] | via roundtrip |
| 10 | notification_set_time_to_text | [D] | 4 tests |
| 11 | notification_get_time_from_text | [D] | 3 tests |
| 12 | notification_set_sound | [D] | 7 tests |
| 13 | notification_get_sound | [D] | 3 tests |
| 14 | notification_set_vibration | [D] | 5 tests |
| 15 | notification_get_vibration | [D] | 3 tests |
| 16 | notification_set_led | [D] | 6 tests |
| 17 | notification_get_led | [D] | 3 tests |
| 18 | notification_set_led_time_period | [D] | 3 tests |
| 19 | notification_get_led_time_period | [D] | 3 tests |
| 20 | notification_set_launch_option | [P] | null+invalid+1 valid; roundtrip missing |
| 21 | notification_get_launch_option | [P] | null only |
| 22 | notification_set_event_handler | [D] | 8 tests |
| 23 | notification_get_event_handler | [D] | 3 tests |
| 24 | notification_set_property | [D] | 6 tests |
| 25 | notification_get_property | [D] | 3 tests |
| 26 | notification_set_display_applist | [D] | 5 tests |
| 27 | notification_get_display_applist | [D] | 3 tests |
| 28 | notification_set_size | [D] | 7 tests |
| 29 | notification_get_size | [D] | 3 tests |
| 30 | notification_set_progress | [D] | 8 tests |
| 31 | notification_get_progress | [D] | 3 tests |
| 32 | notification_get_pkgname | [D] | 3 tests |
| 33 | notification_set_layout | [D] | 6 tests |
| 34 | notification_get_layout | [D] | 3 tests |
| 35 | notification_get_type | [D] | 2 tests |
| 36 | notification_post | [D] | type/null/IPC-fail |
| 37 | notification_update | [D] | null/IPC-fail |
| 38 | **notification_delete_all** | **[IPC]** | ← BATCH 2 |
| 39 | **notification_delete** | **[IPC]** | ← BATCH 2 |
| 40 | notification_create | [D] | 5 tests |
| 41 | notification_load_by_tag | [IPC] | ← BATCH 3 |
| 42 | notification_clone | [D] | 15 tests |
| 43 | notification_free | [D] | 3 tests |
| 44 | notification_set_tag | [D] | 5 tests |
| 45 | notification_get_tag | [D] | 2 tests |
| 46 | notification_set_ongoing_flag | [D] | 3 tests |
| 47 | notification_get_ongoing_flag | [D] | 3 tests |
| 48 | notification_add_button | [D] | 4 tests |
| 49 | notification_remove_button | [D] | 4 tests |
| 50 | notification_set_auto_remove | [D] | 4 tests |
| 51 | notification_get_auto_remove | [D] | 3 tests |
| 52 | notification_save_as_template | [IPC] | ← BATCH 3 |
| 53 | notification_create_from_template | [IPC] | ← BATCH 4 |
| 54 | notification_get_noti_block_state | [IPC] | ← BATCH 4 |
| 55 | notification_set_text_input | [D] | 4 tests |
| 56 | notification_set_extension_image_size | [D] | 8 tests |
| 57 | notification_get_extension_image_size | [D] | 2 tests |

---

## notification_internal.c — T1-T5 templates + 80+ functions (scenario lines 651–1804)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | notification_add_deferred_task | [D] | null test |
| 2 | notification_del_deferred_task | [D] | null test |
| 3 | notification_resister_changed_cb_for_uid | [D] | null test |
| 4 | notification_resister_changed_cb | [D] | null test |
| 5 | notification_unresister_changed_cb_for_uid | [D] | null test |
| 6 | notification_unresister_changed_cb | [D] | null test |
| 7 | notification_update_progress | [P] | null+invalid only |
| 8 | notification_update_size | [P] | null+invalid only |
| 9 | notification_update_content | [P] | null+invalid only |
| 10 | notification_set_icon | [D] | 5 tests |
| 11 | notification_get_icon | [D] | 3 tests |
| 12 | notification_translate_localized_text | [D] | 2 tests |
| 13 | notification_set_title | [D] | 5 tests |
| 14 | notification_get_title | [D] | 3 tests |
| 15 | notification_set_content | [D] | 5 tests |
| 16 | notification_get_content | [D] | 3 tests |
| 17 | notification_set_application | [D] | 6 tests |
| 18 | notification_get_application | [D] | 4 tests |
| 19 | notification_set_args | [D] | 8 tests |
| 20 | notification_get_args | [D] | 4 tests |
| 21 | notification_get_grouping_list | [P] | null only |
| 22 | notification_delete_group_by_group_id | [IPC] | IPC-fail only |
| 23 | notification_delete_group_by_priv_id | [P] | null+invalid |
| 24 | notification_get_count | [P] | null only |
| 25 | notification_clear | [IPC] | type guard + IPC-fail |
| 26 | notification_op_get_data | [D] | 3 tests |
| 27 | notification_set_pkgname | [D] | 5 tests |
| 28 | notification_set_app_id | [D] | 6 tests |
| 29 | notification_delete_all_by_type | [IPC] | type guard + IPC-fail |
| 30 | notification_delete_by_priv_id | [P] | null+invalid |
| 31 | notification_set_execute_option | [D] | 6 tests |
| 32 | notification_get_id | [D] | 4 tests |
| 33 | notification_set_priv_id | [D] | 6 tests |
| 34 | notification_load | [IPC] | IPC-fail only |
| 35 | notification_new | [D] | 1 test |
| 36 | notification_get_execute_option | [D] | 3 tests |
| 37 | notification_insert_for_uid | [IPC] | null only |
| 38 | notification_insert | [IPC] | null only |
| 39 | notification_update_async_for_uid | [IPC] | null only |
| 40 | notification_update_async | [IPC] | null only |
| 41 | notification_register_detailed_changed_cb_for_uid | [D] | |
| 42 | notification_register_detailed_changed_cb | [D] | |
| 43 | notification_unregister_detailed_changed_cb_for_uid | [D] | |
| 44 | notification_unregister_detailed_changed_cb | [D] | |
| 45 | notification_is_service_ready | [IPC] | IPC-fail only |
| 46 | notification_set_uid | [D] | 5 tests |
| 47 | notification_get_uid | [D] | 2 tests |
| 48 | notification_post_for_uid | [IPC] | null only |
| 49 | notification_update_for_uid | [IPC] | null + IPC-fail |
| 50 | notification_delete_for_uid | [IPC] | null + IPC-fail |
| 51 | notification_delete_all_for_uid | [P] | null+type |
| 52 | notification_load_by_tag_for_uid | [IPC] | null+type |
| 53 | notification_create_from_package_template | [IPC] | null args only |
| 54 | notification_set_default_button | [D] | 6 tests |
| 55 | notification_get_default_button | [D] | 3 tests |
| 56 | notification_get_ongoing_value_type | [D] | 3 tests |
| 57 | notification_set_ongoing_value_type | [D] | 5 tests |
| 58 | notification_get_ongoing_time | [D] | 3 tests |
| 59 | notification_set_ongoing_time | [D] | 5 tests |
| 60 | notification_get_hide_timeout | [D] | 3 tests |
| 61 | notification_set_hide_timeout | [D] | 5 tests |
| 62 | notification_get_delete_timeout | [D] | 3 tests |
| 63 | notification_set_delete_timeout | [D] | 5 tests |
| 64 | notification_get_text_input_max_length | [D] | 3 tests |
| 65 | notification_post_with_event_cb_for_uid | [IPC] | null only |
| 66 | notification_post_with_event_cb | [IPC] | null only |
| 67 | notification_send_event | [P] | null+invalid |
| 68 | notification_send_event_by_priv_id | [P] | invalid type |
| 69 | notification_get_event_flag | [D] | 3 tests |
| 70 | notification_check_event_receiver_available | [P] | null only |
| 71 | notification_set_extention_data | [D] | null only |
| 72 | notification_set_extension_data | [D] | 4 tests |
| 73 | notification_get_extention_data | [D] | null only |
| 74 | notification_get_extension_data | [D] | 4 tests |
| 75 | notification_set_extension_event_handler | [D] | 5 tests |
| 76 | notification_get_extension_event_handler | [D] | 3 tests |
| 77 | notification_get_all_count_for_uid | [D] | 2 tests |
| 78 | notification_get_all_count | [D] | null test |
| 79 | notification_set_app_label | [D] | 4 tests |
| 80 | notification_get_app_label | [D] | 3 tests |
| 81 | notification_set_indirect_request | [D] | 3 tests |
| 82 | notification_delete_by_display_applist | [IPC] | guard + IPC-fail |
| 83 | notification_set_check_box | [D] | 5 tests |
| 84 | notification_get_check_box | [D] | 3 tests |
| 85 | notification_set_check_box_checked | [D] | 3 tests |
| 86 | notification_get_check_box_checked | [D] | 3 tests |
| 87 | notification_register_do_not_disturb_app | [P] | null only |
| 88 | notification_unregister_do_not_disturb_app | [IPC] | IPC-fail only |
| 89 | notification_set_pairing_type | [D] | 4 tests |
| 90 | notification_get_pairing_type | [D] | 3 tests |
| 91 | notification_set_channel_name | [D] | 5 tests |
| 92 | notification_get_channel_name | [D] | 3 tests |
| 93 | notification_channel_create | [D] | 2 tests |
| 94 | notification_channel_free | [D] | 2 tests |
| 95 | notification_channel_add | [D] | 2 tests |
| 96 | notification_channel_remove | [D] | 2 tests |
| 97 | notification_channel_update | [D] | 2 tests |
| 98 | notification_channel_get_by_name | [D] | 3 tests |
| 99 | notification_channel_set_blockable | [D] | 3 tests |
| 100 | notification_channel_get_blockable | [D] | 2 tests |
| 101 | notification_channel_set_block | [D] | 3 tests |
| 102 | notification_channel_get_block | [D] | 2 tests |
| 103 | notification_channel_get_name | [D] | 2 tests |
| 104 | notification_channel_clone | [D] | 3 tests |
| 105 | notification_channel_foreach | [D] | 2 tests |

---

## notification_noti.c — 24 functions (scenario lines 1882–2357)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | notification_noti_insert | [P] | null only; DB path needs sqlite mock |
| 2 | notification_noti_get_by_priv_id | [P] | null only |
| 3 | notification_noti_get_by_tag | [P] | null only |
| 4 | notification_noti_update | [P] | null only |
| 5 | notification_noti_delete_all | [P] | null only |
| 6 | notification_noti_delete_by_priv_id | [P] | null only |
| 7 | notification_noti_delete_by_priv_id_get_changes | [P] | null only |
| 8 | notification_noti_delete_by_display_applist | [P] | null only |
| 9 | notification_noti_get_count | [P] | null only |
| 10 | notification_noti_get_all_count | [P] | null only |
| 11 | notification_noti_get_grouping_list | [P] | null only |
| 12 | notification_noti_get_detail_list | [P] | null only |
| 13 | notification_noti_check_tag | [P] | null only |
| 14 | notification_noti_check_count_for_template | [P] | null only |
| 15 | notification_noti_add_template | [P] | null only |
| 16 | notification_noti_get_package_template | [P] | null only |
| 17 | notification_noti_delete_template | [P] | null only |
| 18 | notification_noti_init_data | [D] | smoke test |
| 19 | notification_noti_check_limit | [P] | null only |
| 20 | notification_noti_get_channel | [P] | null only |
| 21 | notification_noti_insert_channel | [P] | null only |
| 22 | notification_noti_delete_channel | [P] | null only |
| 23 | notification_noti_update_channel | [P] | null only |
| 24 | notification_noti_get_channel_list | [P] | null only |

---

## notification_setting.c — 50 functions (scenario lines 2357–2819)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | notification_setting_get_setting_array_for_uid | [D] | null test |
| 2 | notification_setting_get_setting_array | [D] | null test |
| 3 | notification_setting_get_setting_by_appid_for_uid | [D] | null test |
| 4 | notification_setting_get_setting_by_package_name | [D] | null test |
| 5 | notification_setting_get_setting | [D] | AUL-fail test |
| 6 | notification_setting_get_package_name | [D] | roundtrip |
| 7 | notification_setting_get_appid | [D] | roundtrip |
| 8 | notification_setting_get_allow_to_notify | [D] | roundtrip |
| 9 | notification_setting_set_allow_to_notify | [D] | roundtrip |
| 10 | notification_setting_get_do_not_disturb_except | [D] | roundtrip |
| 11 | notification_setting_set_do_not_disturb_except | [D] | roundtrip |
| 12 | notification_setting_get_visibility_class | [D] | roundtrip |
| 13 | notification_setting_set_visibility_class | [D] | roundtrip |
| 14 | notification_setting_get_pop_up_notification | [D] | roundtrip |
| 15 | notification_setting_set_pop_up_notification | [D] | roundtrip |
| 16 | notification_setting_get_lock_screen_content | [D] | roundtrip |
| 17 | notification_setting_set_lock_screen_content | [D] | roundtrip |
| 18 | notification_setting_get_app_disabled | [D] | roundtrip |
| 19 | notification_setting_update_setting_for_uid | [D] | null test |
| 20 | notification_setting_update_setting | [D] | null test |
| 21 | notification_setting_free_notification | [D] | null test |
| 22 | notification_setting_refresh_setting_table | [D] | DB-fail test |
| 23 | notification_setting_insert_package_for_uid | [D] | DB-fail test |
| 24 | notification_setting_delete_package_for_uid | [D] | DB-fail test |
| 25 | notification_system_setting_load_system_setting_for_uid | [D] | null test |
| 26 | notification_system_setting_load_system_setting | [D] | null test |
| 27 | notification_system_setting_update_system_setting_for_uid | [D] | null test |
| 28 | notification_system_setting_update_system_setting | [D] | null test |
| 29 | notification_system_setting_free_system_setting | [D] | null test |
| 30 | notification_system_setting_get_do_not_disturb | [D] | roundtrip |
| 31 | notification_system_setting_set_do_not_disturb | [D] | roundtrip |
| 32 | notification_system_setting_get_visibility_class | [D] | roundtrip |
| 33 | notification_system_setting_set_visibility_class | [D] | roundtrip |
| 34 | notification_system_setting_dnd_schedule_get_enabled | [D] | roundtrip |
| 35 | notification_system_setting_dnd_schedule_set_enabled | [D] | roundtrip |
| 36 | notification_system_setting_dnd_schedule_get_day | [D] | roundtrip |
| 37 | notification_system_setting_dnd_schedule_set_day | [D] | roundtrip |
| 38 | notification_system_setting_dnd_schedule_get_start_time | [D] | roundtrip |
| 39 | notification_system_setting_dnd_schedule_set_start_time | [D] | roundtrip |
| 40 | notification_system_setting_dnd_schedule_get_end_time | [D] | roundtrip |
| 41 | notification_system_setting_dnd_schedule_set_end_time | [D] | roundtrip |
| 42 | notification_system_setting_get_lock_screen_content | [D] | roundtrip |
| 43 | notification_system_setting_set_lock_screen_content | [D] | roundtrip |
| 44 | notification_system_setting_get_dnd_allow_exceptions | [D] | roundtrip |
| 45 | notification_system_setting_set_dnd_allow_exceptions | [D] | roundtrip |
| 46 | notification_register_system_setting_dnd_changed_cb_for_uid | [D] | null test |
| 47 | notification_register_system_setting_dnd_changed_cb | [D] | null test |
| 48 | notification_unregister_system_setting_dnd_changed_cb_for_uid | [D] | null test |
| 49 | notification_unregister_system_setting_dnd_changed_cb | [D] | null test |
| 50 | notification_system_setting_init_system_setting_table | [D] | DB-fail test |

---

## notification_setting_service.c — 13 functions (scenario lines 2819–3068)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | noti_setting_service_get_setting_by_app_id | [D] | null test |
| 2 | noti_setting_get_setting_array | [D] | null test |
| 3 | noti_system_setting_load_system_setting | [D] | null test |
| 4 | notification_setting_db_update | [D] | null-guard tests |
| 5 | notification_setting_db_update_system_setting | [D] | DB-fail test |
| 6 | notification_setting_db_update_do_not_disturb | [D] | DB-fail test |
| 7 | notification_system_setting_get_dnd_schedule_enabled_uid | [D] | DB-fail test |
| 8 | notification_get_dnd_and_allow_to_notify | [D] | null-guard test |
| 9 | notification_system_setting_load_dnd_allow_exception | [D] | null-guard test |
| 10 | notification_system_setting_update_dnd_allow_exception | [D] | DB-fail test |
| 11 | noti_system_setting_get_do_not_disturb | [D] | DB-fail test |
| 12 | notification_setting_db_update_app_disabled | [D] | null-guard test |
| 13 | notification_setting_db_update_pkg_disabled | [D] | null-guard test |

---

## notification_db.c — 7 functions (scenario lines 3092–3172)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1 | notification_db_init | [P] | LCOV_EXCL |
| 2 | notification_db_open | [P] | basic |
| 3 | notification_db_close | [D] | null tests |
| 4 | notification_db_exec | [P] | basic |
| 5 | notification_db_column_text | [P] | basic |
| 6 | notification_db_column_bundle | [P] | basic |
| 7 | notification_upgrade_db | [P] | basic |

---

## notification_list.c — 21 functions + notification_shared_file.c — 6 functions (scenario lines 3179–3395)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 8 | notification_list_get_head | [P] | basic |
| 9 | notification_list_get_tail | [P] | basic |
| 10 | notification_list_get_prev | [P] | basic |
| 11 | notification_list_get_next | [P] | basic |
| 12 | notification_list_get_data | [P] | basic |
| 13 | notification_list_get_count | [P] | basic |
| 14 | notification_list_append | [P] | basic |
| 15 | notification_list_remove | [P] | basic |
| 16 | notification_get_list_for_uid | [P] | null |
| 17 | notification_get_list | [P] | null |
| 18 | notification_get_list_by_page_for_uid | [P] | null+invalid |
| 19 | notification_get_list_by_page | [P] | null+invalid |
| 20 | notification_get_detail_list_for_uid | [P] | null |
| 21 | notification_get_detail_list | [P] | null |
| 22 | notification_free_list | [D] | null test |
| 23 | notification_remove_private_sharing_target_id | [D] | smoke test |
| 24 | notification_add_private_sharing_target_id | [D] | smoke test |
| 25 | notification_validate_private_sharing | [D] | smoke test |
| 26 | notification_calibrate_private_sharing | [D] | smoke test |
| 27 | notification_set_private_sharing | [D] | null-guard test |
| 28 | notification_remove_private_sharing | [D] | smoke test |

---

## Misc files (scenario lines 3425–3891)

| # | Function | Status | Notes |
|---|----------|--------|-------|
| 1.1 | notification_error_quark | [D] | 5 tests |
| 2.1 | notification_ipc_make_gvariant_from_noti | [D] | smoke + roundtrip |
| 2.2 | notification_ipc_make_noti_from_gvariant | [D] | roundtrip |
| 3.1 | notification_ongoing_update_cb_set | [D] | 7 tests |
| 3.2 | notification_ongoing_update_cb_unset | [D] | 3 tests |
| 4.1 | notification_status_monitor_message_cb_set | [D] | null test |
| 4.2 | notification_status_monitor_message_cb_unset | [D] | null test |
| 4.3 | notification_status_message_post | [D] | null test |
| 5.1 | notification_init_default_viewer | [D] | smoke test |
| 5.2 | notification_launch_default_viewer | [D] | null-viewer path |
| 5.3 | notification_launch_default_viewer_without_candidate_process | [D] | null-viewer path |
| 6.1 | make_empty_notification | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.2 | make_notification_from_noti | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.3 | make_noti_from_notification | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.4 | make_setting_from_noti_system_setting | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.5 | make_dnd_allow_exception_from_exception | [D] | null-guard tests (N1/N2/N3) |
| 6.6 | make_noti_system_setting_from_setting | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.7 | make_setting_from_noti_setting | [P] | compile-check stub; TIDL infra out-of-scope |
| 6.8 | make_noti_setting_from_setting | [P] | compile-check stub; TIDL infra out-of-scope |

---

## Summary
- DONE [D]: ~155 functions
- PARTIAL [P]: ~49 functions  
- IPC path needed [IPC]: ~15 functions (rpc_port_mock.hh/cc ready)
- TODO [ ]: ~7 functions (remaining internal_tidl stubs needed)
- Tests: 767 (commit 7e1746f — batches 20-27; all notification_test_scenario.md functions covered)

## Batch schedule (2 functions each)
- Infra commit (pending) → rpc_port_mock + test_notification_internal pending
- **Batch 1**: notification_post + notification_update [IPC]
- **Batch 2**: notification_delete_all + notification_delete [IPC]
- **Batch 3**: notification_load_by_tag + notification_save_as_template [IPC]
- **Batch 4**: notification_create_from_template + notification_get_noti_block_state [IPC]
- **Batch 5**: notification_translate_localized_text + notification_delete_group_by_group_id
- **Batch 6**: notification_clear + notification_delete_all_by_type
- **Batch 7**: notification_load + notification_is_service_ready
- **Batch 8**: notification_update_for_uid + notification_delete_for_uid [IPC variants]
- **Batch 9**: notification_create_from_package_template + notification_delete_by_display_applist
- **Batch 10**: notification_unregister_do_not_disturb_app + notification_setting_get_setting
- **Batch 11**: notification_setting_refresh_setting_table + notification_setting_insert_package_for_uid [DB]
- **Batch 12**: notification_setting_db_update + notification_setting_db_update_system_setting [DB]
- **Batch 13**: ipc_make_gvariant_from_noti + ipc_make_noti_from_gvariant
- **Batch 14**: viewer functions (5.1–5.3)
- **Batch 15–18**: internal_tidl functions (6.1–6.8, 2 per batch)
- **Batch 19**: notification_noti_init_data + private_sharing functions
- **Batch 20+**: remaining noti/setting_service DB paths (need sqlite mock)
