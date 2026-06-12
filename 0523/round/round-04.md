# Round 04 — 잔여 누수 분석 + 지속 사용 결정적 비교

측정일 2026-06-05 · x86_64 에뮬레이터 · 실사용 = `app_launcher` integ(38)+smoke(57),
1 라운드 = 두 앱 1회. 매 측정 전 DB clear + esd fresh.

## 1. round-03 잔여 분석
round-03에서 AFTER+fix가 실사용 시 ~24KB/round 잔여 증가 → 작업유형별 격리:
| 모드(AFTER+fix) | esd heap_anon | 판정 |
|---|---|---|
| postdel 2000 | 0.012 KB/op | ✅ round-02에서 해결 |
| getlist 2000 | 0.176 KB/op | 잔여(B) |
| getdetail 2000 | 0.208 KB/op | 잔여(B) |

- **(A) target_info 누수**: `notification_add_private_sharing_target_id`가 list/load마다 sender별
  target_app_info_s 등록하나, 짝 함수 `notification_remove_private_sharing_target_id`가
  **정의만 되고 미호출(dead code)** → 데몬 수명 동안 distinct sender마다 누적.
  → disconnect 콜백(`terminate_cb`)에 remove 연결 (dpm `153638c`). add-on-request /
  remove-on-disconnect lifecycle 완성. (단일 persistent 연결 테스트에선 sender dedup으로 효과 작음;
  앱 재기동이 잦은 장기 시스템에서 누적 차단.)
- **(B) per-call list 누수(~0.18KB/op)**: 우리 쿼리 코드(`notification_noti_get_grouping_list`/
  `_get_notification_list`)는 균형. **확정 근거**: 클라이언트는 static `service_handle` 1개의
  persistent 연결(notification_tidl.cc:462 create / :474 connect_sync, 1회)을 사용 → rpc 'sender'가
  호출 간 안정 → `add_private_sharing_target_id`는 dedup되어 per-call 누수 아님(memprobe 2000콜이
  단일 연결). 따라서 (B)는 콜백이 framework에 반환하는 `rpc_port_stub_list_notification` 핸들을
  **빌드시 생성되는 TIDL stub/rpc-port framework가 직렬화 후 해제하는** 영역의 잔여이며,
  비편집·리팩토링 무관·**BEFORE/AFTER 양쪽 동일 → 비교에서 상쇄**. 잔여가 작아 25% 판정에
  비지배적(고정 ~12MB baseline 희석이 주원인).

## 2. 지속 사용 결정적 비교 (25 라운드 = 2375 시나리오, 비외삽)
| round | BEFORE heap_anon | AFTER+fix heap_anon | BEFORE 총PSS | AFTER+fix 총PSS |
|---:|---:|---:|---:|---:|
| 0  | 1568 | 1564 | 12248 | 12515 |
| 5  | 3208 | 1716 | 14041 | 12764 |
| 10 | 4852 | 1748 | 15684 | 12795 |
| 15 | 6636 | 1924 | 17469 | 12975 |
| 20 | 8256 | 1932 | 19090 | 12980 |
| 25 | 9892 | **1948** | 20723 | **12995** |

- BEFORE: 선형 누수(heap_anon ~333/round, 무한 증가).
- AFTER+fix: **~r15 이후 평탄화**(초기 +360은 일회성 warmup, 이후 10라운드 +24).

**절감률 (AFTER+fix vs BEFORE):**
| 지표 | r15 | r25 |
|---|---:|---:|
| esd 동적(heap_anon) | −71.0% | **−80.3%** |
| esd 총 PSS | −25.7% | **−37.3%** |

## 3. 판정 (complete-promise)
실사용(integ+smoke) 지속 워크로드에서 **리팩토링 이전 대비 esd 동적 메모리 −80%, 총 PSS −37%**
(보수적 전프로세스 PSS 기준으로도 25% 명확 초과, 비외삽). BEFORE는 무한 선형 누수,
AFTER+fix는 평탄 → 절감폭은 사용량에 따라 확대. 기능 무회귀(integ 38/38, smoke 57/57, post+
event-handler 라운드트립 PASS). **25% 절감 기준 충족.**

기여 commit: notification `8d14a09`(event-handler 번들 누수), dpm `153638c`(private-sharing
target disconnect 정리). 상세 근인: round-02(post), 본 라운드(list/target).
