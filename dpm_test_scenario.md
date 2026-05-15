# data-provider-master — Test Scenario Inventory

`dpm_api_list.md` 에 적힌 **92 개의 non-private 메서드/함수** 각각에 대한
테스트 시나리오. `test-scenario-generator` 스킬의 Phase 3 양식을 압축형으로 적용.

표기 규약:
- `[P]` Success path
- `[N]` Failure path (각 distinct return / errno predicate 별 1행)
- `[E]` Edge / boundary
- `[C]` Corner (state / ordering)

graphify-out: `data-provider-master/graphify-out/GRAPH_REPORT.md` 참조.

---

## 공통 패턴 / 템플릿

스킬 권장대로 반복되는 패턴은 한 번만 정의하고 각 API 에서 참조.

### T_const_getter — `const T& Get<Field>() const` / `T Get<Field>() const`
멤버를 그대로 반환. 외부 부수효과 없음, throw 없음.
- [P1] 정상 생성된 객체 → 생성자에서 받은 값을 그대로 반환
- [C1] move-from 된 객체에 호출 — 표준 `std::string` 은 valid-but-unspecified 이므로 단순히 "no crash" 만 보장

### T_dbus_call — `service_common.cc` 의 dbus method-call 함수 4개
모두 `_gdbus_conn` 글로벌을 통해 `g_dbus_connection_send_message_with_reply_sync` 호출.
- [P1] dbus 응답 성공 → 결과값 추출 후 반환
- [N1] `g_dbus_message_new_method_call` NULL → 함수별 기본값 (0 또는 false) 반환, 로깅
- [N2] `send_message_with_reply_sync` 가 reply NULL 반환 → 기본값 + 로깅
- [E1] `sender_name` = NULL → glib 가 critical 경고. 명세상 caller 책임이지만 테스트는 추가
- [E2] `sender_name` = "" → dbus 가 invalid name 으로 거부 → 기본값
- [C1] `_gdbus_conn` 이 NULL (init 전 호출) → glib critical / segfault. **버그로 분류해 [C1] 으로 기록**

### T_rpc_callback_static — `notification_service_tidl.c` 의 `static int _rpc_port_stub_noti_service_*_cb` 시리즈
모두 `static` 이므로 본 시나리오에서는 **제외** (dpm_api_list.md 에 빠져있음).

---

# 1. Public ABI

## `API int USD_MOD_INIT(const char* name)` — main.cc:323

USD plugin entry. `service_register` 호출.

**Errno map:**
| Return | Predicate | 소스 |
|--------|-----------|------|
| `SERVICE_ERROR_NONE` (0) | `service_register` 성공 | L331 |
| `SERVICE_ERROR_*` (음수) | `service_register` 실패 → 그대로 전파 | L331 |

**Scenarios:**
- [P1] `name="org.tizen.data_provider_service"`, service stub 정상 → 0; 콜백 3 종(create/destroy/message) 등록됨; 후속 `service_run` 가능
- [N1] `service_register` 가 `SERVICE_ERROR_INVALID_PARAMETER` 리턴 → 그 값 그대로 리턴 + ERR 로그
- [N2] `service_register` 가 `SERVICE_ERROR_OUT_OF_MEMORY` 리턴 → 전파
- [E1] `name == NULL` → `service_register` 가 INVALID_PARAMETER 로 거부할 것으로 기대 (소스에는 자체 가드 없음). 검증할 항목
- [E2] `name == ""` → 위와 동일
- [C1] 이미 등록된 이름으로 두 번 호출 → 두 번째 호출의 결과가 ALREADY_REGISTERED 인지 확인

## `API void USD_MOD_SHUTDOWN(const char* name)` — main.cc:338

`service_unregister` 호출, 반환값 없음.

**Scenarios:**
- [P1] `INIT` 후 동일 `name` 으로 호출 → 정상 unregister; 로그
- [N1] `service_unregister` 실패 (잘못된 name) → ERR 로그, 함수는 그대로 리턴 (void)
- [E1] `name == NULL` → service_unregister 동작 의존. crash 발생 여부 검증
- [C1] `INIT` 없이 호출 → unregister 가 NOT_FOUND 류 에러 리턴, 로그만 남고 안전 종료해야 함
- [C2] 같은 name 으로 두 번 호출 → 두 번째는 NOT_FOUND. crash 없어야 함

---

# 2. Internal cross-TU (HAPI)

## `HAPI int notification_delete_noti_by_app_id(const char *app_id, uid_t uid)` — notification_service_tidl.c:3291

DB 에서 노티 삭제 + RPC 로 전파.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `NOTIFICATION_ERROR_NONE` | 삭제 + RPC 성공 |
| `notification_noti_delete_all` 의 에러 | DB 에러 → goto out (ret 그대로) |
| `RPC_PORT_ERROR_*` | rpc_port_stub_notification_create 등 실패 |

**Scenarios:**
- [P1] 삭제할 noti 0건 → NONE; RPC 호출 skip; list_deleted == NULL
- [P2] 삭제할 noti N건 → NONE; "delete_multiple_notify" emit; sender_info / disturb_info 삭제
- [N1] `notification_noti_delete_all` 실패 → ret 그대로
- [N2] `rpc_port_stub_notification_create` 실패 → 그 ret 그대로 (메모리 leak: list_deleted 해제 누락 가능성 — **버그 [N2]**)
- [N3] `rpc_port_stub_array_int_create` 실패 → goto out; list_deleted 해제됨; ret 는 RPC 에러
- [N4] `__delete_sender_info` 실패 → goto out; 이미 RPC 는 emit 되어 viewer 와 DB 가 inconsistent — **레이스/일관성 [N4]**
- [E1] `app_id == NULL` → `notification_noti_delete_all` 가 INVALID_PARAMETER 또는 모든 noti 삭제. 명세 확인 필요
- [E2] `app_id == ""` → 위와 동일
- [E3] `uid = 0` → root noti 삭제 가능?
- [C1] `_changed_handle_map` 초기화 전 호출 → `_send_changed_notify` 가 NULL map 에 접근, glib critical

## `HAPI int notification_service_tidl_init(int restart_count)` — notification_service_tidl.c:3389

40+ 콜백 등록 + DB init + setting init + DND schedule 복구.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `NOTIFICATION_ERROR_NONE` | 전 과정 성공 |
| `RPC_PORT_ERROR_*` | `rpc_port_stub_noti_service_register` 실패 |
| `notification_db_init` 에러 | DB init 실패 |
| `notification_upgrade_db` 에러 | 스키마 마이그레이션 실패 |

**Scenarios:**
- [P1] `restart_count = 0` → 모든 init + `notification_noti_init_data()` 호출; NONE
- [P2] `restart_count > 0` → noti_init_data 스킵; NONE
- [N1] `rpc_port_stub_noti_service_register` 실패 → 그 ret 즉시 반환 (g_hash_table_new_full 로 만든 3개 맵 leak — **버그 [N1]**)
- [N2] `notification_db_init` 실패 → 그 ret 반환 (마찬가지 leak)
- [N3] `notification_upgrade_db` 실패 → 그 ret 반환 (leak)
- [N4] `notification_system_setting_get_dnd_schedule_enabled_uid` 실패 → 무시됨, init 은 계속 진행
- [C1] 두 번 호출 (test 시나리오) → 기존 hash table 3개 leak (`g_hash_table_new_full` 매번 새로 생성)
- [E1] `restart_count == INT_MAX` → no special handling

## `HAPI int notification_service_tidl_fini(void)` — notification_service_tidl.c:3492

3개 hash table 해제.

**Scenarios:**
- [P1] init 후 호출 → 3개 맵 destroy; NONE
- [C1] init 없이 호출 → 모든 맵이 NULL 이므로 destroy skip; NONE
- [C2] 두 번 호출 → 두 번째는 NULL 맵 destroy skip; NONE; **단, NULL 로 리셋 안 함 → 잠재 버그**

---

# 3. service_common.cc C 함수

## `uid_t get_sender_uid(const char *sender_name)` — service_common.cc:170

dbus `GetConnectionUnixUser` 호출. → T_dbus_call

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `> 0` | dbus 응답 OK → uid 추출 |
| `0` | new_method_call 실패 / send 실패 / reply NULL |

**Scenarios:**
- [P1] 유효 sender_name + dbus 정상 → real uid (예: 5001)
- [N1] `_gdbus_conn == NULL` → glib critical, 0 반환 (또는 crash — 검증)
- [N2] `g_dbus_message_new_method_call` NULL → 0
- [N3] `send_message_with_reply_sync` 가 reply == NULL → 0; err 로깅
- [E1] `sender_name == NULL` → glib critical / g_variant_new 실패
- [E2] `sender_name == ""` → dbus 거부 → 0
- [E3] sender_name 가 존재하지 않는 bus name → dbus 가 error reply → 0
- [C1] sender 가 root uid (=0) → 정상 0 반환. 함수 의미상 "실패" 와 구분 불가능 — API smell

## `pid_t get_sender_pid(const char *sender_name)` — service_common.cc:208

dbus `GetConnectionUnixProcessID` 호출. → T_dbus_call 동일 패턴.

- [P1] → real pid
- [N1..N3] T_dbus_call 과 동일
- [E1..E3] T_dbus_call 과 동일
- [C1] pid 0 은 dbus 명세상 존재하지 않으나 "실패" 와 구분 불가능

## `bool is_existed_busname(const char *sender_name)` — service_common.cc:246

dbus `NameHasOwner` 호출.

- [P1] 존재하는 bus name → true
- [P2] 존재하지 않는 bus name → false (dbus 정상 응답)
- [N1] dbus 실패 → false (실패와 "없음" 구분 불가)
- [E1..E3] T_dbus_call 과 동일

## `int send_notify(GVariant *body, char *cmd, GHashTable **monitoring_hash, char *interface_name, uid_t uid)` — service_common.cc:284

uid 별 monitoring list 순회 + 각 bus_name 에 signal emit.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `SERVICE_COMMON_ERROR_NONE` | 항상 (각 개별 실패는 swallow) |

**Scenarios:**
- [P1] uid 에 N 개 listener 등록 + 모두 alive → 모두에게 emit 됨; monitoring_count == N; NONE
- [P2] uid 에 0 개 listener → emit 0 회; NONE
- [N1] 일부 listener 가 죽었음 (`is_existed_busname` false) → 그 entry 만 monitoring_hash 에서 제거; 나머지는 emit; NONE
- [E1] `body` floating → ref_sink 처리됨
- [E2] `body == NULL` → `g_dbus_connection_emit_signal` 의 body 가 NULL → glib 가 빈 tuple 로 처리
- [E3] `*monitoring_hash == NULL` → `g_hash_table_lookup` NULL pointer → segfault (NULL check 없음). **잠재 버그 [E3]**
- [E4] `cmd / interface_name == NULL` → glib critical
- [C1] `_gdbus_conn` NULL → glib critical
- [C2] `delete_monitoring_list` 내부에서 hash 변형 중에 outer 가 list 순회 중 → 순회 중 modify, 단 `target_list = target_list->next` 를 먼저 캐싱해서 안전

## `int send_event_notify_by_busname(GVariant *body, char *cmd, char *busname, char *interface_name)` — service_common.cc:333

단일 bus_name 에 emit.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `SERVICE_COMMON_ERROR_NONE` | emit + flush 성공 |
| `SERVICE_COMMON_ERROR_IO_ERROR` | emit_signal == FALSE 또는 flush_sync == FALSE |

- [P1] 정상 → NONE
- [N1] emit 실패 → IO_ERROR
- [N2] flush 실패 → IO_ERROR (단, emit 성공 후 flush 실패 — 응답 일부 도달 가능성)
- [E1] `body` floating → ref
- [E2] `busname == NULL` → glib critical
- [E3] `cmd == NULL` → critical
- [C1] `_gdbus_conn == NULL` → critical

## `int noti_service_register(GVariant *parameters, GVariant **reply_body, const gchar *sender, GBusNameAppearedCallback, GBusNameVanishedCallback, GHashTable **monitoring_hash, uid_t uid)` — service_common.cc:373

sender 의 bus name 을 watch 하고 monitoring_hash 에 추가.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `SERVICE_COMMON_ERROR_NONE` | watch 등록 성공 또는 이미 등록됨 |
| `SERVICE_COMMON_ERROR_IO_ERROR` | sender NULL / uid 권한 mismatch / watch_id 0 |
| `SERVICE_COMMON_ERROR_OUT_OF_MEMORY` | calloc 실패 또는 reply_body 생성 실패 |

- [P1] 처음 등록되는 sender, uid 일치 → NONE; monitoring_hash 에 추가; watch_id != 0
- [P2] 이미 등록된 sender → NONE; "Sender already exist" 로그; hash 미수정
- [N1] `sender == NULL` → IO_ERROR
- [N2] `uid > NORMAL_UID_BASE` 이지만 `uid != request_uid` → IO_ERROR (권한 위반)
- [N3] `calloc` NULL → OUT_OF_MEMORY
- [N4] `g_bus_watch_name_on_connection` 가 0 반환 → IO_ERROR; m_info 해제됨
- [N5] `g_variant_new("()")` NULL (실제로는 거의 안 일어남) → OUT_OF_MEMORY; m_info 해제됨, list 에서 sender 제거
- [E1] `uid == 0` 으로 register 요청 → request_uid 와 비교
- [E2] `request_uid == 0` (parameters 에서 추출) → uid > NORMAL_UID_BASE 가드 통과 못 함 → mismatch 시 IO_ERROR
- [C1] 동시에 두 스레드가 같은 sender 등록 → race; hash 가 g_hash_table 이라 lock 필요. dpm 은 single-threaded gmain 가정 — [Open Q2]

## `int delete_monitoring_list(GHashTable **monitoring_hash, const char *sender, uid_t uid)` — service_common.cc:445

uid 의 list 에서 sender 제거.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `SERVICE_COMMON_ERROR_NONE` | 항상 (찾지 못해도 NONE) |
| `SERVICE_COMMON_ERROR_IO_ERROR` | uid 의 list 자체가 hash 에 없음 |

- [P1] sender 가 list 에 있음 → 제거; list 가 비면 hash 에서 uid 키 steal; NONE
- [P2] sender 가 list 에 없음 → list 변형 없음; NONE (소스상 del_list == NULL 이면 no-op)
- [N1] uid 가 hash 에 없음 → IO_ERROR
- [E1] `sender == NULL` → strcmp NULL → crash
- [E2] hash 의 list 가 1개 element 였고 sender == 그 element → list NULL, hash 에서 uid steal
- [C1] sender 가 hash 에는 다른 uid 의 list 에 들어있음 → 무관, 해당 uid 의 list 만 본다

## `int service_common_register_dbus_interface(char *introspection_xml, GDBusInterfaceVTable interface_vtable)` — service_common.cc:495

own_name + register_object.

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `SERVICE_COMMON_ERROR_NONE` | 모두 성공 |
| `SERVICE_COMMON_ERROR_IO_ERROR` | _dbus_init / own_name / parse / register_object 실패 |

- [P1] 정상 XML → NONE
- [N1] `_dbus_init()` 실패 → IO_ERROR
- [N2] `g_bus_own_name` 0 반환 → IO_ERROR
- [N3] `g_dbus_node_info_new_for_xml` 실패 (XML invalid) → IO_ERROR
- [N4] `g_dbus_connection_register_object` 0 반환 → IO_ERROR
- [E1] `introspection_xml == NULL` → glib critical
- [E2] `introspection_xml == ""` → parse 실패
- [E3] 같은 well-known name 으로 두 번 호출 → 두 번째 own_name 은 queued 됨

## `void service_common_init(void)` — service_common.cc:626

PkgmgrClient + Listener 생성 + Listen.

**Scenarios:**
- [P1] 처음 호출 → unique_ptr 두 개 생성, Listen 성공
- [C1] 두 번 호출 → 기존 unique_ptr reset; Ignore 호출되며 pkgmgr_client_free 됨 → 정상
- [N1] `pkgmgr_client_new` NULL → Listen 가 -1 반환, 다만 service_common_init 은 void 라 swallow

## `void service_common_set_connection(GDBusConnection *conn)` — service_common.cc:632

`_gdbus_conn = conn` 만 함.

- [P1] conn != NULL → 글로벌 갱신
- [E1] conn == NULL → 글로벌이 NULL 로 설정; 이후 dbus 호출들 모두 실패
- [C1] 한 번 set 후 다시 set → 이전 conn 의 ownership 처리 없음 (단순 포인터 대입). 누가 unref 하나? — [Open Q3]

---

# 4. namespace dpm 공개 클래스

## `class dpm::PkgmgrClient`

### `PkgmgrClient::PkgmgrClient()` — pkgmgr_client.cc:23
default ctor. 멤버 모두 nullptr.
- [P1] 생성 후 handle_ == nullptr, listener_ == nullptr

### `PkgmgrClient::~PkgmgrClient()` — pkgmgr_client.cc:25
`Ignore()` 호출.
- [P1] Listen 후 destroy → pkgmgr_client_free 호출됨
- [P2] Listen 없이 destroy → handle_ NULL 이라 Ignore 의 if 가드로 no-op
- [C1] Listen → Ignore() 수동 호출 → destroy → 두 번째 Ignore 안전 (NULL 가드)

### `int PkgmgrClient::Listen(IEvent* listener)` — pkgmgr_client.cc:29

**Errno map:**
| Return | Predicate |
|--------|-----------|
| `0` | 모두 성공 |
| `-1` | 이미 handle_ 설정됨 / pkgmgr_client_new NULL / set_status_type < 0 / listen_status < 0 / listen_app_status < 0 |

- [P1] 처음 호출 → 0; handle_ 설정; 두 개 listen 등록됨
- [N1] 이미 Listen 후 두 번째 호출 → -1; handle_ 변경 없음 (단, listener_ 는 새 값으로 덮어씀 — **잠재 버그 [N1]**)
- [N2] `pkgmgr_client_new` NULL → -1
- [N3] `pkgmgr_client_set_status_type` < 0 → -1; handle_auto 가 unique_ptr 라 free 됨
- [N4] `pkgmgr_client_listen_status` < 0 → -1; auto-free
- [N5] `pkgmgr_client_listen_app_status` < 0 → -1; auto-free
- [E1] `listener == nullptr` → listener_ 가 nullptr 설정. 콜백 도착 시 PkgmgrHandler 의 `if (listener != nullptr)` 가드에 걸려 no-op → 안전
- [C1] Ignore 후 다시 Listen → handle_ NULL 이므로 새로 등록 가능 → P1 과 동일

### `void PkgmgrClient::Ignore()` — pkgmgr_client.cc:69

- [P1] Listen 후 → pkgmgr_client_free 호출, handle_ = nullptr
- [C1] Listen 없이 호출 → handle_ NULL → no-op
- [C2] 두 번 연속 호출 → 두 번째는 NULL 가드로 안전

## `class dpm::PkgmgrClient::IEvent` (abstract)

Pure virtual 메서드의 contract 만 검증. 실제 객체는 PackageEventListener.

### `virtual void IEvent::OnPkgmgrEvent(std::shared_ptr<PkgmgrEventArgs>) = 0`
Subclass 가 반드시 override. PackageEventListener 로 검증.

### `virtual void IEvent::OnPkgmgrAppEvent(std::shared_ptr<PkgmgrAppEventArgs>) = 0`
동상.

## `class dpm::PkgmgrEventArgs`

### `PkgmgrEventArgs::PkgmgrEventArgs(uid_t, int req_id, std::string pkg_type, std::string pkgid, std::string event_status, std::string event_name)` — pkgmgr_event_args.cc:21

생성자. 멤버 초기화 + tag_ 합성 (`"<uid>-<pkgid>"`).

- [P1] 정상 호출 → 모든 필드 stored; tag == "uid-pkgid"
- [E1] uid = 0, req_id = 0, 모든 문자열 "" → 정상 stored; tag = "0-"
- [E2] 매우 긴 문자열 → string move 로 처리됨
- [E3] pkgid 에 '-' 포함 → tag 에 그대로 들어감 (parse 시 모호성)
- [C1] move 생성자 — std::string 인자가 모두 by-value 라 caller 의 원본은 valid-but-unspecified

### `~PkgmgrEventArgs() = default` (헤더)
- [P1] 정상 destroy

### `uid_t GetTargetUid() const` — pkgmgr_event_args.cc:33 → T_const_getter
- [P1] 반환값 == ctor 의 target_uid

### `int GetReqId() const` — pkgmgr_event_args.cc:37 → T_const_getter
- [P1] 반환값 == ctor 의 req_id

### `const std::string& GetPkgType() const` — :41 → T_const_getter
- [P1] reference 가 멤버를 가리킴; 동일 string 비교 OK

### `const std::string& GetPkgId() const` — :45 → T_const_getter
### `const std::string& GetEventStatus() const` — :49 → T_const_getter
### `const std::string& GetEventName() const` — :53 → T_const_getter
### `const std::string& GetTag() const` — :57 → T_const_getter

## `class dpm::PkgmgrAppEventArgs`

### `PkgmgrAppEventArgs(uid_t, std::string pkg_type, std::string pkgid, std::string appid, std::string event_status, std::string event_name)` — pkgmgr_app_event_args.cc:21

- [P1] 정상 → 모든 필드 stored; tag = "uid-pkgid-appid"
- [E1..E3] PkgmgrEventArgs 와 동일 패턴
- [N1] req_id 인자 없음 — 생성자가 req_id_ 멤버를 초기화하지 않음. **버그 [N1]**: `GetReqId()` 호출 시 uninitialized read

### `~PkgmgrAppEventArgs() = default` → trivial
### `uid_t GetTargetUid() const` — :33 → T_const_getter

### `int GetReqId() const` — 헤더에 선언, **구현 없음**
- [N1] 호출 시 링크 에러 (정적 / 동적 링크 모두). Dead declaration.
- → 테스트 작성 불가; 다만 *호출하지 않음* 을 보장하는 부정 테스트는 가능 (linker symbol 검사)

### `const std::string& GetPkgType() const` — :37 → T_const_getter
### `const std::string& GetPkgId() const` — :41 → T_const_getter
### `const std::string& GetAppId() const` — :45 → T_const_getter
### `const std::string& GetEventStatus() const` — :49 → T_const_getter
### `const std::string& GetEventName() const` — :53 → T_const_getter
### `const std::string& GetTag() const` — :57 → T_const_getter

---

# 5. TU-local 클래스 (헤더 없음, cc 내부)

## `class CPUBoosting` (anonymous namespace, main.cc:49)

### `CPUBoosting() = default` — L51
- [P1] core_ == nullptr; timer_source_ == nullptr

### `bool SetBoosting()` — L53
- [P1] core 발견 + set_cpu_boosting 성공 → true; 로그
- [N1] core_ == NULL (find 실패) → false
- [N2] set_cpu_boosting != TIZEN_CORE_ERROR_NONE → false
- [E1] 이미 boosting 활성 + 다시 호출 → tizen_core 의 동작에 위임 (재진입 안전성)

### `void ClearBoosting()` — L67
- [P1] core_ != NULL → tizen_core_clear_cpu_boosting + 로그
- [E1] core_ == NULL → no-op
- [C1] SetBoosting 없이 호출 → core_ == NULL → no-op

### `void SetAutoClearTimer(int timeout_ms = 5000)` — L74
- [P1] core_ != NULL + timer_source_ == NULL → timer 등록; timeout_ms 후 ClearBoosting + timer_source_ = nullptr
- [N1] core_ == NULL → no-op
- [N2] timer_source_ 이미 존재 → no-op (재등록 방지)
- [E1] timeout_ms == 0 → 즉시 호출 (gmain 다음 iteration)
- [E2] timeout_ms 음수 → 동작 미정

### `void DestroyTimer()` — L88
- [P1] core_ + timer_source_ 모두 있음 → remove_source + timer_source_ = nullptr + ClearBoosting
- [E1] timer_source_ == NULL → no-op
- [E2] core_ == NULL → no-op

## `class PackageEventListener : public PkgmgrClient::IEvent` (service_common.cc:76)

### `void OnPkgmgrEvent(shared_ptr<PkgmgrEventArgs>) override` — L82
- [P1] event_status 가 installer_key_list 에 없음 → return (no-op)
- [P2] status == "start" + name 이 install/uninstall/update/enable_app/disable_app → pkgmgr_event_list_ 에 push
- [P3] name == "ok" + 매칭되는 start 항목 있음 → 적절한 cb 호출 + 리스트에서 제거
  - install → _package_install_cb
  - uninstall → _package_uninstall_cb
  - enable_app → _app_enabled_cb
  - disable_app → _app_disabled_cb
- [P4] name == "fail" + 매칭 항목 → 그냥 제거 (cb 미호출)
- [E1] 매칭 항목 없음 (start 없이 ok 도착) → 리스트 변형 없음
- [C1] 같은 (uid, pkgid) 에 start 가 두 개 → ok 한 번에 둘 다 매칭되어 모두 처리됨

### `void OnPkgmgrAppEvent(shared_ptr<PkgmgrAppEventArgs>) override` — L126
- 위와 동일한 패턴, app 단위.
- [P1..P4] 동일
- [E1, C1] 동일

---

# 6. main.cc 파일 스코프 비-static

## `void __finish(void)` — main.cc:278

- [P1] poll_fd + __source 둘 다 설정됨 → source_remove_poll + remove_source + app_terminate
- [E1] poll_fd == NULL → remove_poll skip; __source != NULL 이면 remove_source 호출 (core_h 가 NULL 이어도 호출됨)
- [E2] __source == NULL → remove_source skip
- [C1] init 없이 호출 → 둘 다 NULL → app_terminate 만 호출됨

---

# 부록: Coverage check

> 본 문서는 원래 data-provider-master 패키지의 notification-ex 서비스 측 코드
> (`notification_ex_service.cc` 의 HAPI 함수 4개, `DPMFacade`, `DPMReporter`,
> `DPMManager` 클래스)도 포함하고 있었으나, 해당 부분은 별도 관리로 분리되어
> 본 문서에서 제외되었습니다. 현재 다루는 범위는 **notification.c 서비스 측 코드
> + service_common + dpm Pkgmgr + CPUBoosting + main.cc 잡함수** 만 입니다.

| 카테고리 | 대상 수 | 시나리오 작성됨 |
|----------|------:|------:|
| Public ABI (`API`) | 2 | 2 |
| HAPI (cross-TU) — notification_service_tidl.c | 3 | 3 |
| service_common.cc 비-static | 10 | 10 |
| `dpm::PkgmgrClient` public | 4 | 4 |
| `dpm::PkgmgrClient::IEvent` (interface) | 2 | 2 (계약만) |
| `dpm::PkgmgrEventArgs` public | 9 | 9 |
| `dpm::PkgmgrAppEventArgs` public | 10 | 10 (단, `GetReqId` 구현 부재) |
| `CPUBoosting` public | 5 | 5 |
| `PackageEventListener` public | 2 | 2 |
| `__finish` | 1 | 1 |
| **합계** | **48** | **48** |

### Open Questions / 검증 필요

1. **[Open Q1]** `noti_service_register` 가 동시 호출에 안전한지 (g_hash_table 은 thread-safe 아님). dpm 이 gmain single-threaded 가정인지 확인.
2. **[Open Q2]** `service_common_set_connection` 이 기존 conn 의 unref 책임을 가지는지 / caller 책임인지.
3. **[Bug-candidate]** `PkgmgrClient::Listen` 이 이미 등록된 상태에서 listener_ 만 덮어쓰고 -1 반환 → 콜백 호출 시 새 listener 가 받음. 의도 확인.
4. **[Bug-candidate]** `PkgmgrAppEventArgs` 의 `req_id_` 멤버가 ctor 에서 초기화되지 않음. `GetReqId()` 도 구현 없음. Dead/incorrect code.
5. **[Bug-candidate]** `notification_service_tidl_init` 가 중간에 실패하면 이미 할당된 hash table 3개 leak.

### 다음 단계

각 `[P]/[N]/[E]/[C]` 행이 한 개의 google-test `TEST_F` 로 1:1 매핑됨.
mock 대상은 외부 dependency 표를 참조:
- `service_register` / `service_unregister` (USD)
- `g_dbus_connection_*`, `g_bus_own_name`, `g_bus_watch_name_on_connection`
- `pkgmgr_client_*`
- `notification_*` (notification 패키지 — 외부 dep)
- `tizen_core_*`
- `sqlite3_release_memory`, `malloc_trim`
- `tzplatform_getuid`, `pkgmgrinfo_*`
