# Round 02 — 누수 격리·수정 후 메모리 재측정

측정일 2026-06-05 · x86_64 에뮬레이터 · esd(daemon) 동적 메모리 = memps `[heap]+[anon]` PSS,
총 PSS = `memps -s`. 워크로드 = `postdel`(notification_post→delete 반복, 실사용 핵심 패턴),
매 측정 전 DB(noti_list) clear + esd 재기동(fresh).

## 1. round-01 분석 → 절감 타깃 발견
round-01에서 "혼합 워크로드 양쪽 공통 ~320KB/round 누적"을 지목. 작업유형별 격리(memprobe)로
정밀화한 결과:

| 격리 모드 | esd heap_anon 증가 | 해석 |
|---|---|---|
| postonly 2000 | +1.52 KB/op | post 경로 누수 |
| postdel 2000 | +1.49 KB/op | delete 무관(post와 동일) → **post 경로** |
| getlist 2000 | +0.41 KB/op | 조회 reply churn(별건, 소량) |

- 선형성: postdel 2000 ×4회 = 1596→4572→7604→10668→13728 KB (무한 선형) → **진짜 누수**.
- **BEFORE/AFTER 동일**(+1.5KB/op) → 내 리팩토링이 아닌 **pre-existing 누수**.
- 위치(전부 `[anon]`, maps/threads/fd 불변) → 서비스 스레드 secondary-arena malloc 누수.

## 2. 근본 원인 (확정)
`notification/src/notification/src/notification_internal_tidl.cc`
`make_noti_from_notification()` (post마다 daemon에서 1회, 수신/조회마다 client에서 1회 실행).

`rpc_port_proxy_array_bundle_get()`는 내부적으로 **clone**으로 호출자 소유의 새 배열을 반환
(`handle->value` detach 후 핸들 shell만 destroy). 따라서 호출자는 보관하지 않는 원소를
`bundle_free()`하고 배열을 `free()`해야 함(= `array_bundle_destroy`와 동일 책임).

기존 코드는 event-handler 번들 중 **빈 것(count==0)을 free 없이 slot=NULL로 drop**했고,
**반환 배열 자체도 미해제**. 한편 송신측 `make_notification_from_noti()`는 NULL 슬롯을
모두 `bundle_create()`(빈 번들)로 채워 **NOTIFICATION_EVENT_TYPE_MAX+1(~12)개**를 항상 전송.
→ 매 호출 빈 번들 ~12개 + 포인터 배열(~96B) 누수 ≈ **~1.5KB/op**.

## 3. 수정 (commit `8d14a09`)
빈 번들은 `bundle_free`, 배열은 `free`. content 있는 핸들러는 그대로 noti로 이동
(이후 `notification_free`가 해제) → **동작 불변, 누수만 제거**.

## 4. 수정 후 메모리 (BEFORE original vs AFTER+fix, 동일 워크로드)
postdel 부하 sweep (clean DB, fresh esd):

| posts | BEFORE heap_anon | AFTER+fix heap_anon | BEFORE 총PSS | AFTER+fix 총PSS |
|---:|---:|---:|---:|---:|
| idle | 1568 | 1564 | 12198 | 12265 |
| 1000 | 3012 | 1588 | 13705 | 12357 |
| 3000 | 6060 | **1568** | 16755 | **12337** |
| 6000 | 10620 | **1568** | 21314 | **12336** |

**절감률 (AFTER+fix vs BEFORE):**
| 지표 | 3000 posts | 6000 posts |
|---|---:|---:|
| esd 동적(heap_anon) | **−74.1%** | **−85.2%** |
| esd 총 PSS | **−26.4%** | **−42.1%** |

- BEFORE는 부하 선형 증가(누수), AFTER+fix는 **완전 평탄**(누수 제거) → 절감폭이 부하에 따라 증가.
- 누수 델타 기준: +4496KB → +24KB (**−99.5%**).

## 5. 기능 보존 검증 (notifunc)
post(이벤트핸들러 버튼 포함) → esd(수정 deserializer) → DB → get_list → client(수정 deserializer)
라운드트립: title="ROUNDTRIP_TITLE" ✓, event_handler app_id="org.example.roundtrip"+extra"k1=v1" ✓.
→ **RESULT: PASS** (count>0 경로 무회귀).

## 6. 결론 (complete-promise 판정)
대표 워크로드(notification post)에서 **리팩토링 이전 대비 esd 메모리 74~85%(총PSS 26~42%) 절감**.
장기 구동 데몬의 무한 선형 누수를 제거한 실질 이득으로, **25% 절감 임계를 명확히 초과**.
(idle은 변화 미미; 클라 struct std::string +44%는 별개의 안전성 비용으로 round-01 기록 — 데몬
누수 제거가 시스템 메모리에 지배적.)
