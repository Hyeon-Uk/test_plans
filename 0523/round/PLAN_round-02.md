# 절감 플랜 (round-02 이후)

round-01 판정: 대표 워크로드 기준 25% 미달성. 절감 타깃을 우선순위로 정의하고 검증 가능한
실험으로 누수원을 격리한 뒤 수정한다.

## 가설
혼합 워크로드의 **양쪽 공통 ~320KB/round (~3.4KB/op)** 누적이 sustained DPM 메모리의 주범.
이 누수는 BEFORE/AFTER 양쪽에 존재(리팩토링 무관, pre-existing). **AFTER에서만 제거**하면
sustained 부하에서 BEFORE(계속 누수) 대비 AFTER가 K라운드 경과 시 ≥25% 낮아진다.
  BEFORE = base + K·L,  AFTER = base + K·(L−fix).  fix→L 이면 K↑ 시 절감률 → 100%.

## 작업유형별 격리 실험 (round-02)
자체 프로브 클라이언트로 단일 경로를 N회 반복하며 esd `[heap]+[anon]` PSS 추적:
- P1 `postdel`: notification_create→post→delete 루프 (insert/delete/sender_info/changed-cb).
- P2 `regcb`:   changed-cb register→unregister 루프 (_changed_handle_map/_event_handle_map).
- P3 `getlist`: notification_get_list 루프 (조회 경로 reply churn).
누적이 큰 경로 = 누수원 카테고리. (채널 경로는 D-RAII-002로 이미 처리됨.)

## 타깃 우선순위
- **T1**: 격리된 누수원 코드 수정 (SQLITE_STMT_LEAK / per-op alloc 미해제 / glib ref 누락).
  - 후보: notification_noti.cc insert/delete의 sqlite3_stmt finalize, get_list reply 해제,
    sender_info/handle map 잔존, g_variant/bundle ref 누락.
- **T2**: 클라 struct 메모리 회귀(+44%) 완화 — 안전성 유지하며 객체 크기 축소
  (예: 희소 멤버를 개별 std::string 대신 묶음/포인터화 검토). 위험도 높아 신중.
- **T3**: 채널-foreach 잔여 ~0.14KB/call churn.

## 검증 기준 (complete-promise)
동일 대표 워크로드(혼합 K=10라운드)에서 esd `[heap]+[anon]` PSS:
`(BEFORE_total − AFTER_total) / BEFORE_total ≥ 0.25` → 종료.
각 라운드 결과는 `round-NN.md`에 원시 수치와 함께 기록.
