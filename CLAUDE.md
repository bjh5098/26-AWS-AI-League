# AWS AI League 2026 Seoul Summit — 대회 결과 및 코드 아카이브

## 대회 결과
- **순위: 13위 / 137명 (상위 ~10%)**
- 최종 점수: 12,232점 (best run)
- 모델: Claude Haiku 4.5 (외부 모델 사용 불가)
- 플랫폼: Amazon Bedrock AgentCore

---

## 아키텍처

```
슈퍼바이저 (Claude Haiku 4.5)
├── Pathfinding_Specialist (Lambda)   — 경로 탐색
├── Blue_Brain_Specialist (Lambda)    — 코드 실행 (c2)
├── Dark_Prophet_Specialist (Lambda)  — 웹 스크래핑 (c4)
└── Medical_API_Specialist (Lambda)   — JSON 추출 (c18)
```

- 슈퍼바이저가 챌린지 유형 판별 → 적절한 서브에이전트에 위임
- c1(가드레일), c3(기억력), c5(간단질문), c30(빨간문), c40(빨간열쇠)는 슈퍼바이저가 직접 처리
- AgentCore Memory로 c40 열쇠코드 저장 → c30에서 역순 답변

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `agent/supervisor_prompt_v2.txt` | **최종 슈퍼바이저 프롬프트** (UI에 복사) |
| `tools/pathfinding_tool.py` | **최종 Pathfinding Lambda** (c30/treasure 회피, 126스텝) |
| `tools/blue_brain_tool.py` | Blue Brain Lambda (Python 코드 실행) |
| `tools/dark_prophet_tool.py` | Dark Prophet Lambda (DuckDuckGo 웹 검색) |
| `tools/medical_api_tool.py` | Medical API Lambda (자연어→JSON 변환) |
| `agent/supervisor_prompt_plain.txt` | 슈퍼바이저 프롬프트 v1 (마크다운 없는 버전) |
| `tools/pathfinding_tool_v1.py` | Pathfinding Lambda v1 (이전 버전, 아카이브) |

---

## 경로탐색 알고리즘 (pathfinding_tool.py)

### smart 전략 핵심 로직
1. 타겟을 **도달 가능성** 기준으로 분류 (c30 통과 없이 가능 vs 불가)
2. Phase 1: c30 없이 도달 가능한 타겟 → greedy nearest 수집
3. Phase 2: c40 방문 (열쇠 획득)
4. Phase 3: c30 통과 필수 타겟 수집 (이제 안전)
5. Phase 4: c30 방문 (열쇠코드 역순 답변)
6. Phase 5: treasure (게임 종료 — 반드시 맨 마지막)

### 회피 규칙
- `wall`: 이동 불가
- `c8`: 스파이크 (-1 생명)
- `c30`: c40 미방문 시 회피 (-5 생명)
- `treasure`: 최종 Phase까지 회피 (도착 즉시 게임 종료)

---

## 챌린지별 전략 요약

| 챌린지 | 점수 | 전략 |
|--------|------|------|
| c1 Violent Violet | +400 | 차단 키워드면 "the hero cannot assist with that request", 아니면 직접 답변 |
| c2 Blue Brain | +600 | Blue_Brain_Specialist Lambda로 코드 실행 |
| c3 Memento | +550 | Memory에서 맵 정보 recall |
| c4 Dark Prophet | +800 | Dark_Prophet_Specialist Lambda로 URL 스크래핑 |
| c5 Bonehead | +250 | 숫자/단어만 출력 (설명 금지) |
| c7 코인 | +250 | 자동 수집 |
| c8 스파이크 | -1생명 | 경로에서 회피 |
| c18 의료 API | +500 | JSON 5필드 추출 |
| c30 빨간 문 | +1000/-5 | c40 방문 후 열쇠코드 역순 답변 |
| c40 빨간 열쇠 | +50 | "감사합니다" + Memory에 코드 저장 |
| treasure | +2000+생명×5 | 맨 마지막 방문 |

---

## 점수 공식
```
총점 = 챌린지 점수 합계
     + 보물 보너스 (2000 + 남은생명×5)
     + 남은생명 × 250
     + 토큰 보너스: 1000 - (총토큰 / 방문챌린지수)
```

---

## 대회 중 발견한 핵심 교훈

1. **c30은 맵의 chokepoint** — c40 전에 절대 통과하면 안 됨 (BFS에서 blocked 처리 필수)
2. **treasure 통과도 게임 종료 트리거** — AVOID_CELLS에 포함 필수
3. **슈퍼바이저 토큰 절약이 점수 직결** — "Output ONLY the final answer" 한 줄로 큰 효과
4. **c5를 c1으로 오분류하면 -250 + 생명 손실** — "c5 is NEVER a guardrail" 명시 필요
5. **Lambda 배포 확인 필수** — SageMaker Studio에서 저장 ≠ 배포, 반드시 검증

---

## 게임 로그 파일

| 파일 | 결과 | 비고 |
|------|------|------|
| `game-events-2026-05-21T05-01-11.json` | 1차 테스트 | 초기 버전 |
| `game-events-2026-05-21T05-14-48.json` | 2차 테스트 | c40/c30 로직 문제 |
| `game-events-2026-05-21T05-20-06.json` | 3차 테스트 | c1 가드레일 이슈 |
| `game-events-2026-05-21T05-36-39.json` | **12,232점** | best run |
| `game-events-2026-05-21T05-57-09.json` | 2,139점 | Lambda 미배포로 c30 사망 |

---

## 파일 구조
```
.
├── CLAUDE.md                         # 이 파일
├── Plan.md                           # 대회 실행 체크리스트
├── game4_analysis.md                 # 4차 게임 분석 + 개선 방향
├── game-events-*.json                # 게임 로그 (5회분)
│
├── agent/
│   ├── supervisor_prompt_v2.txt      # ★ 최종 슈퍼바이저 프롬프트
│   ├── supervisor_prompt_plain.txt   # v1 프롬프트 (마크다운 없음)
│   ├── supervisor_prompt.md          # 프롬프트 문서 버전
│   ├── system_prompt.txt             # 로컬 참고용 (한국어)
│   └── pathfinding_subagent_prompt.txt
│
├── tools/
│   ├── pathfinding_tool.py           # ★ 최종 Pathfinding Lambda (v2)
│   ├── pathfinding_tool_v1.py        # v1 (이전 버전, 아카이브)
│   ├── blue_brain_tool.py            # c2 코드 실행
│   ├── dark_prophet_tool.py          # c4 웹 검색
│   └── medical_api_tool.py           # c18 JSON 추출
│
├── originals/                        # 원본 코드 보관 (복구용)
│   ├── lambda_function_original.py
│   └── pathfinding_subagent_prompt_original.txt
│
├── scripts/
│   ├── inspect_infra.py              # 인프라 자동 파악
│   ├── generate_dataset.py           # RLVR Stage 1 데이터셋
│   ├── reward_function.py            # Stage 1 보상 함수
│   ├── generate_faithfulness_dataset.py  # Stage 2 데이터셋
│   └── faithfulness_reward_function.py   # Stage 2 보상 함수
│
├── algorithms/
│   └── pathfinder.py
├── memory/
│   ├── memory_patterns.py
│   └── hint_store.py
├── cheatsheets/                      # 서비스별 치트시트
└── docs/
```
