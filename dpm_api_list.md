# data-provider-master — Non-Private API List

`private:` 로 마킹된 멤버 / `static` 으로 TU 내부에 가둔 헬퍼 / 익명 네임스페이스
외부에서 호출 불가능한 심볼은 제외하고, **외부 코드 (다른 TU, 다른 shared object,
또는 같은 클래스 외부) 가 호출 가능한 모든 함수/메서드** 만 추렸다.

## Visibility 매크로 정리

| 매크로 | 정의 | 의미 |
|--------|------|------|
| `EXPORT` | `__attribute__((visibility("default")))` | 공유 라이브러리 외부에 노출 |
| `API` | `extern "C" EXPORT` | C ABI + 외부 노출. 실제로 dpm.so 의 export 심볼은 이것뿐 |
| `HAPI` | `__attribute__((visibility("hidden")))` | 같은 .so 내부에서만 보임 (다른 TU 에서는 호출 가능하지만 외부에는 안 보임) |

dpm 은 `tizen-united-service` 가 `dlopen` 해서 쓰는 plugin 형태이므로,
진짜 "public ABI" 는 USD 가 호출하는 두 entry point 뿐이고, 나머지는 전부
같은 `.so` 안에서만 통하는 internal API 다.

---

## 1. Public ABI (`API` / `EXPORT`)

USD 가 dlopen 후 `dlsym` 으로 찾는 모듈 hook. **`dpm.so` 가 외부에 노출하는 유일한 두 심볼.**

| File:Line | Signature |
|-----------|-----------|
| `src/main.cc:323` | `API int USD_MOD_INIT(const char* name)` |
| `src/main.cc:338` | `API void USD_MOD_SHUTDOWN(const char* name)` |

---

## 2. Internal (`HAPI`) — 다른 TU 에서는 호출 가능, 외부에는 hidden

세 모듈 (`main` ↔ `notification_ex_service` ↔ `notification_service_tidl`) 사이의
초기화/종료/배달 entry point. `include/notification_ex_service.h`,
`include/notification_service_tidl.h` 에 prototype 이 있다.

### `src/notification_ex_service.cc`

| Line | Signature |
|------|-----------|
| 816 | `HAPI int notification_ex_service_init(int restart_count)` |
| 838 | `HAPI int notification_ex_service_fini()` |
| 843 | `HAPI GDBusConnection* notification_ex_service_get_gdbus_connection()` |
| 805 | `int notification_register_dbus_interface(void)` *(TU-local helper, but non-static)* |

### `src/notification_service_tidl.c`

| Line | Signature |
|------|-----------|
| 3291 | `HAPI int notification_delete_noti_by_app_id(const char *app_id, uid_t uid)` |
| 3389 | `HAPI int notification_service_tidl_init(int restart_count)` |
| 3492 | `HAPI int notification_service_tidl_fini(void)` |

> 그 외 3,500 줄 가량의 `_rpc_port_stub_noti_service_*_cb` 콜백, `_send_*`, `_check_*` 등은 모두 `static` → 제외.

---

## 3. Service-common C API (`include/service_common.h`)

같은 `.so` 안 다른 TU 에서 호출하는 IPC/모니터링 헬퍼. 헤더에 prototype 이 있고
파일은 `static` 이 아니므로 모두 non-private.

### `src/service_common.cc`

| Line | Signature |
|------|-----------|
| 170 | `uid_t get_sender_uid(const char *sender_name)` |
| 208 | `pid_t get_sender_pid(const char *sender_name)` |
| 246 | `bool is_existed_busname(const char *sender_name)` |
| 284 | `int send_notify(GVariant *body, char *cmd, GHashTable **monitoring_hash, char *interface_name, uid_t uid)` |
| 333 | `int send_event_notify_by_busname(GVariant *body, char *cmd, char *busname, char *interface_name)` |
| 373 | `int noti_service_register(GVariant *parameters, GVariant **reply_body, const gchar *sender, GBusNameAppearedCallback, GBusNameVanishedCallback, GHashTable **monitoring_hash, uid_t uid)` |
| 445 | `int delete_monitoring_list(GHashTable **monitoring_hash, const char *sender, uid_t uid)` |
| 495 | `int service_common_register_dbus_interface(char *introspection_xml, GDBusInterfaceVTable interface_vtable)` |
| 626 | `void service_common_init(void)` |
| 632 | `void service_common_set_connection(GDBusConnection *conn)` |

---

## 4. C++ 클래스 — `namespace dpm` (공유 헤더가 있는 공개 클래스)

### `class dpm::PkgmgrClient` — `src/pkgmgr_client.hh`

PackageManager 이벤트 리스닝 추상화. Public 메서드만.

| Decl | Signature | Impl |
|------|-----------|------|
| `pkgmgr_client.hh:38` | `PkgmgrClient()` | `pkgmgr_client.cc:23` |
| `pkgmgr_client.hh:39` | `virtual ~PkgmgrClient()` | `pkgmgr_client.cc:25` |
| `pkgmgr_client.hh:41` | `int Listen(IEvent* listener)` | `pkgmgr_client.cc:29` |
| `pkgmgr_client.hh:42` | `void Ignore()` | `pkgmgr_client.cc:69` |

> `private: static int PkgmgrHandler(...)`, `static int PkgmgrAppHandler(...)` 는 `private:` 블록이므로 **제외**.

### `class dpm::PkgmgrClient::IEvent` — nested abstract

콜백 인터페이스. 두 메서드 모두 pure virtual / public.

| Decl | Signature |
|------|-----------|
| `pkgmgr_client.hh:34` | `virtual void OnPkgmgrEvent(std::shared_ptr<PkgmgrEventArgs> args) = 0` |
| `pkgmgr_client.hh:35` | `virtual void OnPkgmgrAppEvent(std::shared_ptr<PkgmgrAppEventArgs> args) = 0` |

### `class dpm::PkgmgrEventArgs` — `src/pkgmgr_event_args.hh`

패키지 이벤트 인자 DTO. 모든 public 메서드는 `const` getter.

| Decl | Signature | Impl |
|------|-----------|------|
| `pkgmgr_event_args.hh:29` | `PkgmgrEventArgs(uid_t, int req_id, std::string pkg_type, std::string pkgid, std::string event_status, std::string event_name)` | `pkgmgr_event_args.cc:21` |
| `pkgmgr_event_args.hh:31` | `virtual ~PkgmgrEventArgs() = default` | header |
| `pkgmgr_event_args.hh:33` | `uid_t GetTargetUid() const` | `pkgmgr_event_args.cc:33` |
| `pkgmgr_event_args.hh:34` | `int GetReqId() const` | `pkgmgr_event_args.cc:37` |
| `pkgmgr_event_args.hh:35` | `const std::string& GetPkgType() const` | `pkgmgr_event_args.cc:41` |
| `pkgmgr_event_args.hh:36` | `const std::string& GetPkgId() const` | `pkgmgr_event_args.cc:45` |
| `pkgmgr_event_args.hh:37` | `const std::string& GetEventStatus() const` | `pkgmgr_event_args.cc:49` |
| `pkgmgr_event_args.hh:38` | `const std::string& GetEventName() const` | `pkgmgr_event_args.cc:53` |
| `pkgmgr_event_args.hh:39` | `const std::string& GetTag() const` | `pkgmgr_event_args.cc:57` |

### `class dpm::PkgmgrAppEventArgs` — `src/pkgmgr_app_event_args.hh`

앱 단위 패키지 이벤트 인자 DTO.

| Decl | Signature | Impl |
|------|-----------|------|
| `pkgmgr_app_event_args.hh:29` | `PkgmgrAppEventArgs(uid_t, std::string pkg_type, std::string pkgid, std::string appid, std::string event_status, std::string event_name)` | `pkgmgr_app_event_args.cc:21` |
| `pkgmgr_app_event_args.hh:32` | `virtual ~PkgmgrAppEventArgs() = default` | header |
| `pkgmgr_app_event_args.hh:34` | `uid_t GetTargetUid() const` | `pkgmgr_app_event_args.cc:33` |
| `pkgmgr_app_event_args.hh:35` | `int GetReqId() const` | **선언만 존재, 구현 없음 ⚠️** |
| `pkgmgr_app_event_args.hh:36` | `const std::string& GetPkgType() const` | `pkgmgr_app_event_args.cc:37` |
| `pkgmgr_app_event_args.hh:37` | `const std::string& GetPkgId() const` | `pkgmgr_app_event_args.cc:41` |
| `pkgmgr_app_event_args.hh:38` | `const std::string& GetAppId() const` | `pkgmgr_app_event_args.cc:45` |
| `pkgmgr_app_event_args.hh:39` | `const std::string& GetEventStatus() const` | `pkgmgr_app_event_args.cc:49` |
| `pkgmgr_app_event_args.hh:40` | `const std::string& GetEventName() const` | `pkgmgr_app_event_args.cc:53` |
| `pkgmgr_app_event_args.hh:41` | `const std::string& GetTag() const` | `pkgmgr_app_event_args.cc:57` |

---

## 5. C++ 클래스 — TU-local (cc 파일 안에만 존재, 헤더 없음)

헤더로 공유되진 않지만 같은 TU 안에서 `public:` / `protected:` 로 노출된 메서드.
파일 외부에서 직접 호출은 불가능하지만 **C++ 접근지정자 기준으로는 private 이 아니다**.

### `class DPMFacade` (`notification_ex_service.cc:70`) — 모두 `public:`

| Line | Signature |
|------|-----------|
| 72 | `DPMFacade(unique_ptr<Reporter> reporter, unique_ptr<Manager> manager, int restartCount)` |
| 82 | `void DelegateReporterEvent(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> itemList)` |
| 87 | `void DelegateManagerEvent(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> itemList)` |
| 92 | `void LaunchDefaultViewer(list<shared_ptr<item::AbstractItem>> item, notification_op_type_e status)` |
| 109 | `void LaunchDefaultViewer(shared_ptr<item::AbstractItem> item, notification_op_type_e status)` |
| 117 | `void LaunchDefaultViewer(int64_t privId, notification_op_type_e status, uid_t uid)` |
| 125 | `uid_t GetUid(const IEventInfo& info)` |
| 133 | `void TranslateText(list<shared_ptr<item::AbstractItem>> item)` |
| 138 | `void TranslateText(shared_ptr<item::AbstractItem> item)` |
| 152 | `bool CheckAllowedToNotify(list<shared_ptr<item::AbstractItem>> item)` |
| 168 | `bool CheckAllowedToNotify(shared_ptr<item::AbstractItem> item)` |
| 192 | `bool CheckDoNoDisturbStatus(uid_t uid, const string& owner)` |
| 241 | `void SetDoNoDisturbPolicy(list<shared_ptr<item::AbstractItem>> item)` |
| 246 | `void SetDoNoDisturbPolicy(shared_ptr<item::AbstractItem> item)` |
| 272 | `void SetPopUpPolicy(list<shared_ptr<item::AbstractItem>> item)` |
| 277 | `void SetPopUpPolicy(shared_ptr<item::AbstractItem> item)` |
| 312 | `void SetMemoryTrimTimer(void)` |
| 329 | `static gboolean TimeoutHandler(gpointer data)` |

### `class DPMReporter : public Reporter` (`notification_ex_service.cc:347`)

| Line | Section | Signature |
|------|---------|-----------|
| 349 | protected | `void OnUpdate(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> updatedList)` |
| 377 | protected | `void DoDelete(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> deletedList)` |
| 394 | protected | `void OnDelete(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> deletedList)` |
| 413 | protected | `void OnEvent(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> noti_list) override` |
| 438 | protected | `list<shared_ptr<item::AbstractItem>> OnRequestEvent(const IEventInfo& info) override` |
| 454 | protected | `int OnRequestNumber(const IEventInfo& info) override` |
| 461 | protected | `int UpdateHideApp(list<shared_ptr<item::AbstractItem>> updatedList)` |
| 508 | protected | `void OnRegister(const IEventInfo& info)` |
| 522 | public | `DPMReporter(std::unique_ptr<IEventSender> sender, std::unique_ptr<IEventListener> listener)` |

### `class DPMManager : public Manager` (`notification_ex_service.cc:528`)

| Line | Section | Signature |
|------|---------|-----------|
| 530 | protected | `void OnAdd(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> addedList) override` |
| 563 | protected | `void OnUpdate(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> updatedList) override` |
| 596 | protected | `int DoDelete(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> deletedList)` |
| 611 | protected | `void OnDelete(const IEventInfo& info, list<shared_ptr<item::AbstractItem>> deletedList) override` |
| 639 | protected | `list<shared_ptr<item::AbstractItem>> OnRequestEvent(const IEventInfo& info) override` |
| 665 | protected | `int OnRequestNumber(const IEventInfo& info) override` |
| 674 | protected | `void UpdateHideApp(list<shared_ptr<item::AbstractItem>> updatedList)` |
| 700 | protected | `void SetIndirectRequest(const IEventInfo& info, list<shared_ptr<AbstractItem>> addedList)` |
| 706 | protected | `void SetIndirectRequest(const IEventInfo& info, shared_ptr<AbstractItem> addedItem)` |
| 719 | protected | `void SetIndirectRequest(const IEventInfo& info, shared_ptr<AbstractAction> action)` |
| 757 | protected | `int ValidateUid(const IEventInfo& info, list<shared_ptr<AbstractItem>> addedList)` |
| 768 | protected | `int ValidateUid(const IEventInfo& info, shared_ptr<AbstractItem> addedItem)` |
| 785 | public | `DPMManager(std::unique_ptr<IEventSender> sender, std::unique_ptr<IEventListener> listener)` |

### `class CPUBoosting` (`main.cc:49`, 익명 네임스페이스, 모두 `public:`)

| Line | Signature |
|------|-----------|
| 51 | `CPUBoosting() = default` |
| 53 | `bool SetBoosting()` |
| 67 | `void ClearBoosting()` |
| 74 | `void SetAutoClearTimer(int timeout_ms = 5000)` |
| 88 | `void DestroyTimer()` |

> `private:` 멤버 `tizen_core_h core_`, `tizen_core_source_h timer_source_` 는 **제외**.

### `class PackageEventListener : public PkgmgrClient::IEvent` (`service_common.cc:76`, `public:`)

| Line | Signature |
|------|-----------|
| 78 (decl) / 82 (impl) | `void OnPkgmgrEvent(std::shared_ptr<PkgmgrEventArgs> args) override` |
| 79 (decl) / 126 (impl) | `void OnPkgmgrAppEvent(std::shared_ptr<PkgmgrAppEventArgs> args) override` |

---

## 6. 파일 스코프 비-static 함수 (`main.cc`)

| Line | Signature | 메모 |
|------|-----------|------|
| 278 | `void __finish(void)` | non-static 이지만 헤더 선언 없음. 사실상 TU-local 이나, `static` 키워드가 없으므로 ODR 상 다른 TU 에서 접근 가능 — non-private 으로 분류 |

---

## 부록: 명시적으로 제외된 항목

다음은 의도적으로 빠뜨린 것들 — 모두 진짜 private:

- `private:` 블록 안의 멤버: `PkgmgrClient::PkgmgrHandler`, `PkgmgrClient::PkgmgrAppHandler`,
  `CPUBoosting::core_`, `CPUBoosting::timer_source_`, `PkgmgrEventArgs::target_uid_`/`req_id_`/`pkg_type_`/...,
  `PkgmgrAppEventArgs::target_uid_`/`pkg_type_`/...
- `static` 키워드가 붙은 TU-local 함수: `notification_service_tidl.c` 의 `__refresh_setting_table`,
  `_validate_and_set_param_uid_with_uid`, `_validate_and_set_noti_with_uid`, `__check_channel_state`,
  `__set_channel_state`, `__disturb_noti_compare`, `__delete_disturb_noti_info`,
  `__add_disturb_noti_info`, `_is_dnd_app_exist`, `__free_dnd_app_info`, `__pid_compare`,
  `__print_noti`, `__check_limit`, `_get_current_time`, `_dnd_data_compare`,
  `__malloc_dnd_alarm_id_s`, `_noti_system_setting_set_alarm`, `_send_changed_notify`,
  `_send_event_notify`, `_dnd_schedule_alarm_cb`, `_add_alarm`, `_delete_alarm`,
  `_check_dnd_schedule`, `_notification_launch_viewer`, `_add_noti`, `_update_noti`,
  `__delete_sender_info`, `_delete_noti`, `__add_sender_info`, `__free_deleted_list_info`,
  `__check_privilege_cb`, `__has_notification_privilege`, `__create_pkginfo_by_app_id`,
  `__init_setting_handle_by_app_id`, 약 50 여 개의 `_rpc_port_stub_noti_service_*_cb`,
  `_changed_handle_destroy`, `_event_handle_destroy` 등.
- `service_common.cc` 의 static helper: `_monitoring_app_list_compare_cb`, `_dbus_init`,
  `_init_pkg_privilege_info`, `_package_install_cb`, `_package_uninstall_cb`,
  `_app_enabled_cb`, `_app_disabled_cb`.
- `main.cc` 의 static lifecycle 콜백: `lang_key_changed_cb`, `app_create`, `app_terminate`,
  `signal_handler_dispatch`, `__init_signal_handler`, `ServiceCreateCb`, `ServiceDestroyCb`,
  `ServiceMessageCb`.

## 부록: 의심스러운 항목 (선언만 있고 구현 없음)

`include/service_common.h` 에 prototype 이 있으나 `service_common.cc` 어디에도
구현이 없다 — 사용처도 없음. Dead declaration 으로 보임.

- `int noti_service_unregister(GVariant *parameters, GVariant **reply_body, const gchar *sender, GHashTable **monitoring_hash, uid_t uid)` (`service_common.h:60`)
- `GDBusConnection *service_common_get_connection()` (`service_common.h:62`)
- `void free_monitoring_list(gpointer data)` (`service_common.h:66`)

`pkgmgr_app_event_args.hh` 에 선언되어 있으나 `.cc` 에 구현이 없는 메서드:

- `int PkgmgrAppEventArgs::GetReqId() const` (`pkgmgr_app_event_args.hh:35`) — 호출 시 링크 에러 발생 가능성 있음

---

## 요약

| 카테고리 | 개수 |
|----------|-----:|
| Public ABI (`API`) | 2 |
| Internal cross-TU (`HAPI`) | 6 |
| `service_common.cc` C 함수 | 10 |
| `notification_ex_service.cc` 기타 비-static | 1 |
| `dpm::PkgmgrClient` public | 4 |
| `dpm::PkgmgrClient::IEvent` public | 2 |
| `dpm::PkgmgrEventArgs` public | 9 |
| `dpm::PkgmgrAppEventArgs` public | 10 |
| `DPMFacade` public | 18 |
| `DPMReporter` public+protected | 9 |
| `DPMManager` public+protected | 13 |
| `CPUBoosting` (익명 ns) public | 5 |
| `PackageEventListener` public | 2 |
| `main.cc` 비-static | 1 |
| **합계** | **92** |
