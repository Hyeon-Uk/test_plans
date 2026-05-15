# notification — Coverage Progress

Date: 2026-05-15

## Workflow Executed

1. **Strip LCOV_EXCL markers** — `sed -i` over all `*.c` + `*.cc` / `*.h` / `*.hh` under `src/`; **must restore before commit** (working copy modified, not staged)
2. **Build + coverage** — `gbs build -A x86_64 --include-all --define "gcov 1"` → lcov HTML at `BUILD-ROOTS/.../notification.out/index.html`
3. **Audit** — parsed lcov HTML per source file, mapped uncovered branches to EXPORT_API/HAPI
4. **Scenario doc** — `notification_test_scenarios.md` (full gap inventory)
5. **Quick win batch** — extended `test_notification_db.cc` with +16 tests

## Coverage After Strip

Top-level: **39.8% lines / 58.0% functions** (denominator inflated by stripped LCOV_EXCL blocks)

| File | Lines % | Funcs % | Notes |
|---|---|---|---|
| notification.c | 75.4 | 95.2 | well covered |
| notification_db.c | 17→~75 | 41→100 | **+16 tests this round** |
| notification_error.c | 100 | 100 | |
| notification_group.c | 0 | 0 | **DEAD CODE** (header declares but never EXPORT_API'd) |
| notification_internal.c | 60 | 90.8 | partial |
| notification_internal_tidl.c | 0.4 | 11 | generated TIDL — skip |
| notification_ipc.c | 74.7 | 100 | |
| notification_list.c | 81.2 | 100 | |
| notification_noti.c | 61.7 | 81 | gaps: delete_by_priv_id (0%), get_count (0%) |
| notification_ongoing.c | 100 | 100 | wait — was 40%; check after build |
| notification_setting.c | 51.3 | 89.7 | |
| notification_setting_service.c | 28.7 | 80 | many DB-query funcs untested |
| notification_shared_file.c | 11.3 | 23.3 | **biggest gap** — 6 EXPORT_API for private sharing |
| notification_status.c | 27.3 | 75 | dbus paths untested |
| notification_tidl.c | 13.9 | 29.3 | RPC server required |
| notification_tidl_proxy.c | 0.5 | 0.6 | generated — skip |
| notification_viewer.c | 14.7 | 54.5 | tizen_core paths untested |

## Changes This Round

**Source mocks (`tests/mock/sqlite_mock.{hh,cc}`):**
- Added `sqlite3_prepare` (v1 form, used by `notification_group.c`)
- Added `sqlite3_errmsg` (used by every DB error path)

**Test files:**
- `tests/unittests/src/test_notification_db.cc`: +16 TEST_F cases covering
  - `notification_db_open`: SQLITE_PERM, SQLITE_ERROR
  - `notification_db_close`: sqlite3_close failure → FROM_DB
  - `notification_db_exec`: null db / null query / prepare fail / step fail / null num_changes ok
  - `notification_db_column_text`: null + empty string → NULL
  - `notification_db_column_bundle`: null → NULL
  - `notification_db_init`: open fail / create table fail / success
  - `notification_upgrade_db`: open fail / BEGIN TRANSACTION fail

**Test count:** 800 → 816 (+16), all green.

**Files NOT yet tested (scenarios written, code pending):**
- shared_file.c — 6 EXPORT_API × ~5 scenarios each = ~30 tests
- status.c — 3 EXPORT_API × 4 scenarios = ~12 tests
- setting_service.c — 11+ EXPORT_API × 4 scenarios = ~45 tests
- noti.c delete_by_priv_id, get_count — ~12 tests
- internal.c register/unregister cb — ~10 tests
- db.c upgrade_db rollback — ~6 tests
- notification.c get_text substitution — ~6 tests
- Total remaining: **~120 new test cases** documented in `notification_test_scenarios.md`

## Skipped (Documented)

| File | Reason |
|---|---|
| notification_group.c | Functions declared in header but missing `EXPORT_API` macro — not exported from `libnotification.so`, unreachable from tests. **Source bug** — recommend removing header decls or adding `EXPORT_API` |
| notification_internal_tidl.c | Auto-generated from `.tidl` (946 lines) — TIDL boilerplate, would require real RPC server |
| notification_tidl_proxy.c | Same — 5957 lines of generated TIDL |
| notification_tidl.c | Calls real `rpc_port_stub_*` register that segfaults without service runtime |
| notification_viewer.c (delayed_noti paths) | Tightly coupled to `tizen_core` — would need full core mock |

## Mock Infrastructure Limits Found

1. **`access()` mock hardcoded** — `glib_mock.cc:37-47` always returns 0 for paths containing `.notification.db` or `notification.ini`. Cannot test `notification_db_open` access-fail path or `notification_init_default_viewer` config-missing path through gmock.
2. **No `g_hash_table_*` mock** — blocks testing of OOM paths in `register_changed_cb_for_uid`
3. **No `iniparser` mock** — blocks `init_default_viewer` parse-fail paths
4. **No `security_manager_create_sharing` mock** — blocks `notification_set_private_sharing` IPC failure paths

## Next Actions (Recommended Order)

1. Restore `LCOV_EXCL_*` markers (`git checkout HEAD -- src/`) before any commit
2. Implement scenario batch from `notification_test_scenarios.md` priority list
3. Add missing mocks: `g_hash_table_new`, `iniparser_load`, `security_manager_create_sharing`
4. After each batch (10 funcs), re-run gbs with `--define "gcov 1"` to measure delta
5. Bug report: `notification_group.c` functions have no `EXPORT_API` — header lies

## Files Modified (Working Copy, Uncommitted)

- `src/notification/src/*.c` — LCOV_EXCL markers stripped (must restore)
- `src/notification-ex/*.cc`, `*.h`, `*.hh` — same
- `tests/mock/sqlite_mock.hh` — +2 mock methods
- `tests/mock/sqlite_mock.cc` — +2 extern "C" hooks
- `tests/unittests/src/test_notification_db.cc` — +16 tests
- `notification_test_scenarios.md` — NEW
- `notification_coverage_progress.md` — NEW (this file)

Build status: **GREEN** (816/816 tests pass, gcov enabled).
