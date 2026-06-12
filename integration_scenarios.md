# notification ↔ data-provider-master Integration Test Scenarios

> Author: pipeline analysis agent
> Target packages: `migration/notification` (TIDL client + public API)
>                  `migration/data-provider-master` (DPM, TIDL server `noti_service`)
> Scope: in-process / on-device integration tests that exercise the **real**
>        TIDL channel (`rpc-port`) between the `notification` client library
>        and the `data-provider-master` server — i.e. no mocks at the boundary.

---

## 1. Analyzed test patterns in `appfw_pkgs/`

I scanned every package under `/home/kimhyeonuk/.openclaw/workspace/appfw_pkgs/`
for `integ_tests/`, `tests/`, `test/`, and the spec `%check` section. Findings:

| Package | Has `integ_tests/`? | Test pattern |
|---|:---:|---|
| `badge` | Yes (`tests/integ_tests/`) | Real DB + real TIDL server |
| `shortcut` | Yes (`tests/integ_tests/`) | Real DB + real DBus + real callback round-trip |
| `alarm` | No (only `test/unit_tests/`) | Pure unit, gmock |
| `data-control` | No (only `tests/unit_tests/` + `mock/`) | Pure unit, gmock |
| `notification` | No (only `tests/unittests/`) | Pure unit, gmock |
| `data-provider-master` | No (only `tests/unit_tests/` + `mock/`) | Pure unit, gmock |

So only `badge` and `shortcut` already have an integration tier. **Both are the
direct sibling packages of `notification`** — same author, same TIDL backend
(`data-provider-master`), and the same lifecycle: client library makes RPC
calls, DPM persists to a sqlite DB and broadcasts a change callback. The
notification integration tier should clone their conventions exactly.

### 1.1 `badge/tests/integ_tests/` pattern

- One executable target `badge_integtests`, source files under
  `integ_tests/src/{test_main.cc, test_badge.cc}`.
- `test_main.cc` is a trivial gtest harness — `InitGoogleTest` →
  `RUN_ALL_TESTS`, wrapped in try/catch.
- One `BadgeTest` fixture per file. The fixture's `SetUp`/`TearDown` calls a
  module-private `DbDeleteAll()` helper that opens the real
  `${TZ_SYS_DB}/.badge.db` (path baked in at CMake time via `-DDB_PATH=...`)
  and truncates the badge tables. **No mocks at all.**
- Test body calls the **public C API** (`badge_add`, `badge_set_count`,
  `badge_register_changed_cb`, etc.) and asserts the side effect by either
  - calling the matching getter (`badge_get_count`), or
  - waiting on a `GMainLoop` and asserting the callback fired
    (`badge_register_changed_cb*` tests).
- The change-callback tests are the load-bearing ones — they validate the
  whole pipe: client API → TIDL request → DPM → DB write → DPM broadcast →
  TIDL delegate → client callback → glib mainloop.
- `CMakeLists.txt` links `badge_integtests` against the **real** `${TARGET_BADGE}`
  shared library (no mock layer), pulls in `RPC_PORT_DEPS`, `APP_MANAGER_DEPS`,
  `APP_COMMON_DEPS`, `TIZEN_DATABASE_DEPS`, `BUNDLE_DEPS`, `DLOG_DEPS`,
  `GLIB_2_DEPS`, `GMOCK_DEPS`, `SYSTEM_INFO_DEPS`, and installs to `/usr/bin/`.
- spec ships it in the `-unittests` sub-RPM:
  ```
  %{_bindir}/badge_unittests
  %{_bindir}/badge_integtests
  %{_bindir}/tizen-unittests/%{name}/run-unittest.sh
  ```
  `ctest -V` runs in `%check`, but `badge_integtests` is **not** invoked there
  because it needs a running DPM and a real DB on the device — it runs from
  `run-unittest.sh` (i.e. on a Tizen target via tizen-unittests harness).

### 1.2 `shortcut/tests/integ_tests/` pattern

Same skeleton as badge with three extra wrinkles worth importing:

1. **DB pre-seeding helpers.** Two helpers `DbInsertRecord(...)` and
   `DbInsertName(id, pkgid, lang, name, icon)` write directly into
   `shortcut_service` and `shortcut_name` tables to set up read-side tests
   (`shortcut_get_list`). This is the pattern for "given existing DPM state,
   does the client API read it correctly?"
2. **Negative-path coverage in the integration tier.** Tests like
   `shortcut_add_to_home_n` (invalid shortcut_type),
   `shortcut_add_to_home_widget_n1` (NULL name), `shortcut_get_list_n` (NULL
   callback) assert `SHORTCUT_ERROR_INVALID_PARAMETER` from the *client side*.
   These confirm the input-validation layer fails fast **before** crossing
   the TIDL boundary.
3. **`request_cb` / `remove_cb` round-trip tests.** The pair
   `shortcut_set_request_cb2` + `shortcut_add_to_home_sync` proves the
   request-callback registered on socket A is fired by DPM when socket B issues
   a sync add — a true cross-client integration check. Notification has the
   exact analogue with `register_changed` / `register_event`.

### 1.3 Conventions both packages share

- `${TZ_SYS_DB}/<pkg>.db` path is fixed at build time via `-DDB_PATH=...`.
- Fixture uses `SetUp() { DbDeleteAll(); } TearDown() { DbDeleteAll(); }`
  so every test starts on a clean DB.
- Real TIDL: link against the real client `.so`, real `rpc-port`, expect a
  running DPM on the test host.
- Callbacks are observed through a per-test `GMainLoop`, quit by the callback
  body, asserted by a captured static flag.
- Integration binaries are installed to `/usr/bin/`, never invoked in `%check`.

---

## 2. notification ↔ DPM data flow (recap)

`notification.h` (and `notification_internal.h`) → `notification_tidl.c`
(generated proxy) → **rpc-port socket `org.tizen.data_provider_service`** →
`data-provider-master/src/notification_service_tidl.c` (stub callbacks) →
`notification_noti.c` (DB ops) / `notification_setting_service.c` →
`${TZ_SYS_DB}/.notification.db` → broadcast via delegate → client
`register_changed` / `register_event` callbacks.

Key TIDL methods (`tidl/noti_service.tidl`) that the integration tests must
exercise:

- CRUD: `add_noti`, `update_noti`, `refresh_noti`, `delete_single_noti`,
  `delete_multiple_noti`, `delete_noti_by_display_applist`.
- Read: `get_noti_count`, `get_all_noti_count`, `load_noti_by_tag`,
  `load_noti_by_priv_id`, `load_noti_grouping_list`, `load_noti_detail_list`.
- Setting: `update_noti_setting`, `update_noti_sys_setting`,
  `get_setting_array`, `get_setting_by_app_id`, `load_system_setting`,
  `update_dnd_allow_exception`, `get_noti_block_state`.
- Template: `save_as_template`, `create_from_template`,
  `create_from_package_template`.
- Channel: `channel_insert`, `channel_delete`, `channel_update`,
  `channel_get`, `channel_get_list`.
- Event / delegate: `register_changed`/`unregister_changed`,
  `register_event`/`unregister_event`, `send_event`,
  `send_event_by_priv_id`, `check_event_receiver`, `reset_event_handler`.
- DND: `register_dnd_app`, `unregister_dnd_app`, `update_dnd_allow_exception`.
- Service lifecycle: `register_service`.

Tables touched on DPM side: `noti_list`, `noti_group_list`,
`noti_setting`, `noti_system_setting`, `noti_dnd_allow_exceptions`,
`noti_template`, `noti_channel`.

---

## 3. Integration test scenarios

### Categories

1. Basic CRUD (`TC-INT-001..006`)
2. Setting / configuration (`TC-INT-007..011`)
3. Error handling / negative path (`TC-INT-012..015`)
4. Concurrency / multi-client (`TC-INT-016..018`)
5. Lifecycle / persistence (`TC-INT-019..021`)
6. Privilege / per-uid isolation (`TC-INT-022..024`)
7. Channel + template + DND (`TC-INT-025..028`)

Difficulty: **LOW** ≈ same shape as `badge_integtests`; **MED** ≈ needs a
`GMainLoop` callback or DB pre-seed; **HIGH** ≈ needs two processes, signal
injection, or restart of DPM.

---

### Category 1 — Basic CRUD

#### TC-INT-001: notification_post writes a row visible via notification_load_by_tag
- **Purpose:** Smoke check the add path: client API → TIDL `add_noti` → DPM
  inserts row → client `load_noti_by_tag` reads it back.
- **Preconditions:** `data-provider-master.service` is running; `.notification.db`
  cleared in `SetUp()`.
- **Input:** `notification_h` built with `notification_create(NOTIFICATION_TYPE_NOTI)`,
  `notification_set_text(TITLE, "hi")`, `notification_set_tag("tc001")`.
- **Steps:**
  1. `notification_post(noti)` → expect `NOTIFICATION_ERROR_NONE` and a non-zero `priv_id`.
  2. `notification_load_by_tag("tc001")` → expect non-NULL handle.
  3. `notification_get_text(loaded, NOTIFICATION_TEXT_TYPE_TITLE, &out)` →
     expect `"hi"`.
- **Expected:** all returns `NOTIFICATION_ERROR_NONE`, title matches.
- **Difficulty:** LOW

#### TC-INT-002: notification_update mutates an existing row
- **Purpose:** Verify `update_noti` TIDL path overwrites in DB.
- **Preconditions:** A notification already posted (use TC-001 setup).
- **Input:** Same handle with `notification_set_text(CONTENT, "v2")`.
- **Steps:**
  1. Post initial noti, capture `priv_id`.
  2. Update content text and call `notification_update(noti)`.
  3. `notification_load_by_priv_id(app_id, priv_id)` → verify content == "v2".
- **Expected:** Returns `NOTIFICATION_ERROR_NONE`; row's `priv_id` unchanged.
- **Difficulty:** LOW

#### TC-INT-003: notification_delete removes the row
- **Purpose:** Verify `delete_single_noti` TIDL path.
- **Steps:**
  1. Post a noti and capture handle.
  2. `notification_delete(noti)` → `NOTIFICATION_ERROR_NONE`.
  3. `notification_load_by_priv_id(app_id, priv_id)` → expect
     `NOTIFICATION_ERROR_FROM_DB` or returned handle NULL.
  4. `notification_get_count(NOTIFICATION_TYPE_NOTI, NULL, NOTIFICATION_GROUP_ID_NONE, NOTIFICATION_PRIV_ID_NONE, &count)`
     → expect `count == 0`.
- **Difficulty:** LOW

#### TC-INT-004: notification_delete_all clears by type
- **Purpose:** Verify `delete_multiple_noti` for whole-type wipe.
- **Steps:**
  1. Post 3 NOTI + 2 ONGOING notifications.
  2. `notification_delete_all(NOTIFICATION_TYPE_NOTI)` → `NONE`.
  3. `notification_get_all_count(NOTIFICATION_TYPE_NOTI, &c1)` → 0.
  4. `notification_get_all_count(NOTIFICATION_TYPE_ONGOING, &c2)` → 2.
- **Difficulty:** LOW

#### TC-INT-005: notification_get_list returns posted notifications in order
- **Purpose:** Verify `load_noti_grouping_list` returns the expected list with
  the correct sort order (insert_time descending).
- **Steps:** Post 3 notifications, sleep 10ms between each. Then
  `notification_get_list(NOTIFICATION_TYPE_NOTI, -1, &list)` and walk the list
  with `notification_list_get_head / get_next`. Assert size == 3 and order is
  newest-first.
- **Difficulty:** LOW

#### TC-INT-006: notification_get_count by group_id filters correctly
- **Purpose:** Verify get_noti_count argument routing (group_id filter).
- **Steps:** Post two with `set_group_id(7)`, one with `set_group_id(8)`. Call
  `notification_get_count(NOTIFICATION_TYPE_NONE, NULL, 7, NOTIFICATION_PRIV_ID_NONE, &c)`
  → expect 2.
- **Difficulty:** LOW

---

### Category 2 — Setting / configuration

#### TC-INT-007: notification_setting_update_setting persists to DPM
- **Purpose:** Verify `update_noti_setting` TIDL writes `noti_setting` row.
- **Steps:**
  1. `notification_setting_get_setting_by_appid("org.tizen.test", &setting)` —
     baseline.
  2. `notification_setting_set_allow_to_notify(setting, false)`.
  3. `notification_setting_update_setting(setting)` → `NONE`.
  4. Re-fetch via `..._get_setting_by_appid` → assert `allow == false`.
- **Difficulty:** LOW

#### TC-INT-008: system setting DND round-trip
- **Purpose:** Verify `update_noti_sys_setting` + `load_system_setting`.
- **Steps:** Set DND=true, schedule_enabled=true, dnd_start_hour=22,
  dnd_end_hour=7. `notification_system_setting_update_system_setting(sys)`.
  Re-load and assert all four fields.
- **Difficulty:** LOW

#### TC-INT-009: DND allow-exception list round-trip
- **Purpose:** `update_dnd_allow_exception` per-(type,value) tuple.
- **Steps:** Add three allow-exceptions of different types
  (NOTIFICATION_DND_SCHEDULE_TYPE_*). Reload the system_setting and assert the
  exception list size and contents.
- **Difficulty:** MED

#### TC-INT-010: get_setting_array enumerates every package
- **Purpose:** After setting overrides for two app IDs,
  `get_setting_array` must return both with the correct overrides.
- **Steps:** Update setting for `app.a` (block) and `app.b` (allow). Call
  `notification_setting_get_setting_array(&arr, &count)` and verify the two
  entries are present.
- **Difficulty:** MED

#### TC-INT-011: notification_get_noti_block_state composes all three flags
- **Purpose:** Verify `get_noti_block_state` returns the AND of system DND,
  DND-except, and per-app allow_to_notify.
- **Steps:** Set sys DND=true, DND-except for app=true,
  per-app allow_to_notify=false; call `notification_get_noti_block_state(app)`;
  expect `allow == 0`.
- **Difficulty:** MED

---

### Category 3 — Error handling / negative path

#### TC-INT-012: client API rejects NULL handle before TIDL
- **Purpose:** Mirror `shortcut_add_to_home_widget_n1` — input validation must
  fail fast on the client side, no socket traffic.
- **Steps:** `notification_post(NULL)` → expect
  `NOTIFICATION_ERROR_INVALID_PARAMETER` (not `..._SERVICE_NOT_READY`).
- **Difficulty:** LOW

#### TC-INT-013: DPM unavailable returns SERVICE_NOT_READY
- **Purpose:** Verify `notification_tidl.c` reports a service-unavailable error
  instead of crashing when DPM socket is missing.
- **Preconditions:** Stop `data-provider-master.service` in `SetUpTestSuite`.
  Restart it in `TearDownTestSuite`.
- **Steps:** `notification_post(valid_handle)` → expect
  `NOTIFICATION_ERROR_SERVICE_NOT_READY` (or `..._IO_ERROR` depending on
  current mapping — assert one of the documented error codes, *not* a crash).
- **Difficulty:** HIGH (needs systemctl on the test host)

#### TC-INT-014: invalid tag returns NOT_EXIST_ID
- **Purpose:** `load_noti_by_tag` for a non-existent tag must return a typed
  failure, not garbage.
- **Steps:** `notification_load_by_tag("does-not-exist")` → expect NULL handle
  and `get_last_result() == NOTIFICATION_ERROR_FROM_DB` or
  `..._NOT_EXIST_ID`.
- **Difficulty:** LOW

#### TC-INT-015: delete of unknown priv_id returns NOT_EXIST_ID
- **Purpose:** `delete_single_noti` for a `priv_id` that was never posted.
- **Steps:** Build a fresh `notification_h`, set `priv_id` to 99999 (raw),
  call `notification_delete(noti)` → expect a `NOT_EXIST_ID`-class error.
- **Difficulty:** LOW

---

### Category 4 — Concurrency / multi-client

#### TC-INT-016: register_changed callback fires on cross-thread post
- **Purpose:** The marquee end-to-end test — same shape as `badge_register_changed_cb`.
  Thread A registers `notification_register_changed_cb`. Thread B posts.
  Thread A's `GMainLoop` must receive the delegate callback.
- **Steps:**
  1. Main thread: `g_main_loop_new`, `notification_register_changed_cb(cb,
     &flag)` → expects `NONE`.
  2. Detach a thread that creates a notification and calls `notification_post`.
  3. `g_main_loop_run`. Inside `cb`, set `flag=true` and `g_main_loop_quit`.
  4. Assert `flag == true` and `NOTIFICATION_ERROR_NONE`.
- **Difficulty:** MED

#### TC-INT-017: two clients see each other's posts (broadcast fan-out)
- **Purpose:** Verify DPM broadcasts to every registered viewer, not just the
  poster. Models the desktop-style "every notification panel updates" path.
- **Steps:** Fork the test process. Child: register changed-cb, mainloop.
  Parent: sleep 50ms, post a noti. Child must receive callback within 1s.
- **Difficulty:** HIGH

#### TC-INT-018: rapid post storm (200 posts) — no drops, monotonic priv_id
- **Purpose:** Stress the TIDL queue and DB transactions. Verifies DPM
  serializes `add_noti` requests and that returned `priv_id` is monotonic and
  unique.
- **Steps:** Loop `notification_post` 200 times in tight succession; collect
  each `priv_id`. Then `notification_get_all_count` → expect 200; verify
  set(priv_ids).size() == 200 and that the list is strictly increasing.
- **Difficulty:** MED

---

### Category 5 — Lifecycle / persistence

#### TC-INT-019: data survives client-side fini → init
- **Purpose:** Verify state lives in DPM, not client memory.
- **Steps:** Post a noti, capture tag. Call any client `_fini` if available
  (or just dlclose/reload — drop in helper). Re-load and call
  `notification_load_by_tag(tag)` → row still there.
- **Difficulty:** MED

#### TC-INT-020: data survives DPM restart
- **Purpose:** DPM persists to disk; restarting the service keeps the row.
- **Preconditions:** Posts a noti, then `systemctl restart data-provider-master`.
- **Steps:** After restart, retry `notification_load_by_tag(tag)` — row still
  there; client-side socket reconnects transparently.
- **Difficulty:** HIGH

#### TC-INT-021: register_changed survives DPM reconnect
- **Purpose:** A registered viewer should reattach after DPM bounce and still
  see broadcasts (`notification_tidl.c` reconnect path).
- **Steps:** Register cb. Restart DPM. Sleep 500ms for reconnect. Post a noti
  from the same process. Assert cb fires.
- **Difficulty:** HIGH

---

### Category 6 — Privilege / per-uid isolation

#### TC-INT-022: notification.tidl `[privilege = "...notification"]` enforced
- **Purpose:** TIDL stub rejects callers without the `notification` privilege.
- **Steps:** Run the test binary as an `app_fw`-unprivileged user (use
  `setuid`/`security-manager` helper to drop the priv). Call
  `notification_post` → expect `NOTIFICATION_ERROR_PERMISSION_DENIED`.
- **Difficulty:** HIGH

#### TC-INT-023: per-uid row isolation
- **Purpose:** uid argument in every TIDL call must scope the DB query —
  posting as uid 5001 must be invisible to a load issued for uid 5002.
- **Steps:** Post under uid 5001 (set via setresuid in a child). Then under
  uid 5002, `notification_get_all_count(NOTIFICATION_TYPE_NONE, &c)` → expect 0
  (or only 5002's own).
- **Difficulty:** HIGH

#### TC-INT-024: deleting another app's noti is rejected
- **Purpose:** `delete_single_noti(app_id, priv_id, uid)` must verify
  ownership server-side.
- **Steps:** Post as `app.A`. Construct a noti handle that claims
  `caller_app_id = "app.A"` but call `notification_delete` from a process
  whose AUL appid is `app.B` → expect
  `NOTIFICATION_ERROR_PERMISSION_DENIED` or `INVALID_OPERATION`.
- **Difficulty:** HIGH

---

### Category 7 — Channel, template, DND

#### TC-INT-025: channel_insert + channel_get round-trip
- **Purpose:** Verify TIDL channel CRUD against `noti_channel` table.
- **Steps:**
  1. `notification_set_channel("ch1", true, false)` (or the matching internal
     API that wraps `channel_insert`).
  2. Query via `notification_channel_get_list(app_id, &list)` → contains "ch1".
  3. `notification_channel_update("ch1", true, true)`; re-query → `is_blocked == true`.
  4. `notification_channel_delete("ch1")`; re-query → not present.
- **Difficulty:** MED

#### TC-INT-026: save_as_template + create_from_template round-trip
- **Purpose:** Verify TIDL template path against `noti_template` table.
- **Steps:**
  1. Build a noti with set_text/set_image/set_sound.
  2. `notification_save_as_template(noti, "tpl1")` → `NONE`.
  3. New empty handle; `notification_create_from_template(&new_h, "tpl1")`
     → `NONE`. Assert title, image, sound match.
- **Difficulty:** MED

#### TC-INT-027: register_dnd_app + DND override
- **Purpose:** `register_dnd_app` whitelists pid for DND. While system DND is
  on, a posted noti from the whitelisted pid still triggers the changed_cb.
- **Steps:**
  1. Set sys setting `do_not_disturb = true`.
  2. `notification_register_dnd_app(uid, getpid())`.
  3. Register changed_cb, post a noti.
  4. Callback must fire (DND bypassed).
- **Difficulty:** MED

#### TC-INT-028: send_event + register_event delegate
- **Purpose:** Reverse channel — viewer-side `register_event` callback must
  receive the event posted by `notification_send_event_by_priv_id`.
- **Steps:**
  1. Process P1 (or thread): `notification_register_detailed_changed_cb` /
     `notification_register_event_cb`; mainloop.
  2. P2: post noti, get priv_id, then `notification_send_event_by_priv_id(
     priv_id, NOTIFICATION_EVENT_TYPE_CLICK_ON_BUTTON_1)`.
  3. P1's event cb must fire with the matching priv_id and event_type.
- **Difficulty:** HIGH

---

## 4. Suggested layout under `migration/notification/`

Mirror `badge`/`shortcut`:

```
migration/notification/tests/
├── CMakeLists.txt                # add_subdirectory(unittests) + add_subdirectory(integ_tests)
├── mock/                         # (unchanged, only for unit tests)
├── unittests/                    # (unchanged)
└── integ_tests/
    ├── CMakeLists.txt            # link real notification.so + RPC_PORT_DEPS
    └── src/
        ├── test_main.cc          # gtest harness (copy from badge)
        ├── test_notification_crud.cc          # TC-INT-001..006
        ├── test_notification_setting.cc       # TC-INT-007..011
        ├── test_notification_error.cc         # TC-INT-012..015
        ├── test_notification_concurrency.cc   # TC-INT-016..018
        ├── test_notification_lifecycle.cc     # TC-INT-019..021
        ├── test_notification_privilege.cc     # TC-INT-022..024
        └── test_notification_channel.cc       # TC-INT-025..028
```

In the spec:

```
%files unittests
%{_bindir}/notification_unittests
%{_bindir}/notification_integtests
%{_bindir}/tizen-unittests/%{name}/run-unittest.sh
```

Do **not** add `notification_integtests` to `%check` — it requires a live DPM
+ writable `${TZ_SYS_DB}/.notification.db` and (for the HIGH cases) systemctl,
which are not available in the GBS sandbox. It runs from the on-device
`run-unittest.sh` exactly like `badge_integtests`.

---

## 5. Coverage tally

| Category | Count | LOW | MED | HIGH |
|---|---:|---:|---:|---:|
| 1. CRUD                | 6 | 6 | 0 | 0 |
| 2. Setting / config    | 5 | 2 | 3 | 0 |
| 3. Error / negative    | 4 | 3 | 0 | 1 |
| 4. Concurrency         | 3 | 0 | 2 | 1 |
| 5. Lifecycle           | 3 | 0 | 1 | 2 |
| 6. Privilege / uid     | 3 | 0 | 0 | 3 |
| 7. Channel/template/DND | 4 | 0 | 3 | 1 |
| **Total**              | **28** | **11** | **9** | **8** |

Recommended landing order: ship the 11 LOW cases first (one source file each
in CRUD + Setting + Error) — they prove the wiring against a clean DPM with no
extra fixtures. Then layer MED (mainloop callbacks, channels, templates), and
keep HIGH (DPM bounce, fork, privilege drop) for a follow-up patch once the
test host has the systemctl/security-manager hooks plumbed.
