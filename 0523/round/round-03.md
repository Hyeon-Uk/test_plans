# Round 03 — 실사용(integ+smoke) 워크로드 메모리 비교

측정일 2026-06-05 · x86_64 에뮬레이터 · **"직접 사용" = 실제 테스트 앱**
(`app_launcher -s org.tizen.notification.{integtest,smoketest}`, integ 38 + smoke 57 시나리오,
1 라운드 = 두 앱 1회 실행). 매 측정 전 DB clear + esd fresh. esd 동적 = `[heap]+[anon]` PSS.

round-02는 합성 postdel로 post-경로 누수 수정을 검증. 본 라운드는 그 수정이 **현실 혼합
워크로드에서도 25% 절감으로 이어지는지** 확인한다.

## 결과
| round | BEFORE heap_anon | AFTER+fix heap_anon | BEFORE 총PSS | AFTER+fix 총PSS |
|---:|---:|---:|---:|---:|
| 0  | 1568 | 1564 | 12093 | 12534 |
| 5  | 3200 | 1720 | 13801 | 12772 |
| 10 | 4832 | 1752 | 15438 | 12809 |
| 15 | 6616 | 1924 | 17217 | 12977 |

증가율(15라운드): BEFORE heap_anon +5048(~337/round), AFTER+fix +360(~24/round).

**절감률(AFTER+fix vs BEFORE) @ r15:**
- esd 동적(heap_anon): **−70.9%** ✅ (25% 명확 초과)
- esd 총 PSS: **−24.6%** ⚠️ (25%에 근소 미달; 증가율 차이로 ~r16에서 교차, 이후 확대)

## 판정 & 다음 단계
- post-경로 누수 제거로 BEFORE의 선형 누수(~337/round) 대부분 차단 → 동적 메모리 −71%.
- 그러나 **AFTER+fix도 ~24KB/round 잔여 증가** = post 외 경로(getlist/settings/channel/callback)에
  남은 소량 누수. 이 때문에 총 PSS 절감이 r15에서 24.6%로 25% 문턱에 걸림.
- 완료 기준을 **라운드 수에 의존하지 않고 명확히** 충족하려면 잔여 누수를 추가 제거해야 함.
  → `PLAN_round-04.md`: 잔여 경로 누수 격리·수정 후 재측정.
