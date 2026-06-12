# Round 01 — 메모리 비교 측정 (baseline 정식화)

측정일 2026-06-05 · x86_64 에뮬레이터 · 방법론 `../MEMORY_MEASUREMENT_PLAN.md`
요약 출처: `../MEMORY_COMPARISON_REPORT.md` (직전 hands-on 측정을 round-01로 고정)

## 비교 대상
| | notification | data-provider-master |
|---|---|---|
| BEFORE | `a70da0c` (char* struct, `.c`) | `ef7933c` (`.c`) |
| AFTER  | `2515021` (struct→std::string) | `f8abd7f` (C→C++ + 컨테이너 + D-RAII-002) |

## 측정 결과
| 항목 | BEFORE | AFTER | 변화 | 판정 |
|---|---:|---:|---|---|
| DPM 채널-foreach (fresh esd, 채널10×3000) | +4684 KB | +860 KB | **−82%** | ✅ 달성 |
| DPM 혼합(integ+smoke ×5) heap_anon 증가 | +1680 KB | +1628 KB | ≈0% | ⚠️ 미미 |
| DPM idle 상주 (lib PSS) | 476 KB | 472 KB | ≈0% | ⚠️ 미미 |
| DPM idle esd heap_anon | 1568 KB | 1568 KB | 0% | ⚠️ 미미 |
| 클라 3000 noti 보유 VmData | 2712 KB | 3900 KB | **+44%** | ❌ 악화 |

## 25% 절감 판정 (complete-promise 기준)
- 채널-foreach 시나리오만 −82%로 단독 충족하나, **idle/혼합은 중립·클라는 악화** →
  "리팩토링 이전 대비 메모리 사용률 25% 절감"을 **전반적/대표 워크로드 기준으로는 미달성**.
- 따라서 다음 단계로 **왜 절감이 안 됐는지 분석 + 추가 절감 플랜 + 재리팩토링** 진행.

## 왜 절감이 안 됐나 (원인 분석)
1. **혼합/idle 중립**: 리팩토링의 1차 목표가 C→C++ 안전성이라 상주/일반 경로 메모리는 그대로.
   dnd 컨테이너(GList→STL) 절감은 상주형이라 DND 부하시에만 수 KB.
2. **클라 악화(+44%)**: struct 15개 문자열 멤버 `char*`(8B) → `std::string`(~32B SSO)로
   객체 자체가 noti당 ~360B 증가. 안전성 비용(예고된 트레이드오프).
3. **숨은 진짜 누수**: 혼합 워크로드에서 **양쪽 공통 ~+320KB/round 누적** 관찰 →
   리팩토링과 무관한 **기존(pre-existing) 누수**. 이게 sustained 메모리의 주범.

## 다음 라운드 타깃 (절감 아이템)
→ `PLAN_round-02.md` 참조. 우선순위:
- **T1 (최고)**: 혼합 워크로드 ~320KB/round 누수원 규명 & 수정 (sustained에서 BEFORE≫AFTER 유도).
- **T2**: 클라 struct 메모리 회귀 완화 (안전성 유지하며 객체 크기 축소 방안 검토).
- **T3**: 채널-foreach 잔여 ~0.14KB/call churn 추가 절감 검토.
