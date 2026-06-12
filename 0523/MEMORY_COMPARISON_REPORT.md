# 리팩토링 전/후 메모리 비교 레포트 (notification / data-provider-master)

측정일 2026-06-04 · x86_64 에뮬레이터 · 방법론: `MEMORY_MEASUREMENT_PLAN.md`(memps + 델타 + A/B)

## 0. 비교 대상 (A/B)

| | notification | data-provider-master |
|---|---|---|
| **BEFORE** | `a70da0c` (Step A 직전, char* struct, `.c`) | `ef7933c` (B0 직전, `.c`) |
| **AFTER**  | `2515021` (struct→std::string 완료) | `f8abd7f` (C→C++ + 컨테이너 + D-RAII-002 누수수정) |

- lib RPM(3종)만 교체해 측정. 워크로드(integ/smoke/chleak/notimem)는 공개 ABI가 동일하므로
  고정 바이너리 사용.
- DPM 메모리 = `esd` 프로세스(libdata-provider-master.so dlopen). 측정은 `memps`의
  `[heap]+[anon]` PSS 합(동적) + 라이브러리 PSS(상주).
- 클라 메모리 = 테스트 바이너리 프로세스의 `/proc/self/status` VmRSS/VmData.

---

## 1. 요약

| 측정 항목 | BEFORE | AFTER | 변화 |
|---|---:|---:|---|
| **DPM 채널-foreach 누수** (fresh esd, 채널10×foreach3000) | **+4684 KB** | **+860 KB** | **−82% (≈ −3.8 MB)** ✅ |
| DPM 혼합 워크로드 (integ+smoke ×5) heap_anon 증가 | +1680 KB | +1628 KB | ≈ 0 (양쪽 공통 잔존 증가) |
| DPM idle 상주 — `libdata-provider-master.so` PSS | 476 KB | 472 KB | ≈ 0 |
| DPM idle — esd `[heap]+[anon]` PSS | 1568 KB | 1568 KB | 0 |
| **클라 3000 noti 보유 — VmData** | **2712 KB** | **3900 KB** | **+1188 KB (+44%, ≈ +396 B/noti)** ⚠️ |
| 클라 3000 noti 보유 — VmRSS | ≈ 11.9 MB | ≈ 13.1 MB | +≈ 1.2 MB |

**핵심**: DPM은 **채널 리스트 누수 제거(D-RAII-002)로 부하 시 메모리 폭증을 ~82% 차단**(큰 이득).
클라이언트는 struct `char*→std::string` 전환의 **객체 크기 증가로 noti당 ~396B 증가**(안전성
리팩토링의 비용, 예고된 트레이드오프).

---

## 2. DPM — 채널-foreach 누수 (D-RAII-002) ★헤드라인

타깃 클라이언트 `chleak N L` = 채널 N개 생성 후 `notification_channel_foreach()` L회 호출
(매 호출이 DPM `_rpc_port_stub_noti_service_channel_get_list_cb` 유발).

**동일조건 단일 실행 (fresh esd, 채널10 × foreach3000):**
```
BEFORE : esd heap_anon 1568 → 6252 kB   (+4684 kB)
AFTER  : esd heap_anon 1568 → 2428 kB   (+ 860 kB)
```
→ **−82%**. BEFORE는 foreach마다 채널 리스트(노드+app_id/channel_name strdup+
notification_channel_s) 전체를 누수(소유 변수 `_channel_list`를 iterator로 advance 후
NULL에 free하던 버그). AFTER는 별도 cursor로 정상 해제.

**선형성(진짜 누수) 확인 (채널5):**
```
BEFORE : 1568 →(+1000)→ 2272 →(+1000)→ 3056 →(+2000)→ 4664 kB   (≈ +0.78 KB/foreach)
AFTER  : 1568 →(+1000)→ 1648 →(+4000)→ 2284 kB                  (≈ +0.14 KB/foreach)
```
BEFORE는 무한 선형 증가, AFTER는 ~5.5배 낮음. AFTER 잔여 증가(~0.14KB/call)는 reply 경로
churn/arena 단편화로 추정(양쪽 공통·BEFORE에선 큰 누수에 가려져 있던 부분).

---

## 3. DPM — 혼합 워크로드 / idle 상주

**integ(38) + smoke(57) ×5 라운드, esd heap_anon:**
```
round0(idle) 1  2  3  4  5
BEFORE : 1504 1916 2212 2536 2856 3184 kB   (총 +1680)
AFTER  : 1568 1944 2240 2508 2864 3196 kB   (총 +1628)
```
→ **거의 동일**. 이 워크로드는 채널-foreach를 거의 호출하지 않아 D-RAII-002 효과가 안 드러나며,
양쪽 공통의 ~+320KB/round 누적이 존재(리팩토링과 무관한 기존 누적, 별도 조사 대상).

**idle 상주(memps):** `libdata-provider-master.so` PSS 476→472 kB, esd 전체 PSS ≈ 12190 kB로
**before/after 동일** — C→C++/STL 전환이 코드/정적 크기를 키우지 않음(컨테이너 정적영역 포함).

> dnd 컨테이너 절감(D-LIST-001/002, D-OWN-004: GList→unordered_map/vector, 문서상
> −1.2KB/−240B/−200B)은 **상주형**이라 DND 부하 시에만 수 KB 수준으로 나타남(본 측정의
> 혼합/채널 시나리오에선 비중 작음).

---

## 4. 클라이언트(notification lib) — struct std::string 비용

`notimem 3000` = 노티 3000개 생성 + caller_app_id/sound_path/vibration_path/tag 채우고
**동시 보유**, 자기 프로세스 status 측정.
```
BEFORE (char*)       : VmRSS ≈ 11.9 MB, VmData 2712 kB
AFTER  (std::string) : VmRSS ≈ 13.1 MB, VmData 3900 kB
```
→ **VmData +1188 KB (+44%), noti당 ≈ +396 B 증가**. 원인: struct `_notification`의 15개
문자열 멤버가 `char*`(8B/멤버) → `std::string`(≈32B/멤버, SSO 인라인 버퍼)로 커져
**객체 자체가 noti당 ~360B 증가**(긴 문자열은 양쪽 다 heap). 즉 이 전환은 메모리 절감이
아니라 **소유권/안전성(누수·double-free·use-after-free 차단) 목적**이며, 비용으로 클라
메모리가 소폭 증가함(사전 고지한 트레이드오프 그대로).

**그러나 실사용 보유량(1~50개)에서는 차이 없음** (round-05): N=1/10/50에서 BEFORE/AFTER
VmData가 600/600/732 kB로 **완전 동일**. +44%는 N=3000 합성 극단부하에서만 나타나며, 실제 앱은
수~수십 개만 보유하므로 struct 차이(~396B×50≈20KB)가 페이지 granularity에 흡수되어 **관측 가능한
증가 없음**. → 실사용 기준 클라이언트 메모리 회귀 없음.

---

## 4.5. 추가 라운드(round/) — post 경로 누수 제거 ★최대 이득

§3에서 "별도 조사 대상"으로 남긴 양쪽 공통 누적을 작업유형별로 격리한 결과
**post 경로 ~1.5KB/op 무한 선형 누수**(pre-existing)를 발견·수정함
(`test_plans/0523/round/round-01.md`, `round-02.md`).

- 원인: `make_noti_from_notification()`이 `rpc_port_proxy_array_bundle_get()`이 반환한
  **호출자 소유 배열의 빈 event-handler 번들(~12개)과 배열 자체를 미해제**. 수정 commit `8d14a09`.
- 효과(postdel sweep, clean DB): esd 동적 메모리 3000posts −74%/6000posts −85%,
  총 PSS 3000posts −26.4%/6000posts −42.1%, 누수 델타 −99.5%. BEFORE 선형증가 → AFTER 평탄.
- 기능 보존: post→get_list 라운드트립에서 title·event_handler 정상(PASS).
- 이 누수는 §3의 ~320KB/round 공통 누적의 주범이었음(혼합 워크로드의 post 비중).

**실사용(integ 38 + smoke 57) 지속 워크로드 비교 (round-03/04, 25라운드=2375시나리오):**
| round | BEFORE heap_anon | AFTER+fix | BEFORE 총PSS | AFTER+fix 총PSS |
|---:|---:|---:|---:|---:|
| 15 | 6636 | 1924 | 17469 | 12975 |
| 25 | 9892 | 1948 | 20723 | 12995 |

→ esd 동적 메모리 **−80.3%**, 총 PSS **−37.3%** @r25 (BEFORE 선형누수, AFTER+fix 평탄).
추가 수정: dpm `153638c` — `notification_remove_private_sharing_target_id`(dead code)를 disconnect
콜백에 연결해 list/load의 target_app_info_s 누적 차단. 잔여 per-call list 누수는 빌드시 생성되는
TIDL stub/framework 영역(비편집·BEFORE/AFTER 동일·상쇄).

## 5. 결론

| 영역 | 메모리 영향 | 성격 |
|---|---|---|
| **DPM, 채널 부하** | **대폭 개선 (−82%, −3.8MB/측정)** | 실제 누수(D-RAII-002) 제거 |
| DPM, 일반/idle | 중립 | 코드·상주 동일 |
| DPM, dnd 컨테이너 | 소폭 개선(상주, DND 부하 시) | GList→STL |
| **클라이언트** | **소폭 악화 (+44% VmData, +396B/noti)** | std::string 안전성 비용 |

- **순효과**: 데몬(DPM)은 부하 시 메모리 폭증을 막아 **시스템 안정성/메모리에 실질 이득**.
  클라이언트는 보유 노티 수에 비례해 약간 증가(앱은 보통 소수 노티만 보유 → 절대 영향 작음).
- 리팩토링의 1차 목표는 **C→C++ 안전성/소유권**이었고 메모리는 부수 효과. 메모리 절감 자체가
  목표였던 항목(dnd 컨테이너)은 상주 수 KB 수준으로 작게 기여.
- 추가 조사 권장: §3의 **양쪽 공통 ~+320KB/round 누적**(리팩토링 무관, 별도 누수 가능성).

---

## 부록. 재현 방법

```sh
# 빌드: BEFORE = (noti a70da0c, dpm ef7933c), AFTER = (noti 2515021, dpm f8abd7f)
#   각 커밋 checkout 후 gbs build, RPM을 /tmp/mem_before, /tmp/mem_after 로 분리 보관
# 타깃 클라(누수): chleak.cc — 채널 N 생성 + notification_channel_foreach L회
# 클라 풋프린트:   notimem.cc — 노티 N개 생성/멤버채움/보유 후 /proc/self/status
#   (둘 다 GBS chroot에서 g++ `pkg-config notification ...` 로 빌드, sdb push → /usr/bin)

# 측정 루틴(각 버전):
sdb shell "rpm -Uvh --force --nodeps <버전 RPM 3종>; systemctl restart esd.service; sleep 6"
EPID=$(sdb shell "pgrep -x esd")
ha(){ sdb shell "memps $1 | awk '/\[heap\]|\[anon\]/{d+=\$5}END{print d}'"; }   # esd 동적 PSS
# DPM 누수:  ha(baseline) → sdb shell /usr/bin/chleak 10 3000 → ha(after)
# 클라:      sdb shell /usr/bin/notimem 3000  (VmRSS/VmData 출력)
```
(계측 바이너리 chleak/notimem, esd LD_PRELOAD drop-in 등은 측정용 임시물 — 프로덕션/스펙 커밋 금지.)
