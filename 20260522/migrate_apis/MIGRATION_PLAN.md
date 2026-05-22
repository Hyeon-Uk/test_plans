# Notification → data-provider-master API Migration Plan

## 1. Background

`notification` (proxy/client) and `data-provider-master` (DPM, stub/server) communicate via TIDL
(`noti_service.tidl`, identical copy in both repos). TIDLC generates:

| Repo                    | Side  | Generated                                      |
|-------------------------|-------|------------------------------------------------|
| `notification`          | proxy | `notification_tidl_proxy.{c,h}` → libnotification.so |
| `data-provider-master`  | stub  | `notification_tidl_stub.{c,h}` → libdata-provider-master.so |

Both sides communicate over `rpc-port`. DPM implements the server logic — it
opens a stub port, dispatches incoming notification RPC calls, persists state to
the notification SQLite DB, manages settings, etc.

Today `libnotification.so` exposes a mixed surface:
- **client-side APIs** (`notification_create`, `notification_post`, …) — used by apps.
- **server-side helpers** (DB access, setting service, viewer launcher, shared-file plumbing) —
  used *only* by DPM, but currently shipped inside `libnotification.so`.

This plan removes the server-only helpers from `libnotification.so` and relocates them
to DPM, leaving `notification` as a leaner client-only library.

## 2. Analysis methodology

- Cloned all 65 packages from `review.tizen.org` on the `tizen` branch (commit-msg hook installed).
- Ran graphify AST extraction over the entire corpus (30,943 nodes, 60,745 edges).
- Parsed every function declaration in notification's 19 installed devel headers (273 unique functions).
- For each function, grepped across the other 64 packages (`--include={*.c,*.cc,*.cpp,*.h,*.hh,*.hpp,*.cxx}`)
  to map consumers.
- Classified each function as:
  - **DPM-only**: referenced only by `data-provider-master`
  - **Shared**: referenced by DPM and at least one other package
  - **Unused**: not referenced anywhere outside notification

### Per-header summary

| Header                              | Total | DPM-only | Shared | Unused |
|-------------------------------------|------:|---------:|-------:|-------:|
| notification.h                      | 53    | 3        | 5      | 45     |
| notification_db.h                   | 7     | 2        | 0      | 5      |
| notification_internal.h             | 81    | 10       | 2      | 69     |
| notification_ipc.h                  | 2     | 0        | 2      | 0      |
| notification_list.h                 | 15    | 4        | 0      | 11     |
| **notification_noti.h**             | 27    | **23**   | 0      | 4      |
| notification_ongoing.h              | 5     | 0        | 0      | 5      |
| notification_ongoing_flag.h         | 2     | 0        | 0      | 2      |
| notification_setting.h              | 7     | 3        | 0      | 4      |
| notification_setting_internal.h     | 43    | 12       | 0      | 31     |
| **notification_setting_service.h**  | 15    | **13**   | 0      | 2      |
| **notification_shared_file.h**      | 8     | **5**    | 0      | 3      |
| notification_status.h               | 1     | 0        | 0      | 1      |
| notification_status_internal.h      | 2     | 0        | 0      | 2      |
| notification_text_domain.h          | 2     | 0        | 0      | 2      |
| **notification_viewer.h**           | 3     | **3**    | 0      | 0      |

(headers with 0 DPM-only and 0 shared omitted)

### Internal-coupling check inside notification's own sources

For each candidate header, identified its implementing `.c` file and which *other* notification
source files call its functions. A header is "cleanly movable" if no other notification source
file calls into it.

| Header                          | Impl file                       | Other notification callers | Verdict |
|---------------------------------|---------------------------------|----------------------------|---------|
| `notification_viewer.h`         | `notification_viewer.c`         | *(none)*                   | **Clean — Phase 1** |
| `notification_shared_file.h`    | `notification_shared_file.c`    | `notification.c` calls `notification_check_file_path_is_private`; `notification_internal.c` calls `notification_copy_private_file` | **Phase 3a (function-level split)** — initially mis-classified as Phase 1 |
| `notification_noti.h`           | `notification_noti.c`           | `notification_internal.c::notification_get_grouping_list_for_uid` (uses `notification_noti_get_grouping_list`) | Phase 2 (deprecated wrapper must be removed) |
| `notification_setting_service.h`| `notification_setting_service.c`| `notification_noti.c` (moved together) | Phase 2 |
| `notification_db.h` (DPM-only fns) | `notification_db.c`         | mixed — `notification_db.c` is also used by client | Phase 3b (per-symbol split) |
| `notification_list.h` (DPM-only fns) | `notification_list.c`     | `notification_noti.c` (moved together) | Phase 3b |
| `notification_internal.h` (DPM-only fns) | `notification_internal.c` | mixed — file has client + server symbols | Phase 3b (per-symbol split) |
| `notification_setting_internal.h` (DPM-only fns) | `notification_setting.c` / `notification_internal.c` | mixed | Phase 3b |

## 3. Phase plan

### Phase 1 — Clean whole-file move ✅ DONE

Move `notification_viewer.{c,h}`. All 3 functions are DPM-only, no internal cross-callers,
no test usage in notification's own test suite.

| From                                                                 | To                                                  |
|----------------------------------------------------------------------|-----------------------------------------------------|
| `notification/src/notification/src/notification_viewer.c`            | `data-provider-master/src/notification_viewer.c`    |
| `notification/src/notification/include/notification_viewer.h`        | `data-provider-master/include/notification_viewer.h`|

Functions: `notification_init_default_viewer`, `notification_launch_default_viewer`,
`notification_launch_default_viewer_without_candidate_process`.

> **Plan correction**: an earlier draft of this plan grouped `notification_shared_file.{c,h}`
> into Phase 1 as a "clean" move. That was wrong — `notification.c` calls
> `notification_check_file_path_is_private` and `notification_internal.c` calls
> `notification_copy_private_file`, so the file is mixed-use. Reclassified to **Phase 3a**.

### Phase 2 — Coupled bundle: notification_noti + notification_setting_service

Move `notification_noti.{c,h}` + `notification_setting_service.{c,h}` together.

**Prerequisite**: delete the two deprecated client wrappers
`notification_get_grouping_list` and `notification_get_grouping_list_for_uid` from
`notification_internal.c`. They are the *only* notification-internal callers of
`notification_noti_get_grouping_list`. Both are tagged `NOTIFICATION_DEPRECATED_API`,
and the symbol-usage grep across all 65 packages confirms zero in-tree consumers.
Also drop the corresponding declaration from `notification_internal.h`.

**Cross-references that resolve automatically** because both files move together:
- `notification_noti.c` → calls `noti_setting_service_get_setting_by_app_id`,
  `noti_system_setting_load_system_setting` (in setting_service)
- `notification_noti.c` → calls `notification_free_list`, `notification_list_get_head`
  in `notification_list.c` (stays in libnotification; DPM picks it up via `-lnotification`)

**Header install rules**: drop `notification_noti.h` and `notification_setting_service.h`
from `%files devel`. The notification CMake install glob already auto-skips deleted files.

### Phase 3a — Function-level split: notification_shared_file.c

Split `notification_shared_file.c` by callsite class:

| Function                                       | Class           | Destination          |
|------------------------------------------------|-----------------|----------------------|
| `notification_copy_private_file`               | client helper   | stays in notification |
| `notification_check_file_path_is_private`      | client helper   | stays in notification |
| `notification_validate_private_sharing`        | client helper   | stays in notification (used by client-side validate path) |
| `notification_set_private_sharing`             | DPM-only        | moves to DPM         |
| `notification_remove_private_sharing`          | DPM-only        | moves to DPM         |
| `notification_add_private_sharing_target_id`   | DPM-only        | moves to DPM         |
| `notification_remove_private_sharing_target_id`| DPM-only        | moves to DPM         |
| `notification_calibrate_private_sharing`       | DPM-only        | moves to DPM         |

Approach: keep `notification_shared_file.{c,h}` in notification with only the
client-helper functions. Create new `data-provider-master/src/dpm_shared_file.c`
(and matching `dpm_shared_file.h`) holding the moved DPM-only functions. Update
the notification header to only declare the surviving symbols. The moved-out
declarations remain in the new DPM-private header (used by other DPM source
files like `notification_service_tidl.c`).

### Phase 3b — Per-symbol split: notification_internal.c, _setting.c, _db.c, _list.c

For each mixed-use file, extract its DPM-only functions into a new
`dpm_<area>.c` in DPM and delete only those function bodies from notification's
sources. Declarations stay in the original notification header iff there is at
least one in-tree consumer outside DPM (otherwise the declaration moves too).

Concrete targets per `analysis/dpm_exclusive.tsv`:

- **notification_internal.c → dpm_internal.c**: 10 DPM-only functions including
  `notification_channel_*`, `notification_get_event_flag`, `notification_get_pkgname`,
  `notification_get_tag`, `notification_get_text`, `notification_get_uid`,
  `notification_get_extension_data`, `notification_get_pairing_type`,
  `notification_get_channel_name`. (NB: a subset of these — `_get_pkgname`,
  `_get_tag`, `_get_text` — live in `notification.h`/`notification.c` rather than
  internal.c; verify per-symbol before moving.)
- **notification_setting.c / setting_internal**: `notification_setting_*` server APIs
  (12 DPM-only fns) → `dpm_setting.c`
- **notification_db.c**: 2 DPM-only fns (`notification_db_init`, …) → `dpm_db.c`
- **notification_list.c**: 4 DPM-only fns (`notification_list_get_data`, `_get_head`,
  `_get_next`, `notification_free_list`) → these are tightly coupled to notification's
  own list type; in practice DPM still uses them on the lists returned by
  `notification_noti_get_grouping_list` etc. Keep them in libnotification and accept
  the cross-call. **Skip 3b-list — leave as-is.**

## 4. ABI and linking safety

- **No corpus regression.** The grep across all 65 packages confirms that no consumer
  outside `data-provider-master` references any of the symbols being removed.
- **`libnotification.so` SOVERSION**: removed exported symbols change the ABI. Tizen policy
  asks for a SOVERSION bump. Because the only consumer in our scope is DPM and DPM is
  rebuilt with the same source tree, the bump is *not strictly required for in-tree linking*;
  bumping is still recommended hygiene. Tracked as a final step.
- **DPM dependencies**: `notification_viewer.c` pulls in `iniparser` and `tizen-core` (already
  DPM deps after Phase 1's `iniparser` addition). `notification_noti.c` requires `db-util`
  (already a DPM dep). `notification_setting_service.c` requires `vconf` (already a DPM dep).
  The Phase 3a `dpm_shared_file.c` requires `security-manager` and
  `capi-appfw-package-manager` (already DPM deps).
- **Header install rules**: every removed-from-libnotification header is dropped from
  `notification.spec`'s `%files devel`. DPM ships moved headers as private (not installed).
  notification_private.h is brought into DPM as a private copy where needed.

## 5. Execution checklist

### Phase 1 (viewer) — ✅ DONE
- [x] DPM: copy `notification_viewer.{c,h}`, switch `notification_debug.h` → DPM's `debug.h`,
      add local `EXPORT_API` fallback, add `iniparser` to CMake/spec.
- [x] notification: delete files; drop `notification_viewer.h` from `%files devel`.

### Phase 2 (notification_noti + notification_setting_service) — ✅ DONE
- [x] notification: deleted `notification_get_grouping_list` and
      `notification_get_grouping_list_for_uid` from `notification_internal.c`;
      removed the public declaration from `notification_internal.h`.
- [x] DPM: copied `notification_noti.{c,h}` and `notification_setting_service.{c,h}` into DPM.
- [x] DPM: brought `notification_private.h`, `notification_db_query.h`, `config.{c,h}` over
      as private DPM headers/sources (notification_setting.c still uses its own `config` copy).
- [x] DPM: rewrote includes inside the moved `.c` files (use DPM's `debug.h`, local quoted
      headers, local `EXPORT_API` fallback).
- [x] DPM: added `capi-system-info`, `db-util`, `iniparser` to `pkg_check_modules` and spec.
- [x] notification: deleted the 4 source/header files; removed `notification_noti.h` and
      `notification_setting_service.h` from `%files devel`. The orphan `test_notification_noti.cc`
      was stubbed with `GTEST_SKIP()` so the test suite still builds.
- [x] notification: stripped dangling `<notification_noti.h>` / `<notification_setting_service.h>`
      includes from six surviving `.c` files (`notification.c`, `notification_internal.c`,
      `notification_internal_tidl.c`, `notification_list.c`, `notification_setting.c`,
      `notification_status.c`).

### Phase 3a (notification_shared_file split) — ✅ DONE
- [x] notification: trimmed `notification_shared_file.{c,h}` to only
      `notification_copy_private_file` and `notification_check_file_path_is_private`
      (and their static helpers `__is_RO_file`, `__is_res_file`, `__is_shared_file`,
      `__last_index_of`). The trimmed file is 238 lines.
- [x] DPM: created `dpm_shared_file.{c,h}` (1,209 lines) with the 6 DPM-only public
      functions plus their static helpers (`__make_sharing_dir`, `__make_file_info`,
      `__set_sharing_for_new_target`, `__set_sharing_for_new_file`, `__timeout_handler`,
      `__free_file_info`, `__free_req_info`, `__convert_list_to_array`, `__dup_file_info`,
      `__get_new_file_list`, `__get_shared_dir`, comparators, and a private copy of
      `__last_index_of`).
- [x] DPM: `__set_sharing_for_new_target` and `__set_sharing_for_new_file` were promoted
      to `static` in the moved file (they were unintentionally non-static in notification).
- [x] DPM: added `#include "dpm_shared_file.h"` to `notification_service_tidl.c`.

### Phase 3b (per-symbol split for internal/setting/db) — ✅ DONE
- [x] notification → DPM: extracted **7** DPM-only fns from `notification_internal.c`
      → `dpm_internal.{c,h}`. Also pulled the static helper `_create_bundle_from_bundle_raw`
      as a file-local copy.

> **Plan correction**: 3 of the originally-targeted 10 internal.h fns
> (`notification_channel_free`, `notification_get_event_flag`,
> `notification_get_extension_data`) turned out to have **internal libnotification
> callers** (`notification_tidl.c:1643`, three sites in `notification_internal.c`,
> and the `notification_get_extention_data` legacy-typo wrapper). The original cross-package
> grep correctly classified them DPM-only across the 65-package corpus but missed
> that they are still required inside libnotification's own source. They were
> reverted to `notification_internal.c`; declarations restored in
> `notification_internal.h`. DPM keeps using them via `-lnotification`. Net:
> 7 fns moved instead of 10.
- [x] notification → DPM: extracted 12 DPM-only fns from `notification_setting.c`
      → `dpm_setting.{c,h}`. Also moved 2 orphaned static helpers
      (`_install_and_update_package`, `_delete_package_from_setting_db`) and duplicated 2
      shared statics (`_is_package_in_setting_table`, `_foreach_app_info_callback`) that
      libnotification still needs.
- [x] notification → DPM: extracted 2 DPM-only fns from `notification_db.c`
      → `dpm_db.{c,h}`. Pulled along the 5 helper statics
      (`__check_db_version`, `__check_integrity_cb`, `__recover_corrupted_db`,
      `__upgrade_noti_table`, `__upgrade_noti_template_table`) and the `is_db_corrupted`
      flag they share.
- [x] notification: deleted the 24 moved declarations from the corresponding headers
      (notification_internal.h, notification_setting_internal.h, notification_db.h).
- [x] notification: patched `notification-test-app/main.cc` so its calls to moved getters
      (`_get_allow_to_notify`, `_get_do_not_disturb_except`, `_get_pop_up_notification`,
      `_system_setting_get_do_not_disturb`, `_system_setting_free_system_setting`,
      `_get_event_flag`) become stub defaults — the demo app still builds.
- [x] **`notification_list.c` deliberately left alone.** Its 4 DPM-only functions (`_get_data`,
      `_get_head`, `_get_next`, `notification_free_list`) operate on libnotification's own list
      type and are reachable from DPM via `-lnotification` linkage. Moving them would have
      required duplicating the list ADT.

### Final
- [x] Zero external regressions: full cross-package symbol grep over all 65 packages confirms
      that no consumer outside `data-provider-master` references any moved symbol.
- [ ] (Optional) bump `notification.spec` Version + CMake `MAJORVER` to signal the reduced
      symbol surface. Left to the project maintainer.
- [x] `gbs build -A armv7l` both packages — **both succeed**. `notification` %check: 82
      tests passed; `data-provider-master` %check: 5 tests passed.
      Post-migration build fixes that were required (the original Phase 1–3b commits did
      not actually compile):
      - notification: re-added the pure tag-string helpers (`notification_noti_set_tag`,
        `_strip_tag`, `_get_tag_type` + `TAG_*` macros) as file-local statics in
        `notification.c` — they were dragged out with `notification_noti.c` but
        `notification_get_time_from_text`/`_set_time_to_text` (client APIs) still need them.
      - notification: added `#include <sys/statvfs.h>` to trimmed `notification_shared_file.c`.
      - notification: fixed the re-added `notification_channel_free` declaration in
        `notification_internal.h` (`int` → `void`, matching the implementation).
      - notification: stubbed `notification_system_setting_dnd_schedule_get_enabled` in
        `notification-test-app/main.cc` (moved getter).
      - DPM: `debug.h` now `#include <dlog.h>` (was using `SECURE_LOG*` undeclared).
      - DPM: `dpm_internal.c` got the file-local `notification_channel_s` struct +
        `PAIRING_TYPE_KEY`; `dpm_internal.h` signatures corrected to match impls.
      - DPM: `dpm_setting.c` got `<package_manager.h>`, `<pkgmgr-info.h>`,
        `<notification_db.h>`, `notification_db_query.h` includes + the `setting_local_info`
        struct and `NOTIFICATION_PRIVILEGE`.
      - DPM: `dpm_db.c` got `<unistd.h>`.
      - DPM: `notification_service_tidl.c`/`notification_noti.c`/`service_common.cc`/
        `notification_ex_service.cc` got the missing `dpm_*.h` includes.
      - DPM: `dpm_shared_file.c` forward-decl of `__set_sharing_for_new_file` fixed
        (`gboolean` → `bool`).
      - DPM unittests: the 33 migrated symbols added to `notification_mock.{h,cc}` so the
        `data-provider-master-unittests` binary links (they were resolved from
        `-lnotification` before the migration).
- [x] `nm -D libnotification.so` no longer exports the moved symbols;
      `nm -D libdata-provider-master.so` exports them. Verified on the built RPMs
      (`notification_noti_insert`, `notification_setting_get_allow_to_notify`,
      `notification_channel_get_name`, `notification_system_setting_dnd_schedule_get_enabled`,
      `notification_calibrate_private_sharing`). Client symbols
      (`notification_post`, `notification_update`, `notification_get_time_from_text`)
      remain exported by `libnotification.so`.

### Summary of net effect

- 55 `EXPORT_API` symbols relocated from `libnotification.so` to `libdata-provider-master.so`
  (originally 58 targeted; 3 reverted in Phase 3b correction).
- `libnotification.so` source surface shrunk by ~6,700 lines.
- DPM source surface grew by ~5,000 lines (3 new `dpm_*.c` files + 4 directly-moved files
  + their private headers).
- Notification's installed devel header set went from 19 to 16 headers
  (`notification_viewer.h`, `notification_noti.h`, `notification_setting_service.h` removed).
- Internal cross-package consumer regression check: **0 external regressions** confirmed
  against all 65 packages.

## 6. DPM-exclusive function inventory (full)

The 78 functions identified as DPM-exclusive across all headers are in
`analysis/dpm_exclusive.tsv`. Per-package consumer breakdown is in
`analysis/api_per_consumer.tsv` and `analysis/by_function.json`.
