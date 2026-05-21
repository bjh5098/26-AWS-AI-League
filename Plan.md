# AI League 2026 Seoul Summit — 대회 완료 요약

> **결과: 13위 / 137명 (상위 ~10%)**
> 최고 점수: 12,232점 | 모델: Claude Haiku 4.5 | 플랫폼: Amazon Bedrock AgentCore

---

## 최종 구성 (대회 종료 시점)

### 슈퍼바이저 에이전트
- [x] 모델: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
- [x] System Prompt: `agent/supervisor_prompt_v2.txt`
- [x] AgentCore Memory: `pear_memory-3jmYDVAXWN` (ACTIVE)
- [x] Guardrail: `ai-league-guardrail` (연결됨)
- [x] Navigation Prompt: `Use strategy smart.`

### 서브에이전트 (4개)
- [x] Pathfinding_Specialist — 경로 탐색 Lambda
- [x] Blue_Brain_Specialist — 코드 실행 Lambda (c2)
- [x] Dark_Prophet_Specialist — 웹 검색 Lambda (c4)
- [x] Medical_API_Specialist — JSON 추출 Lambda (c18)

### Lambda 도구
- [x] `AgentCoreGatewayTool-Pathfinding` — `tools/pathfinding_tool_v2.py`
- [x] `AgentCoreGatewayTool-BlueBrain` — `tools/blue_brain_tool.py`
- [x] `AgentCoreGatewayTool-DarkProphet` — `tools/dark_prophet_tool.py`
- [x] `AgentCoreGatewayTool-MedicalAPI` — `tools/medical_api_tool.py`

### Guardrail 설정
- [x] Content Filters: 전부 LOW
- [x] Denied Topics: Edible_Flowers, Organ_Transplant, Weeds
- [x] 차단 메시지: `the hero cannot assist with that request`

---

## 게임 실행 이력

| # | 시간 | 점수 | 결과 | 핵심 이슈 |
|---|------|------|------|----------|
| 1 | 05:01 | 낮음 | 초기 테스트 | 기본 설정 확인 |
| 2 | 05:14 | 낮음 | c30 사망 | c40 미방문 상태로 c30 진입 |
| 3 | 05:20 | 낮음 | c1 타임아웃 | 가드레일 루프 |
| 4 | 05:36 | **12,232** | 완주 | best run — c5 오답 1건, c4 오답 1건 |
| 5 | 05:57 | 2,139 | c30 사망 | Lambda 미배포 (구버전 실행) |

---

## 점수 분석 (Game 4 — 12,232점)

```
챌린지 점수:  8,800
보물 보너스:  2,000
생명 보너스:    750 (3생명 × 250)
토큰 보너스:    682 (1000 - 4766/15)
──────────────────
총점:       12,232
```

### 점수 손실 원인
| 이슈 | 손실 | 원인 |
|------|------|------|
| c5 "광합성" 오답 | -500 | 슈퍼바이저가 식물 키워드를 c1으로 오분류 |
| c4 두번째 오답 | -1,050 | Dark Prophet Lambda 스크래핑 부정확 |

### 수정 완료 (v2에 반영)
- [x] supervisor_prompt_v2: "c5 is NEVER a guardrail" 명시
- [x] supervisor_prompt_v2: "Output ONLY the final answer" 토큰 절약
- [x] pathfinding_tool_v2: c30 회피 (c40 전), treasure 회피 (최종까지)

---

## 핵심 교훈

1. **c30은 chokepoint** — BFS에서 c40 획득 전까지 `'c30'`을 blocked에 포함해야 함
2. **treasure 통과 = 게임 종료** — AVOID_CELLS에 `'treasure'` 포함 필수
3. **Lambda 배포 ≠ 저장** — SageMaker Studio에서 클라우드 아이콘으로 Deploy 필수
4. **슈퍼바이저 토큰이 점수** — 서두/설명 한 줄 제거가 보너스 +100점 이상
5. **가드레일 오분류 치명적** — c5 일반 질문을 c1으로 분류하면 -250 + 생명 손실

---

## 미적용 최적화 (시간 부족)

- [ ] RLVR 커스텀 모델 (50% 토큰 패널티 감소)
- [ ] Dark Prophet URL fetch 정확도 개선
- [ ] pathfinding_tool_v2 실제 배포 및 검증 (Game 5에서 구버전 실행됨)
