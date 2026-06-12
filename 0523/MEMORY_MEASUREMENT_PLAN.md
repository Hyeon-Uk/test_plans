# notification / data-provider-master 메모리 측정 방법론 (0523)

REFACTORING_ANALYSIS.md의 메모리 절감 아이템(LIST_OVERHEAD / UNNECESSARY_ALLOC /
STRDUP_OVERUSE / HARDCODED_BUFFER)의 효과를 **두 패키지로 분리하여** 정량 측정하기
위한 설계. 측정 대상은 x86_64 에뮬레이터.

---

## 0. 핵심 과제: 두 패키지는 "다른 프로세스"에 있다

| 패키지 | 산출물 | 적재 위치 | 메모리가 잡히는 곳 |
|---|---|---|---|
| `notification` | `libnotification.so` (클라이언트 라이브러리) | 알림을 쓰는 **모든 앱 프로세스**에 로드 | 각 클라이언트 프로세스(=테스트 앱)의 힙/데이터 |
| `data-provider-master` | `libdata-provider-master.so` (데몬) | **`/usr/bin/esd`** 가 dlopen (확인: pid의 `/proc/<esd>/maps`에 매핑됨) | `esd` 프로세스의 힙/데이터 |

따라서 "분리 측정"의 정의:
- **notification 측 메모리** = 테스트 앱 프로세스에서 `libnotification.so` 코드가
  유발한 할당(struct `_notification`, 직렬화 버퍼 등).
- **DPM 측 메모리** = `esd` 프로세스에서 `libdata-provider-master.so` 코드가 유발한
  할당(DB row 캐시, dnd 컨테이너, 채널 리스트 등).

`esd`는 여러 서비스를 함께 호스팅하므로 **절대값이 아니라 시나리오 전/후 델타**와
**모듈 귀속(attribution)** 으로 DPM 몫만 분리해야 한다.

---

## 1. 에뮬레이터 환경 제약 (실측 확인됨)

| 수단 | 가용 | 비고 |
|---|---|---|
| **`memps`** (Tizen 메모리 도구) | ✅ ★주력 | 매핑별 S/P(CODE/DATA)·PSS·SWAP + OBJECT NAME. smaps의 상위 도구 |
| `/proc/<pid>/status` (VmRSS/VmData/VmSize) | ✅ | 보조(빠른 전체) |
| `/proc/<pid>/smaps` (Pss/Rss/Private_Dirty, 매핑별) | ✅ | memps 미가용 시 폴백 |
| `/proc/<pid>/smaps_rollup` | ❌ | 미지원 |
| `valgrind` / `massif` | ❌ | 미설치 |
| 디바이스 `gcc/g++` | ❌ | shim은 **GBS chroot 교차 빌드 후 push** |
| `gdb` | ✅ | 보조 |
| root (`sdb root on`) | ✅ | esd 재시작/LD_PRELOAD 주입 가능 |
| `esd.service` | `ExecStart=/usr/bin/esd`, `Environment=AUL_BLINK=1` | drop-in으로 `LD_PRELOAD` 주입 가능 |

함의: 측정 주력은 **`memps`(PSS, 매핑별/OBJECT별) + 시나리오 전/후 델타**.
커스텀 LD_PRELOAD shim은 **선택**(esd 내 DPM vs glib/sqlite 코드 귀속을 세분할 때만).
RSS/PSS는 glibc가 free 후 OS에 즉시 반환하지 않으므로(arena), **상주는 memps PSS**,
**할당 수준 진실(누수/회수)은 shim live-bytes 또는 `malloc_trim` 후 PSS**로 본다.

> 실측 예(현 esd): `libdata-provider-master.so` PSS=468KB(P-CODE 456+P-DATA 12),
> esd 전체 `[heap]`+`[anon]` PSS≈1912KB. → DPM **코드/정적**은 memps로 직접,
> DPM **동적**은 anon/heap 합의 시나리오 전후 델타로.

---

## 2. 측정 방법 (memps 주력 → 델타 → (선택)할당귀속)

### A. 전체 프로세스 PSS (memps)
- `memps -s <pid>` → 총 PSS 한 줄(S/P CODE/DATA, PSS, SWAP). DPM=esd pid, 클라=테스트앱 pid.
- 시나리오 전/후 ΔPSS. esd는 공유 호스트라 **idle 베이스라인 차감 + N회 평균** 필수.

### B. 라이브러리별 상주 (memps, partial)
- `memps <pid>` 출력에서 OBJECT NAME으로 라인 선택:
  - `…/mod/libdata-provider-master.so` → DPM **코드(P-CODE)+정적(P-DATA)** 상주 (esd 내)
  - `…/libnotification.so*` → 클라 코드/정적 (테스트 앱 내)
- 이 값은 **코드/정적영역**만. 동적 힙은 `[heap]`/`[anon]`(backing 없음)이라 .so 귀속
  안 됨 → 동적은 C로.
- 정적 컨테이너 버킷(예: `static std::unordered_map _dnd_alarm_id_map`)도 힙(anon)에 있음.

### C. 동적 메모리 — 델타법(주력) + shim(선택)
**C-1 델타법 (shim 불필요, 권장):** 대상 프로세스의 `[heap]`+`[anon]` PSS 합을 memps로
구해 **시나리오 전/후 차이**를 본다.
- 클라: 테스트 앱은 **오직 노티 API만** 호출 → Δ(anon+heap) = `libnotification.so` 동적 몫.
- DPM: 시나리오가 **DPM 경로만** 자극(노티 post/dnd/channel) → esd Δ(anon+heap) ≈ DPM 동적 몫.
- 컨테이너 절감(dnd map/vector), struct std::string, DB row 캐시 모두 이 Δ로 드러남.
- 누수/회수(S6)는 사이클 후 Δ가 0 복귀하는지로 판정(단 arena 보존 → `malloc_trim` 보조).

**C-2 LD_PRELOAD shim `libmemprobe.so` (선택, 세분 귀속 시만):**
한 프로세스 안에서 **어느 .so 코드가 할당했는지**(DPM vs glib-노드 vs sqlite) 구분이
필요할 때만. esd `[anon]`은 OBJECT가 없어 memps로는 "esd 안의 DPM코드 vs glib코드"를
못 가르므로, GList→STL 노드 오버헤드 같은 미세 항목을 코드 단위로 보고 싶을 때 사용.

동작:
1. `malloc/calloc/realloc/free/posix_memalign/aligned_alloc` 를 `RTLD_NEXT`로 래핑.
2. 각 할당마다 호출자 프레임(`__builtin_return_address` 또는 `backtrace(2~3)`)을
   `dladdr()`로 해석 → 소속 .so 경로 → 버킷(`notification`/`dpm`/`glib`/`sqlite`/`other`).
3. 버킷별 live bytes / peak / 누적 count / 평균 크기 누적. 헤더 8~16B로 size 기록.
4. `SIGUSR1` 수신 시 또는 `atexit`에 `/tmp/memprobe.<pid>.log` 로 덤프(버킷 표).
5. 재진입/초기화 가드(`__thread in_hook`, dlsym 부트스트랩) 필수.

빌드: GBS chroot에서 Tizen 툴체인으로 `-shared -fPIC -ldl`(+`-funwind-tables`,
backtrace용) 컴파일 → `.so` push. (디바이스 gcc 없음)

> 정확도: 호출자 1프레임 귀속은 wrapper(예: `_dup_string`, `g_list_append`)가 중간에
> 끼면 그 wrapper의 .so로 귀속될 수 있다. 보완: 프레임 2~3개를 보고 **첫 번째
> non-glib/non-libc 프레임**을 채택하는 정책으로 노티/DPM 코드에 귀속. glib 컨테이너
> 노드(GList) 할당은 `glib` 버킷으로 잡혀, GList→STL 전환의 효과(노드 오버헤드 감소)가
> `glib` 버킷 감소로 드러난다.

### D. 영속 풋프린트 (보조)
- `/opt/dbspace/.notification.db` 크기 (DPM이 노티/세팅/채널 저장). RAM은 아니나
  post/delete 시나리오의 상태 증가/회수 확인용.

---

## 3. 계측 주입 방법

> **C-1 델타법(주력)은 주입이 전혀 필요 없다** — 외부에서 `memps <pid>`만 호출.
> 아래 LD_PRELOAD 주입은 **C-2 shim을 쓸 때만** 필요(선택).

### 클라이언트(notification)
```
LD_PRELOAD=/usr/lib/libmemprobe.so  <테스트앱 실행>
```
- 앱 런처 경유 시: 매니페스트/런처 env 또는 직접 바이너리 실행에 LD_PRELOAD.

### DPM(esd)
systemd drop-in 생성 후 재시작:
```
# /etc/systemd/system/esd.service.d/memprobe.conf
[Service]
Environment=LD_PRELOAD=/usr/lib/libmemprobe.so
```
```
sdb shell "systemctl daemon-reload && systemctl restart esd.service"
```
- 측정 종료 후 drop-in 제거 + 재시작으로 원복(잔여 리소스 정리 원칙).

---

## 4. 테스트 시나리오 (notification API 기반)

각 시나리오: **(1) idle 베이스라인 스냅샷 → (2) 워밍업 1회 → (3) 본 측정 N회 →
(4) 스냅샷 → (5) 정리 후 스냅샷**. 스냅샷 = {앱 VmRSS/VmData, esd VmRSS/VmData,
앱·esd smaps의 .so별 Pss, 앱·esd memprobe 버킷 덤프(SIGUSR1)}.

| ID | 시나리오 | 주 호출 API | 측정 의도(어느 절감 아이템) |
|---|---|---|---|
| S0 | idle | 없음 | 베이스라인(차감용) |
| S1 | create-only ×N (post 안 함) | `notification_create`/`set_text`/`set_image`/`set_sound`/.../`free` | **클라 struct `_notification` std::string 풋프린트** (B1b) |
| S2 | post ×N | `notification_post` | **DPM DB-row 캐시 + 직렬화** per-noti |
| S3 | post + changed_cb | `notification_register_detailed_changed_cb` 등 | 콜백 구조체(N-LIST-001/N-ALLOC-003 후보) |
| S4 | DND: register dnd app + set dnd schedule | `notification_register_dnd_app`(stub경유)/setting DND | **`__dnd_app_list`/`_dnd_alarm_id_list`/`__disturb_noti_list` 컨테이너** (D-LIST-001/002, D-OWN-004) |
| S5 | channel CRUD + get_list 반복 | `notification_*_channel*` | **`_channel_list`** (D-RAII-002 누수 수정 검증) |
| S6 | steady-state: (post ×M → delete_all) ×K | post/`delete_all` | **누수/회수 검출**: K 사이클 후 esd RSS·live-bytes가 베이스라인 복귀해야 함 |
| S7 | scale sweep: N=1,10,100,1000 post | post | **per-notification 바이트** 회귀선 → DPM 1건당 메모리 |

매핑 요약: 내가 적용한 절감 아이템의 효과는 주로 **S4**(dnd 컨테이너 -1.2KB/-240B/-200B)
와 **S6/S5**(누수 회수, D-RAII-002), 그리고 struct std::string은 **S1/S2**.

---

## 5. 테스트 앱 구성

### 권장: 전용 `notification-memtest` 서비스앱 (integ/smoke 미러)
- 위치: `notification/tests/mem_tests/` (integ_tests 구조 복제).
- 형태: gtest 불필요. **phase-driven CLI/서비스앱** — 인자로 시나리오 ID + N 받음.
  ```
  notification-memtest --scenario S4 --count 100 --out /tmp/memtest.S4.json
  ```
- 동작: 각 phase 진입 시 (a) dlog 마커 출력, (b) phase 사이 `sleep`로 정상화 대기.
  스냅샷은 **호스트 하니스가 외부에서 `memps`로 수집**(앱 pid + esd pid). shim 사용 시에만
  self/esd에 `SIGUSR1`로 버킷 덤프 추가.
- 패키징: `notification.spec`에 `%package -n notification-memtests`
  (integtests 블록 복제, app id `org.tizen.notification.memtest`).
- 빠른 반복용 대안: 패키징 없이 GBS chroot에서 빌드한 standalone 바이너리를 push +
  `LD_PRELOAD` 실행(=integ 디버그 때 쓴 방식).

### 호스트 하니스 스크립트
- `mem-harness.sh` (호스트):
  1. (옵션) esd drop-in 주입 + 재시작, 앱은 LD_PRELOAD로 실행
  2. 각 시나리오 실행 → `memprobe-snapshot.sh`로 앱·esd 스냅샷 수집(pull)
  3. 베이스라인 차감 + 버킷별/.so별 표 출력
  4. **A/B 모드**: 동일 시나리오를 baseline RPM vs 현재 RPM에서 각각 돌려 diff
- `mem-snapshot.sh` (호스트→sdb): 주어진 pid에 `memps <pid>` 실행 → 총 PSS,
  `libdata-provider-master.so`/`libnotification.so` PSS, `[heap]+[anon]` PSS 합을 파싱해
  단일 JSON으로. (shim 사용 시 memprobe 로그도 pull)

---

## 6. A/B 비교 (절감 효과 정량화)

목표: "리팩토링 전 vs 후" 동일 시나리오 메모리 차이.
- **before**: 해당 아이템 직전 커밋의 RPM, **after**: 현재 RPM.
  - dnd 컨테이너: before = `c80f258`(tidl 변환 전) / after = `adc4a40`.
  - struct std::string: before = `f0ac770`직전 / after = 해당 B1b 그룹 커밋.
  - 채널 누수(D-RAII-002): before = `cae3923` / after = `f8abd7f`, **S5/S6에서 누수 회수**가
    after에서만 베이스라인 복귀해야 함(가장 명확한 신호).
- 각 빌드를 설치→esd 재시작→시나리오→스냅샷, 그리고
  Δ(after) vs Δ(before) 를 버킷별/.so별/per-noti로 비교.

---

## 7. 보고 지표

시나리오별로 다음을 표로:
- DPM(esd): ΔVmRSS, ΔVmData, memprobe `dpm` 버킷 Δlive/Δpeak, smaps `libdata-provider-master.so` Pss
- 클라(앱): ΔVmRSS, memprobe `notification` 버킷 Δlive/Δpeak, smaps `libnotification.so` Pss
- 부수: `glib` 버킷(GList→STL 효과), sqlite 버킷, .notification.db 크기
- S6: K 사이클 후 잔여(=누수) — 0에 수렴해야 정상
- S7: per-notification 바이트(회귀 기울기)

---

## 8. 산출물(툴) 목록

1. `notification/tests/mem_tests/host/mem-snapshot.sh` — **memps 기반** pid 스냅샷
   (총 PSS / 대상 .so PSS / heap+anon PSS) → JSON. ★주력, 디바이스 빌드 불필요.
2. `notification/tests/mem_tests/host/mem-harness.sh` — 시나리오 오케스트레이션 + 베이스라인
   차감 + A/B diff.
3. `notification/tests/mem_tests/src/memtest_main.c` — phase-driven 시나리오 앱(노티 API).
4. (선택) `notification/tests/mem_tests/libmemprobe/memprobe.c` — LD_PRELOAD 귀속 shim
   (GBS chroot 교차빌드, C-2 세분 귀속용).
5. (옵션) `notification.spec` `%package -n notification-memtests`.

---

## 9. 주의/함정

- **std::string SSO**: 짧은 문자열(≤15B)은 힙 할당이 없다 → char*+strdup 대비 오히려
  힙 할당 횟수↓. memprobe count로 확인(절감이 "바이트"보다 "할당 횟수"로 나타날 수 있음).
- **Pss vs RSS**: 코드 페이지는 공유 → 라이브러리 코드 비교는 Pss. 힙은 Private.
- **glibc arena**: free해도 RSS 즉시 안 줄어듦 → 누수 판단은 **memprobe live-bytes**(정확)
  와 RSS(상주) 둘 다 보고. `malloc_trim(0)`을 시나리오 종료 훅에서 한 번 호출해 RSS
  반환을 유도(측정 보조, 프로덕션 변경 아님).
- **esd 공유 호스트**: 절대 RSS 의미 적음 → 항상 idle 베이스라인 차감 + 동일 시나리오 반복.
- **계측 비침습 원칙**: LD_PRELOAD shim·systemd drop-in·standalone 바이너리는 전부
  **측정용 임시물**. 프로덕션 코드/스펙에 커밋 금지(필요 시 별도 memtests 패키지로만).
- **GList 귀속**: g_list_* 노드는 glib 내부 malloc → `glib` 버킷. GList→STL 전환 효과는
  `glib` 버킷 감소 + `dpm`(STL 노드) 소폭 증가의 **순감**으로 읽는다.

---

## 부록 A. `libmemprobe.so` 스켈레톤 (핵심 로직)

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

enum { B_NOTI, B_DPM, B_GLIB, B_SQLITE, B_OTHER, B_N };
static const char *BN[B_N] = {"notification","dpm","glib","sqlite","other"};
static long long live[B_N], peak[B_N], cnt[B_N];
static __thread int in_hook;

static void *(*real_malloc)(size_t);
static void  (*real_free)(void*);
static void *(*real_calloc)(size_t,size_t);
static void *(*real_realloc)(void*,size_t);

struct hdr { size_t size; int bucket; uint32_t magic; };
#define MAGIC 0xMEM0BEEFu

static int classify(void *caller) {        /* dladdr → .so 경로 → 버킷 */
    Dl_info di;
    if (!caller || !dladdr(caller, &di) || !di.dli_fname) return B_OTHER;
    const char *n = di.dli_fname;
    if (strstr(n,"libnotification.so")) return B_NOTI;
    if (strstr(n,"libdata-provider-master")) return B_DPM;
    if (strstr(n,"libglib")||strstr(n,"libgobject")||strstr(n,"libgio")) return B_GLIB;
    if (strstr(n,"libsqlite")) return B_SQLITE;
    return B_OTHER;
}
/* 호출자: 첫 non-libc/non-self 프레임 채택 (backtrace 3~4) */
static int caller_bucket(void) {
    void *bt[5]; int n = backtrace(bt, 5);
    for (int i = 2; i < n; i++) { int b = classify(bt[i]); if (b!=B_OTHER) return b; }
    return B_OTHER;
}
/* malloc 래퍼: hdr 부착 → 버킷 집계 (recursion 가드, dlsym 부트스트랩 생략 표기) */
void *malloc(size_t sz){
    if (!real_malloc) real_malloc = dlsym(RTLD_NEXT,"malloc");
    if (in_hook) return real_malloc(sz);
    in_hook=1;
    int b = caller_bucket();
    struct hdr *h = real_malloc(sizeof(*h)+sz);
    if (h){ h->size=sz; h->bucket=b; h->magic=MAGIC;
            live[b]+=sz; cnt[b]++; if(live[b]>peak[b]) peak[b]=live[b]; }
    in_hook=0;
    return h ? (h+1) : NULL;
}
void free(void *p){
    if (!real_free) real_free = dlsym(RTLD_NEXT,"free");
    if (!p){ return; }
    struct hdr *h = (struct hdr*)p - 1;
    if (h->magic==MAGIC){ live[h->bucket]-=h->size; real_free(h); }
    else real_free(p);          /* 우리가 안 잡은 것 */
}
/* calloc/realloc/posix_memalign 동형 + dlsym 부트스트랩(초기 static buffer) 필요 */

static void dump(int sig){ (void)sig;
    char path[64]; snprintf(path,sizeof path,"/tmp/memprobe.%d.log",getpid());
    FILE *f=fopen(path,"w"); if(!f) return;
    for(int b=0;b<B_N;b++) fprintf(f,"%-13s live=%lld peak=%lld cnt=%lld\n",
                                   BN[b],live[b],peak[b],cnt[b]);
    fclose(f);
}
__attribute__((constructor)) static void init(void){ signal(SIGUSR1,dump); }
__attribute__((destructor))  static void fini(void){ dump(0); }
```
(주의: 실제 구현은 dlsym 부트스트랩 정적버퍼, calloc/realloc/메모리정렬, 스레드 안전,
MAGIC 오타 수정 등 보강 필요. 위는 설계 골격.)

## 부록 B. memps 기반 스냅샷 (호스트, 주력)
```sh
# usage: mem_snapshot <pid>   → 총PSS / DPM .so PSS / noti .so PSS / heap+anon PSS (kB)
mem_snapshot() {
  sdb shell "memps $1 2>/dev/null | awk '
    /libdata-provider-master\.so/ { dpm += \$5 }
    /libnotification\.so/         { noti += \$5 }
    /\[heap\]|\[anon\]/           { dyn += \$5 }
    { tot += \$5 }
    END { printf \"total_pss=%d dpm_so_pss=%d noti_so_pss=%d heap_anon_pss=%d\n\",
                 tot, dpm, noti, dyn }'"
}
# 델타 = (시나리오 후) - (idle 베이스라인). DPM 동적 = esd heap_anon_pss 델타,
# 클라 동적 = 테스트앱 heap_anon_pss 델타.
```
(폴백, memps 부재 시 smaps 직접: `/^Pss:/`행을 직전 매핑 헤더의 OBJECT로 합산.)
