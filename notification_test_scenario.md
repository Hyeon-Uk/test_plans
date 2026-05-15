# notification — Test Scenario Inventory

`notification_api_list.md` 에 등재된 **`notification.c` 계열 `EXPORT_API` export 사이트** 각각에
대한 test scenario. `test-scenario-generator` 스킬의 Phase 3 양식을 압축형으로 적용.

> 참고: 본 문서는 원래 notification-ex 모듈(C++ 헤더 43 classes, stub.cc C ABI 183 entries)도
> 포함하고 있었으나, 해당 부분은 별도 관리로 분리되어 본 문서에서 제외되었습니다.
> 현재 다루는 범위: **notification.c 계열 + DB/Settings/list/shared_file/misc** 만.

표기 규약:
- `[P]` Success path
- `[N]` Failure path (각 distinct return / errno predicate 별 1행)
- `[E]` Edge / boundary value
- `[C]` Corner case (state / ordering / re-entrancy)
- `T_xxx` 반복 패턴 템플릿 — chunks 안에서 정의/참조

graphify 분석: `notification/graphify-out/GRAPH_REPORT.md` 참조.

분량 때문에 **5 개 chunk** 로 나뉘어 작성되었음. Chunk 목차:

| § | Chunk | 대상 파일 | API 수 |
|---|-------|----------|------:|
| 3 | Public C API | `src/notification/src/notification.c` | 57 |
| 4 | Internal C API | `src/notification/src/notification_internal.c` | 105 |
| 5 | DB & Settings | `notification_noti.c` (24) + `notification_setting.c` (50) + `notification_setting_service.c` (13) | 87 |
| 6 | DB primitives & list & shared file | `notification_db.c` (7) + `notification_list.c` (15) + `notification_shared_file.c` (6) | 28 |
| 7 | 기타 작은 파일들 | error/ipc/ongoing/status/viewer/internal_tidl | 19 |
| **합계** | | | **296** |

각 chunk 는 자체 coverage check 와 open question 목록을 가짐.

---

# Test Scenarios — `src/notification/src/notification.c` (57 EXPORT_API)

## Common templates (referenced below)

### Template T_SIMPLE_SET — trivial mutator
A setter of the shape: `if (noti == NULL) return INVALID_PARAMETER; noti->field = value; return NONE;`
Scenarios:
- [P1] valid handle + value → NONE; verify `noti->field` mutated.
- [N1] `noti == NULL` → INVALID_PARAMETER.

### Template T_SIMPLE_GET — trivial accessor
A getter of the shape: `if (noti == NULL || out == NULL) return INVALID_PARAMETER; *out = noti->field; return NONE;`
Scenarios:
- [P1] valid handle + non-NULL out → NONE; `*out` matches stored field.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `out == NULL` → INVALID_PARAMETER.

### Template T_FOR_UID_DELEGATE — `_for_uid` thin wrapper
Body is `return notification_X_for_uid(noti, aul_getuid());`.
Scenarios:
- [P1] delegation → all return codes are propagated from `_for_uid` variant; uid = `aul_getuid()`.
  See scenarios for the corresponding `_for_uid` function for full errno coverage.

---

### `int notification_set_image(notification_h noti, notification_image_type_e type, const char *image_path)` — L96
**Errno map:**
| Return | Predicate (source line) |
| NOTIFICATION_ERROR_NONE | success or `image_path==NULL` with no prior bundle | L125, L153 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or type out of (NONE, MAX] | L107, L111 |

**Scenarios:**
- [P1] valid `noti`, type ICON, non-NULL path, no prior bundle → NONE; `noti->b_image_path` created with key `"<type>"=path`.
- [P2] valid `noti`, type ICON, non-NULL path, prior bundle had same key → NONE; old entry deleted then re-added.
- [P3] valid `noti`, type ICON, `image_path == NULL`, no prior bundle → NONE; bundle NOT created (early return).
- [P4] valid `noti`, type ICON, `image_path == NULL`, prior bundle had key → NONE; that key removed.
- [P5] `priv_path` returned non-NULL by `notification_check_file_path_is_private` → entry pushed into `b_priv_image_path`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `type == NOTIFICATION_IMAGE_TYPE_NONE` → INVALID_PARAMETER (boundary).
- [N3] `type > NOTIFICATION_IMAGE_TYPE_MAX` → INVALID_PARAMETER.
- [E1] empty string `""` for image_path → NONE; entry stored verbatim.
- [C1] called repeatedly with different image_types → bundle accumulates multiple keys.

### `int notification_get_image(notification_h noti, notification_image_type_e type, char **image_path)` — L156
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | always on valid args | L193 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `image_path==NULL`, or type out of range | L165, L169 |

**Scenarios:**
- [P1] handle has `b_image_path` with key for type → NONE; `*image_path` points into bundle.
- [P2] `b_image_path == NULL`, type == ICON, `app_icon_path` set → NONE; `*image_path == app_icon_path`.
- [P3] `b_image_path == NULL`, type != ICON → NONE; `*image_path == NULL`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `image_path == NULL` → INVALID_PARAMETER.
- [N3] `type == 0` (NONE) → INVALID_PARAMETER.
- [N4] `type > MAX` → INVALID_PARAMETER.
- [E1] bundle exists but no key for the requested type → NONE; `*image_path == NULL` (or app_icon fallback for ICON).

### `int notification_set_time(notification_h noti, time_t input_time)` — L196
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L206 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L199 |

**Scenarios:**
- [P1] `input_time > 0` → NONE; `noti->time == input_time`.
- [P2] `input_time == 0` → NONE; `noti->time == time(NULL)` (current time).
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [E1] negative time_t (e.g. -1) → still stored as-is (no validation other than 0 sentinel).

### `int notification_get_time(notification_h noti, time_t *ret_time)` — L209
T_SIMPLE_GET on `noti->time`.

### `int notification_get_insert_time(notification_h noti, time_t *ret_time)` — L219
T_SIMPLE_GET on `noti->insert_time`.

### `int notification_set_text(notification_h noti, notification_text_type_e type, const char *text, const char *key, int args_type, ...)` — L230
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L440 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, type out of (NONE, MAX], or unknown variable type in vararg list | L249, L253, L415 |

**Scenarios:**
- [P1] `text` non-NULL, `key`==NULL, no varargs (`NOTIFICATION_VARIABLE_TYPE_NONE`) → NONE; `b_text[type]=text`, `num_format_args=0`.
- [P2] `text==NULL` and previous `b_text` has key → NONE; existing entry removed.
- [P3] `key` non-NULL → NONE; `b_key[type]=key`; new bundle created if absent.
- [P4] var-arg `TYPE_INT` → NONE; stored as `<type>type<n>=1`, `<type>value<n>=<int>`.
- [P5] var-arg `TYPE_DOUBLE` → stored as `%.2f` formatted value.
- [P6] var-arg `TYPE_STRING` → stored.
- [P7] var-arg `TYPE_COUNT` → stored with count pos.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `type <= NOTIFICATION_TEXT_TYPE_NONE` → INVALID_PARAMETER.
- [N3] `type > NOTIFICATION_TEXT_TYPE_MAX` → INVALID_PARAMETER.
- [N4] unknown `var_type` in vararg list → return value is INVALID_PARAMETER, `num_format_args` set to 0.
- [E1] `text` longer than `NOTI_TEXT_RESULT_LEN` → truncated via snprintf (no error).
- [E2] both `text==NULL` and `key==NULL` and `args_type==NONE` → NONE (no-op except b_format_args bookkeeping).
- [C1] called repeatedly with same type → previous value replaced.
- [C2] format arg list mixed (INT,STRING,DOUBLE) → all stored sequentially; `num_format_args` matches count.

### `int notification_get_text(notification_h noti, notification_text_type_e type, char **text)` — L443
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success or no text found | L510, L527, L790 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `text==NULL`, or type out of (NONE, MAX] | L462, L466 |

**Scenarios:**
- [P1] `b_text` has plain text for type, no format args → NONE; `*text` points to bundle string.
- [P2] `b_key` set + `domain/dir` set → NONE; returns `dgettext(domain, key)` result; falls back to system catalog if dgettext returns same pointer.
- [P3] `b_key` only (no domain) → NONE; `dgettext("sys_string", key)`.
- [P4] `is_translation == true` and got a base string → NONE; bypass format expansion.
- [P5] format args present with `%d` token → NONE; result_str built with int substitution; written to `temp_title`/`temp_content`.
- [P6] format token `%s` translated through dgettext → NONE; concatenated.
- [P7] format token `%f` → NONE; printed as `%.2f`.
- [P8] indexed token `%1$d`/`%2$s`/`%3$f` → NONE; correct arg index used.
- [P9] `TYPE_COUNT` with LEFT pos prefixes count, RIGHT pos suffixes.
- [P10] no text at all (no `b_text`, no `b_key`) → NONE; `*text == NULL`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `text == NULL` → INVALID_PARAMETER.
- [N3] `type <= NONE` → INVALID_PARAMETER.
- [N4] `type > MAX` → INVALID_PARAMETER.
- [E1] format string longer than `NOTI_TEXT_RESULT_LEN` → buffer is truncated, WARN emitted, no error.
- [E2] `%%` literal in template → single `%` written.
- [C1] called twice on TITLE → `temp_title` freed & reallocated.

### `int notification_set_text_domain(notification_h noti, const char *domain, const char *dir)` — L793
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L810 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti`, `domain`, or `dir` NULL | L797 |

**Scenarios:**
- [P1] valid args, no prior domain/dir → NONE; both strdup'd into handle.
- [P2] called twice → previous domain/dir freed before strdup.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `domain == NULL` → INVALID_PARAMETER.
- [N3] `dir == NULL` → INVALID_PARAMETER.
- [E1] empty strings → NONE; stored verbatim.
- [C1] strdup OOM → not handled (potential undefined; no return code path). Document as open question.

### `int notification_get_text_domain(notification_h noti, char **domain, char **dir)` — L813
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | always when noti != NULL | L826 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L818 |

**Scenarios:**
- [P1] both pointers non-NULL and fields set → NONE; both filled.
- [P2] only `domain` requested (dir NULL) → NONE; only domain written.
- [P3] only `dir` requested → NONE.
- [P4] both pointers non-NULL but stored fields are NULL → NONE; output pointers untouched (caller responsible for init).
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [E1] both `domain` and `dir` NULL → NONE; no-op.

### `int notification_set_time_to_text(notification_h noti, notification_text_type_e type, time_t time)` — L829
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success (delegates to `notification_set_text`) | L849 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `time<=0`, or type out of range | L837, L841 |
| (other) | return from `notification_noti_set_tag` propagated | L847 |
| (other) | return from `notification_set_text` propagated | L849 |

**Scenarios:**
- [P1] valid args → NONE; calls set_text with `<TIME>...</TIME>` tagged string.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `time == 0` → INVALID_PARAMETER.
- [N3] `time < 0` → INVALID_PARAMETER.
- [N4] type out of (NONE, MAX] → INVALID_PARAMETER.
- [N5] `notification_noti_set_tag` returns non-NONE (buf_tag too small) → that errno propagated.
- [C1] downstream `notification_set_text` errno propagated.

### `int notification_get_time_from_text(notification_h noti, notification_text_type_e type, time_t *time)` — L852
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L880 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`/`time==NULL`/range/`get_text` failed/`ret_text==NULL`/tag invalid/strip returned NULL | L860, L864, L868, L871, L875 |

**Scenarios:**
- [P1] valid handle with TIME-tagged text → NONE; `*time = atol(stripped)`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `time == NULL` → INVALID_PARAMETER.
- [N3] type out of range → INVALID_PARAMETER.
- [N4] `notification_get_text` returned error → INVALID_PARAMETER.
- [N5] `notification_get_text` returned NONE but `ret_text == NULL` → INVALID_PARAMETER.
- [N6] text exists but `notification_noti_get_tag_type == TAG_TYPE_INVALID` (no TIME tag) → INVALID_PARAMETER.
- [N7] `notification_noti_strip_tag` returns NULL → INVALID_PARAMETER.
- [E1] tag value is non-numeric → `atol == 0`; succeeds with `*time = 0`.

### `int notification_set_sound(notification_h noti, notification_sound_type_e type, const char *path)` — L883
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L929 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, type out of [NONE..MAX], or type==USER_DATA with NULL path | L890, L894, L925 |

**Scenarios:**
- [P1] type DEFAULT (or non-user-data), any path → NONE; `sound_path` cleared, `sound_type` set.
- [P2] type USER_DATA with valid path → NONE; `sound_path = strdup(path)`, priv path set if applicable.
- [P3] called twice (USER_DATA, USER_DATA) → previous `sound_path`/`priv_sound_path` freed.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `type < NONE` → INVALID_PARAMETER.
- [N3] `type > MAX` → INVALID_PARAMETER.
- [N4] type == USER_DATA + `path == NULL` → INVALID_PARAMETER; `sound_type` reset to DEFAULT.
- [E1] empty path string + USER_DATA → NONE (strdup of "" succeeds).

### `int notification_get_sound(notification_h noti, notification_sound_type_e *type, const char **path)` — L932
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L946 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `type==NULL` | L937 |

**Scenarios:**
- [P1] valid args, sound type USER_DATA → NONE; `*type` set, `*path` set if path arg given.
- [P2] non-USER_DATA → NONE; `*path` left untouched.
- [P3] `path == NULL` and USER_DATA → NONE; only `*type` written.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `type == NULL` → INVALID_PARAMETER.

### `int notification_set_vibration(notification_h noti, notification_vibration_type_e type, const char *path)` — L949
Mirror of `notification_set_sound`. Same errno map and scenario template.

**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L995 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, type out of [NONE..MAX], USER_DATA with NULL path | L956, L960, L991 |

**Scenarios:** [P1]–[P3], [N1]–[N4], [E1] as in `notification_set_sound`, against `vibration_path`/`priv_vibration_path`.

### `int notification_get_vibration(notification_h noti, notification_vibration_type_e *type, const char **path)` — L998
Mirror of `notification_get_sound` on `vibration_*` fields. Same errnos: NONE / INVALID_PARAMETER. Scenarios as above.

### `int notification_set_led(notification_h noti, notification_led_op_e operation, int led_argb)` — L1014
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1031 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or operation out of [OFF..MAX] | L1019, L1023 |

**Scenarios:**
- [P1] op == ON_CUSTOM_COLOR → NONE; both `led_operation` and `led_argb` stored.
- [P2] op == OFF/ON_DEFAULT_COLOR → NONE; `led_argb` ignored.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] op < OFF → INVALID_PARAMETER.
- [N3] op > MAX → INVALID_PARAMETER.
- [E1] led_argb == 0 with ON_CUSTOM_COLOR → NONE; stored.

### `int notification_get_led(notification_h noti, notification_led_op_e *operation, int *led_argb)` — L1034
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1048 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `operation==NULL` | L1038 |

**Scenarios:**
- [P1] operation set, current op is ON_CUSTOM_COLOR, `led_argb != NULL` → NONE; both written.
- [P2] current op != ON_CUSTOM_COLOR → NONE; `led_argb` left untouched.
- [P3] `led_argb == NULL` with ON_CUSTOM_COLOR → NONE; only operation written.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `operation == NULL` → INVALID_PARAMETER.

### `int notification_set_led_time_period(notification_h noti, int on_ms, int off_ms)` — L1051
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1060 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `on_ms<0` or `off_ms<0` | L1054 |

**Scenarios:**
- [P1] positive values → NONE; both stored.
- [P2] zero values → NONE; stored.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `on_ms < 0` → INVALID_PARAMETER.
- [N3] `off_ms < 0` → INVALID_PARAMETER.

### `int notification_get_led_time_period(notification_h noti, int *on_ms, int *off_ms)` — L1063
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | always when noti != NULL | L1074 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L1067 |

**Scenarios:**
- [P1] both pointers non-NULL → NONE; both written.
- [P2] only `on_ms` non-NULL → NONE; only it written.
- [P3] both pointers NULL → NONE; no-op.
- [N1] `noti == NULL` → INVALID_PARAMETER.

### `int notification_set_launch_option(notification_h noti, notification_launch_option_type type, void *option)` — L1077
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1103 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `option==NULL`, type != APP_CONTROL, or `app_control_export_as_bundle` failed | L1086, L1093 |
| (other) | propagated from `notification_set_execute_option` | L1097/L1103 |

**Scenarios:**
- [P1] valid app_control handle → NONE; delegates to `notification_set_execute_option(SINGLE_LAUNCH)`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `option == NULL` → INVALID_PARAMETER.
- [N3] `type != NOTIFICATION_LAUNCH_OPTION_APP_CONTROL` → INVALID_PARAMETER.
- [N4] `app_control_export_as_bundle` returns non-NONE → INVALID_PARAMETER.
- [C1] downstream `notification_set_execute_option` errno propagated.

### `int notification_get_launch_option(notification_h noti, notification_launch_option_type type, void *option)` — L1106
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1150 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `option==NULL`, or type mismatch | L1115, L1118 |
| NOTIFICATION_ERROR_IO_ERROR | app_control_create or app_control_import_from_bundle failed | L1134, L1140 |
| (other) | return from `notification_get_execute_option` propagated when it != NONE | L1146 |

**Scenarios:**
- [P1] noti has a SINGLE_LAUNCH execute option → NONE; imports bundle into new `app_control_h`, `*option` set.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `option == NULL` → INVALID_PARAMETER.
- [N3] `type != APP_CONTROL` → INVALID_PARAMETER.
- [N4] `notification_get_execute_option` returns non-NONE or `b == NULL` → that errno propagated (LCOV_EXCL).
- [N5] `app_control_create` failed → IO_ERROR.
- [N6] `app_control_import_from_bundle` failed → IO_ERROR (app_control_new destroyed).

### `int notification_set_event_handler(notification_h noti, notification_event_type_e event_type, app_control_h event_handler)` — L1153
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1183 (via err init) |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or event_type out of [CLICK_ON_BUTTON_1..MAX] | L1159, L1167 |
| (other) | `app_control_export_as_bundle` error returned verbatim | L1173 |

**Scenarios:**
- [P1] valid args, no prior bundle for slot → NONE; `b_event_handler[event_type]` set.
- [P2] valid args, prior bundle present → NONE; old bundle freed, new one stored.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `event_type < CLICK_ON_BUTTON_1` → INVALID_PARAMETER.
- [N3] `event_type > MAX` → INVALID_PARAMETER.
- [N4] `app_control_export_as_bundle(event_handler, &b)` fails (including when `event_handler == NULL`) → its error code propagated.
- [C1] event_handler NULL → app_control_export error propagated.

### `int notification_get_event_handler(notification_h noti, notification_event_type_e event_type, app_control_h *event_handler)` — L1186
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1226+L1242 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL`, `event_handler==NULL`, event_type out of range | L1193, L1202 |
| NOTIFICATION_ERROR_NOT_EXIST_ID | `b_event_handler[event_type] == NULL` | L1211 |
| NOTIFICATION_ERROR_IO_ERROR | `app_control_create`/`import` failed | L1220, L1233 |

**Scenarios:**
- [P1] handler present → NONE; new app_control built and returned.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `event_handler == NULL` → INVALID_PARAMETER.
- [N3] event_type out of range → INVALID_PARAMETER.
- [N4] slot empty → NOT_EXIST_ID.
- [N5] `app_control_create` failure → IO_ERROR.
- [N6] `app_control_import_from_bundle` failure → IO_ERROR; app_control_new destroyed.
- [C1] On any failure after the slot exists, output `*event_handler` is set to NULL via the `out:` cleanup.

### `int notification_set_property(notification_h noti, int flags)` — L1245
T_SIMPLE_SET on `noti->flags_for_property`.

### `int notification_get_property(notification_h noti, int *flags)` — L1256
T_SIMPLE_GET on `noti->flags_for_property`.

### `int notification_set_display_applist(notification_h noti, int applist)` — L1267
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1278 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L1271 |

**Scenarios:**
- [P1] applist `0xffffffff` → NONE; remapped to `NOTIFICATION_DISPLAY_APP_ALL`.
- [P2] regular bitmask → NONE; stored verbatim.
- [N1] `noti == NULL` → INVALID_PARAMETER.

### `int notification_get_display_applist(notification_h noti, int *applist)` — L1281
T_SIMPLE_GET on `noti->display_applist`.

### `int notification_set_size(notification_h noti, double size)` — L1292
T_SIMPLE_SET on `noti->progress_size`. No range validation — any double accepted (including negatives, NaN).

### `int notification_get_size(notification_h noti, double *size)` — L1303
T_SIMPLE_GET on `noti->progress_size`.

### `int notification_set_progress(notification_h noti, double percentage)` — L1314
T_SIMPLE_SET on `noti->progress_percentage`. No range validation.

### `int notification_get_progress(notification_h noti, double *percentage)` — L1325
T_SIMPLE_GET on `noti->progress_percentage`.

### `int notification_get_pkgname(notification_h noti, char **pkgname)` — L1336
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1347 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `pkgname==NULL` | L1340 |

**Scenarios:**
- [P1] `caller_app_id` set → NONE; `*pkgname = caller_app_id` (alias, not strdup).
- [P2] `caller_app_id == NULL` → NONE; `*pkgname = NULL`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `pkgname == NULL` → INVALID_PARAMETER.

### `int notification_set_layout(notification_h noti, notification_ly_type_e layout)` — L1350
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1358 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or layout out of [NONE..MAX] | L1353 |

**Scenarios:**
- [P1] layout in range → NONE.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `layout < NOTIFICATION_LY_NONE` → INVALID_PARAMETER.
- [N3] `layout > NOTIFICATION_LY_MAX` → INVALID_PARAMETER.

### `int notification_get_layout(notification_h noti, notification_ly_type_e *layout)` — L1361
T_SIMPLE_GET on `noti->layout`.

### `int notification_get_type(notification_h noti, notification_type_e *type)` — L1372
T_SIMPLE_GET on `noti->type`.

### `int notification_post(notification_h noti)` — L1383
T_FOR_UID_DELEGATE → `notification_post_for_uid(noti, aul_getuid())`. See scenarios for `_for_uid` variant for full errno coverage (including PERMISSION_DENIED, FROM_DB, IO_ERROR, SERVICE_NOT_READY).

### `int notification_update(notification_h noti)` — L1388
T_FOR_UID_DELEGATE → `notification_update_for_uid(noti, aul_getuid())`. See `_for_uid` for full errno set.

### `int notification_delete_all(notification_type_e type)` — L1393
T_FOR_UID_DELEGATE → `notification_delete_all_for_uid(type, aul_getuid())`. See `_for_uid` for full errno set.

### `int notification_delete(notification_h noti)` — L1398
T_FOR_UID_DELEGATE → `notification_delete_for_uid(noti, aul_getuid())`. See `_for_uid` for full errno set.

### `notification_h notification_create(notification_type_e type)` — L1631
Thin wrapper over `_notification_create(type)`.
**Errno map (via `set_last_result`, return is `notification_h` not int):**
| Return | Predicate |
| non-NULL handle, last_result = NONE | success | L1620 |
| NULL, last_result = INVALID_PARAMETER | type out of (NONE..MAX] | L1473–L1477 |
| NULL, last_result = OUT_OF_MEMORY | calloc failed | L1480–L1485 |
| NULL, last_result = IO_ERROR | caller_app_id lookup / pkg_id strdup / etc. failed | L1615–L1618 |

**Scenarios:**
- [P1] type NOTI → non-NULL; layout = NOTI_EVENT_SINGLE; defaults applied (auto_remove=true, etc.).
- [P2] type ONGOING → non-NULL; layout = ONGOING_PROGRESS.
- [N1] `type == NOTIFICATION_TYPE_NONE` → NULL, last_result = INVALID_PARAMETER.
- [N2] `type > MAX` → NULL, last_result = INVALID_PARAMETER.
- [N3] calloc failure (LCOV_EXCL) → NULL, last_result = OUT_OF_MEMORY.
- [N4] `notification_get_app_id_by_pid` returns NULL → NULL, last_result = IO_ERROR.
- [N5] aul_app_get_pkgid_bypid failure followed by `strdup(caller_app_id)` failure → IO_ERROR.
- [E1] regular UID path with successful package_info / appinfo lookup → fields domain, dir, app_label set.
- [C1] Second call with same uid uses cached `_pkg_id`, `_locale_directory`, `_label`.

### `notification_h notification_load_by_tag(const char *tag)` — L1636
T_FOR_UID_DELEGATE → `notification_load_by_tag_for_uid(tag, aul_getuid())`. See `_for_uid` for full errno set (INVALID_PARAMETER for NULL tag, FROM_DB, NOT_EXIST_ID).

### `int notification_clone(notification_h noti, notification_h *clone)` — L1641
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1773 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `clone==NULL` | L1648 |
| NOTIFICATION_ERROR_OUT_OF_MEMORY | calloc failed | L1655 |

**Scenarios:**
- [P1] full source handle → NONE; all scalar fields copied, all bundles `bundle_dup`'d, all strings `strdup`'d.
- [P2] source has NULL pkg_id/caller_app_id/launch_app_id/args/etc. → NONE; corresponding new fields stay NULL.
- [P3] `b_event_handler[]` slots: some NULL, some set → only set slots duplicated.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `clone == NULL` → INVALID_PARAMETER.
- [N3] calloc failure (LCOV_EXCL) → OUT_OF_MEMORY.
- [C1] Caller frees clone with `notification_free` → no double-free of source.
- [C2] strdup OOM mid-way → fields silently NULL; current code does not roll back (open question).

### `int notification_free(notification_h noti)` — L1776
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1872 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L1783 |

**Scenarios:**
- [P1] fully-populated handle → NONE; every owned pointer (pkg_id, caller_app_id, launch_app_id, args, group_args, b_execute_option, b_service_*, b_event_handler[], b_image_path, b_priv_image_path, sound/vibration paths, domain, dir, b_text, b_key, b_format_args, app_icon_path, app_label, temp_title, temp_content, tag, channel_name) freed, then noti itself.
- [P2] zero-initialised handle (e.g. clone of empty struct) → NONE; no crash, all NULL checks short-circuit.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [C1] double-free guard: caller's responsibility — no internal sentinel; calling twice = UB.
- [C2] every `b_event_handler[i]` for i in [0..MAX] inspected.

### `int notification_set_tag(notification_h noti, const char *tag)` — L1875
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1887 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L1878 |

**Scenarios:**
- [P1] non-NULL tag, no prior tag → NONE; `noti->tag = strdup(tag)`.
- [P2] non-NULL tag, prior tag exists → NONE; old tag freed first.
- [P3] `tag == NULL` → NONE; no-op (prior tag kept).
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [E1] empty string tag "" → NONE; stored.

### `int notification_get_tag(notification_h noti, const char **tag)` — L1890
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1896 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` | L1893 |

**Scenarios:**
- [P1] valid args, tag set → NONE; `*tag` aliases `noti->tag`.
- [P2] valid args, tag is NULL inside handle → NONE; `*tag = NULL`.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [C1] `tag == NULL` (out-pointer) — code dereferences without checking → potential SEGV (open question, NOT guarded).

### `int notification_set_ongoing_flag(notification_h noti, bool ongoing_flag)` — L1907
T_SIMPLE_SET on `noti->ongoing_flag`.

### `int notification_get_ongoing_flag(notification_h noti, bool *ongoing_flag)` — L1917
T_SIMPLE_GET on `noti->ongoing_flag`.

### `int notification_add_button(notification_h noti, notification_button_index_e button_index)` — L1927
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1934 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or button_index not in [BUTTON_1..6] ∪ [BUTTON_7..10] | L1929 |

**Scenarios:**
- [P1] BUTTON_1..BUTTON_6 → NONE.
- [P2] BUTTON_7..BUTTON_10 → NONE.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] button index below BUTTON_1 → INVALID_PARAMETER.
- [N3] button index between BUTTON_6 and BUTTON_7 (gap) → INVALID_PARAMETER.
- [N4] button index above BUTTON_10 → INVALID_PARAMETER.
- [C1] Function is currently a validation-only no-op (does not actually allocate a slot — note in docs).

### `int notification_remove_button(notification_h noti, notification_button_index_e button_index)` — L1937
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L1949 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or index out of supported ranges | L1939 |

**Scenarios:**
- [P1] index valid, `b_event_handler[index-1]` present → NONE; bundle freed and slot cleared.
- [P2] index valid, slot already NULL → NONE; no-op.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] index in gap (BUTTON_6+1..BUTTON_7-1) → INVALID_PARAMETER.
- [N3] index < BUTTON_1 or > BUTTON_10 → INVALID_PARAMETER.

### `int notification_set_auto_remove(notification_h noti, bool auto_remove)` — L1952
T_SIMPLE_SET on `noti->auto_remove`.

### `int notification_get_auto_remove(notification_h noti, bool *auto_remove)` — L1962
T_SIMPLE_GET on `noti->auto_remove`.

### `int notification_save_as_template(notification_h noti, const char *template_name)` — L1972
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | (from tidl call) |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `template_name==NULL` | L1974 |
| (other) | propagated from `notification_tidl_request_save_as_template` (IO_ERROR, PERMISSION_DENIED, SERVICE_NOT_READY, FROM_DB, etc.) | L1979 |

**Scenarios:**
- [P1] valid args → delegates to `notification_tidl_request_save_as_template`. See IPC scenarios for failure paths.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `template_name == NULL` → INVALID_PARAMETER.
- [E1] empty template_name "" → delegated; server-side likely rejects.

### `notification_h notification_create_from_template(const char *template_name)` — L1982
**Errno map (handle, last_result):**
| Return | Predicate |
| non-NULL, last_result NONE | success | L1995/2003 |
| NULL, last_result INVALID_PARAMETER | template_name == NULL | L1987–L1990 |
| NULL, last_result = tidl error code | IPC failure | L1995–L2000 |

**Scenarios:**
- [P1] valid template_name, server returns a notification → non-NULL handle.
- [N1] `template_name == NULL` → NULL, last_result = INVALID_PARAMETER.
- [N2] tidl returns non-NONE → NULL, `notification_free(noti)` called on partial handle, last_result set to tidl error.
- [C1] When tidl fails but populated some noti, `notification_free` cleans up.

### `int notification_get_noti_block_state(notification_block_state_e *state)` — L2006
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L2037 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `state==NULL` | L2015 |
| (other) | propagated from `notification_tidl_get_noti_block_state` (IO_ERROR, SERVICE_NOT_READY, PERMISSION_DENIED) | L2020–L2024 |

**Scenarios:**
- [P1] `allow_to_notify==1, do_not_disturb==0` → NONE; `*state = ALLOWED`.
- [P2] `allow_to_notify==1, do_not_disturb==1, do_not_disturb_except==0` → NONE; `*state = DO_NOT_DISTURB`.
- [P3] `allow_to_notify==1, do_not_disturb==1, do_not_disturb_except==1` → NONE; `*state = ALLOWED` (exception wins).
- [P4] `allow_to_notify==0` → NONE; `*state = BLOCKED`.
- [N1] `state == NULL` → INVALID_PARAMETER.
- [N2] tidl call returns non-NONE → that errno propagated; app_id freed.
- [C1] `notification_get_app_id_by_pid` returns NULL → tidl still invoked with NULL app_id; result depends on server.

### `int notification_set_text_input(notification_h noti, int text_input_max_length)` — L2040
T_SIMPLE_SET on `noti->text_input_max_length`. No range validation — negatives accepted.

### `int notification_set_extension_image_size(notification_h noti, int height)` — L2050
**Errno map:**
| Return | Predicate |
| NOTIFICATION_ERROR_NONE | success | L2057 |
| NOTIFICATION_ERROR_INVALID_PARAMETER | `noti==NULL` or `height<=0` | L2052 |

**Scenarios:**
- [P1] positive height → NONE.
- [N1] `noti == NULL` → INVALID_PARAMETER.
- [N2] `height == 0` → INVALID_PARAMETER.
- [N3] `height < 0` → INVALID_PARAMETER.

### `int notification_get_extension_image_size(notification_h noti, int *height)` — L2060
T_SIMPLE_GET on `noti->extension_image_size`.

---

## Coverage check
- Functions covered: 57 / 57
- Open questions:
  1. `notification_set_text_domain` / `notification_set_tag` / `notification_clone`: `strdup` OOM is not checked. Behaviour on allocation failure is undefined — should they return `OUT_OF_MEMORY`?
  2. `notification_get_tag` does not null-check the `tag` out-pointer (writes `*tag` unconditionally); a `NULL tag` argument is a SEGV. Intentional or bug?
  3. `notification_set_text`: when `args_type == NOTIFICATION_VARIABLE_TYPE_NONE` is passed initially, the `while` loop is skipped and `noti->b_format_args` is unconditionally overwritten with a fresh empty bundle if no prior bundle existed — potential leak/state confusion. Worth a regression test.
  4. `notification_add_button` performs only validation; it does not allocate a slot or set state. Is this intentional vs. a TODO?
  5. `notification_get_noti_block_state`: server is called with possibly NULL `app_id` (if `notification_get_app_id_by_pid` failed). Should we early-return INVALID_PARAMETER instead?
  6. `notification_set_image` deletes the public-bundle key (`bundle_del(b, ...)`) on the priv-path branch where it likely meant `priv_b` — looks like a copy-paste bug at L140. Confirm.
  7. `notification_get_event_handler`: the `out:` block unconditionally sets `*event_handler = app_control_new`; on the NOT_EXIST_ID and INVALID_PARAMETER paths `app_control_new` is NULL — caller receives an explicit NULL write even though the function failed. Document expected contract.
# notification_internal.c — Test Scenario Inventory

File: `src/notification/src/notification_internal.c`
APIs covered: 105 EXPORT_API functions (per `notification_api_list.md`).

## Templates (referenced by `[T#]`)

> Reuse aggressively — many setters/getters in this file follow these shapes.

### T1 — Simple field getter on `notification_h`
```
Errno map:
| NOTIFICATION_ERROR_INVALID_PARAMETER | noti == NULL OR out_arg == NULL |
| NOTIFICATION_ERROR_NONE              | success                          |
Scenarios:
- [P1] valid noti + non-null out → returns NONE, *out = field value
- [N1] noti == NULL → INVALID_PARAMETER
- [N2] out == NULL → INVALID_PARAMETER (when applicable)
- [E1] field is zero/default after fresh notification_create()
- [C1] read after corresponding setter — round-trip
```

### T2 — Simple field setter on `notification_h` (no range check)
```
Errno map:
| NOTIFICATION_ERROR_INVALID_PARAMETER | noti == NULL |
| NOTIFICATION_ERROR_NONE              | success      |
Scenarios:
- [P1] valid noti, valid value → NONE; field updated
- [N1] noti == NULL → INVALID_PARAMETER
- [E1] boundary value (0, MAX, false→true toggle)
- [C1] overwrite previous value
```

### T3 — String setter (strdup, NULL-check args)
```
Errno map:
| INVALID_PARAMETER | noti == NULL OR str == NULL |
| NONE              | success                      |
Scenarios:
- [P1] valid noti + non-empty str → NONE; field is strdup'd
- [N1] noti == NULL → INVALID_PARAMETER
- [N2] str == NULL → INVALID_PARAMETER
- [E1] empty string ""
- [E2] very long string (>4 KiB)
- [E3] embedded multibyte / UTF-8
- [C1] overwrite — previous strdup freed, no leak (ASan)
- [C2] called twice with same noti
```

### T4 — IPC-dispatching delete/post/update wrapper
```
Errno map:
| INVALID_PARAMETER       | basic NULL / range guards (per fn)              |
| OUT_OF_MEMORY           | strdup of app_id fails (rare)                   |
| <propagated from IPC>   | notification_tidl_request_* return value        |
| SERVICE_NOT_READY       | IPC up but master not ready (propagated)        |
| IO_ERROR / PERMISSION_DENIED | propagated                                |
Scenarios:
- [P1] happy path → IPC returns NONE → NONE
- [N1] guard failure → INVALID_PARAMETER (no IPC call)
- [N2] IPC returns IO_ERROR  → IO_ERROR
- [N3] IPC returns PERMISSION_DENIED → PERMISSION_DENIED
- [N4] IPC returns SERVICE_NOT_READY → SERVICE_NOT_READY
- [N5] IPC returns FROM_DB → FROM_DB
- [E1] app_id == NULL → uses notification_get_app_id_by_pid(getpid())
- [C1] CPU inheritance set/cleared around IPC call (verify by mock)
```

### T5 — CB register / unregister on `_noti_cb_hash` (changed/detailed)
```
Errno map:
| INVALID_PARAMETER | callback == NULL                                  |
| INVALID_PARAMETER | _noti_cb_hash == NULL on unregister               |
| INVALID_PARAMETER | uid not in hash on unregister                     |
| INVALID_PARAMETER | callback not found in list on unregister          |
| OUT_OF_MEMORY     | malloc(notification_cb_info_s) fails on register  |
| IO_ERROR          | notification_tidl_monitor_init fails on register  |
| NONE              | success                                           |
Scenarios (register):
- [P1] first registration (hash NULL → created)
- [P2] second registration same uid → appended to list
- [N1] callback == NULL → INVALID_PARAMETER
- [N2] malloc fail → OUT_OF_MEMORY
- [N3] monitor_init fails → IO_ERROR, prior insert rolled back via unresister
Scenarios (unregister):
- [P3] valid registered cb → NONE; hash entry removed when list empty
- [N4] callback == NULL → INVALID_PARAMETER
- [N5] _noti_cb_hash == NULL → INVALID_PARAMETER
- [N6] uid not in hash → INVALID_PARAMETER
- [N7] callback not in list → INVALID_PARAMETER
- [C1] register/unregister round-trip; hash size 0 triggers monitor_fini
```

---

## Functions

### `notification_add_deferred_task(deferred_task_cb, user_data)` — L300
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | deferred_task_cb == NULL (L304) |
| <propagated>      | notification_tidl_add_deffered_task return (L308) |

**Scenarios:**
- [P1] non-NULL cb → IPC NONE → NONE
- [N1] cb == NULL → INVALID_PARAMETER (no IPC)
- [N2] IPC → IO_ERROR → IO_ERROR
- [N3] IPC → OUT_OF_MEMORY → OUT_OF_MEMORY
- [N4] IPC → SERVICE_NOT_READY → SERVICE_NOT_READY
- [C1] user_data == NULL allowed → forwarded

### `notification_del_deferred_task(deferred_task_cb)` — L313
**Errno map:**
| INVALID_PARAMETER | deferred_task_cb == NULL (L317) |
| <propagated>      | notification_tidl_del_deffered_task (L321) |

**Scenarios:**
- [P1] cb previously added → IPC NONE → NONE
- [N1] cb == NULL → INVALID_PARAMETER
- [N2] IPC → IO_ERROR → IO_ERROR
- [N3] IPC → NOT_EXIST_ID (cb never added) → propagated
- [C1] double-delete → second call propagates IPC error

### `notification_resister_changed_cb_for_uid(callback, user_data, uid)` — L328
Uses [T5] register.
**Errno map:**
| INVALID_PARAMETER | callback == NULL (L334) |
| OUT_OF_MEMORY     | malloc fail (L341) |
| IO_ERROR          | tidl_monitor_init fail (L361) |
| NONE              | success (L368) |

**Scenarios:**
- [P1] hash NULL → fresh allocation, then insert
- [P2] hash exists, uid absent → new list inserted
- [P3] hash exists, uid present → list appended
- [N1] callback == NULL → INVALID_PARAMETER
- [N2] malloc fail → OUT_OF_MEMORY
- [N3] monitor_init fail → IO_ERROR + rollback (unresister_for_uid called)
- [E1] uid == 0 (root) accepted
- [C1] same cb registered twice for same uid → both kept (no dedup)

### `notification_resister_changed_cb(callback, user_data)` — L373
**Errno map:** forwarded from `_for_uid` with `aul_getuid()`.
**Scenarios:**
- [P1] forwards to _for_uid; uid = aul_getuid()
- [N1] callback == NULL → INVALID_PARAMETER (propagated)
- [C1] aul_getuid() returns root → still valid

### `notification_unresister_changed_cb_for_uid(callback, uid)` — L393
Uses [T5] unregister.
**Errno map:**
| INVALID_PARAMETER | callback == NULL (L400) |
| INVALID_PARAMETER | _noti_cb_hash == NULL (L403) |
| INVALID_PARAMETER | uid not in hash (L407) |
| INVALID_PARAMETER | cb not in list (L426) |
| NONE              | success (L435) |

**Scenarios:**
- [P1] valid cb, list len > 1 → list shrinks, hash replaced
- [P2] valid cb, list len == 1 → list deleted, hash steals entry, monitor_fini fires when hash empty
- [N1] callback == NULL → INVALID_PARAMETER
- [N2] _noti_cb_hash == NULL (never registered) → INVALID_PARAMETER
- [N3] uid never registered → INVALID_PARAMETER
- [N4] cb not in list → INVALID_PARAMETER
- [C1] last entry removal calls notification_tidl_monitor_fini()

### `notification_unresister_changed_cb(callback)` — L438
**Scenarios:** [P1] forwards to _for_uid with aul_getuid(). [N1] callback == NULL → INVALID_PARAMETER.

### `notification_update_progress(noti, priv_id, progress)` — L444
**Errno map:**
| INVALID_PARAMETER | priv_id <= NONE && noti == NULL (L455) |
| <propagated>      | notification_ongoing_update_progress (L474) |

**Scenarios:**
- [P1] valid noti, priv_id=-1 → uses noti->priv_id
- [P2] valid priv_id, noti=NULL → uses caller pid app_id
- [N1] priv_id<=NONE && noti==NULL → INVALID_PARAMETER
- [E1] progress < 0.0 → clamped to 0.0
- [E2] progress > 1.0 → clamped to 1.0
- [E3] progress == 0.0 / 1.0 exact
- [E4] progress = NaN → behavior (passes comparison, treated as input_progress = progress)
- [N2] ongoing_update returns IO_ERROR → IO_ERROR
- [C1] noti->caller_app_id == NULL when strdup'ing — strdup(NULL) crash potential

### `notification_update_size(noti, priv_id, size)` — L483
**Errno map:** mirror of update_progress.
**Scenarios:**
- [P1] valid noti, priv_id=-1
- [P2] valid priv_id, noti=NULL
- [N1] both invalid → INVALID_PARAMETER
- [E1] size < 0.0 → clamped to 0.0
- [E2] size very large (1e20) → passed through unclamped
- [N2] IPC error propagated

### `notification_update_content(noti, priv_id, content)` — L520
**Errno map:**
| INVALID_PARAMETER | priv_id<=NONE && noti==NULL |
| <propagated>      | notification_ongoing_update_content |

**Scenarios:**
- [P1] valid noti+content
- [N1] both invalid → INVALID_PARAMETER
- [E1] content == NULL → forwarded (IPC handles)
- [E2] content == "" empty
- [E3] very long content
- [C1] noti==NULL path uses caller app_id

### `notification_set_icon(noti, icon_path)` — L554
Wrapper over `notification_set_image(NOTIFICATION_IMAGE_TYPE_ICON)`. Uses [T3].
**Scenarios:**
- [P1] valid noti+path → NONE
- [N1] noti==NULL → INVALID_PARAMETER (from set_image)
- [N2] icon_path==NULL → INVALID_PARAMETER (from set_image, see set_image semantics)
- [E1] empty path; [E2] non-existent file accepted at this layer

### `notification_get_icon(noti, icon_path)` — L563
**Errno map:** propagated from notification_get_image.
**Scenarios:**
- [P1] previously set icon → NONE, *icon_path populated
- [N1] noti==NULL → INVALID_PARAMETER (from get_image)
- [N2] icon_path==NULL → NONE but no write (defensive branch L572)
- [E1] icon never set → NONE with ret_image_path==NULL (no write because cond at L572)
- [C1] returned pointer is internal (no free)

### `notification_translate_localized_text(noti)` — L580
**Errno map:**
| OUT_OF_MEMORY | bundle_create fails for b_text (L598) |
| NONE          | success (L621) |
*No NULL-noti guard: noti->is_translation = false will crash if noti==NULL.*

**Scenarios:**
- [P1] noti with title+content set → b_text bundle populated, is_translation=true
- [N1] noti==NULL → SEGV (open question: defensive guard missing)
- [N2] bundle_create returns NULL → OUT_OF_MEMORY
- [E1] no text set (all types unset) → loop exits, is_translation=true, ret=NONE
- [E2] b_text already non-NULL → reuse (does not realloc)
- [C1] same key already present → bundle_del + re-add
- [C2] num_format_args zeroed each iteration

### `notification_set_title(noti, title, loc_title)` — L626
Wrapper of notification_set_text. [T3]-like.
**Scenarios:**
- [P1] valid noti+title → NONE
- [N1] noti==NULL → INVALID_PARAMETER
- [E1] title==NULL with loc_title==NULL → INVALID_PARAMETER (from set_text)
- [E2] loc_title==NULL but title set → NONE
- [E3] embedded format args "%d" — variable type NONE

### `notification_get_title(noti, title, loc_title)` — L637
**Errno map:** propagated from notification_get_text.
**Scenarios:**
- [P1] title set → *title populated, *loc_title=NULL
- [N1] noti==NULL → INVALID_PARAMETER (from get_text)
- [E1] title==NULL out arg → skipped, no write
- [E2] loc_title==NULL out arg → skipped
- [E3] no title set → ret_text=NULL, *title=NULL

### `notification_set_content(noti, content, loc_content)` — L658
Wrapper of notification_set_text(TEXT_TYPE_CONTENT). Same as set_title.
**Scenarios:**
- [P1] valid; [N1] noti==NULL → INVALID_PARAMETER; [E1] loc_content==NULL ok; [E2] empty string ok

### `notification_get_content(noti, content, loc_content)` — L669
Mirror of get_title. Same shape.
**Scenarios:**
- [P1] content set; [N1] noti==NULL; [E1] out args NULL → skip; [E2] no content set → *content=NULL

### `notification_set_application(noti, app_id)` — L690
Uses [T3].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR app_id==NULL (L693) |
| NONE              | success (L701) |

**Scenarios:**
- [P1] valid; [N1] noti==NULL; [N2] app_id==NULL; [E1] empty string;
- [E2] very long app_id; [C1] overwrite — previous launch_app_id freed

### `notification_get_application(noti, app_id)` — L706
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR app_id==NULL (L709) |
| NONE              | success (L717) |

**Scenarios:**
- [P1] launch_app_id set → *app_id = launch_app_id
- [P2] launch_app_id NULL → *app_id = caller_app_id (fallback)
- [N1] noti==NULL; [N2] app_id==NULL
- [C1] returned pointer is internal — caller must not free

### `notification_set_args(noti, args, group_args)` — L722
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR args==NULL (L725) |
| NONE              | success (L741) |

**Scenarios:**
- [P1] args only → noti->args replaced (bundle_dup'd), group_args left NULL
- [P2] args + group_args → both dup'd
- [N1] noti==NULL; [N2] args==NULL
- [C1] previous noti->args freed (no leak)
- [C2] previous group_args freed when new group_args==NULL → ends as NULL
- [E1] bundle_dup may fail (returns NULL) — not checked here (open question)

### `notification_get_args(noti, args, group_args)` — L746
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR args==NULL (L750) |
| NONE              | success (L761) |

**Scenarios:**
- [P1] args set → *args = noti->args
- [P2] args unset → *args = NULL
- [P3] group_args set & out non-NULL → *group_args populated
- [N1] noti==NULL; [N2] args==NULL (the out-pointer)
- [E1] group_args out NULL → skipped
- [C1] returned bundles are internal — no free

### `notification_get_grouping_list(type, count, list)` — L784
Forwards to _for_uid(aul_getuid()). _for_uid has:
**Errno map:**
| INVALID_PARAMETER | list==NULL (L772) |
| <propagated>      | notification_noti_get_grouping_list (L776) |

**Scenarios:**
- [P1] valid type+count+list → NONE
- [N1] list==NULL → INVALID_PARAMETER
- [N2] noti_get_grouping_list → FROM_DB → FROM_DB
- [E1] count == 0 → empty list returned
- [E2] count == INT_MAX
- [E3] type out of range → propagated INVALID_PARAMETER from inner

### `notification_delete_group_by_group_id(app_id, type, group_id)` — L792
[T4] IPC wrapper.
**Errno map:** propagated from notification_tidl_request_delete_multiple.
**Scenarios:**
- [P1] valid app_id → IPC NONE → NONE
- [P2] app_id==NULL → uses caller pid app_id
- [N1] IPC IO_ERROR; [N2] IPC PERMISSION_DENIED; [N3] IPC SERVICE_NOT_READY
- [E1] group_id is unused (function does not pass it) — open question
- [C1] no INVALID_PARAMETER guards before IPC

### `notification_delete_group_by_priv_id(app_id, type, priv_id)` — L840
Forwards to _for_uid. [T4].
**Scenarios:**
- [P1] valid → NONE
- [P2] app_id==NULL → caller pid used
- [N1] IPC NOT_EXIST_ID → NOT_EXIST_ID
- [N2] IPC IO_ERROR; [N3] PERMISSION_DENIED
- [E1] priv_id == 0 (passed verbatim — open question, no guard here)

### `notification_get_count(type, app_id, group_id, priv_id, count)` — L882
Forwards to _for_uid with `aul_getuid()`. _for_uid:
**Errno map:**
| INVALID_PARAMETER | count==NULL (L856) |
| <propagated>      | tidl_request_get_count (L865) |

**Scenarios:**
- [P1] valid → NONE, *count populated
- [N1] count==NULL → INVALID_PARAMETER
- [P2] app_id==NULL → caller pid used
- [N2] IPC IO_ERROR; [N3] FROM_DB; [N4] SERVICE_NOT_READY
- [E1] group_id == NOTIFICATION_GROUP_ID_NONE / priv_id == NONE → all-count semantic

### `notification_clear(type)` — L906
Forwards to _for_uid. _for_uid:
**Errno map:**
| INVALID_PARAMETER | type<=NONE OR type>MAX (L894) |
| <propagated>      | tidl_request_delete_multiple (L898) |

**Scenarios:**
- [P1] valid type → NONE
- [N1] type == NONE → INVALID_PARAMETER
- [N2] type == NOTIFICATION_TYPE_MAX+1 → INVALID_PARAMETER
- [E1] type == 1 (lower bound after NONE)
- [E2] type == NOTIFICATION_TYPE_MAX (upper inclusive)
- [N3] IPC errors propagated

### `notification_op_get_data(noti_op, type, data)` — L911
**Errno map:**
| INVALID_PARAMETER | noti_op==NULL OR data==NULL (L914) |
| INVALID_PARAMETER | type not in enum (L933 default) |
| NONE              | success (L937) |

**Scenarios:**
- [P1] each type {TYPE, PRIV_ID, NOTI, EXTRA_INFO_1, EXTRA_INFO_2} → correct field copied
- [N1] noti_op==NULL; [N2] data==NULL; [N3] unknown type
- [E1] enum values at boundary (lowest valid / highest valid)
- [C1] data alignment — *((int*)data) requires int-aligned buffer (UB if misaligned)

### `notification_set_pkgname(noti, pkgname)` — L942
Alias to notification_set_app_id. Use scenarios of set_app_id.

### `notification_set_app_id(noti, app_id)` — L950
[T3].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR app_id==NULL (L953) |
| NONE              | success (L964) |

**Scenarios:**
- [P1] valid; [N1] noti==NULL; [N2] app_id==NULL
- [E1] empty string; [E2] very long
- [C1] overwrite: previous caller_app_id freed
- [C2] called twice — no leak

### `notification_delete_all_by_type(app_id, type)` — L995
Forwards to _for_uid. _for_uid:
**Errno map:**
| INVALID_PARAMETER | type<=NONE OR type>MAX (L975) |
| <propagated>      | IPC tidl_request_delete_multiple (L984) |

**Scenarios:**
- [P1] valid type, app_id set → NONE
- [P2] app_id==NULL → caller pid app_id
- [N1] type==NONE; [N2] type>MAX → INVALID_PARAMETER
- [N3] IPC IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY

### `notification_delete_by_priv_id(app_id, type, priv_id)` — L1029
Forwards to _for_uid.
**Errno map:**
| INVALID_PARAMETER | priv_id<=NONE (L1009) |
| <propagated>      | tidl_request_delete_single (L1018) |

**Scenarios:**
- [P1] valid; [N1] priv_id == NONE → INVALID_PARAMETER
- [N2] priv_id == -1 → INVALID_PARAMETER
- [P2] app_id==NULL → caller pid used
- [N3] IPC NOT_EXIST_ID → NOT_EXIST_ID; [N4] PERMISSION_DENIED; [N5] IO_ERROR
- [E1] priv_id == 1 (lower bound)

### `notification_set_execute_option(noti, type, text, key, service_handle)` — L1036
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1046) |
| INVALID_PARAMETER | type<=EXECUTE_NONE OR type>EXECUTE_MAX (L1049) |
| NONE              | success (L1113) |

**Scenarios:**
- [P1] type==RESPONDING with text+key+service_handle → bundle populated, b_service_responding dup'd
- [P2] type==SINGLE_LAUNCH; [P3] type==MULTI_LAUNCH (same shape)
- [N1] noti==NULL; [N2] type==NONE; [N3] type==MAX+1
- [E1] text==NULL → only key written
- [E2] key==NULL → only text written
- [E3] service_handle==NULL → previous bundle freed, no new dup
- [C1] called twice with same type → previous bundle freed and replaced
- [C2] b_execute_option lazy-init when NULL
- [E4] very long text/key (>32 chars) — buf_key snprintf truncates only the key buffer, not value

### `notification_get_id(noti, group_id, priv_id)` — L1118
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1121) |
| NONE              | success (L1134) |

**Scenarios:**
- [P1] both out non-NULL → both populated
- [P2] group_id<NONE → clamped to NONE
- [N1] noti==NULL
- [E1] group_id out == NULL → skipped
- [E2] priv_id out == NULL → skipped
- [E3] both out NULL → still NONE
- [C1] freshly created noti → priv_id == NOTIFICATION_PRIV_ID_NONE

### `notification_set_priv_id(noti, priv_id)` — L1139
[T2].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR priv_id<=0 (L1141) |
| NONE              | success (L1146) |

**Scenarios:**
- [P1] valid; [N1] noti==NULL; [N2] priv_id==0; [N3] priv_id==-1
- [E1] priv_id == 1 (boundary); [E2] priv_id == INT_MAX

### `notification_load(app_id, priv_id)` — L1173
Forwards to _for_uid which uses last_result:
**Errno map (last_result):**
| <IPC ret>      | from tidl_request_load_noti_by_priv_id |
| NOTIFICATION_ERROR_NONE | on success |

**Scenarios:**
- [P1] valid → returns notification_h, last_result==NONE
- [N1] IPC NOT_EXIST_ID → returns NULL, last_result==NOT_EXIST_ID
- [N2] IPC IO_ERROR → NULL + last_result set
- [N3] IPC PERMISSION_DENIED → NULL
- [E1] app_id==NULL → forwarded (IPC may reject)
- [E2] priv_id<=0 → no guard here, forwarded
- [C1] mutex_unlock called on failure path (verify no leak)

### `notification_new(type, group_id, priv_id)` — L1181
Wrapper over notification_create(type). group_id/priv_id ignored.
**Scenarios:**
- [P1] valid type → handle returned, last_result==NONE
- [N1] invalid type → NULL (from create)
- [N2] OOM in calloc → NULL
- [E1] group_id, priv_id arguments are discarded (open question — surprising)

### `notification_get_execute_option(noti, type, text, service_handle)` — L1193
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1203) |
| INVALID_PARAMETER | type<=NONE OR type>MAX (L1206) |
| NONE              | success (L1257) |

**Scenarios:**
- [P1] RESPONDING with key set + domain → dgettext(domain, key)
- [P2] domain==NULL, key set → dgettext("sys_string", key)
- [P3] key not set → falls back to text<type>
- [P4] SINGLE_LAUNCH / MULTI_LAUNCH paths
- [N1] noti==NULL; [N2] invalid type
- [E1] text==NULL out arg → skipped
- [E2] service_handle==NULL out arg → skipped
- [E3] both out args NULL → still NONE
- [C1] b for type is NULL (option never set) → text/service unset, return NONE
- [C2] dir==NULL but domain set → uses sys_string branch

### `notification_insert_for_uid(noti, priv_id, uid)` — L1262
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1269) |
| INVALID_PARAMETER | type<=NONE OR type>MAX (L1272) |
| <propagated>      | tidl_request_insert (L1280) |
| <propagated>      | notification_get_event_flag (L1291) |
| <propagated>      | tidl_event_monitor_init (L1297) |

**Scenarios:**
- [P1] valid noti, event_flag=false → NONE, priv_id populated
- [P2] event_flag=true → also calls event_monitor_init
- [N1] noti==NULL; [N2] type==NONE; [N3] type>MAX
- [N4] IPC insert IO_ERROR → IO_ERROR
- [N5] get_event_flag fails → propagated
- [N6] event_monitor_init IO_ERROR → IO_ERROR (after insert succeeded!)
- [E1] priv_id out==NULL → skipped, no write
- [C1] noti->uid set to uid; insert_time set; priv_id field populated
- [C2] partial-failure: insert succeeded but monitor init failed → state inconsistent (open question)

### `notification_insert(noti, priv_id)` — L1306
Forwards to _for_uid with aul_getuid(). Same scenarios as _for_uid.

### `notification_update_async_for_uid(noti, result_cb, user_data, uid)` — L1312
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1317) |
| <propagated>      | tidl_request_update (L1325) |

**Scenarios:**
- [P1] valid noti → IPC NONE → NONE
- [N1] noti==NULL → INVALID_PARAMETER
- [N2] IPC NOT_EXIST_ID; [N3] PERMISSION_DENIED; [N4] IO_ERROR
- [E1] result_cb==NULL / user_data==NULL → ignored (function name says async but synchronous IPC, callback unused — open question)
- [C1] noti->uid updated; insert_time refreshed

### `notification_update_async(noti, result_cb, user_data)` — L1331
Forwards to _for_uid. Same as above.

### `notification_register_detailed_changed_cb_for_uid(callback, user_data, uid)` — L1339
[T5] register, detailed variant.
**Errno map:**
| INVALID_PARAMETER | callback==NULL (L1346) |
| OUT_OF_MEMORY     | malloc fail (L1352) |
| IO_ERROR          | tidl_monitor_init fail (L1373) |
| NONE              | success |

**Scenarios:** see [T5] — same shape; rollback uses notification_unregister_detailed_changed_cb_for_uid.

### `notification_register_detailed_changed_cb(callback, user_data)` — L1385
Forwards. Scenarios as above.

### `notification_unregister_detailed_changed_cb_for_uid(callback, user_data, uid)` — L1405
[T5] unregister, detailed variant.
**Errno map:** same as unresister_changed_cb_for_uid.
**Scenarios:** see [T5] unregister section.

### `notification_unregister_detailed_changed_cb(callback, user_data)` — L1452
Forwards. Same shape.

### `notification_is_service_ready(void)` — L1461
**Errno map:** propagated from `notification_tidl_is_master_ready`.
**Scenarios:**
- [P1] master ready → 1
- [P2] master not ready → 0
- [N1] IPC failure (IO_ERROR / SERVICE_NOT_READY) → propagated
- [C1] CPU inheritance bracketed

### `notification_set_uid(noti, uid)` — L1472
[T2].
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1475) |
| NONE              | success |

**Scenarios:**
- [P1] valid; [N1] noti==NULL
- [E1] uid==0; [E2] uid==(uid_t)-1; [E3] uid==REGULAR_UID_MIN
- [C1] overwrite previous uid

### `notification_get_uid(noti, uid)` — L1482
[T1].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR uid==NULL (L1485) |
| NONE              | success |

**Scenarios:**
- [P1] valid; [N1] noti==NULL; [N2] uid==NULL
- [E1] read default uid (0 after create) — verify in fixture

### `notification_post_for_uid(noti, uid)` — L1560
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1567) |
| INVALID_PARAMETER | type<=NONE OR type>MAX (L1570) |
| <propagated>      | tidl_request_insert (L1582) |
| <propagated>      | get_event_flag (L1588) |
| <propagated>      | tidl_event_monitor_init (L1594) |

**Scenarios:**
- [P1] event_flag=false, IPC NONE → NONE; priv_id populated; insert_time set
- [P2] event_flag=true → also monitor_init
- [N1] noti==NULL; [N2] type==NONE; [N3] type>MAX
- [N4] IPC insert IO_ERROR → private files rolled back (g_list_foreach __remove_private_file)
- [N5] get_event_flag fails (post-insert) → propagated, files NOT rolled back (insert already succeeded)
- [N6] event_monitor_init fail → propagated
- [C1] __copy_private_file: image/sound/vibration paths copied (verify list freed)
- [C2] noti->uid = uid

### `notification_update_for_uid(noti, uid)` — L1610
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1614) (also issues tidl_request_refresh + mutex_unlock) |
| <propagated>      | tidl_request_update (L1629) |

**Scenarios:**
- [P1] valid → IPC NONE → NONE; insert_time refreshed
- [N1] noti==NULL → INVALID_PARAMETER **AND** tidl_request_refresh(uid) is invoked + mutex_unlock (open question — surprising side effects)
- [N2] IPC NOT_EXIST_ID / IO_ERROR / PERMISSION_DENIED propagated

### `notification_delete_for_uid(noti, uid)` — L1635
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1637) |
| <propagated>      | tidl_request_delete_single (L1643) |

**Scenarios:**
- [P1] valid → NONE
- [N1] noti==NULL → INVALID_PARAMETER
- [N2] IPC NOT_EXIST_ID; [N3] PERMISSION_DENIED; [N4] IO_ERROR
- [E1] noti->caller_app_id == NULL → forwarded as NULL (no guard)

### `notification_delete_all_for_uid(type, uid)` — L1649
**Errno map:**
| INVALID_PARAMETER | type<=NONE OR type>MAX (L1654) |
| <propagated>      | tidl_request_delete_multiple (L1660) |

**Scenarios:**
- [P1] valid; [N1] type==NONE; [N2] type>MAX
- [N3] IPC IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY
- [C1] caller_app_id from caller pid always (no app_id arg)
- [E1] caller_app_id == NULL (pid lookup failed) → forwarded as NULL

### `notification_load_by_tag_for_uid(tag, uid)` — L1671
Returns notification_h, sets last_result.
**Errno map (last_result):**
| INVALID_PARAMETER | tag==NULL (L1677) |
| OUT_OF_MEMORY     | get_app_id_by_pid fail (L1684) |
| <propagated>      | tidl_request_load_noti_by_tag (L1691) |

**Scenarios:**
- [P1] valid tag → noti returned, last_result==NONE
- [N1] tag==NULL → NULL, last_result==INVALID_PARAMETER
- [N2] get_app_id_by_pid==NULL → NULL, last_result==OUT_OF_MEMORY
- [N3] IPC NOT_EXIST_ID → NULL + last_result
- [N4] IPC IO_ERROR → NULL + mutex_unlock executed
- [E1] empty tag "" → forwarded; depends on IPC
- [C1] caller_app_id always freed

### `notification_create_from_package_template(app_id, template_name)` — L1705
Returns notification_h.
**Errno map (last_result):**
| INVALID_PARAMETER | app_id==NULL OR template_name==NULL (L1710) |
| <propagated>      | tidl_request_create_from_package_template (L1717) |

**Scenarios:**
- [P1] valid → noti returned
- [N1] app_id==NULL; [N2] template_name==NULL
- [N3] IPC NOT_EXIST_ID → notification_free(NULL or partial) then NULL (open question — free of possibly-uninitialized noti, possible UB)
- [N4] IPC IO_ERROR → free path triggered
- [C1] last_result always set

### `notification_set_default_button(noti, index)` — L1730
[T2] with range.
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1732) |
| INVALID_PARAMETER | index<0 OR index>BUTTON_6 (L1735) |
| NONE              | success |

**Scenarios:**
- [P1] valid index ∈ [0..BUTTON_6]; [N1] noti==NULL; [N2] index==-1; [N3] index==BUTTON_6+1
- [E1] index==0; [E2] index==BUTTON_6 (boundary)

### `notification_get_default_button(noti, index)` — L1743
[T1].
**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] index==NULL; [E1] default value when never set

### `notification_get_ongoing_value_type(noti, type)` — L1753 — [T1]
**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] type==NULL

### `notification_set_ongoing_value_type(noti, type)` — L1763
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1765) |
| INVALID_PARAMETER | type<PERCENT OR type>TIME (L1768) |
| NONE              | success |

**Scenarios:**
- [P1] PERCENT; [P2] TIME; [N1] noti==NULL; [N2] type==PERCENT-1; [N3] type==TIME+1

### `notification_get_ongoing_time(noti, current, duration)` — L1776
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR current==NULL OR duration==NULL (L1778) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1..N3] each NULL arg; [E1] defaults zero

### `notification_set_ongoing_time(noti, current, duration)` — L1787
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1789) |
| INVALID_PARAMETER | current<0 OR duration<0 OR current>duration (L1792) |
| NONE              | success |

**Scenarios:**
- [P1] current<=duration both nonneg; [N1] noti==NULL; [N2] current<0; [N3] duration<0; [N4] current>duration
- [E1] current==0, duration==0; [E2] current==duration (equal allowed)
- [E3] very large values INT_MAX (no upper bound check)

### `notification_get_hide_timeout(noti, timeout)` — L1801 — [T1]
**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] timeout==NULL

### `notification_set_hide_timeout(noti, timeout)` — L1811
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR timeout<0 (L1813) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] timeout==-1; [E1] timeout==0; [E2] timeout==INT_MAX

### `notification_get_delete_timeout(noti, timeout)` — L1821 — [T1]
Same as get_hide_timeout.

### `notification_set_delete_timeout(noti, timeout)` — L1831
Same shape as set_hide_timeout.

### `notification_get_text_input_max_length(noti, text_input_max_length)` — L1841 — [T1]
**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] text_input_max_length==NULL

### `notification_post_with_event_cb_for_uid(noti, cb, userdata, uid)` — L1853
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR cb==NULL (L1862) |
| INVALID_PARAMETER | type<=NONE OR type>MAX (L1865) |
| <propagated>      | tidl_request_insert (L1874) |
| <propagated>      | tidl_event_monitor_init (L1887) |
| OUT_OF_MEMORY     | malloc(event_cb_info) (L1905) |

**Scenarios:**
- [P1] new priv_id → info appended to __noti_event_cb_list
- [P2] existing priv_id (find_list hit) → info->cb / userdata replaced
- [N1] noti==NULL; [N2] cb==NULL; [N3] type out of range
- [N4] tidl insert fails → private files rolled back, return error
- [N5] event_monitor_init fails (post-insert) → return error, files not rolled back
- [N6] malloc fail → OUT_OF_MEMORY (after insert + monitor — possibly leaks IPC-allocated id)
- [C1] mutex_lock/unlock around list mutation
- [C2] event_flag forced true; insert_time stamped

### `notification_post_with_event_cb(noti, cb, userdata)` — L1928
Forwards to _for_uid with aul_getuid(). Same scenarios.

### `notification_send_event(noti, event_type)` — L1933
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L1938) |
| INVALID_PARAMETER | event_type not in any allowed range (L1947) |
| INVALID_PARAMETER | event_flag retrieval fails or false (L1951) |
| <propagated>      | tidl_send_event (L1955) |

**Scenarios:**
- [P1] CLICK_ON_BUTTON_1..EVENT_TYPE_MAX → NONE
- [P2] HIDDEN_BY_USER..HIDDEN_BY_EXTERNAL → NONE
- [P3] PRESSED..DELETED → NONE
- [P4] CHECK_BOX → NONE
- [N1] noti==NULL
- [N2] event_type outside all 4 ranges → INVALID_PARAMETER
- [N3] event_flag==false → INVALID_PARAMETER
- [N4] get_event_flag fails → INVALID_PARAMETER (note: collapsed to INVALID_PARAMETER, not propagated)
- [N5] IPC IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY
- [E1] event_type at each range boundary (lo, hi)

### `notification_send_event_by_priv_id(priv_id, event_type)` — L1961
**Errno map:**
| INVALID_PARAMETER | priv_id<=0 (L1965) |
| INVALID_PARAMETER | event_type not in allowed ranges (L1974) |
| <propagated>      | tidl_send_event (L1978) |

**Scenarios:**
- [P1..P4] one per allowed event-type range
- [N1] priv_id==0; [N2] priv_id==-1; [N3] event_type invalid
- [N4] IPC errors propagated
- [E1] priv_id==1 (boundary); [E2] each event range boundary

### `notification_get_event_flag(noti, flag)` — L1984 — [T1]
**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] flag==NULL; [E1] default false on fresh noti

### `notification_check_event_receiver_available(noti, available)` — L1994
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR available==NULL (L1999) |
| <propagated>      | notification_get_id (L2002) |
| <propagated>      | tidl_check_event_receiver (L2009) |

**Scenarios:**
- [P1] valid noti, posted priv_id → NONE, *available populated
- [N1] noti==NULL; [N2] available==NULL
- [N3] get_id fails → propagated
- [N4] IPC IO_ERROR / SERVICE_NOT_READY propagated
- [E1] priv_id == NONE (not posted) → IPC may reject

### `notification_set_extention_data(noti, key, value)` — L2023
Alias to notification_set_extension_data — share scenarios.

### `notification_set_extension_data(noti, key, value)` — L2028
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR key==NULL (L2035) |
| NONE              | bundle_del NONE branch when value==NULL (L2044) |
| INVALID_PARAMETER | bundle_del fails when value==NULL (L2046) |
| NONE              | success (L2059) |

**Scenarios:**
- [P1] value non-NULL, key new → encoded + added; ret NONE
- [P2] value non-NULL, key exists → old deleted, new added
- [P3] value==NULL, key exists → bundle_del succeeds, NONE
- [N1] noti==NULL; [N2] key==NULL
- [N3] value==NULL, key not present → bundle_del fails → INVALID_PARAMETER
- [E1] empty key ""; [E2] very long key; [E3] very long encoded value
- [C1] noti->args lazily created when NULL
- [C2] bundle_encode failure (raw==NULL) — not checked here; raw fed to bundle_add_str (open question)

### `notification_get_extention_data(noti, key, value)` — L2062
Alias to notification_get_extension_data.

### `notification_get_extension_data(noti, key, value)` — L2067
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR key==NULL OR value==NULL (L2073) |
| INVALID_PARAMETER | noti->args==NULL (L2076) |
| INVALID_PARAMETER | bundle_get_str != NONE (L2082) |
| IO_ERROR          | _create_bundle_from_bundle_raw returns NULL (L2086) |
| NONE              | success |

**Scenarios:**
- [P1] valid → bundle returned
- [N1..N3] each NULL arg
- [N4] noti->args==NULL (never set) → INVALID_PARAMETER
- [N5] key absent → INVALID_PARAMETER
- [N6] stored value malformed → bundle_decode→NULL → IO_ERROR
- [E1] stored empty string → bundle_decode NULL → IO_ERROR

### `notification_set_extension_event_handler(noti, event, event_handler)` — L2097
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR event_handler==NULL (L2109) |
| INVALID_PARAMETER | event<HIDDEN_BY_USER OR event>HIDDEN_BY_EXTERNAL (L2114) |
| IO_ERROR          | app_control_export_as_bundle fail (L2133) |
| IO_ERROR          | bundle_encode fail (L2140) |
| IO_ERROR          | bundle_add_str fail (L2147) |
| NONE              | success |

**Scenarios:**
- [P1] valid → bundle entry added; NONE
- [N1] noti==NULL; [N2] event_handler==NULL; [N3] event out of range (both sides)
- [N4] export_as_bundle fails → IO_ERROR
- [N5] bundle_encode fails → IO_ERROR
- [N6] bundle_add_str fails → IO_ERROR
- [E1] event at each boundary (HIDDEN_BY_USER, HIDDEN_BY_EXTERNAL)
- [C1] noti->args lazily created
- [C2] existing key deleted before re-add
- [C3] b_raw and app_control_bundle always freed (verify with ASan)

### `notification_get_extension_event_handler(noti, event, event_handler)` — L2162
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR event_handler==NULL (L2173) |
| INVALID_PARAMETER | event out of range (L2178) |
| INVALID_PARAMETER | bundle_get_str returns NULL (L2187) — note: if noti->args==NULL also crashes here (no guard) |
| IO_ERROR          | _create_bundle_from_bundle_raw NULL (L2193) |
| IO_ERROR          | app_control_create fail (L2199) |
| IO_ERROR          | app_control_import_from_bundle fail (L2206) |
| NONE              | success |

**Scenarios:**
- [P1] valid set → get returns app_control
- [N1] noti==NULL; [N2] event_handler==NULL; [N3] event out of range
- [N4] noti->args==NULL → SEGV (open question — no guard)
- [N5] key absent → INVALID_PARAMETER
- [N6] malformed raw → IO_ERROR
- [N7] app_control_create fail → IO_ERROR
- [N8] import_from_bundle fail → app_control_destroyed + IO_ERROR
- [C1] app_control_bundle freed in out label

### `notification_get_all_count_for_uid(type, count, uid)` — L2224
**Errno map:**
| INVALID_PARAMETER | count==NULL (L2228) |
| INVALID_PARAMETER | type<NONE OR type>MAX (L2233) |
| <propagated>      | tidl_request_get_all_count (L2239) |

**Scenarios:**
- [P1] valid → NONE, *count populated
- [N1] count==NULL; [N2] type<NONE; [N3] type>MAX
- [E1] type==NONE (allowed — boundary)
- [N4] IPC FROM_DB; [N5] IO_ERROR; [N6] SERVICE_NOT_READY

### `notification_get_all_count(type, count)` — L2249
Forwards to _for_uid. Same scenarios.

### `notification_set_app_label(noti, label)` — L2254
[T3].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR label==NULL (L2256) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] label==NULL; [E1] empty string; [E2] long string; [C1] overwrite frees previous

### `notification_get_app_label(noti, label)` — L2267
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR label==NULL (L2269) |
| NONE              | success (note: *label NOT written when app_label==NULL — UB) |

**Scenarios:**
- [P1] app_label set → *label populated
- [N1] noti==NULL; [N2] label==NULL
- [C1] app_label==NULL → *label uninitialized + ret NONE (open question — caller reads uninit)

### `notification_set_indirect_request(noti, pid, uid)` — L2310
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR pid<=1 OR uid<REGULAR_UID_MIN (L2317) |
| INVALID_PARAMETER | aul_app_get_appid_bypid != AUL_R_OK (L2321) |
| NONE              | success |

**Scenarios:**
- [P1] all three service bundles + each event handler bundle → __set_caller_info applied
- [N1] noti==NULL; [N2] pid==1 (init); [N3] pid==0; [N4] uid<REGULAR_UID_MIN
- [N5] aul_app_get_appid_bypid fails (pid not running) → INVALID_PARAMETER
- [E1] no service bundles / no event handlers set → still NONE
- [C1] iterates i=0..NOTIFICATION_EVENT_TYPE_MAX inclusive

### `notification_delete_by_display_applist(display_applist)` — L2364
Forwards to _for_uid:
**Errno map:**
| INVALID_PARAMETER | display_applist<NOTIFICATION_TRAY (L2354) |
| <propagated>      | tidl_request_delete_by_display_applist (L2358) |

**Scenarios:**
- [P1] valid display_applist → NONE
- [N1] display_applist<NOTIFICATION_TRAY → INVALID_PARAMETER
- [N2] IPC IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY
- [E1] bitmask combinations (NOTIFICATION_TRAY | INDICATOR | TICKER)

### `notification_set_check_box(noti, flag, checked)` — L2369
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L2372) |
| NONE              | success |

**Scenarios:**
- [P1] flag=true checked=true; [P2] flag=true checked=false; [P3] flag=false checked=false
- [N1] noti==NULL
- [C1] re-call overwrites both fields

### `notification_get_check_box(noti, flag, checked)` — L2383
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR flag==NULL OR checked==NULL (L2386) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1..N3] each NULL arg; [E1] defaults false/false

### `notification_set_check_box_checked(noti, checked)` — L2397
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L2400) |
| NONE              | success |

**Scenarios:** [P1] true; [P2] false; [N1] noti==NULL; [C1] does NOT touch noti->check_box flag

### `notification_get_check_box_checked(noti, checked)` — L2410
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR checked==NULL (L2413) |
| NONE              | success |

**Scenarios:**
- [P1] check_box==true → *checked = check_box_value
- [P2] check_box==false → *checked = false (ignores check_box_value!)
- [N1] noti==NULL; [N2] checked==NULL
- [C1] subtle: set_check_box_checked(true) without set_check_box(true,...) → getter returns false

### `notification_register_do_not_disturb_app(callback, user_data)` — L2428
**Errno map:**
| INVALID_PARAMETER | callback==NULL (L2434) |
| <propagated>      | tidl_request_register_dnd_app (L2438) |
| <propagated>      | tidl_event_monitor_init (L2446) |

**Scenarios:**
- [P1] valid → IPC NONE → monitor init NONE → NONE; globals set
- [N1] callback==NULL → INVALID_PARAMETER
- [N2] register IPC fails (IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY)
- [N3] event_monitor_init fails after successful register → leaves server-side reg alive (state inconsistent)
- [C1] _disturb_callback / _disturb_user_data set
- [C2] called twice → second overwrites globals; server-side double register (open question)

### `notification_unregister_do_not_disturb_app(void)` — L2461
**Errno map:**
| <propagated> | tidl_request_unregister_dnd_app (L2468) |

**Scenarios:**
- [P1] previously registered → IPC NONE → NONE; callback cleared
- [N1] IPC IO_ERROR / SERVICE_NOT_READY → propagated, callback NOT cleared
- [N2] never registered → IPC may return NOT_EXIST / NONE → propagated
- [C1] __noti_event_cb_list==NULL → event_monitor_fini called
- [C2] __noti_event_cb_list non-empty → fini skipped

### `notification_set_pairing_type(noti, pairing)` — L2506
**Errno map:**
| INVALID_PARAMETER | noti==NULL (L2512) |
| NONE              | success |

**Scenarios:**
- [P1] pairing=true; [P2] pairing=false
- [N1] noti==NULL
- [C1] noti->args lazily created
- [C2] previous PAIRING_TYPE_KEY value deleted before re-add

### `notification_get_pairing_type(noti, pairing)` — L2534
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR noti->args==NULL OR pairing==NULL (L2541) |
| INVALID_PARAMETER | bundle_get_str != NONE OR value==NULL (L2545) |
| NONE              | success |

**Scenarios:**
- [P1] previously set "true" → *pairing=true
- [P2] previously set "false" → *pairing=false
- [N1] noti==NULL; [N2] noti->args==NULL; [N3] pairing==NULL
- [N4] key absent in args → INVALID_PARAMETER
- [E1] stored value "TRUE" (uppercase) → falls into else branch, returns false (case-sensitive)

### `notification_set_channel_name(noti, channel_name)` — L2560
[T3].
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR channel_name==NULL (L2563) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1] noti==NULL; [N2] channel_name==NULL; [E1] empty/long; [C1] overwrite frees previous

### `notification_get_channel_name(noti, channel_name)` — L2578
**Errno map:**
| INVALID_PARAMETER | noti==NULL OR channel_name==NULL (L2581) |
| NONE              | success (returns internal pointer, possibly NULL) |

**Scenarios:** [P1] set then get; [N1..N2] NULL args; [E1] never set → *channel_name=NULL but ret NONE

### `notification_channel_create(channel_name, channel)` — L2622
**Errno map:**
| INVALID_PARAMETER | channel==NULL OR channel_name==NULL (L2627) |
| OUT_OF_MEMORY     | calloc fail (L2634) |
| NONE              | success |

**Scenarios:**
- [P1] valid → channel handle returned with caller pid app_id
- [N1] channel==NULL; [N2] channel_name==NULL
- [N3] calloc fail → OUT_OF_MEMORY
- [C1] app_id from notification_get_app_id_by_pid; strdup of NULL possible if pid lookup fails (open question)
- [E1] long channel_name

### `notification_channel_free(channel)` — L2650
Returns void.
**Scenarios:**
- [P1] valid channel → freed cleanly (ASan)
- [N1] channel==NULL → early return, no SEGV
- [C1] app_id==NULL OR channel_name==NULL → individually skipped
- [C2] double-free → UB (open question, no nullify)

### `notification_channel_add(channel)` — L2670
**Errno map:**
| INVALID_PARAMETER | channel==NULL OR app_id==NULL OR channel_name==NULL (L2677) |
| <propagated>      | tidl_request_insert_channel (L2684) |

**Scenarios:**
- [P1] valid → NONE
- [N1] channel==NULL; [N2] app_id field NULL; [N3] channel_name field NULL
- [N4] IPC ALREADY_EXIST_ID → ALREADY_EXIST_ID
- [N5] IPC FROM_DB / IO_ERROR / PERMISSION_DENIED

### `notification_channel_remove(channel)` — L2698
Mirror of add. IPC → tidl_request_delete_channel.
**Scenarios:**
- [P1] valid → NONE
- [N1..N3] NULL guards
- [N4] IPC NOT_EXIST_ID; [N5] PERMISSION_DENIED; [N6] FROM_DB; [N7] IO_ERROR

### `notification_channel_update(channel)` — L2725
Mirror of add. IPC → tidl_request_update_channel.
**Scenarios:**
- [P1] valid → NONE (note: returns NONE explicitly, not `ret`, even though `ret` could be NONE — open question)
- [N1..N3] NULL guards
- [N4] IPC NOT_EXIST_ID; [N5] FROM_DB; [N6] IO_ERROR; [N7] PERMISSION_DENIED

### `notification_channel_get_by_name(channel_name, channel)` — L2753
**Errno map:**
| INVALID_PARAMETER | channel_name==NULL OR channel==NULL OR app_id==NULL (L2765) |
| OUT_OF_MEMORY     | calloc fail (L2773) |
| <propagated>      | tidl_request_get_channel (L2780) |

**Scenarios:**
- [P1] existing channel → handle returned with app_id+name+flags
- [N1] channel_name==NULL; [N2] channel==NULL; [N3] caller app_id lookup fails
- [N4] calloc fail → OUT_OF_MEMORY
- [N5] IPC NOT_EXIST_ID → calloc'd memory freed, error propagated
- [N6] IPC IO_ERROR / FROM_DB / PERMISSION_DENIED
- [C1] app_id always freed in out label

### `notification_channel_set_blockable(channel, blockable)` — L2804
[T2].
**Errno map:** INVALID_PARAMETER if channel==NULL.
**Scenarios:** [P1] true; [P2] false; [N1] channel==NULL

### `notification_channel_get_blockable(channel, blockable)` — L2821
**Errno map:** INVALID_PARAMETER if channel==NULL (note: no NULL-guard on `blockable` out — open question).
**Scenarios:**
- [P1] true; [P2] false; [N1] channel==NULL
- [E1] blockable out==NULL → SEGV (open question)

### `notification_channel_set_block(channel, block)` — L2838 — [T2]
**Scenarios:** [P1] true; [P2] false; [N1] channel==NULL

### `notification_channel_get_block(channel, block)` — L2855
Same shape as get_blockable; same open question for NULL `block` out.

### `notification_channel_get_name(channel, channel_name)` — L2872
**Errno map:**
| INVALID_PARAMETER | channel==NULL OR channel_name==NULL (L2877) |
| NONE              | success |

**Scenarios:** [P1] valid; [N1] channel==NULL; [N2] channel_name==NULL; [E1] channel_name field NULL → *out=NULL, ret NONE

### `notification_channel_clone(channel, clone)` — L2889
**Errno map:**
| INVALID_PARAMETER | channel==NULL OR app_id==NULL OR channel_name==NULL OR clone==NULL (L2895) |
| OUT_OF_MEMORY     | calloc fail (L2903) |
| NONE              | success |

**Scenarios:**
- [P1] valid → deep copy returned
- [N1..N4] each guard
- [N5] calloc fail → OUT_OF_MEMORY
- [C1] strdup of app_id/channel_name may fail → returned NULL fields (open question, strdup return not checked)

### `notification_channel_foreach(app_id, cb, user_data)` — L2919
**Errno map:**
| INVALID_PARAMETER | cb==NULL (L2925) |
| IO_ERROR          | app_id==NULL AND notification_get_app_id_by_pid fails (L2934) |
| <propagated>      | tidl_request_channel_get_list (L2941) |

**Scenarios:**
- [P1] app_id provided → IPC iterates
- [P2] app_id==NULL → caller pid app_id used
- [N1] cb==NULL → INVALID_PARAMETER
- [N2] app_id==NULL and pid lookup fails → IO_ERROR
- [N3] IPC FROM_DB / IO_ERROR / PERMISSION_DENIED / SERVICE_NOT_READY
- [E1] zero channels for app_id → cb never invoked, ret NONE
- [C1] _app_id freed in out label

---

## Coverage check
- Functions covered: 105 / 105
- Open questions:
  1. `notification_translate_localized_text` lacks a NULL-noti guard — `noti->is_translation = false` will SEGV if called with NULL.
  2. `notification_update_for_uid` performs `tidl_request_refresh(uid)` + `__notification_mutex_unlock()` on the `noti==NULL` branch — surprising side effects on the INVALID_PARAMETER path.
  3. `notification_create_from_package_template` calls `notification_free(noti)` on IPC failure, but `noti` may be uninitialized / unset by the IPC stub — potential UB.
  4. `notification_new(type, group_id, priv_id)` silently discards `group_id` and `priv_id` — API contract is misleading.
  5. `notification_update_async_for_uid` ignores `result_cb` and `user_data`; the IPC call is synchronous.
  6. `notification_get_extension_event_handler` does not guard `noti->args == NULL`; will SEGV at L2186 if args was never created.
  7. `notification_get_app_label` returns NONE without writing `*label` when `app_label==NULL` — caller reads uninitialized memory.
  8. `notification_channel_update` returns hard-coded `NOTIFICATION_ERROR_NONE` instead of `ret` at L2750; correct because the prior branch short-circuits non-NONE returns, but inconsistent style.
  9. `notification_set_extension_data` does not check `bundle_encode` result before calling `bundle_add_str(noti->args, key, (const char *)raw)`; if encode fails, `raw` may be NULL.
  10. `notification_channel_get_blockable` / `notification_channel_get_block` / `notification_set_check_box_checked` lack NULL-guards on their out pointers / value semantics.
  11. `notification_insert_for_uid` and `notification_post_for_uid` leave the IPC-allocated id alive when post-insert steps (event flag fetch, monitor init) fail — partial-failure inconsistency.
  12. `notification_get_check_box_checked` returns `*checked=false` whenever `noti->check_box==false`, ignoring any prior `notification_set_check_box_checked(true)` call — subtle.
  13. `notification_get_pairing_type` string compare is case-sensitive on `"true"` — any other stored value silently returns `false`.
  14. `notification_channel_free` does not null-out fields after free; double-free is UB.
  15. `notification_op_get_data` writes to `data` via `*((int*)data)` and `*((notification_h *)data)` without alignment / size guarantees from the caller — UB if misaligned.
# Test Scenario Inventory: notification DB & Settings Layer

Files:
- `notification_noti.c` — 24 EXPORT_API functions (DB operations on noti_list, noti_template, noti_channel)
- `notification_setting.c` — 50 EXPORT_API functions (setting accessors + DnD + system_setting + dnd callbacks)
- `notification_setting_service.c` — 13 EXPORT_API functions (server-side setting DB ops)

---

## Common Templates

**T_get_setting_field** — getter on opaque handle `(handle, out*)`:
- P1: valid handle + valid out → `NONE`, `*out = handle->field`
- N1: `handle == NULL` → `INVALID_PARAMETER`
- N2: `out == NULL` → `INVALID_PARAMETER`
- E1: field at default/zero value
- C1: field after preceding setter

**T_set_setting_field** — setter on opaque handle `(handle, value)`:
- P1: valid handle + value → `NONE`, `handle->field == value`
- N1: `handle == NULL` → `INVALID_PARAMETER`
- E1: extreme value (0, INT_MIN, INT_MAX, false, true)
- C1: idempotent re-set with same value

**T_db_update** — SQL UPDATE wrapper:
- P1: matching row → `NONE`
- N1: NULL required arg → `INVALID_PARAMETER`
- N2: `notification_db_open()` fails → `get_last_result()` (`FROM_DB` / `IO_ERROR`)
- N3: `sqlite3_mprintf` OOM → `OUT_OF_MEMORY`
- N4: `notification_db_exec` fails → `FROM_DB`
- E1: no matching row (num_changes==0) → `NONE` (or `NOT_EXIST_ID` for app_disabled/pkg_disabled)

**T_db_insert** — SQL INSERT wrapper:
- P1: new row → `NONE`
- N1: NULL required arg → `INVALID_PARAMETER`
- N2: open db fails → `get_last_result()` (`FROM_DB`)
- N3: mprintf OOM → `OUT_OF_MEMORY`
- N4: prepare/step fails (UNIQUE etc.) → `FROM_DB`
- E1: empty string arg
- C1: duplicate unique key

**T_db_select** — SQL SELECT wrapper:
- P1: row found → `NONE` + out populated
- N1: NULL out → `INVALID_PARAMETER`
- N2: open db fails → `get_last_result()`
- N3: mprintf OOM → `OUT_OF_MEMORY`
- N4: prepare fails → `FROM_DB`
- N5: malloc(result) fails → `OUT_OF_MEMORY`
- E1: no rows → `NOT_EXIST_ID` (or `NONE` for count queries)

**T_db_delete** — SQL DELETE wrapper:
- P1: row exists → `NONE`
- N1: NULL arg → `INVALID_PARAMETER`
- N2: open db fails → `get_last_result()`
- N3: mprintf OOM → `OUT_OF_MEMORY`
- N4: db_exec fails → `FROM_DB`
- E1: nothing to delete → `NONE` (silent)

---

## File 1 — notification_noti.c (24 functions)

### `int notification_noti_insert(notification_h noti)` — L1050
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `noti == NULL` L1059, or `_check_text_input != NONE` L1078 |
| PERMISSION_DENIED | `_is_allowed_to_notify(noti) == false` L1064 |
| FROM_DB / IO_ERROR | `notification_db_open` fails → `get_last_result()` L1086 |
| OUT_OF_MEMORY | `sqlite3_mprintf` returns NULL L1091 |
| FROM_DB | `sqlite3_prepare_v2 != SQLITE_OK` L1100, or `sqlite3_step` not OK/DONE L1117 |
| NONE | success L1116 |

**Scenarios:**
- [P1] valid noti, allowed-to-notify, insert succeeds → `NONE`, `noti->priv_id == last_rowid`
- [N1] `noti == NULL` → `INVALID_PARAMETER`
- [N2] `_is_allowed_to_notify == false` (DB row blocks) → `PERMISSION_DENIED`
- [N3] db_open fails → `FROM_DB` (via get_last_result)
- [N4] sqlite3_mprintf OOM → `OUT_OF_MEMORY`
- [N5] prepare_v2 fails (malformed SQL/schema) → `FROM_DB`
- [N6] step fails (constraint or busy) → `FROM_DB`
- [N7] `_check_text_input` invalid → `INVALID_PARAMETER`
- [E1] noti with NULL caller_app_id (NOTIFICATION_CHECK_STR yields empty)
- [E2] do_not_disturb returns warn → still proceeds
- [C1] pop-up disabled → display_applist masked, still inserts

### `int notification_noti_get_by_priv_id(notification_h noti, int priv_id)` — L1137
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `priv_id < 0` or `noti == NULL` L1142 |
| OUT_OF_MEMORY | mprintf NULL L1148 |
| NONE / FROM_DB / NOT_EXIST_ID | `_get_notification(query_where, noti)` L1155 |

**Scenarios:**
- [P1] valid priv_id + handle → `NONE`
- [N1] `priv_id < 0` → `INVALID_PARAMETER`
- [N2] `noti == NULL` → `INVALID_PARAMETER`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] _get_notification can't find row → `NOT_EXIST_ID`
- [E1] priv_id == 0 (boundary)
- [E2] priv_id == INT_MAX

### `int notification_noti_get_by_tag(notification_h noti, char *app_id, char *tag, uid_t uid)` — L1165
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `tag == NULL` or `noti == NULL` L1170 |
| OUT_OF_MEMORY | mprintf NULL L1177 |
| NONE / NOT_EXIST_ID / FROM_DB | _get_notification |

**Scenarios:**
- [P1] valid app_id+tag → `NONE`
- [N1] `tag == NULL` → `INVALID_PARAMETER`
- [N2] `noti == NULL` → `INVALID_PARAMETER`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] no row → `NOT_EXIST_ID`
- [E1] `app_id == NULL` (allowed — %Q handles NULL)
- [E2] empty tag string
- [C1] uid=0 (root)

### `int notification_noti_update(notification_h noti)` — L1193
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `noti == NULL` L1200 |
| PERMISSION_DENIED | `_is_allowed_to_notify == false` L1205 |
| FROM_DB / IO_ERROR | db_open fails L1220 |
| NOT_EXIST_ID | `_notification_noti_check_priv_id` not ALREADY_EXIST_ID L1225 |
| OUT_OF_MEMORY | mprintf NULL L1233 |
| FROM_DB | prepare fails L1241, or step !OK/DONE L1257 |
| NONE | step OK/DONE L1255 |

**Scenarios:**
- [P1] update existing row → `NONE`
- [N1] noti NULL → `INVALID_PARAMETER`
- [N2] not allowed → `PERMISSION_DENIED`
- [N3] db_open fail → `FROM_DB`
- [N4] priv_id not in DB → `NOT_EXIST_ID`
- [N5] mprintf OOM → `OUT_OF_MEMORY`
- [N6] prepare fail → `FROM_DB`
- [N7] step fail (constraint) → `FROM_DB`
- [E1] same priv_id but different uid
- [C1] _create_update_query inner failure propagated

### `int notification_noti_delete_all(notification_type_e type, const char *app_id, int *deleted_num, int **deleted_list, uid_t uid)` — L1273
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L1287 |
| OUT_OF_MEMORY | mprintf NULL (L1297, L1312, L1333, L1370) or calloc fail L1349 |
| FROM_DB | prepare fail L1339, or db_exec fail |
| NONE | success |

**Scenarios:**
- [P1] type=NONE, app_id=NULL, uid=N → all rows for uid deleted, `*deleted_num == count`
- [P2] type set, app_id set → filtered delete
- [P3] deleted_list non-NULL → populated, deleted_num set
- [N1] db_open fails → `FROM_DB`
- [N2] mprintf OOM (each branch) → `OUT_OF_MEMORY`
- [N3] _get_noti_count fails → propagated
- [N4] prepare fails on SELECT priv_id → `FROM_DB`
- [N5] calloc(tmp) fails → `OUT_OF_MEMORY`
- [N6] notification_db_exec fails → `FROM_DB` (tmp freed)
- [E1] app_id == "" (empty) → same as NULL branch
- [E2] count == 0 → skip SELECT, just DELETE
- [E3] deleted_list == NULL → don't allocate tmp
- [C1] deleted_num == NULL → don't set

### `int notification_noti_delete_by_priv_id(const char *app_id, int priv_id)` — L1407
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `app_id == NULL` L1413 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L1422 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] valid app_id, existing priv_id → `NONE`
- [N1] app_id == NULL → `INVALID_PARAMETER`
- [N2] db_open fails → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] db_exec fails → `FROM_DB`
- [E1] no matching row → `NONE` (silent)
- [E2] priv_id == 0

### `int notification_noti_delete_by_priv_id_get_changes(const char *app_id, int priv_id, int *num_changes, uid_t uid)` — L1440
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L1449 |
| OUT_OF_MEMORY | mprintf NULL L1456 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] delete existing → `NONE`, `*num_changes >= 1`
- [N1] db_open fails → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] db_exec fail → `FROM_DB`
- [E1] no row → `NONE`, `*num_changes == 0`
- [E2] `app_id == NULL` (allowed by %Q, but matches nothing)
- [C1] num_changes == NULL out → db_exec still runs (NULL safe)

### `int notification_noti_delete_by_display_applist(int display_applist, int *deleted_num, notification_deleted_list_info_s **deleted_list, uid_t uid)` — L1475
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `display_applist < NOTIFICATION_DISPLAY_APP_NOTIFICATION_TRAY` L1489 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL or calloc(info) fail L1535 |
| FROM_DB | prepare fail L1525, or db_exec fail |
| NONE | success |

**Scenarios:**
- [P1] display_applist set, deleted rows match → `NONE`
- [N1] display_applist < TRAY → `INVALID_PARAMETER`
- [N2] db_open fails → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] _get_noti_count fail → propagated
- [N5] prepare fail → `FROM_DB`
- [N6] calloc fail → `OUT_OF_MEMORY` (info freed via __free_deleted_list)
- [N7] db_exec fail → `FROM_DB`, deleted_list freed
- [E1] count == 0 → skip alloc, just exec DELETE
- [E2] deleted_list NULL → don't allocate info
- [C1] deleted_num NULL → not set

### `int notification_noti_get_count(notification_type_e type, const char *app_id, int group_id, int priv_id, int *count, uid_t uid)` — L1597
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L1620 |
| OUT_OF_MEMORY | mprintf NULL (multiple sites L1626, L1653, L1661, L1672, L1682, L1688) |
| FROM_DB | prepare fail L1694 |
| NONE | success |

**Scenarios:**
- [P1] group_id=NONE, priv_id=NONE, type=NONE → returns total count for app_id,uid
- [P2] group_id set → filter on group_id
- [P3] priv_id set → resolves internal_group_id
- [P4] type set + SIM_INSERTED → adds `type=` clause
- [P5] SIM not inserted → adds `flag_simmode = 0`
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM at any of 6 sites → `OUT_OF_MEMORY`
- [N3] prepare fail → `FROM_DB`
- [E1] vconf_get_int fails → defaults to SIM_INSERTED
- [E2] step returns nothing → `*count == 0`
- [C1] app_id == NULL (matches no row)

### `int notification_noti_get_all_count(notification_type_e type, int *count, uid_t uid)` — L1733
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `count == NULL` L1741 |
| FROM_DB / IO_ERROR | db_open fail → `get_last_result()` L1747 |
| FROM_DB | mprintf NULL L1763 (note: returns FROM_DB not OOM here) |
| FROM_DB | prepare fail L1771 |
| NONE | success |

**Scenarios:**
- [P1] type=NONE → count of all rows for uid → `NONE`, `*count == N`
- [P2] type set → count filtered
- [N1] `count == NULL` → `INVALID_PARAMETER`
- [N2] db_open fails → `FROM_DB`
- [N3] mprintf OOM → `FROM_DB` (note: code uses FROM_DB instead of OOM)
- [N4] prepare fail → `FROM_DB`
- [E1] no rows → `*count == 0`
- [C1] uid == 0

### `int notification_noti_get_grouping_list(notification_type_e type, int page_number, int count_per_page, notification_list_h *list, int *list_count, uid_t uid)` — L1800
**Errno map:**
| Return | Predicate |
| --- | --- |
| OUT_OF_MEMORY | mprintf NULL (L1824, L1834, L1842, L1862) |
| Propagated NONE/FROM_DB | `_get_notification_list` L1867 |

**Scenarios:**
- [P1] uid=GLOBAL_UID, count_per_page>0, type set → paginated list
- [P2] uid != GLOBAL_UID → uid filter added
- [P3] count_per_page <= 0 → no LIMIT
- [P4] SIM not inserted → flag_simmode=0
- [N1] mprintf OOM (each of 4 sites) → `OUT_OF_MEMORY`
- [N2] _get_notification_list fails → propagated
- [E1] page_number == 1 (start_index=0)
- [E2] count_per_page == 0 → falls to else branch
- [C1] type=NONE + SIM inserted → query_where NULL is OK

### `int notification_noti_get_detail_list(const char *app_id, int group_id, int priv_id, int count, notification_list_h *list, uid_t uid)` — L1882
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L1902 |
| OUT_OF_MEMORY | mprintf NULL L1931, L1940 |
| NONE / FROM_DB | _get_notification_list |

**Scenarios:**
- [P1] priv_id=NONE,group_id=NONE → all rows for app_id+uid
- [P2] priv_id set → resolves internal_group_id
- [P3] SIM not inserted → adds flag_simmode=0
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] _get_notification_list fail → propagated
- [E1] vconf fails → defaults SIM_INSERTED
- [E2] app_id == NULL (no rows match)

### `int notification_noti_check_tag(notification_h noti)` — L1962
**Errno map:**
| Return | Predicate |
| --- | --- |
| NOT_EXIST_ID | `noti->tag == NULL` or `strlen(noti->tag)==0` L1972, or step returned no row L2013 |
| FROM_DB / IO_ERROR | db_open fail L1978 |
| OUT_OF_MEMORY | mprintf NULL L1986 |
| FROM_DB | prepare fail L1993 (note: ret left as sqlite ret) |
| ALREADY_EXIST_ID | row found, `result > 0` L2011 (sets noti->priv_id) |

**Scenarios:**
- [P1] new tag → `NOT_EXIST_ID`
- [P2] existing tag → `ALREADY_EXIST_ID`, `noti->priv_id` updated
- [N1] noti->tag == NULL → `NOT_EXIST_ID` (early)
- [N2] strlen(noti->tag)==0 → `NOT_EXIST_ID`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] prepare fail → sqlite ret leaks (potential bug — ret is sqlite error code, not mapped)
- [E1] noti->caller_app_id NULL → NOTIFICATION_CHECK_STR returns ""

### `int notification_noti_check_count_for_template(notification_h noti, int *count)` — L2029
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `noti==NULL` or `count==NULL` L2037 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2047 |
| FROM_DB | prepare fail L2055 |
| NONE | success, `*count` set |

**Scenarios:**
- [P1] noti+count valid → `NONE`, `*count == N`
- [N1] noti == NULL → `INVALID_PARAMETER`
- [N2] count == NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] prepare fail → `FROM_DB`
- [E1] no template rows → `*count == 0`
- [C1] noti->caller_app_id NULL

### `int notification_noti_add_template(notification_h noti, char *template_name)` — L2085
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `noti==NULL` or `template_name==NULL` L2093 |
| FROM_DB / IO_ERROR | db_open fail L2102 |
| OUT_OF_MEMORY | mprintf NULL L2111 |
| FROM_DB | prepare fail L2119, step !OK/DONE L2135 |
| NONE | step OK/DONE L2133 |

**Scenarios:**
- [P1] valid noti+name → `NONE` (INSERT OR REPLACE)
- [N1] noti == NULL → `INVALID_PARAMETER`
- [N2] template_name == NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] prepare fail → `FROM_DB`
- [N6] step fail → `FROM_DB`
- [N7] _create_insertion_query inner fail → propagated
- [E1] empty template_name string
- [C1] existing same key → REPLACE semantics

### `int notification_noti_get_package_template(notification_h noti, char *app_id, char *template_name)` — L2151
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | any of noti/app_id/template_name NULL L2156 |
| OUT_OF_MEMORY | mprintf NULL L2163 |
| NONE / NOT_EXIST_ID / FROM_DB | _get_notification |

**Scenarios:**
- [P1] valid → `NONE`
- [N1] noti NULL → `INVALID_PARAMETER`
- [N2] app_id NULL → `INVALID_PARAMETER`
- [N3] template_name NULL → `INVALID_PARAMETER`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] not found → `NOT_EXIST_ID`

### `int notification_noti_delete_template(const char *pkg_id)` — L2176
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `pkg_id == NULL` L2182 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2191 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] valid pkg_id → `NONE`
- [N1] pkg_id NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] db_exec fail → `FROM_DB`
- [E1] no rows → `NONE`

### `void notification_noti_init_data(void)` — L2211
**Errno map:**
| Return | Predicate |
| --- | --- |
| (void) | always |

**Scenarios:**
- [P1] db_open OK + query OK → DELETE executed
- [N1] db_open fail → early return (logged)
- [N2] mprintf OOM → close db + early return
- [N3] db_exec fail → logged, still closes db
- [E1] no ONGOING+VOLATILE rows → exec succeeds, 0 rows affected
- [C1] no return value — purely side effect

### `int notification_noti_check_limit(notification_h noti, uid_t uid, GList **list)` — L2240
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | `noti == NULL` L2250 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2259, L2281 |
| FROM_DB | prepare fail L2289, or _get_noti_count fail |
| NONE | success |

**Scenarios:**
- [P1] count <= NOTI_LIMIT → `NONE`, list unchanged
- [P2] count > NOTI_LIMIT → `NONE`, list appended with priv_ids to delete
- [N1] noti NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM (both sites) → `OUT_OF_MEMORY`
- [N4] _get_noti_count fail → propagated
- [N5] prepare fail → `FROM_DB`
- [E1] caller_app_id NULL → matches nothing
- [C1] *list NULL (deref'd at g_list_append — caller must pass &list)

### `int notification_noti_get_channel(const char *app_id, const char *channel_name, int *blockable, int *is_blocked)` — L2320
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/channel_name/is_blocked NULL L2332 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2343 |
| FROM_DB | prepare fail L2348, or step !ROW/!DONE L2364 |
| NONE | SQLITE_ROW or SQLITE_DONE |

**Scenarios:**
- [P1] channel exists → `NONE`, `*blockable`/`*is_blocked` set
- [P2] channel absent (SQLITE_DONE) → `NONE`, zero
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] channel_name NULL → `INVALID_PARAMETER`
- [N3] is_blocked NULL → `INVALID_PARAMETER`
- [N4] db_open fail → `FROM_DB`
- [N5] mprintf OOM → `OUT_OF_MEMORY`
- [N6] prepare fail → leaks sqlite ret (potential)
- [N7] step gives error code → `FROM_DB`
- [E1] blockable NULL → not validated, deref crash possible (corner)

### `int notification_noti_insert_channel(const char *app_id, const char *channel_name, int blockable, int is_blocked)` — L2385
**Errno map:** T_db_insert
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/channel_name NULL L2394 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2405 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] new (app_id, channel_name) → `NONE`
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] channel_name NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] db_exec fail (e.g., UNIQUE constraint) → `FROM_DB`
- [E1] empty channel_name
- [C1] duplicate → constraint violation

### `int notification_noti_delete_channel(const char *app_id, const char *channel_name)` — L2426
**Errno map:** T_db_delete
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/channel_name NULL L2435 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2445 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] existing → `NONE`
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] channel_name NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] db_exec fail → `FROM_DB`
- [E1] missing row → `NONE`

### `int notification_noti_update_channel(const char *app_id, const char *channel_name, int blockable, int is_blocked)` — L2466
**Errno map:** T_db_update
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/channel_name NULL L2475 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2486 |
| NONE / FROM_DB | db_exec |

**Scenarios:**
- [P1] existing → `NONE`, fields updated
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] channel_name NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] db_exec fail → `FROM_DB`
- [E1] missing row → `NONE` (no changes)

### `int notification_noti_get_channel_list(const char *app_id, GList **channel_list)` — L2507
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/channel_list NULL L2521 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L2530 |
| FROM_DB / sqlite ret | prepare fail L2535 |
| NONE | success (also when 0 rows) |

**Scenarios:**
- [P1] N rows → list appended N channel handles, `NONE`
- [P2] 0 rows → empty list, `NONE`
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] channel_list NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] prepare fail → sqlite ret (not mapped; potential bug)
- [E1] notification_channel_create_with_info returns NULL → row skipped
- [C1] caller passes pre-existing *channel_list → appended (not replaced)

---

## File 2 — notification_setting.c (50 functions)

### `int notification_setting_get_setting_array_for_uid(notification_setting_h *setting_array, int *count, uid_t uid)` — L54
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | setting_array/count NULL L56 |
| Propagated | `notification_tidl_request_get_setting_array(...)` L61 |

**Scenarios:**
- [P1] valid args → tidl result propagated
- [N1] setting_array NULL → `INVALID_PARAMETER`
- [N2] count NULL → `INVALID_PARAMETER`
- [N3] tidl returns IO_ERROR → propagated
- [N4] tidl returns NOT_EXIST_ID → propagated
- [E1] uid=0 (root) → forwarded

### `int notification_setting_get_setting_array(notification_setting_h *setting_array, int *count)` — L64
**Errno map:** delegates to `_for_uid(..., aul_getuid())`.

**Scenarios:**
- [P1] valid → propagated
- [N1] setting_array NULL → `INVALID_PARAMETER`
- [N2] count NULL → `INVALID_PARAMETER`
- [E1] aul_getuid()==-1 corner (still forwarded as uid_t)

### `int notification_setting_get_setting_by_appid_for_uid(const char *app_id, notification_setting_h *setting, uid_t uid)` — L69
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/setting NULL L71 |
| Propagated | tidl_request_get_setting_by_app_id |

**Scenarios:**
- [P1] valid → tidl propagated
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] setting NULL → `INVALID_PARAMETER`
- [N3] tidl IO_ERROR → propagated
- [N4] tidl NOT_EXIST_ID → propagated
- [E1] empty app_id string forwarded

### `int notification_setting_get_setting_by_package_name(const char *package_name, notification_setting_h *setting)` — L81
**Errno map:** delegate to `_for_uid(package_name, setting, aul_getuid())`.

**Scenarios:**
- [P1] valid → propagated
- [N1] package_name NULL → `INVALID_PARAMETER` (from delegate)
- [N2] setting NULL → `INVALID_PARAMETER`
- [E1] empty package_name

### `int notification_setting_get_setting(notification_setting_h *setting)` — L88
**Errno map:**
| Return | Predicate |
| --- | --- |
| NOT_EXIST_ID | `notification_get_app_id_by_pid(getpid())` returns NULL L94 |
| Propagated | get_setting_by_package_name |

**Scenarios:**
- [P1] running PID has known app_id → propagated tidl result
- [N1] PID resolves to NULL app_id → `NOT_EXIST_ID`
- [N2] tidl IO_ERROR → propagated
- [E1] setting NULL → propagated `INVALID_PARAMETER` via inner call
- [C1] app_id allocated, must be freed

### `int notification_setting_get_package_name(notification_setting_h setting, char **value)` — L106
Uses T_get_setting_field.
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | setting/value NULL L108 |
| NOT_EXIST_ID | `setting->package_name == NULL` L113 |
| NONE | success |

**Scenarios:**
- [P1] populated handle → `NONE`, `*value = strdup(package_name)`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [N3] package_name NULL → `NOT_EXIST_ID`
- [E1] empty package_name (SAFE_STRDUP("")) → `NONE`
- [C1] SAFE_STRDUP OOM (returns NULL) — caller sees NULL `*value` but ret still `NONE`

### `int notification_setting_get_appid(notification_setting_h setting, char **app_id)` — L125
Same shape as get_package_name (T_get_setting_field + NOT_EXIST_ID for NULL field).

**Scenarios:**
- [P1] populated → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] app_id NULL → `INVALID_PARAMETER`
- [N3] setting->app_id NULL → `NOT_EXIST_ID`
- [E1] empty app_id string
- [C1] SAFE_STRDUP OOM (`*app_id == NULL` corner)

### `int notification_setting_get_allow_to_notify(notification_setting_h setting, bool *value)` — L144
T_get_setting_field.

**Scenarios:**
- [P1] valid → `NONE`, `*value == setting->allow_to_notify`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] field == false / true

### `int notification_setting_set_allow_to_notify(notification_setting_h setting, bool value)` — L156
T_set_setting_field.

**Scenarios:**
- [P1] valid → `NONE`, handle updated
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] value true→false toggle

### `int notification_setting_get_do_not_disturb_except(notification_setting_h setting, bool *value)` — L168
T_get_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] default 0

### `int notification_setting_set_do_not_disturb_except(notification_setting_h setting, bool value)` — L180
T_set_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] value true/false

### `int notification_setting_get_visibility_class(notification_setting_h setting, int *value)` — L193
T_get_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] INT_MIN/INT_MAX

### `int notification_setting_set_visibility_class(notification_setting_h setting, int value)` — L205
T_set_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] negative class

### `int notification_setting_get_pop_up_notification(notification_setting_h setting, bool *value)` — L218
T_get_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] default 0

### `int notification_setting_set_pop_up_notification(notification_setting_h setting, bool value)` — L229
T_set_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] true/false

### `int notification_setting_get_lock_screen_content(notification_setting_h setting, lock_screen_content_level_e *level)` — L240
T_get_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] level NULL → `INVALID_PARAMETER`
- [E1] enum 0/MAX

### `int notification_setting_set_lock_screen_content(notification_setting_h setting, lock_screen_content_level_e level)` — L252
T_set_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] out-of-range enum (still stored)

### `int notification_setting_get_app_disabled(notification_setting_h setting, bool *value)` — L264
T_get_setting_field.
- [P1] → `NONE`
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] default 0

### `int notification_setting_update_setting_for_uid(notification_setting_h setting, uid_t uid)` — L277
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | setting NULL L279 |
| Propagated | `notification_tidl_update_setting(setting, uid)` L284 |

- [P1] valid → propagated
- [N1] setting NULL → `INVALID_PARAMETER`
- [N2] tidl IO_ERROR → propagated
- [E1] uid=0

### `int notification_setting_update_setting(notification_setting_h setting)` — L287
Delegate to `_for_uid` with aul_getuid().
- [P1] valid → propagated
- [N1] setting NULL → `INVALID_PARAMETER`

### `int notification_setting_free_notification(notification_setting_h setting)` — L292
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | setting NULL L294 |
| NONE | freed |

- [P1] valid → `NONE`, package_name/app_id/handle freed
- [N1] setting NULL → `INVALID_PARAMETER`
- [E1] handle with NULL fields (SAFE_FREE handles NULL)
- [C1] double-free guarded by SAFE_FREE only on the inner pointers; calling twice on same handle = UAF (corner)

### `int notification_setting_refresh_setting_table(uid_t uid)` — L526
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L537 |
| FROM_DB | pkgmgrinfo_appinfo_filter_create/add_string/foreach not PMINFO_R_OK L541, L549, L559 |
| NONE | success |

- [P1] uid valid, packages iterated → `NONE`
- [N1] db_open fail → `FROM_DB`
- [N2] filter_create fail → `FROM_DB`
- [N3] add_string PRIVILEGE fail → `FROM_DB`
- [N4] foreach_appinfo fail → `FROM_DB`
- [E1] no privileged packages → still `NONE`
- [C1] uid=0

### `int notification_setting_insert_package_for_uid(const char *package_name, uid_t uid)` — L577
Delegate to `_install_and_update_package` (NULL package_name passed to pkgmgrinfo_appinfo_filter_add_string can fail).
**Errno map:** see _install_and_update_package: db_open fail, FROM_DB at each pkgmgr stage.

- [P1] valid package → `NONE`
- [N1] db_open fail → `FROM_DB`
- [N2] filter_create fail → `FROM_DB`
- [N3] add_string(PRIVILEGE) fail → `FROM_DB`
- [N4] add_string(APP_PACKAGE) fail → `FROM_DB`
- [N5] foreach_appinfo fail → `FROM_DB`
- [E1] empty package_name
- [C1] package not present in DB → no insert, still `NONE`

### `int notification_setting_delete_package_for_uid(const char *package_name, uid_t uid)` — L582
Delegate to `_delete_package_from_setting_db`.
**Errno map:** db_open fail, OUT_OF_MEMORY mprintf, FROM_DB db_exec.

- [P1] existing package → `NONE`
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] db_exec fail → `FROM_DB`
- [E1] package not in table → early `NONE`
- [C1] package_name NULL → _is_package_in_setting_table likely false → no-op `NONE`

### `int notification_system_setting_load_system_setting_for_uid(notification_system_setting_h *system_setting, uid_t uid)` — L587
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | system_setting NULL L589 |
| Propagated | tidl_request_load_system_setting |

- [P1] valid → propagated
- [N1] system_setting NULL → `INVALID_PARAMETER`
- [N2] tidl IO_ERROR → propagated
- [E1] uid=0

### `int notification_system_setting_load_system_setting(notification_system_setting_h *system_setting)` — L597
Delegate to `_for_uid` with aul_getuid().
- [P1] → propagated
- [N1] NULL → `INVALID_PARAMETER`

### `int notification_system_setting_update_system_setting_for_uid(notification_system_setting_h system_setting, uid_t uid)` — L602
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | system_setting NULL L604 |
| Propagated | tidl_update_system_setting |

- [P1] → propagated
- [N1] NULL → `INVALID_PARAMETER`
- [E1] uid=0

### `int notification_system_setting_update_system_setting(notification_system_setting_h system_setting)` — L612
Delegate.
- [P1] → propagated
- [N1] NULL → `INVALID_PARAMETER`

### `int notification_system_setting_free_system_setting(notification_system_setting_h system_setting)` — L617
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | NULL L619 |
| NONE | freed |

- [P1] handle with exceptions → `NONE`, g_list_free_full called
- [P2] handle with NULL exceptions → `NONE`, no list free
- [N1] NULL → `INVALID_PARAMETER`
- [C1] double-free corner

### `int notification_system_setting_get_do_not_disturb(notification_system_setting_h system_setting, bool *value)` — L634
T_get_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [E1] default 0

### `int notification_system_setting_set_do_not_disturb(notification_system_setting_h system_setting, bool value)` — L646
T_set_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] toggle

### `int notification_system_setting_get_visibility_class(notification_system_setting_h system_setting, int *value)` — L658
T_get_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`

### `int notification_system_setting_set_visibility_class(notification_system_setting_h system_setting, int value)` — L670
T_set_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] INT_MIN/INT_MAX

### `int notification_system_setting_dnd_schedule_get_enabled(notification_system_setting_h system_setting, bool *enabled)` — L682
T_get_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] enabled NULL → `INVALID_PARAMETER`

### `int notification_system_setting_dnd_schedule_set_enabled(notification_system_setting_h system_setting, bool enabled)` — L694
T_set_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`

### `int notification_system_setting_dnd_schedule_get_day(notification_system_setting_h system_setting, int *day)` — L706
T_get_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] day NULL → `INVALID_PARAMETER`
- [E1] day == bitmask 0/127 (all days)

### `int notification_system_setting_dnd_schedule_set_day(notification_system_setting_h system_setting, int day)` — L718
T_set_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] day < 0 or > 127 (stored as-is; not validated)

### `int notification_system_setting_dnd_schedule_get_start_time(notification_system_setting_h system_setting, int *hour, int *min)` — L730
**Errno map:** INVALID if handle/hour/min NULL; else NONE.

- [P1] → `NONE`, hour/min set
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] hour NULL → `INVALID_PARAMETER`
- [N3] min NULL → `INVALID_PARAMETER`
- [E1] hour=0,min=0

### `int notification_system_setting_dnd_schedule_set_start_time(notification_system_setting_h system_setting, int hour, int min)` — L743
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] hour=24, min=60 (no validation; stored)
- [E2] negative hour/min

### `int notification_system_setting_dnd_schedule_get_end_time(notification_system_setting_h system_setting, int *hour, int *min)` — L756
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] hour NULL → `INVALID_PARAMETER`
- [N3] min NULL → `INVALID_PARAMETER`

### `int notification_system_setting_dnd_schedule_set_end_time(notification_system_setting_h system_setting, int hour, int min)` — L769
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] end < start corner

### `int notification_system_setting_get_lock_screen_content(notification_system_setting_h system_setting, lock_screen_content_level_e *level)` — L782
T_get_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] level NULL → `INVALID_PARAMETER`

### `int notification_system_setting_set_lock_screen_content(notification_system_setting_h system_setting, lock_screen_content_level_e level)` — L794
T_set_setting_field.
- [P1] → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [E1] enum out-of-range

### `int notification_system_setting_get_dnd_allow_exceptions(notification_system_setting_h system_setting, dnd_allow_exception_type_e type, int *value)` — L821
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | handle/value NULL L826 OR list lookup returns NULL L836 |
| NONE | match found |

- [P1] type exists in list → `NONE`, `*value` set
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] value NULL → `INVALID_PARAMETER`
- [N3] type not in list → `INVALID_PARAMETER`
- [E1] empty list → `INVALID_PARAMETER`

### `int notification_system_setting_set_dnd_allow_exceptions(notification_system_setting_h system_setting, dnd_allow_exception_type_e type, int value)` — L843
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | handle NULL L848 |
| OUT_OF_MEMORY | malloc fail L862 |
| NONE | added/updated |

- [P1] new type → allocate, append → `NONE`
- [P2] existing type → update value → `NONE`
- [N1] handle NULL → `INVALID_PARAMETER`
- [N2] malloc fail → `OUT_OF_MEMORY`
- [E1] value 0/MAX
- [C1] type duplicates twice in list (first match wins on update)

### `int notification_register_system_setting_dnd_changed_cb_for_uid(dnd_changed_cb callback, void *user_data, uid_t uid)` — L914
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | callback NULL L920, or duplicate found L946 |
| IO_ERROR | tidl_monitor_init fail L923 |
| OUT_OF_MEMORY | malloc fail L932 |
| NONE | inserted into hash |

- [P1] first cb for uid → hash created/inserted → `NONE`
- [P2] new cb for existing uid list → appended → `NONE`
- [N1] callback NULL → `INVALID_PARAMETER`
- [N2] tidl_monitor_init fail → `IO_ERROR`
- [N3] malloc(dnd_data) fail → `OUT_OF_MEMORY`
- [N4] duplicate callback → free dnd_data, `INVALID_PARAMETER`
- [E1] user_data NULL → allowed
- [C1] multiple uids served by same hash

### `int notification_register_system_setting_dnd_changed_cb(dnd_changed_cb callback, void *user_data)` — L960
Delegate.
- [P1] → propagated
- [N1] callback NULL → `INVALID_PARAMETER`

### `int notification_unregister_system_setting_dnd_changed_cb_for_uid(dnd_changed_cb callback, uid_t uid)` — L965
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | callback NULL L971, hash NULL L974, list for uid NULL L979, or callback not found L989 |
| NONE | removed |

- [P1] removal of existing cb → `NONE`; may call tidl_monitor_fini when hash empty
- [N1] callback NULL → `INVALID_PARAMETER`
- [N2] hash NULL (never registered) → `INVALID_PARAMETER`
- [N3] no list for uid → `INVALID_PARAMETER`
- [N4] callback not in list → `INVALID_PARAMETER`
- [E1] last cb in uid list → uid removed via g_hash_table_steal
- [E2] last cb overall → tidl_monitor_fini invoked
- [C1] same cb registered for multiple uids → only the per-uid one removed

### `int notification_unregister_system_setting_dnd_changed_cb(dnd_changed_cb callback)` — L1008
Delegate.
- [P1] → propagated
- [N1] callback NULL → `INVALID_PARAMETER`

### `int notification_system_setting_init_system_setting_table(uid_t uid)` — L1062
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L1072 |
| OUT_OF_MEMORY | mprintf NULL L1085, L1100 |
| Propagated FROM_DB | db_exec fail L1091, L1106 |
| NONE | success, or uid already initialized (early out) |

- [P1] uid not present → insert into system_setting + dnd_allow_exception, `NONE`
- [P2] uid already present → early `NONE`
- [N1] db_open fail → `FROM_DB`
- [N2] system_setting mprintf OOM → `OUT_OF_MEMORY`
- [N3] dnd_allow_exception mprintf OOM → `OUT_OF_MEMORY`
- [N4] db_exec system_setting fail → propagated
- [N5] db_exec dnd_allow_exception fail → propagated
- [E1] uid=0 (root)
- [C1] table missing — propagates FROM_DB from db_exec

---

## File 3 — notification_setting_service.c (13 functions)

### `int noti_setting_service_get_setting_by_app_id(const char *app_id, notification_setting_h *setting, uid_t uid)` — L90
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id/setting NULL L103 |
| FROM_DB / IO_ERROR | db_open fail L109 |
| OUT_OF_MEMORY | mprintf NULL L115, malloc fail L140 |
| FROM_DB | sqlite3_get_table not SQLITE_OK L122 |
| NOT_EXIST_ID | row_count==0 L129 |
| NONE | populated setting |

- [P1] row exists → `NONE`, `*setting` populated
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] setting NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] get_table fail → `FROM_DB`
- [N6] row_count==0 → `NOT_EXIST_ID`
- [N7] malloc(result) fail → `OUT_OF_MEMORY`
- [E1] empty app_id string
- [C1] uid=0

### `int noti_setting_get_setting_array(notification_setting_h *setting_array, int *count, uid_t uid)` — L173
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | setting_array/count NULL L186 |
| FROM_DB / IO_ERROR | db_open fail L191 |
| OUT_OF_MEMORY | mprintf NULL L199, malloc fail L222 |
| FROM_DB | get_table fail L205 |
| NOT_EXIST_ID | row_count==0 L213 |
| NONE | success |

- [P1] N rows → `NONE`, array populated, `*count == N`
- [N1] setting_array NULL → `INVALID_PARAMETER`
- [N2] count NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] get_table fail → `FROM_DB`
- [N6] no rows → `NOT_EXIST_ID`
- [N7] malloc fail → `OUT_OF_MEMORY`
- [E1] only disabled apps → 0 rows → `NOT_EXIST_ID`
- [C1] uid=0

### `int noti_system_setting_load_system_setting(notification_system_setting_h *system_setting, uid_t uid)` — L259
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | system_setting NULL L271 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L283, malloc fail L298 |
| FROM_DB | get_table fail L289 |
| NONE | success (incl. row_count==0 → defaults) |

- [P1] row found → fields populated
- [P2] row_count==0 → all defaults (do_not_disturb=0...) → `NONE`
- [N1] system_setting NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] get_table fail → `FROM_DB`
- [N5] malloc fail → `OUT_OF_MEMORY`
- [E1] uid=0

### `int notification_setting_db_update(const char *package_name, const char *app_id, int allow_to_notify, int do_not_disturb_except, int visibility_class, int pop_up_notification, int lock_screen_content_level, uid_t uid)` — L348
T_db_update.
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | package_name/app_id NULL L357 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L374 |
| NONE / FROM_DB | db_exec |

- [P1] valid → `NONE`
- [N1] package_name NULL → `INVALID_PARAMETER`
- [N2] app_id NULL → `INVALID_PARAMETER`
- [N3] db_open fail → `FROM_DB`
- [N4] mprintf OOM → `OUT_OF_MEMORY`
- [N5] db_exec fail → `FROM_DB`
- [E1] no matching row → `NONE` (silent)
- [E2] visibility_class=INT_MAX

### `int notification_setting_db_update_system_setting(int do_not_disturb, int visibility_class, int dnd_schedule_enabled, int dnd_schedule_day, int dnd_start_hour, int dnd_start_min, int dnd_end_hour, int dnd_end_min, int lock_screen_content_level, uid_t uid)` — L392
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L403 |
| OUT_OF_MEMORY | mprintf NULL L415 |
| NONE / FROM_DB | db_exec |

- [P1] valid → `NONE` (INSERT OR REPLACE)
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] db_exec fail → `FROM_DB`
- [E1] num_changes==0 → still `NONE` (warning logged)
- [C1] uid=0

### `int notification_setting_db_update_do_not_disturb(int do_not_disturb, uid_t uid)` — L440
T_db_update.
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L454 |
| NONE / FROM_DB | db_exec |

- [P1] uid present → `NONE`
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] db_exec fail → `FROM_DB`
- [E1] uid not in table → `NONE` (no rows updated)
- [E2] do_not_disturb=0/1

### `int notification_system_setting_get_dnd_schedule_enabled_uid(uid_t **uids, int *count)` — L475
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L487 |
| OUT_OF_MEMORY | mprintf NULL L494, malloc fail L513 |
| FROM_DB | get_table fail L500 |
| NONE | row_count==0 (early) or success |

- [P1] N enabled uids → `NONE`, *uids set, *count==N
- [P2] no enabled rows → `NONE`, uids/count untouched (caller must zero-init)
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] get_table fail → `FROM_DB`
- [N4] malloc fail → `OUT_OF_MEMORY`
- [E1] uids/count NULL — not validated → corner crash
- [C1] caller responsibility to free *uids

### `int notification_get_dnd_and_allow_to_notify(const char *app_id, int *do_not_disturb, int *do_not_disturb_except, int *allow_to_notify, uid_t uid)` — L542
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id NULL L559, or row_count==0 in setting query L593 or system_setting L610 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L571 or L580 |
| FROM_DB | get_table fail L587 / L603 |
| NONE | success |

- [P1] app_id setting + system row → `NONE`, three outs populated
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM (setting or system) → `OUT_OF_MEMORY`
- [N4] get_table setting fail → `FROM_DB`
- [N5] setting row missing → `INVALID_PARAMETER`
- [N6] get_table system fail → `FROM_DB`
- [N7] system row missing → `INVALID_PARAMETER`
- [E1] do_not_disturb/_except/allow_to_notify pointer NULL — not validated → potential deref
- [C1] uid==TZ_SYS_GLOBALAPP_USER fallback

### `int notification_system_setting_load_dnd_allow_exception(dnd_allow_exception_h *dnd_allow_exception, int *count, uid_t uid)` — L638
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | dnd_allow_exception NULL L651 |
| FROM_DB / IO_ERROR | db_open fail L656 |
| OUT_OF_MEMORY | mprintf NULL L662, malloc fail L680 |
| FROM_DB | get_table fail L668 |
| NONE | row_count==0 or success |

- [P1] N rows → `NONE`, data populated
- [P2] 0 rows → `NONE`, no allocation (count not written — caller must zero-init)
- [N1] dnd_allow_exception NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] get_table fail → `FROM_DB`
- [N5] malloc fail → `OUT_OF_MEMORY`
- [E1] count == NULL — not validated when row_count>0 → crash corner
- [C1] uid=0

### `int notification_system_setting_update_dnd_allow_exception(int type, int value, uid_t uid)` — L711
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L719 |
| OUT_OF_MEMORY | mprintf NULL L726 |
| NONE / FROM_DB | db_exec |

- [P1] valid → `NONE` (INSERT OR REPLACE)
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] db_exec fail → `FROM_DB`
- [E1] num_changes==0 → still `NONE` (warned)
- [E2] type/value INT_MIN/INT_MAX

### `int noti_system_setting_get_do_not_disturb(int *do_not_disturb, uid_t uid)` — L750
**Errno map:**
| Return | Predicate |
| --- | --- |
| FROM_DB / IO_ERROR | db_open fail L761 |
| OUT_OF_MEMORY | mprintf NULL L766 |
| FROM_DB | get_table fail L773, or _get_table_field_data_int returns false L784 |
| INVALID_PARAMETER | row_count==0 L780 |
| NONE | success |

- [P1] uid present → `NONE`, *do_not_disturb set
- [N1] db_open fail → `FROM_DB`
- [N2] mprintf OOM → `OUT_OF_MEMORY`
- [N3] get_table fail → `FROM_DB`
- [N4] no row for uid → `INVALID_PARAMETER`
- [N5] table field extraction fails (NULL cell) → `FROM_DB`
- [E1] do_not_disturb out-pointer NULL — passed to atoi via _get_table_field_data_int — not validated → corner crash

### `int notification_setting_db_update_app_disabled(const char *app_id, bool value, uid_t uid)` — L804
T_db_update.
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | app_id NULL L811 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L822 |
| NOT_EXIST_ID | db_exec NONE but num_changes <= 0 L829 |
| NONE / FROM_DB | db_exec |

- [P1] existing app → `NONE`, num_changes==1
- [N1] app_id NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] db_exec fail → `FROM_DB`
- [N5] no rows affected → `NOT_EXIST_ID`
- [E1] value true/false toggle
- [C1] uid mismatch → no rows → `NOT_EXIST_ID`

### `int notification_setting_db_update_pkg_disabled(const char *pkg_id, bool value, uid_t uid)` — L845
T_db_update (same shape as app_disabled).
**Errno map:**
| Return | Predicate |
| --- | --- |
| INVALID_PARAMETER | pkg_id NULL L852 |
| FROM_DB / IO_ERROR | db_open fail |
| OUT_OF_MEMORY | mprintf NULL L863 |
| NOT_EXIST_ID | num_changes<=0 L870 |
| NONE / FROM_DB | db_exec |

- [P1] existing pkg → `NONE`
- [N1] pkg_id NULL → `INVALID_PARAMETER`
- [N2] db_open fail → `FROM_DB`
- [N3] mprintf OOM → `OUT_OF_MEMORY`
- [N4] db_exec fail → `FROM_DB`
- [N5] no rows affected → `NOT_EXIST_ID`
- [E1] value true/false
- [C1] uid mismatch → `NOT_EXIST_ID`

---

## Coverage check
- notification_noti.c: 24 / 24
- notification_setting.c: 50 / 50
- notification_setting_service.c: 13 / 13
- Total: 87 / 87
# Test Scenario Inventory - notification: DB / List / Shared-File

Scope: 7 EXPORT_API in notification_db.c + 15 EXPORT_API in notification_list.c + 6 EXPORT_API in notification_shared_file.c = 28 functions.

Legend: [P]ositive / [N]egative / [E]dge / [C]orner

Notation:
- NE = NOTIFICATION_ERROR_NONE
- INV = NOTIFICATION_ERROR_INVALID_PARAMETER
- DB = NOTIFICATION_ERROR_FROM_DB
- PERM = NOTIFICATION_ERROR_PERMISSION_DENIED
- OOM = NOTIFICATION_ERROR_OUT_OF_MEMORY
- IO = NOTIFICATION_ERROR_IO_ERROR
- EXIST = NOTIFICATION_ERROR_ALREADY_EXIST_ID

set_last_result(...) is the side-channel for getters that return a pointer.

---

## A. notification_db.c (7/7)

### 1. notification_db_init(void) - LCOV_EXCL but EXPORT_API
Errno map: NE (open + create table + integrity_check ok) | DB (sqlite3_open_v2 fail, exec CREATE fail, integrity check fail or is_db_corrupted=true, recover open/exec fail).
- [P1] DB fresh: opens, runs CREATE_NOTIFICATION_TABLE, PRAGMA integrity ok -> NE.
- [P2] DB already exists and clean -> NE (CREATE table is idempotent via IF NOT EXISTS).
- [N1] sqlite3_open_v2 fails (perm denied on DBPATH dir / disk full) -> DB.
- [N2] CREATE_NOTIFICATION_TABLE exec fails (syntax / locked) -> DB.
- [N3] PRAGMA integrity_check returns ok but sql_ret != SQLITE_OK -> DB.
- [N4] integrity_check callback sees non-ok -> is_db_corrupted=true triggers __recover_corrupted_db -> if recover succeeds returns NE, else DB.
- [E1] sql_ret is SQLITE_CORRUPT or SQLITE_NOTADB -> recovery path runs (unlink DBPATH + reopen + recreate). Verify file is recreated.
- [C1] Recovery: second sqlite3_open_v2(CREATE|RW) fails -> unlink + DB.
- [C2] Recovery: CREATE table after recover fails -> DB, errmsg freed.

### 2. notification_db_open(void)
Errno map (via set_last_result): NE (return non-NULL db) | DB (access fail, open fail with non-PERM) | PERM (sqlite3 returns SQLITE_PERM).
- [P1] DBPATH R/W accessible, open succeeds -> non-NULL handle.
- [N1] access(DBPATH, R_OK|W_OK) != 0 -> NULL, last_result DB.
- [N2] sqlite3_open_v2 returns SQLITE_PERM -> NULL, last_result PERM.
- [N3] sqlite3_open_v2 returns other err (SQLITE_CANTOPEN, etc.) -> NULL, last_result DB.
- [E1] DBPATH exists but is dir / symlink loop -> access fails -> DB.
- [C1] DBPATH disappears between access() and open() -> NULL + DB.

### 3. notification_db_close(sqlite3 **db)
Errno map: NE | INV (db==NULL or *db==NULL) | DB (sqlite3_close != SQLITE_OK).
- [P1] Valid open db -> NE, *db set to NULL.
- [N1] db == NULL -> INV.
- [N2] *db == NULL -> INV.
- [N3] sqlite3_close returns SQLITE_BUSY (uncompleted stmts) -> DB, *db unchanged.
- [E1] Double-close: pass &db after a previous successful close (now *db==NULL) -> INV.
- [C1] Pass freshly-opened-then-leaked-stmt db -> SQLITE_BUSY -> DB.

### 4. notification_db_exec(sqlite3 *db, const char *query, int *num_changes)
Errno map: NE | INV (db==NULL or query==NULL) | DB (prepare_v2 fail, step != OK/DONE).
- [P1] Valid INSERT, num_changes != NULL -> NE, *num_changes == sqlite3_changes.
- [P2] Valid UPDATE/DELETE w/ num_changes == NULL -> NE, no crash (NULL-check guards write).
- [P3] Valid CREATE/DROP (step returns SQLITE_DONE) -> NE.
- [N1] db == NULL -> INV.
- [N2] query == NULL -> INV (strlen(NULL) avoided by short-circuit order).
- [N3] Malformed SQL -> sqlite3_prepare_v2 fail -> DB.
- [N4] Constraint violation / runtime error on step (SQLITE_CONSTRAINT) -> DB.
- [E1] Empty string query -> prepare returns OK with NULL stmt; step on NULL stmt is UB; spec accepts DB.
- [E2] num_changes is NULL but step succeeds -> NE, no segfault.
- [C1] Re-entered with stale db (closed handle) -> DB.

### 5. notification_db_column_text(sqlite3_stmt *stmt, int col)
Errno map: NONE (returns char*; no set_last_result).
- [P1] Column has text abc -> returns strdup(abc) (caller frees).
- [N1] Column is SQL NULL -> sqlite3_column_text returns NULL -> returns NULL.
- [N2] Column is empty string -> returns NULL (per col_text[0] == 0 guard).
- [E1] stmt == NULL -> sqlite3_column_text(NULL,...) is UB; documented as must not pass NULL.
- [E2] col out of range -> sqlite3 returns NULL/empty -> caller-side returns NULL.
- [C1] strdup fails (OOM) -> returns NULL (callers must treat NULL as no value or OOM - known ambiguity).

### 6. notification_db_column_bundle(sqlite3_stmt *stmt, int col)
Errno map: NONE (returns bundle*; no set_last_result).
- [P1] Column holds valid encoded bundle -> bundle_decode returns non-NULL bundle.
- [N1] Column is SQL NULL -> returns NULL.
- [N2] Column is empty string -> returns NULL.
- [N3] Column contains malformed encoded bundle -> bundle_decode returns NULL.
- [E1] col out of range -> NULL.
- [C1] Caller must bundle_free returned bundle - leak risk if forgotten.

### 7. notification_upgrade_db(void)
Errno map: NE | DB (open fail, BEGIN fail, upgrade_noti_table fail, upgrade_template fail, set user_version fail, END/ROLLBACK fail) | OOM (sqlite3_mprintf returns NULL).
- [P1] DB already at DB_VERSION (__check_db_version returns 0) -> END TRANSACTION -> NE.
- [P2] DB at version 1 (no check_box): version_num=2, runs CREATE_UPGRADE_DB + UPGRADE_DB_TO_2 + CREATE_UPGRADE_TEMPLATE + UPGRADE_TEMPLATE_TO_2 + PRAGMA user_version -> NE.
- [P3] DB at version 2 (check_box exists, no channel_name): version_num=3, runs *_TO_3 path -> NE.
- [N1] sqlite3_open_v2 fail -> DB (no close needed - open failed).
- [N2] BEGIN TRANSACTION fails -> close db -> DB.
- [N3] __upgrade_noti_table fails (CREATE_UPGRADE_DB sqlite_exec err) -> ROLLBACK, return DB.
- [N4] __upgrade_noti_template_table fails -> ROLLBACK, return DB.
- [N5] sqlite3_mprintf returns NULL -> ROLLBACK, return OOM.
- [N6] PRAGMA user_version=N exec fails -> ROLLBACK, return DB.
- [E1] END TRANSACTION fails after success path -> overwrite ret to DB.
- [E2] ROLLBACK fails after error path -> overwrite ret to DB (loses original cause).
- [C1] Race: two concurrent upgrade callers - second hits BEGIN TRANSACTION failure (SQLITE_BUSY) -> DB.
- [C2] DB schema in unexpected state (no noti_list table) -> sqlite3_table_column_metadata fails -> version_num=2 path attempted -> error chain -> DB.

---

## B. notification_list.c (15/15)

T_list_get template applies to head/tail/prev/next/data; T_list_modify to append/remove/free; the notification_get_list* family delegates to notification_tidl_request_load_noti_*.

Note: _notification_list_create is internal (not EXPORT_API). Skipped from the 28 count.

### 8. notification_list_get_head(notification_list_h list)  (T_list_get)
Errno (set_last_result): NE | INV (list==NULL).
- [P1] Middle node -> walks prev to head; returns head; last_result NE.
- [P2] Already at head (prev==NULL) -> returns same node; NE.
- [N1] list == NULL -> NULL, INV.
- [E1] Single-element list -> returns same node; NE.
- [C1] Cyclic prev chain (corrupted) -> infinite loop (defensive test: bounded iterations).

### 9. notification_list_get_tail(notification_list_h list)  (T_list_get)
Errno (set_last_result): NE | INV.
- [P1] Middle node -> walks next to tail; NE.
- [P2] Already at tail (next==NULL) -> same node; NE.
- [N1] list==NULL -> NULL, INV.
- [E1] Single-element list -> same node; NE.
- [C1] Cyclic next chain -> infinite loop.

### 10. notification_list_get_prev(notification_list_h list)  (T_list_get)
Errno (set_last_result): NE | INV.
- [P1] Mid/tail node -> returns prev pointer; NE.
- [P2] Head node (prev==NULL) -> returns NULL; NE.
- [N1] list==NULL -> NULL, INV.
- [E1] Distinguishing return-NULL: at head vs INV requires caller to read last_result.

### 11. notification_list_get_next(notification_list_h list)  (T_list_get)
Errno (set_last_result): NE | INV.
- [P1] Mid/head node -> returns next pointer; NE.
- [P2] Tail node (next==NULL) -> returns NULL; NE.
- [N1] list==NULL -> NULL, INV.
- [E1] NULL-at-tail vs INV - disambiguate via last_result.

### 12. notification_list_get_data(notification_list_h list)  (T_list_get)
Errno (set_last_result): NE | INV.
- [P1] Node with noti -> returns cur_list->noti; NE.
- [P2] Node with noti==NULL (e.g. freshly created via _notification_list_create) -> returns NULL; NE.
- [N1] list==NULL -> NULL, INV.
- [E1] NULL-data vs INV - disambiguate via last_result.

### 13. notification_list_get_count(notification_list_h list)
Errno (set_last_result): NE | INV (returns 0).
- [P1] 3-element list, called on tail -> returns 3 (uses get_head then walks next); NE.
- [P2] Single element -> 1; NE.
- [N1] list==NULL -> 0, INV.
- [E1] Called on middle node -> still 3 (head normalization).
- [C1] Pre-test: notification_list_get_head indirectly invoked - ensures get_head INV path NOT triggered here.

### 14. notification_list_append(notification_list_h list, notification_h noti)  (T_list_modify)
Errno (set_last_result): NE | INV (noti==NULL) | OOM (_notification_list_create returns NULL).
- [P1] list == NULL (start of list), valid noti -> creates new head node; new_list==cur_list; NE.
- [P2] Non-empty list, valid noti -> walks to tail, allocates new node, links bidirectionally, returns NEW node (not head); NE.
- [N1] noti == NULL (regardless of list) -> NULL, INV.
- [N2] First-time append, malloc fails inside _notification_list_create -> NULL, OOM.
- [N3] Append-to-existing, malloc fails for new_list -> NULL, OOM.
- [E1] Append onto middle node - walks via get_tail; correctness intact.
- [C1] Append to list whose tail->next is non-NULL (caller corruption) -> get_tail walks past; eventually overwrites; defensive test catches via post-conditions.

### 15. notification_list_remove(notification_list_h list, notification_h noti)  (T_list_modify)
Errno: no set_last_result; return value carries result.
- [P1] Remove middle node - relinks prev<->next; returns get_head(prev_list).
- [P2] Remove head - prev_list==NULL, next_list != NULL sets next_list->prev=NULL; returns next_list.
- [P3] Remove tail - next_list==NULL, sets prev_list->next=NULL; returns get_head(prev_list).
- [P4] Remove only element - both prev/next NULL -> frees node, returns NULL.
- [N1] noti not present in list - loop finishes, prev_list==NULL && next_list==NULL -> returns NULL (ambiguous with only-element removed).
- [N2] list == NULL -> notification_list_get_head(NULL) sets last_result INV, returns NULL -> loop never enters -> returns NULL. No errno propagation.
- [E1] Duplicate noti in list - only first occurrence (from head) is removed (break after free).
- [C1] noti==NULL but a node has cur_list->noti==NULL -> matches and removes that node (likely unintended; treat as defined behavior).
- [C2] After removal, caller continues to use the freed cur_list pointer - UAF risk.

### 16. notification_get_list_for_uid(type, count, list, uid)
Errno: NE | INV (list==NULL) | propagates notification_tidl_request_load_noti_grouping_list error (DB/IO/PERM/...).
- [P1] tidl returns NE with non-empty get_list -> *list = get_head(get_list), NE.
- [P2] tidl returns NE with get_list==NULL (no records) -> *list untouched, NE.
- [N1] list == NULL -> INV (no tidl call).
- [N2] tidl returns error (DB/IO/PERM) -> propagate same code; *list untouched.
- [E1] type invalid enum -> behavior delegated to tidl/server side.
- [E2] count == 0 or negative -> delegated to tidl; verify returned list empty/NULL.
- [C1] tidl returns NE but get_list is a non-head node - get_head normalizes.

### 17. notification_get_list(type, count, list)
Wrapper -> notification_get_list_for_uid(..., aul_getuid()).
- [P1] Normal user uid path -> mirrors 16 P1.
- [N1] list==NULL -> INV.
- [N2] aul_getuid() returns root/0 (system) -> tidl auth path; propagate result.
- All scenarios identical to 16; uid is fixed.

### 18. notification_get_list_by_page_for_uid(type, page_number, count_per_page, list, uid)
Errno: NE | INV (list==NULL OR page_number<=0) | propagated tidl error.
Special: count_per_page > COUNT_PER_PAGE_MAX(100) is clamped to 100 (NOT an error).
- [P1] page_number=1, count_per_page=50 -> NE, list populated.
- [P2] page_number=5, count_per_page=200 -> clamped to 100; tidl called with 100; NE.
- [N1] list==NULL -> INV.
- [N2] page_number == 0 -> INV.
- [N3] page_number < 0 -> INV.
- [N4] tidl returns error -> propagate; *list untouched.
- [E1] count_per_page == COUNT_PER_PAGE_MAX -> not clamped.
- [E2] count_per_page == COUNT_PER_PAGE_MAX + 1 -> clamped to 100.
- [E3] count_per_page < 0 -> not clamped (no negative guard); tidl receives negative - server-side handling.
- [C1] tidl returns NE but get_list==NULL -> *list = get_head(NULL) triggers get_head INV + NULL store (defect: writes NULL but returns NE). Known latent bug; document.

### 19. notification_get_list_by_page(type, page_number, count_per_page, list)
Wrapper -> calls _for_uid with aul_getuid(). Inherits 18 full matrix.

### 20. notification_get_detail_list_for_uid(app_id, group_id, priv_id, count, list, uid)
Errno: NE | INV (list==NULL OR app_id==NULL) | propagated tidl error.
- [P1] Valid app_id + non-empty result -> *list = get_head(get_list), NE.
- [P2] Valid app_id + tidl returns get_list==NULL -> *list untouched, NE.
- [N1] list==NULL -> INV.
- [N2] app_id==NULL -> INV.
- [N3] tidl returns error -> propagate.
- [E1] group_id == NOTIFICATION_GROUP_ID_NONE (-1) -> delegated to tidl.
- [E2] priv_id == NOTIFICATION_PRIV_ID_NONE (-1) -> delegated.
- [E3] count == 0 -> delegated; empty list.
- [C1] Very long app_id -> delegated.

### 21. notification_get_detail_list(app_id, group_id, priv_id, count, list)
Wrapper -> 20 with aul_getuid(). Inherits 20 matrix.

### 22. notification_free_list(notification_list_h list)  (T_list_modify)
Errno: NE | INV (list==NULL).
- [P1] Multi-element list -> iterates: get_head, get_data, remove (frees node), notification_free(noti) per element. End state: all freed; returns NE.
- [P2] Single-element list -> one iteration; NE.
- [N1] list==NULL -> INV.
- [E1] List where one element has noti==NULL -> notification_free(NULL) must be safe (defined as no-op).
- [C1] Called twice on same list -> first frees; second is UAF.
- [C2] List corrupted with cycle -> infinite loop in remove (since head changes each iter, eventually NULL).

---

## C. notification_shared_file.c (6/6)

All under LCOV_EXCL_START markers; still part of EXPORT_API surface. Heavy reliance on filesystem, security-manager, glib timer, package_manager - mocks required.

### 23. notification_remove_private_sharing_target_id(const char *sender, uid_t uid)
Returns: void (no errno surface).
- [P1] uid+sender present in __uid_list[uid].target_app_list -> entry removed; app_id/tidl_sender_name/struct freed.
- [N1] uid not in __uid_list -> early return (no-op).
- [N2] uid present but sender not in target_app_list -> no-op.
- [N3] sender==NULL -> __comp_target_app returns -1 always -> no match -> no-op.
- [E1] Multiple entries with same sender -> only first found removed.
- [C1] Concurrent add/remove -> race on target_app_list (no lock - document threading contract).

### 24. notification_add_private_sharing_target_id(pid_t pid, const char *sender, uid_t uid)
Returns: void (errors logged + early returns).
- [P1] First-ever call for uid -> creates uid_info_s, appends to __uid_list; then adds target.
- [P2] uid exists, sender new -> appends target_app_info to uid_info->target_app_list.
- [P3] uid+sender already exist -> early target_app != NULL branch -> no-op.
- [N1] calloc(uid_info) fails -> OOM trapped by __OOM_CHECK macro -> returns void (no error signal).
- [N2] notification_get_app_id_by_pid(pid) returns NULL -> early return (uid_info already allocated - partial state).
- [N3] calloc(target_info) fails -> frees app_id, returns.
- [N4] strdup(sender) fails -> frees target_info, app_id, returns.
- [E1] sender==NULL -> strdup(NULL) is UB; depends on libc - typically segfault. Assume contract: never NULL.
- [E2] pid invalid -> notification_get_app_id_by_pid returns NULL -> N2.
- [C1] Same sender twice -> P3 path (duplicate suppression).

### 25. notification_validate_private_sharing(notification_h updated_noti)
Returns: bool - true = valid, false = invalid (public path same as private path).
- [P1] No b_image_path AND no priv variants AND no sound/vibration priv -> returns true.
- [P2] image paths exist and differ for every index -> true.
- [P3] sound paths differ -> true.
- [N1] For some image index: updated_path == private_path -> false.
- [N2] sound_path == priv_sound_path -> false.
- [N3] vibration_path == priv_vibration_path -> false.
- [E1] Only one image path set (only b_image_path, no b_priv_image_path) -> skips for-loop, no false; checks sound/vibration -> true.
- [E2] updated_path NULL for some i but populated for others -> continue on NULL.
- [E3] private_path NULL for some i -> continue.
- [C1] updated_noti==NULL -> UB (-> deref); contract: never NULL.

### 26. notification_calibrate_private_sharing(notification_h updated_noti, notification_h source_noti)
Returns: void. Side-effect: rewrites updated_noti paths to match source_noti where they overlap with the private copy.
- [P1] image path equal to private_path: copies source_noti->b_image_path[i] over updated_noti->b_image_path[i].
- [P2] sound_path == priv_sound_path: frees + replaces from source_noti->sound_path.
- [P3] vibration_path == priv_vibration_path: frees + replaces from source_noti->priv_vibration_path (NOTE asymmetry: uses priv_vibration_path of source, not vibration_path - likely a defect; document).
- [N1] source_noti->b_image_path lookup fails (BUNDLE_ERROR) -> updated path stays (no-op).
- [N2] source_noti->sound_path == NULL -> updated_noti->sound_path ends up NULL (free + NULL, no copy).
- [N3] source_noti->priv_vibration_path == NULL -> updated_noti->vibration_path ends up NULL.
- [N4] strdup(source_path) OOM -> sound_path / vibration_path becomes NULL; ERR logged.
- [E1] paths differ for all -> no mutation.
- [E2] image bundle present in updated but priv-image bundle absent -> outer if-guard skips loop.
- [C1] updated_noti==NULL or source_noti==NULL -> UB; contract: never NULL.
- [C2] Defect probe: vibration uses priv_vibration_path source - verify intent vs spec.

### 27. notification_set_private_sharing(notification_h noti, uid_t uid)
Errno: NE | INV (noti==NULL OR noti->caller_app_id==NULL) | OOM (uid_info/req_data/app_id calloc-strdup fail) | IO (__set_sharing_for_new_file OR __set_sharing_for_new_target fail).
- [P1] First-ever call for uid+app_id, noti has priv paths -> creates uid_info + req_data, copies files, registers PS, returns NE.
- [P2] Existing req_data + new priv_id, no new files -> appends priv_id; __set_sharing_for_new_target for already-known targets -> NE.
- [P3] Existing req_data with active timer -> destroys timer, no-leak; NE.
- [P4] req_data->dir == NULL (no priv resources) -> skips __make_sharing_dir; still NE if no new files.
- [N1] noti == NULL -> INV.
- [N2] noti->caller_app_id == NULL -> INV.
- [N3] calloc(uid_info) fails -> OOM.
- [N4] calloc(req_data) fails -> OOM.
- [N5] strdup(noti->caller_app_id) fails -> OOM (with __free_req_info cleanup).
- [N6] __set_sharing_for_new_file fails (security_manager error / OOM in path_array) -> IO, priv_id removed from list.
- [N7] __set_sharing_for_new_target fails -> IO, priv_id removed.
- [E1] Same priv_id added twice -> __comp_priv_id finds it -> not duplicated in list.
- [E2] __get_new_file_list returns NULL (no priv paths to share) -> skips file-sharing block; still calls target_app sharing.
- [E3] is_overlapping == true from __make_file_info -> file-sharing drops then re-applies (test target_app_table iteration).
- [C1] Recover from prior failed call where req_data exists but priv_id_list missing -> behaves as P2.
- [C2] noti->priv_id == 0 / negative -> stored as-is via GINT_TO_POINTER; allowed.
- [C3] __get_shared_dir(noti) returns NULL even though priv paths exist (no data/.notification substring) -> req_data->dir stays NULL, __make_sharing_dir skipped.

### 28. notification_remove_private_sharing(const char *src_app_id, int priv_id, uid_t uid)
Returns: void (errors logged; ultimate cleanup via __timeout_handler).
- [P1] uid+src_app_id+priv_id all present, priv_id_list still non-empty after remove -> early return, NO timer scheduled.
- [P2] uid+src_app_id+priv_id all present, priv_id_list empty after remove -> destroy existing timer, schedule new MAX_TIMEOUT (5000ms) timer; expect __timeout_handler to drop PS and free req_data.
- [P3] Existing timer is non-NULL -> destroyed before re-arming.
- [N1] uid not in __uid_list -> early return.
- [N2] uid present, src_app_id not in sharing_req_list -> early return.
- [N3] priv_id not in priv_id_list -> early return.
- [N4] tizen_core_add_timer returns non-NONE -> direct call to __timeout_handler(req_data) (synchronous cleanup) - drop_retry_count=0 path.
- [E1] src_app_id == NULL -> __comp_sharing_req_list returns -1 always -> early return (N2 path).
- [E2] priv_id == 0 or negative -> compared as pointer value; if matching entry exists, removed.
- [C1] Timer fires while priv_id_list is non-empty again (re-added) -> handler clears req_data->timer=NULL, returns false, no cleanup.
- [C2] __timeout_handler SECURITY_MANAGER failure with drop_retry_count < MAX_RETRY_CNT(3) -> returns true (timer re-armed).
- [C3] tizen_core_find_from_this_thread returns NULL core -> tizen_core_add_timer(NULL,...) likely errors -> falls into N4 synchronous path.

---

## Coverage Check

| File | Function count | Listed |
|---|---|---|
| notification_db.c | 7 | 7 (sections 1-7) |
| notification_list.c | 15 EXPORT_API | 15 (sections 8-22; internal _notification_list_create excluded from count) |
| notification_shared_file.c | 6 | 6 (sections 23-28) |
| Total | 28 | 28/28 |

Verified per EXPORT_API list:
- db: notification_db_init, notification_db_open, notification_db_close, notification_db_exec, notification_db_column_text, notification_db_column_bundle, notification_upgrade_db -> 7/7.
- list: notification_list_get_head/tail/prev/next/data/count, notification_list_append/remove, notification_get_list_for_uid, notification_get_list, notification_get_list_by_page_for_uid, notification_get_list_by_page, notification_get_detail_list_for_uid, notification_get_detail_list, notification_free_list -> 15/15.
- shared_file: notification_remove_private_sharing_target_id, notification_add_private_sharing_target_id, notification_validate_private_sharing, notification_calibrate_private_sharing, notification_set_private_sharing, notification_remove_private_sharing -> 6/6.

TOTAL: 28/28 covered.
# Notification – Miscellaneous Test Scenarios (misc files)

Files covered (source order):
1. notification_error.c  — `notification_error_quark`
2. notification_ipc.c    — `notification_ipc_make_gvariant_from_noti`, `notification_ipc_make_noti_from_gvariant`
3. notification_ongoing.c — `notification_ongoing_update_cb_set`, `notification_ongoing_update_cb_unset`
4. notification_status.c — `notification_status_monitor_message_cb_set`, `notification_status_monitor_message_cb_unset`, `notification_status_message_post`
5. notification_viewer.c — `notification_init_default_viewer`, `notification_launch_default_viewer`, `notification_launch_default_viewer_without_candidate_process`
6. notification_internal_tidl.c — `make_empty_notification`, `make_notification_from_noti`, `make_noti_from_notification`, `make_setting_from_noti_system_setting`, `make_dnd_allow_exception_from_exception`, `make_noti_system_setting_from_setting`, `make_setting_from_noti_setting`, `make_noti_setting_from_setting`

Tag legend: `[P]` Positive, `[N]` Negative, `[E]` Edge, `[C]` Corner.

---

## 1. notification_error.c

### 1.1 `notification_error_quark(void)`

**Signature:** `EXPORT_API GQuark notification_error_quark(void);`

**Behavior:** Returns the GQuark used to register the notification error domain with GIO so that GError values returned over D-Bus carry the right freedesktop names. Wraps `g_quark_try_string` + `g_dbus_error_register_error_domain` against a static table of 11 entries (`NOTIFICATION_ERROR_INVALID_PARAMETER`, `OUT_OF_MEMORY`, `IO_ERROR`, `PERMISSION_DENIED`, `FROM_DB`, `ALREADY_EXIST_ID`, `FROM_DBUS`, `NOT_EXIST_ID`, `SERVICE_NOT_READY`, `INVALID_OPERATION`, `MAX_EXCEEDED`).

**Errno map**
| Path | Return | Trigger |
|------|--------|---------|
| First call, quark not yet registered | non-zero `GQuark` | `g_quark_try_string` returns 0 → `domain_name = strdup(...)`; `g_dbus_error_register_error_domain` initialises `quark_volatile` |
| Subsequent call, quark already in the global table | same `GQuark` as first call | `g_quark_try_string` returns non-zero → `domain_name` set to static literal; re-register is a no-op |
| `strdup` returns NULL under OOM (very rare) | still returns the (now zero) `GQuark` from `quark_volatile` | passes NULL `domain_name` to GIO; GIO behaviour is implementation defined, function does not abort |

**Scenarios**
- [P] First-call registration returns non-zero quark and matches `g_quark_from_string("notification-error-quark")`.
- [P] Repeated calls return the same `GQuark` (idempotence).
- [P] After registration, `g_dbus_error_get_remote_error()` on a GError with one of the registered codes returns the matching `org.freedesktop.Notification.Error.*` string.
- [N] Unknown error code mapping: calling `g_dbus_error_get_remote_error` with an error not in the table returns NULL (verifies the table boundary; "unknown code" coverage).
- [E] Concurrent first-call from two threads — both calls eventually return the same quark (the function relies on `static volatile gsize quark_volatile` + GIO's internal once-init).
- [C] Use after `ui-gadget` library unload: simulate `domain_name` pointing into freed memory by triggering the strdup branch — function still returns a valid GQuark (this is the explicit bug-fix the source comment documents).

---

## 2. notification_ipc.c

### 2.1 `notification_ipc_make_gvariant_from_noti(notification_h noti, bool translate)`

**Signature:** `EXPORT_API GVariant *notification_ipc_make_gvariant_from_noti(notification_h, bool);`

**Behavior:** Serialises a `notification_h` into a `GVariant("(v)")` whose inner variant is `a{iv}` keyed by `NOTIFICATION_DATA_TYPE_*`. Optionally runs `notification_translate_localized_text(noti)` first. All `bundle *` fields are first `bundle_encode`d to raw bytes; NULL/zero fields are simply skipped. Always emits the always-on numeric fields (type, layout, group_id, internal_group_id, priv_id, pkg_id, caller_app_id, display_applist, sound_type, vibration_type, led_operation, ongoing_flag, ongoing_value_type, ongoing_current, ongoing_duration, auto_remove, default_button, hide_timeout, delete_timeout, text_input_max_length, event_flag, translation, extension_image_size, check_box, check_box_value, uid).

**Errno map**
| Path | Return | Trigger |
|------|--------|---------|
| `noti` non-NULL, no translation, all optional fields NULL | non-NULL `GVariant *` containing only always-on keys | Default minimal notification |
| `noti` non-NULL, `translate == true` | non-NULL `GVariant *` with translated `b_text` | Calls `notification_translate_localized_text` first |
| `noti` non-NULL, every optional bundle/string set | non-NULL `GVariant *` containing every key in the schema | All `if (noti->...)` branches taken |
| `noti == NULL` | undefined / crash | Function does NOT NULL-check. **Caller contract violation.** |

**Scenarios**
- [P] Minimal notification, translate=false → result contains the always-on keys and nothing else; reverse round-trip with `notification_ipc_make_noti_from_gvariant` reproduces same values.
- [P] Fully populated notification (every optional bundle and every event handler `b_event_handler[0..MAX]` set) — every `NOTIFICATION_DATA_TYPE_*` key is present exactly once.
- [P] translate=true forces `notification_translate_localized_text(noti)` to fire (verify side-effect on `b_text`).
- [P] Event-handler matrix: only `b_event_handler[NOTIFICATION_EVENT_TYPE_CLICK_ON_BUTTON_3]` set → only `BUTTON3_EVENT` key present, others absent.
- [N] `noti == NULL` → caller-contract violation, function dereferences NULL. (Document; do not exercise unguarded; gate with EXPECT_DEATH if at all.)
- [E] `noti->pkg_id` set to empty string — still emitted (function does not short-circuit on empty string for non-bundle string fields).
- [E] `progress_size != 0.0` but `progress_percentage == 0.0` → only PROGRESS_SIZE emitted, PROGRESS_PERCENTAGE omitted (and vice-versa).
- [E] `led_argb == 0`, `led_on_ms == 0`, `led_off_ms == 0` — all three skipped; `LED_OPERATION` still emitted (always-on).
- [E] `noti->time == 0` and `noti->insert_time == 0` — both skipped.
- [E] `num_format_args == 0` — `NUM_FORMAT_ARGS` key omitted.
- [C] `bundle_encode` returns non-NULL but encoder yields empty payload — key still emitted as zero-length string.
- [C] A bundle field non-NULL but already freed: undefined; document as caller-contract violation.
- [C] All 11 event handler slots set — verify NOTIFICATION_EVENT_TYPE_MAX boundary loop reaches the last index exactly once.

### 2.2 `notification_ipc_make_noti_from_gvariant(notification_h noti, GVariant *variant)`

**Signature:** `EXPORT_API int notification_ipc_make_noti_from_gvariant(notification_h, GVariant *);`

**Behavior:** Inverse of 2.1. Walks `a{iv}` into a `GHashTable` keyed by `int*`, then pulls each `NOTIFICATION_DATA_TYPE_*` out with `_variant_dict_lookup`. For string-bundle pairs decodes raw bundles via `bundle_decode`. Free-then-strdup for `pkg_id`, `caller_app_id`, `domain`, `dir`. Always returns `NOTIFICATION_ERROR_NONE` on success.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | All lookups succeeded (missing keys are silently ignored — they stay at zero/NULL) |
| `NOTIFICATION_ERROR_INVALID_PARAMETER` | `noti == NULL` or `variant == NULL` |
| `NOTIFICATION_ERROR_OUT_OF_MEMORY` | `_variant_to_int_dict` failed → either `g_hash_table_new_full` returned NULL, or `calloc(sizeof(int),1)` for `hash_key` returned NULL (LCOV_EXCL'd) |

**Scenarios**
- [P] Round-trip: serialize via 2.1, deserialize via 2.2 → all numeric, string, and bundle fields recovered.
- [P] Variant carries only the always-on keys → optional fields end up at zero/NULL; return is NONE.
- [P] Variant carries every key including all 11 event-handler keys → each `noti->b_event_handler[i]` is non-NULL.
- [N] `noti == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER`, variant untouched.
- [N] `variant == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER`.
- [N] OOM from `g_hash_table_new_full` (mock to return NULL) → `NOTIFICATION_ERROR_OUT_OF_MEMORY`.
- [N] OOM mid-iteration: first calloc succeeds, second returns NULL — function unrefs the hash table and returns `NOTIFICATION_ERROR_OUT_OF_MEMORY`. (LCOV_EXCL path.)
- [E] Variant with the wrong inner type for a known key (e.g. PRIV_ID stored as string instead of int) → `_variant_dict_lookup` returns FALSE silently, that field stays at its prior value (still NONE returned).
- [E] Variant with duplicate keys → last writer wins (hash table semantics).
- [E] Empty `a{iv}` variant → all optional fields stay zero, return NONE.
- [C] `_dup_string` on incoming empty string (e.g. `pkg_id == ""`) → final `noti->pkg_id == NULL` (per `_dup_string`'s `string[0] == '\0'` short-circuit).
- [C] Previously-populated `noti` re-used: free-then-overwrite for `pkg_id`/`caller_app_id`/`domain`/`dir`, BUT not for sound_path, vibration_path, app_icon_path, etc. — old values leak. Document this as a known caller-contract requirement: pass a zeroed-out `_notification` struct.
- [C] Variant carrying `NOTIFICATION_DATA_TYPE_NUM_FORMAT_ARGS = INT_MAX` — copied verbatim into `noti->num_format_args`; no range validation.

---

## 3. notification_ongoing.c

### 3.1 `notification_ongoing_update_cb_set(callback, user_data)`

**Signature:** `EXPORT_API int notification_ongoing_update_cb_set(notification_ongoing_update_cb, void *);`

**Behavior:** Currently a stub. Logs WARN("not working now") and unconditionally returns `NOTIFICATION_ERROR_NONE`. Does not store the callback. Does not validate arguments.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always |

**Scenarios**
- [P] Call with valid callback + user_data → `NOTIFICATION_ERROR_NONE`.
- [P] Call with `callback == NULL` and any user_data → still `NOTIFICATION_ERROR_NONE` (stub, no validation).
- [N] No real failure path exists in current code (stub). Verify `NOTIFICATION_ERROR_NONE` is the only return for now.
- [E] Called 100x in a row → always NONE, no state leak.
- [C] After-stub regression guard: once a real implementation lands, this test must be the first to fail (placeholder check on `errno` propagation).

### 3.2 `notification_ongoing_update_cb_unset(void)`

**Signature:** `EXPORT_API int notification_ongoing_update_cb_unset(void);`

**Behavior:** Stub. Logs WARN and returns `NOTIFICATION_ERROR_NONE`.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always |

**Scenarios**
- [P] Plain call → `NOTIFICATION_ERROR_NONE`.
- [P] Call without any prior `_cb_set` → still NONE (no state to clear).
- [N] No failure path in current code.
- [E] Repeated unset is idempotent.
- [C] Same regression-guard note as 3.1.

> Note: `notification_ongoing_update_progress`, `_update_size`, `_update_content` are also stubs but are not `EXPORT_API`, so they are out of scope for this 19-function audit.

---

## 4. notification_status.c

### 4.1 `notification_status_monitor_message_cb_set(callback, user_data)`

**Signature:** `EXPORT_API int notification_status_monitor_message_cb_set(notification_status_message_cb, void *);`

**Behavior:** Subscribes the singleton `md` to the system-bus D-Bus signal `org.tizen.system.notification.status_message::status_message` at path `/Org/Tizen/System/Notification/Status_message`. Lazily creates the system-bus connection on first call. Stores `callback` + `user_data` in the module-static `md`. Signal frames are routed through `__notification_status_message_dbus_callback`.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Bus connection up and signal subscribed |
| `NOTIFICATION_ERROR_INVALID_PARAMETER` | `callback == NULL` |
| `NOTIFICATION_ERROR_FROM_DBUS` | `g_bus_get_sync(SYSTEM)` returned NULL, OR `g_dbus_connection_signal_subscribe` returned 0 |

**Scenarios**
- [P] First call with valid callback → opens conn, subscribes, returns NONE; `md.callback` and `md.data` updated.
- [P] Second call (already subscribed) → reuses `md.conn`, skips subscribe, updates only `md.callback`/`md.data` → NONE.
- [P] Emit a matching signal externally → callback is invoked with the message and the stored `user_data`.
- [N] `callback == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER`; `md` unchanged.
- [N] `g_bus_get_sync` fails (mock returns NULL with GError) → `NOTIFICATION_ERROR_FROM_DBUS`; `md.conn` left NULL.
- [N] `g_dbus_connection_signal_subscribe` returns 0 → `NOTIFICATION_ERROR_FROM_DBUS`; `md.conn` is `g_object_unref`'d. Verify no double-free on follow-up unset.
- [E] Sender process signal with empty `message` string → callback NOT invoked (the dbus_callback short-circuits on `strlen(message) <= 0`).
- [E] `md.callback` becomes NULL between subscribe and signal arrival → dbus_callback logs "No callback" and drops the frame.
- [C] Reentrancy: subscribed callback calls `_cb_set` again with a new callback — store overwrites cleanly, no double-subscribe.
- [C] Set→post→unset→set rapid cycle without losing messages emitted between unset and re-set (documents that no buffering exists).

### 4.2 `notification_status_monitor_message_cb_unset(void)`

**Signature:** `EXPORT_API int notification_status_monitor_message_cb_unset(void);`

**Behavior:** Tears down the subscription if present, unrefs `md.conn`, clears `md.callback`/`md.data`. Always returns `NOTIFICATION_ERROR_NONE`.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always |

**Scenarios**
- [P] After `_cb_set` → unset clears subscription; further signal emits do NOT reach the callback.
- [P] Unset without prior set → still NONE; no crash (both `md.message_id` and `md.conn` are zero/NULL on first use).
- [P] After unset, `_cb_set` again succeeds and reopens a new connection.
- [N] No failure path (stub-like).
- [E] Double unset is idempotent → second call sees `md.message_id == 0` and `md.conn == NULL`.
- [C] Unset during pending signal delivery — guarded by GIO's internal serialization; verify callback is not invoked after unset returns.

### 4.3 `notification_status_message_post(const char *message)`

**Signature:** `EXPORT_API int notification_status_message_post(const char *);`

**Behavior:** Opens a temporary system-bus connection, emits the `status_message` signal carrying `(s)` payload, flushes, then unrefs the connection. Returns one of three codes.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | `g_dbus_connection_emit_signal` and `g_dbus_connection_flush_sync` both succeed |
| `NOTIFICATION_ERROR_INVALID_PARAMETER` | `message == NULL` |
| `NOTIFICATION_ERROR_FROM_DBUS` | `g_bus_get_sync` failed, OR `g_dbus_connection_emit_signal` returned FALSE, OR `g_dbus_connection_flush_sync` returned FALSE |

**Scenarios**
- [P] Valid non-empty `"hello"` → returns NONE; an observer subscribed via `_cb_set` receives `"hello"`.
- [P] Valid empty string `""` → still emits (function does not enforce non-empty; observer callback drops it on its end).
- [P] Multibyte UTF-8 string transmitted intact.
- [N] `message == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER` (no D-Bus traffic).
- [N] `g_bus_get_sync` returns NULL → `NOTIFICATION_ERROR_FROM_DBUS`; cleanup branch `if (err)` `g_error_free` and `if (conn)` skipped (LCOV_EXCL'd).
- [N] `g_dbus_connection_emit_signal` returns FALSE → `NOTIFICATION_ERROR_FROM_DBUS`; conn still unrefed.
- [N] `g_dbus_connection_flush_sync` returns FALSE → `NOTIFICATION_ERROR_FROM_DBUS`.
- [E] Very long `message` (> typical D-Bus message limit, e.g. 128MB) — D-Bus emit may fail → `NOTIFICATION_ERROR_FROM_DBUS`.
- [C] Post when bus daemon is dead — `g_bus_get_sync` failure path returns `FROM_DBUS`.
- [C] No subscriber present — emit still succeeds → NONE (D-Bus signals are fire-and-forget).

---

## 5. notification_viewer.c

### 5.1 `notification_init_default_viewer(void)`

**Signature:** `EXPORT_API int notification_init_default_viewer(void);`

**Behavior:** Lazily reads `/usr/share/notification/notification.ini`, looks up the `Notification:DefaultViewer` key via `iniparser`, and caches the result in module-static `_default_viewer` (strdup'd). Idempotent: if `_default_viewer != NULL`, returns 0 immediately. Uses POSIX return codes (`0` / `-1`) — NOT the `NOTIFICATION_ERROR_*` family.

**Errno map**
| Return | Trigger |
|--------|---------|
| `0` | Already initialised, OR file accessible + iniparser loaded + (viewer key present or absent — both succeed) |
| `-1` | `access(F_OK)` failed (file missing/unreadable), OR `iniparser_load` returned NULL |

**Scenarios**
- [P] Default conf present with `Notification:DefaultViewer=org.tizen.foo` → returns 0; `_default_viewer == "org.tizen.foo"`.
- [P] Default conf present without the key → returns 0; `_default_viewer` stays NULL (no strdup).
- [P] Second call after success → returns 0 immediately, no file IO.
- [N] Conf file missing → `access` returns -1, function returns -1; `_default_viewer` unchanged (still NULL).
- [N] Conf file present but malformed → `iniparser_load` returns NULL, function returns -1.
- [E] Empty viewer value `Notification:DefaultViewer=` — iniparser_getstring returns "" → strdup of "" is cached. Document as edge.
- [E] Permission-denied on the conf file — `access(F_OK)` ignores read bits and returns 0; iniparser_load will fail → -1.
- [C] Init called twice from constructor + first API call — second one no-ops; no leak on `_default_viewer`.

### 5.2 `notification_launch_default_viewer(int priv_id, notification_op_type_e status, uid_t uid)`

**Signature:** `EXPORT_API int notification_launch_default_viewer(int, notification_op_type_e, uid_t);`

**Behavior:** Thin wrapper around `__launch_default_viewer(priv_id, status, uid, /*candidate=*/true)`. Sets the `__K_EX_USE_CANDIDATE_PROCESS=true` extra and asks AUL to launch the cached `_default_viewer`. If a delayed list is non-empty, queues this request; otherwise sends an async launch request.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | `_default_viewer == NULL` (no-op success), OR launch async OK, OR push-to-delayed-list OK |
| `NOTIFICATION_ERROR_OUT_OF_MEMORY` | `app_control_create` / `set_app_id` / `add_extra_data` (priv_id or op_type) failed |
| `NOTIFICATION_ERROR_IO_ERROR` | `tizen_core_find("data-provider-master", ...)` or `tizen_core_add_timer` failed inside the delayed-push path |
| `<other>` | Whatever `__push_delayed_noti` returns on its second-chance fallback path |

**Scenarios**
- [P] `_default_viewer` set, delayed list empty → async `app_control_send_launch_request_async` invoked; returns NONE.
- [P] `_default_viewer == NULL` → returns NONE immediately without app_control work.
- [P] candidate flag is `true` → `__K_EX_USE_CANDIDATE_PROCESS=true` extra present on app_control.
- [P] `priv_id`, `status` rendered into extras as decimal strings (verify `snprintf("%d",...)`).
- [N] `app_control_create` returns non-NONE → `NOTIFICATION_ERROR_OUT_OF_MEMORY`.
- [N] `app_control_set_app_id` fails → `NOTIFICATION_ERROR_OUT_OF_MEMORY`; `app_control` destroyed in `out:`.
- [N] `app_control_add_extra_data` for `NOTIFICATION_PRIVATE_ID` fails → `NOTIFICATION_ERROR_OUT_OF_MEMORY`.
- [N] `app_control_add_extra_data` for `NOTIFICATION_OP_TYPE` fails → `NOTIFICATION_ERROR_OUT_OF_MEMORY`.
- [N] async launch fails → falls back to `__push_delayed_noti`; if that also fails → returns its error (`NOTIFICATION_ERROR_OUT_OF_MEMORY` / `IO_ERROR`).
- [N] `__push_delayed_noti` → `app_control_clone` failure → `NOTIFICATION_ERROR_OUT_OF_MEMORY`.
- [N] `__push_delayed_noti` → `tizen_core_find` failure → `NOTIFICATION_ERROR_IO_ERROR`.
- [N] `__push_delayed_noti` → `tizen_core_add_timer` failure → `NOTIFICATION_ERROR_IO_ERROR`.
- [E] Delayed list already at `DELAY_LIMIT (50)` — `__check_limit` drops the head element (oldest), logs and frees; new push still proceeds.
- [E] `priv_id == INT_MIN` → snprintf produces `"-2147483648"`, fits in 32-byte buf.
- [C] Re-entrant call from `__pop_delayed_noti_cb` while `__rec_mutex` already held by caller — recursive mutex prevents deadlock.
- [C] candidate-key add fails (`app_control_add_extra_data` for `__K_EX_USE_CANDIDATE_PROCESS`) — current code only logs ERR and continues; function does NOT short-circuit, so the launch still proceeds. Document this divergence vs. the other extras.

### 5.3 `notification_launch_default_viewer_without_candidate_process(int priv_id, notification_op_type_e status, uid_t uid)`

**Signature:** `EXPORT_API int notification_launch_default_viewer_without_candidate_process(int, notification_op_type_e, uid_t);`

**Behavior:** Same as 5.2 but `candidate = false` → skips the `__K_EX_USE_CANDIDATE_PROCESS` extra entirely.

**Errno map**
Same as 5.2.

**Scenarios**
- [P] `_default_viewer` set → launch request sent without the candidate-process extra; returns NONE.
- [P] `_default_viewer == NULL` → returns NONE without any app_control work.
- [N] Same OOM / IO_ERROR matrix as 5.2 (`app_control_create`, `set_app_id`, both `add_extra_data` calls, `app_control_clone`, `tizen_core_find`, `tizen_core_add_timer`).
- [N] Async launch failure path falls back to `__push_delayed_noti` exactly like 5.2.
- [E] Verify `__K_EX_USE_CANDIDATE_PROCESS` is absent — diff vs. the 5.2 path is exactly the candidate branch.
- [E] Called repeatedly with same `priv_id` — each call generates an independent app_control; viewer must dedup on its side.
- [C] Mixed sequence: 5.2 then 5.3 with same priv_id — second extra map does NOT include candidate flag; document the asymmetry.
- [C] `uid` is logically unused inside `__launch_default_viewer` — passing `(uid_t)-1` does not crash; behaviour identical to a valid uid.

---

## 6. notification_internal_tidl.c

### 6.1 `make_empty_notification(void *notihandle)`

**Signature:** `EXPORT_API int make_empty_notification(void *);`

**Behavior:** Initialises an `rpc_port_proxy_notification_h` to a fully sentinel/empty state (`-1` for ints, `""` for strings, empty bundle for every bundle field, `false` for bools, `0.0` for the two progress doubles). Iterates every field; each failure logs WARN but execution continues. Frees the shared `empty_bundle` at the end.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always (failures from every setter are logged, never propagated) |

**Scenarios**
- [P] Pass a freshly created `rpc_port_proxy_notification_h` → returns NONE; subsequent get_* calls on the handle yield the sentinel defaults (`type == -1`, `pkg_id == ""`, `ongoing_flag == false`, `progress_size == 0.0`).
- [P] Verify the empty event_handler array is set (creates `rpc_port_proxy_array_bundle_h`, applies, destroys).
- [P] Verify `empty_bundle` is freed via `bundle_free` even on early-WARN paths.
- [N] `notihandle == NULL` → cast to `rpc_port_proxy_notification_h` and every setter is called with NULL; each setter returns non-NONE and is silently logged. Function still returns NONE — document this as a caller-contract gap.
- [N] Any single rpc_port_proxy_*_set_* failure → loop continues, no early return.
- [E] If `bundle_create` for `empty_bundle` returns NULL (OOM), every setter that consumes it operates on NULL — current code does not guard. Document as OOM gap; scenario should mock bundle_create.
- [E] `rpc_port_proxy_array_bundle_create` failure — `_event_handler` is undefined, the subsequent `set_event_handler` and `destroy` operate on garbage. Document as defect candidate.
- [C] Replay: calling `make_empty_notification` twice on the same handle is idempotent.
- [C] Multi-threaded use of the same handle — concurrent setters are NOT serialised by this function; caller must guarantee single-owner.

### 6.2 `make_notification_from_noti(void *notihandle, notification_h noti, bool translate)`

**Signature:** `EXPORT_API int make_notification_from_noti(void *, notification_h, bool);`

**Behavior:** Marshals a `notification_h` into the rpc_port proxy handle (the wire-side equivalent of 2.1). If `translate`, calls `notification_translate_localized_text` first. For every nullable bundle field falls back to the shared `empty_bundle`. Strings flow through `__get_str_value` which returns `""` for NULL. All setter failures log WARN but never propagate. Always returns NONE.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always |

**Scenarios**
- [P] Fully populated `noti` + valid `notihandle`, translate=false → every setter called with the real value (bundles, strings, ints, doubles, bools).
- [P] translate=true → `notification_translate_localized_text(noti)` is invoked exactly once before any setter.
- [P] Nullable bundle field NULL (e.g. `noti->b_text == NULL`) → setter receives `empty_bundle`, NOT NULL.
- [P] Nullable string NULL (e.g. `noti->pkg_id == NULL`) → setter receives `""` via `__get_str_value`.
- [P] Event-handler array: all `NOTIFICATION_EVENT_TYPE_MAX+1` slots packaged via `rpc_port_proxy_array_bundle_set`. NULL slots are replaced with `bundle_create()` IN-PLACE on `noti->b_event_handler[i]` — verify that the original notification is mutated (this is a side-effect worth noting).
- [N] `notihandle == NULL` → every setter sees NULL handle; setters all fail and are silently logged → still returns NONE. Document as gap.
- [N] `noti == NULL` → undefined; dereferences `noti->type` first (will crash). Caller-contract violation.
- [E] `notification_translate_localized_text` mutates `b_text` mid-call — verify the translated bundle is the one finally serialised.
- [E] `bundle_create` returns NULL inside the event-handler fix-up loop → `noti->b_event_handler[i]` left NULL; setter receives NULL; still returns NONE.
- [E] `rpc_port_proxy_array_bundle_create` fails → `_event_handler` undefined → setter on garbage. Same defect candidate as 6.1.
- [C] Side-effect: After this function runs, all `b_event_handler[i]` that were originally NULL are now valid empty bundles; the caller will leak them if it does not destroy.
- [C] `noti` shared with another thread that mutates fields mid-call — values seen by setters are torn. Function does not lock.

### 6.3 `make_noti_from_notification(notification_h *noti, void *notihandle)`

**Signature:** `EXPORT_API int make_noti_from_notification(notification_h *, void *);`

**Behavior:** Inverse of 6.2. Allocates `struct _notification` with `calloc`. Pulls every `rpc_port_proxy_notification_get_*` into the new struct. For string fields: if the proxy returned an empty string, frees it and stores NULL; otherwise transfers ownership. Always returns NONE on success.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | calloc succeeded; getters either succeeded or logged WARN and proceeded |
| `NOTIFICATION_ERROR_OUT_OF_MEMORY` | `calloc(1, sizeof(struct _notification))` returned NULL |

**Scenarios**
- [P] Round-trip with 6.2 → same field values recovered; bundles round-trip via the rpc array layer.
- [P] Proxy returns `pkg_id == ""` → resulting `_noti->pkg_id == NULL` (verify the empty-string-to-NULL normalisation).
- [P] Proxy returns `caller_app_id == "org.tizen.bar"` → ownership transferred (no extra strdup).
- [P] `*noti` is set only at the very end via `*noti = _noti;` — verify it is untouched on the early OOM path.
- [N] `calloc` returns NULL → `NOTIFICATION_ERROR_OUT_OF_MEMORY`; `*noti` untouched.
- [N] Any individual `rpc_port_proxy_notification_get_*` returns non-NONE → logged and skipped; function returns NONE. Document that partial failures are not visible to the caller.
- [E] `notihandle == NULL` — every getter sees a NULL handle and probably returns an error code; current code logs each and continues; `_noti` ends up zero-initialised → returns NONE with a fully zero notification. Caller-contract gap.
- [E] `noti == NULL` → final `*noti = _noti;` dereferences NULL → crash. Caller-contract violation.
- [C] Sequence: getter for `pkg_id` returns NONE but `pkg_id == ""` from the proxy — `free(pkg_id)` is invoked; verify no double-free if the proxy returns a literal vs heap pointer (proxy contract is heap; document).
- [C] String-empty-to-NULL pattern repeats for `caller_app_id`, `launch_app_id`, `domain`, `dir`, `sound_path`, `priv_sound_path`, `vibration_path`, `priv_vibration_path`, `app_icon_path`, `app_label`, `temp_title`, `temp_content`, `tag`, `channel_name` — verify each individually.

### 6.4 `make_setting_from_noti_system_setting(notification_system_setting_h *setting, void *settinghandle)`

**Signature:** `EXPORT_API int make_setting_from_noti_system_setting(notification_system_setting_h *, void *);`

**Behavior:** Allocates a `struct notification_system_setting` and fills DND/visibility fields via `rpc_port_proxy_noti_system_setting_get_*`. Iterates the dnd-allow-exception list via foreach + helper callback. Returns NONE unless calloc fails.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always, except OOM |
| `NOTIFICATION_ERROR_OUT_OF_MEMORY` | calloc returned NULL |

**Scenarios**
- [P] Proxy handle with valid scalar fields → `*setting` populated; do_not_disturb, dnd_schedule_enabled, dnd_schedule_day, dnd_start_hour, dnd_start_min, dnd_end_hour, dnd_end_min, visibility_class, lock_screen_content_level all match.
- [P] dnd_allow_exceptions list non-empty → each exception cloned into `_setting->dnd_allow_exceptions` via the foreach callback.
- [P] Empty dnd_allow_exceptions list → `_setting->dnd_allow_exceptions == NULL`; return NONE.
- [N] calloc returns NULL → `NOTIFICATION_ERROR_OUT_OF_MEMORY`; `*setting` untouched.
- [N] `settinghandle == NULL` → getters operate on NULL, no return-value check at all (these are bare calls without `if`). Result is zeroed `_setting`; still returns NONE. Caller-contract gap.
- [E] `_rpc_port_proxy_list_noti_system_setting_dnd_allow_exception_cb` returns false mid-iteration (OOM inside) → foreach aborts; `_setting->dnd_allow_exceptions` ends up partial. Function still returns NONE.
- [E] `lock_screen_content_level` value outside the enum range → cast preserves the raw int. Document.
- [C] `setting == NULL` (the out-pointer) → final `*setting = _setting;` crashes. Caller-contract violation.
- [C] Memory ownership: caller now owns `_setting` and its `dnd_allow_exceptions` list — verify clean-up requires `g_list_free_full` with element-free.

### 6.5 `make_dnd_allow_exception_from_exception(void *exception_handle, dnd_allow_exception_h dnd_allow_exception)`

**Signature:** `EXPORT_API int make_dnd_allow_exception_from_exception(void *, dnd_allow_exception_h);`

**Behavior:** Sets type+value on the proxy exception handle from the local struct. Logs each setter failure but does not propagate.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Both setters returned (regardless of success), AND both inputs non-NULL |
| `NOTIFICATION_ERROR_INVALID_PARAMETER` | `exception_handle == NULL` OR `dnd_allow_exception == NULL` |

**Scenarios**
- [P] Both inputs valid → setter for `type` and `value` invoked; returns NONE.
- [N] `exception_handle == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER`.
- [N] `dnd_allow_exception == NULL` → `NOTIFICATION_ERROR_INVALID_PARAMETER`.
- [N] Both NULL → `NOTIFICATION_ERROR_INVALID_PARAMETER`.
- [E] `rpc_port_proxy_..._set_type` fails — logged ERR, function still proceeds to set_value and returns NONE. Document gap.
- [E] `rpc_port_proxy_..._set_value` fails → logged ERR; function still returns NONE.
- [C] `dnd_allow_exception->type` out of enum range → marshalled verbatim, no range check.
- [C] `dnd_allow_exception->value` empty/sentinel — verify it round-trips through the proxy.

### 6.6 `make_noti_system_setting_from_setting(void *settinghandle, notification_system_setting_h setting)`

**Signature:** `EXPORT_API int make_noti_system_setting_from_setting(void *, notification_system_setting_h);`

**Behavior:** Inverse of 6.4. Pushes scalar DND fields onto the proxy. If `setting->dnd_allow_exceptions` is non-empty, creates a proxy list, walks the GList, creates+populates+adds+destroys each proxy exception, and finally calls `set_dnd_allow_exceptions`. On any of these list operations failing, logs and short-circuits the list step but still returns NONE.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always (every failure is logged-and-swallowed) |

**Scenarios**
- [P] Setting with empty dnd_allow_exceptions → only scalar setters fire; returns NONE.
- [P] Setting with one exception → list created, exception created+populated+added+destroyed, list set on handle; returns NONE.
- [P] Setting with N>1 exceptions → loop iterates each; verify `g_list_first` resets a non-head iterator before the loop (defensive against caller passing a mid-list pointer).
- [N] `settinghandle == NULL` → every setter sees NULL; each logs ERR and proceeds. Function returns NONE. Caller-contract gap.
- [N] `setting == NULL` → first scalar setter dereferences NULL (`setting->do_not_disturb`) → crash. Caller-contract violation.
- [N] `rpc_port_proxy_list_..._create` fails → ERR logged, function returns NONE early (skipping the list-set entirely). Verify code path returns NONE not an error.
- [E] `rpc_port_proxy_..._exception_create` fails mid-iteration → that exception is skipped (ERR logged); loop continues with the next; final `set_dnd_allow_exceptions` runs with a partial list.
- [E] `make_dnd_allow_exception_from_exception` returns INVALID_PARAMETER inside the loop (only if both inputs become NULL — unlikely here) → exception added empty; loop continues.
- [E] `rpc_port_proxy_list_..._add` fails → ERR logged; exception is destroyed; loop continues.
- [C] After-loop list is empty (all creates failed) — `set_dnd_allow_exceptions` still called with the empty list_handle. Document.
- [C] Settings struct mutated mid-call from another thread — torn read, no locks.

### 6.7 `make_setting_from_noti_setting(notification_setting_h setting, void *settinghandle)`

**Signature:** `EXPORT_API int make_setting_from_noti_setting(notification_setting_h, void *);`

**Behavior:** Reads per-app noti_setting fields (pkg_name, app_id, allow_to_notify, dnd_except, pop_up_noti, visibility_class, lock_screen_content_level, app_disabled) from the proxy handle and writes them into the caller-allocated `notification_setting_h`. Same empty-string→NULL normalisation for `package_name` and `app_id` as in 6.3. Each getter failure is logged ERR but never propagated.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always (no early return) |

**Scenarios**
- [P] Proxy returns realistic per-app settings → `setting->package_name`, `app_id`, four bools, two ints all match.
- [P] Empty `pkg_name` from proxy → `setting->package_name == NULL`, original string freed.
- [P] Empty `app_id` from proxy → `setting->app_id == NULL`, freed.
- [N] `setting == NULL` → first write (`setting->package_name = pkg_name`) crashes. Caller-contract violation.
- [N] `settinghandle == NULL` → getters all log ERR and continue; resulting `setting` is mostly zeroed but with potentially-uninitialised string-pointer reads (`pkg_name`, `app_id` may be uninitialised if getter never wrote them). Defect candidate worth a scenario.
- [E] Getter for `pkg_name` returns NONE but writes NULL into `pkg_name` — `strlen(NULL)` crashes. Document as defect candidate (current code does not NULL-check before `strlen`).
- [E] Getter for `lock_screen_content_level` returns a value outside the enum range — copied verbatim.
- [C] Reusing a `setting` struct that already has heap-allocated `package_name`/`app_id` → old pointers leak (no free-before-overwrite). Document caller-contract: zero-init the struct first.
- [C] `app_disabled` is bool but proxy returns garbage int — implicit narrowing.

### 6.8 `make_noti_setting_from_setting(void *settinghandle, notification_setting_h setting)`

**Signature:** `EXPORT_API int make_noti_setting_from_setting(void *, notification_setting_h);`

**Behavior:** Inverse of 6.7. Walks the eight setters via `__get_str_value`-protected string passes; bools/ints flow through unchecked. Each setter failure is logged ERR but never propagated. Always returns NONE.

**Errno map**
| Return | Trigger |
|--------|---------|
| `NOTIFICATION_ERROR_NONE` | Always |

**Scenarios**
- [P] Fully populated `setting` → every setter invoked with the real value; returns NONE.
- [P] `setting->package_name == NULL` → setter receives `""` via `__get_str_value`.
- [P] `setting->app_id == NULL` → setter receives `""`.
- [N] `setting == NULL` → first access `__get_str_value(setting->package_name)` dereferences NULL. Caller-contract violation.
- [N] `settinghandle == NULL` → setters all log ERR; function still returns NONE. Gap.
- [E] Any single setter failure (e.g. `set_visibility_class`) — logged, loop continues, return NONE.
- [E] `lock_screen_content_level` cast to `(int)` — truncation if enum is wider; document.
- [C] Round-trip with 6.7 → all fields preserved including empty-string-to-NULL on the reverse hop.
- [C] Concurrent mutation of `setting` mid-call — torn writes onto the proxy.

---

## Coverage check
- error: 1/1, ipc: 2/2, ongoing: 2/2, status: 3/3, viewer: 3/3, internal_tidl: 8/8
- Total: 19 / 19

---

# Final Coverage Summary

| Chunk | API 수 (목표) | 작성됨 | 비고 |
|-------|-------------:|-------:|------|
| §1 notification-ex headers | 43 cls / ~370 mtd | ✓ | mock_listener/mock_sender 는 stale stub (Open Q 참조) |
| §2 stub.cc C ABI | 183 | 183 ✓ | 12 템플릿 + 31 특수 함수 |
| §3 notification.c | 57 | 57 ✓ | 3 템플릿 (T_SIMPLE_SET/GET/FOR_UID_DELEGATE) |
| §4 notification_internal.c | 105 | 105 ✓ | 5 템플릿 (T1..T5) |
| §5 noti+setting+setting_service | 87 | 87 ✓ | T_get_setting_field / T_set_setting_field 등 |
| §6 db+list+shared_file | 28 | 28 ✓ | shared_file 은 LCOV_EXCL_START — 통합테스트로 검증 |
| §7 error/ipc/ongoing/status/viewer/internal_tidl | 19 | 19 ✓ | |
| **Total** | **522** | **522** | **100% coverage** |

## 종합 open questions / 잠재 결함 (각 chunk 에서 surfaced)

### Chunk 1 (ex headers)
- `mock_listener.h` / `mock_sender.h` 가 stale: 존재하지 않는 헤더 include + 잘못된 override 시그니처. 컴파일 안 됨.
- `EventInfo::GetRequestId()` allocation 정책 미정.
- `DBManager` / `SharedFile` 의 raw int 반환 → `NotificationError` enum 매핑 필요.

### Chunk 2 (stub.cc)
- `noti_ex_item_group_get_app_label`, `_input_selector_set_multi_language_contents`, `_find_by_id`, `_item_set_channel`, 일부 reporter list ops: NULL 검증 누락 → 잠재 SIGSEGV.
- `noti_ex_item_get_private_id`: `GetInfo()` null-deref 가능.
- `noti_ex_style_get_padding`: 형제 getter 들과 errno 불일치.
- `noti_ex_reporter_find_all`: NOT_EXIST_ID 분기에서 `*count = 0` 누락.
- `noti_ex_manager_create` / `_reporter_create`: `nothrow new` 결과 null 검증 누락.
- 다수의 `_get_*_str`: strdup OOM 검증 누락 (일관성 결여).

### Chunk 3 (notification.c)
- L140 copy-paste bug 의심 (`bundle_del(b, ...)` 가 `priv_b` 의도였을 가능성).
- `notification_get_tag`: tag out-pointer NULL 미검사.
- `notification_get_event_handler`: `out:` cleanup 이 실패시에도 `*event_handler` 무조건 write.
- `notification_add_button`: validation-only, state mutation 없음.
- `notification_clone` / `notification_set_text_domain`: strdup/bundle_dup 실패 silently ignored.

### Chunk 4 (notification_internal.c)
- `translate_localized_text` NULL 가드 누락.
- `update_for_uid` 의 mutex+refresh side effect (에러 경로).
- `notification_new` 가 두 인자 무시.
- `notification_get_extension_event_handler`: `noti->args` 무가드 read.
- `get_app_label`: NONE 반환했지만 `*label` 미작성.
- `insert_for_uid` / `post_for_uid`: 부분 실패 시 id leak.

### Chunk 5 (noti+setting)
- `get_channel`, `check_tag`, `get_channel_list`: raw sqlite 에러 코드를 그대로 leak (FROM_DB 매핑 누락).
- `notification_noti_get_all_count`: sqlite3_mprintf NULL 시 FROM_DB (OUT_OF_MEMORY 가 맞는데).
- `notification_system_setting_get_dnd_schedule_enabled_uid`, `_get_do_not_disturb`, `_load_dnd_allow_exception`, `_get_dnd_and_allow_to_notify`: out-pointer 미검증 → 잠재 crash.
- `notification_noti_init_data`: void 반환, side-effect 만.

### Chunk 6 (db+list+shared_file)
- `notification_get_list_by_page_for_uid` (L312): `get_list==NULL` 일 때도 `*list = get_head` → caller 가 NE 받지만 `*list==NULL`.
- `notification_calibrate_private_sharing`: vibration 분기가 `priv_vibration_path` 를 읽지만 sound 분기는 `sound_path` 사용 (asymmetry).
- `notification_list_remove`: NULL 반환이 "only-element removed" vs "noti not found" 구분 불가.
- `notification_db_column_text`: NULL 반환이 SQL NULL / 빈 문자열 / strdup OOM 셋 모두 의미 가능.

### Chunk 7 (misc)
- `notification_ongoing_*_cb_set/unset`: 현재 stub. NONE 만 반환.
- `notification_init_default_viewer`: POSIX 0/-1 반환 (notification errno family 아님).
- TIDL marshaling 함수들: 일부 setter 실패 silently swallow.

## 다음 단계

각 `[P]/[N]/[E]/[C]` 행 = 한 개 google-test `TEST_F` 와 1:1 매핑.
template 인 행은 template 정의의 시나리오를 그대로 매핑.

mock 대상 (notification 패키지 외부 dep):
- sqlite3 API (db_open, prepare_v2, step, column_text, mprintf, exec, get_table)
- glib API (g_variant_*, g_dbus_*, g_bus_*, g_hash_table_*, g_list_*)
- bundle API
- pkgmgr-info API
- security-manager API
- tzplatform_config
- vconf
- aul
- tizen_core

test fixture 패턴: `TestFixture + ModuleMock + mock_hook` (Tizen AppFW 표준).
