# AWS AI League 2026 Seoul Summit

> Amazon Bedrock AgentCore 기반 던전 탐색 AI 에이전트 — **13위 / 137명 (상위 ~10%)**

![Leaderboard](assets/leaderboard.jpeg)

## Overview

AWS AI League는 제한 시간 내에 던전 맵을 탐색하며 코인을 수집하고, 챌린지를 해결하며 보물에 도달하는 AI 에이전트 경쟁 대회입니다.

- **대회**: AWS AI League 2026 Seoul Summit (2026.05.21, 13:00~15:00 KST, 2시간)
- **플랫폼**: Amazon Bedrock AgentCore (Runtime, Memory, Gateway, Guardrails)
- **모델**: Claude Haiku 4.5 (외부 모델 호출 시 실격)
- **게임 시간**: 5분/게임
- **최고 점수**: 11,995점 (최고 총 출력 토큰: 8,320)

## Architecture

```
Supervisor Agent (Claude Haiku 4.5)
│
├── Pathfinding_Specialist    BFS 경로 탐색 (Lambda)
├── Blue_Brain_Specialist     Python 코드 실행 (Lambda)
├── Dark_Prophet_Specialist   웹 스크래핑 (Lambda)
└── Medical_API_Specialist    JSON 추출 (Lambda)
```

슈퍼바이저가 챌린지 유형을 판별하여 적절한 서브에이전트에 위임하거나 직접 처리합니다.

## Scoring Formula

```
총점 = 챌린지 점수 합계
     + 보물 보너스 (2000 + 남은생명 x 5)
     + 남은생명 x 250
     + 토큰 보너스: 1000 - (총토큰 / 방문챌린지수)
```

## Key Challenges

| Challenge | Points | Strategy |
|-----------|--------|----------|
| c1 Violent Violet | +400 | Guardrail 차단 or 직접 답변 |
| c2 Blue Brain | +600 | Lambda 코드 실행 |
| c3 Memento | +550 | AgentCore Memory recall |
| c4 Dark Prophet | +800 | URL 스크래핑 |
| c5 Bonehead | +250 | 숫자만 출력 |
| c7 Coin | +250 | 자동 수집 |
| c8 Spike | -1 life | 경로 회피 |
| c18 Medical API | +500 | NLP to JSON |
| c30 Red Door | +1000 / -5 lives | c40 열쇠 필수 |
| c40 Red Key | +50 | Memory에 코드 저장 |
| Treasure | +2000 | 최종 도달 (게임 종료) |

## Pathfinding Algorithm

`tools/pathfinding_tool.py` — Phase 기반 최적 경로:

1. **Phase 1**: c30 통과 없이 도달 가능한 타겟을 greedy nearest로 수집
2. **Phase 2**: c40 방문 (열쇠 획득)
3. **Phase 3**: c30 통과 필수 타겟 수집 (열쇠 획득 후 안전)
4. **Phase 4**: c30 방문 (열쇠코드 역순 답변)
5. **Phase 5**: Treasure (게임 종료 — 반드시 마지막)

회피 셀: `wall`, `c8`(스파이크), `c30`(c40 전), `treasure`(최종 Phase까지)

## Lessons Learned

1. **c30은 맵의 chokepoint** — c40 획득 전 BFS에서 반드시 blocked 처리
2. **Treasure 통과 = 즉시 게임 종료** — 경유지로 사용 불가
3. **토큰 절약이 점수** — 응답 서두/설명 제거만으로 보너스 +100점 이상
4. **Guardrail 오분류 치명적** — c5 일반 질문을 c1으로 잘못 차단하면 점수 + 생명 동시 손실
5. **Lambda 배포 확인 필수** — SageMaker Studio에서 저장 ≠ 배포

## Project Structure

```
.
├── agent/
│   ├── supervisor_prompt_v2.txt   # Final supervisor system prompt
│   ├── supervisor_prompt_plain.txt
│   └── system_prompt.txt
│
├── tools/
│   ├── pathfinding_tool.py        # Final pathfinding lambda (v2)
│   ├── blue_brain_tool.py         # Code execution (c2)
│   ├── dark_prophet_tool.py       # Web scraping (c4)
│   └── medical_api_tool.py        # JSON extraction (c18)
│
├── scripts/
│   ├── inspect_infra.py           # Infrastructure discovery
│   ├── generate_dataset.py        # RLVR Stage 1 dataset
│   └── reward_function.py         # RLVR reward function
│
├── originals/                     # Original code backup
├── game-events-*.json             # Game logs (5 runs)
├── assets/                        # Screenshots
└── docs/                          # Workshop guides
```

## Tech Stack

- **Agent Orchestration**: Amazon Bedrock AgentCore
- **LLM**: Claude Haiku 4.5 (Anthropic via Bedrock)
- **Tools**: AWS Lambda (Python 3.12)
- **Memory**: AgentCore Memory API
- **Guardrails**: Amazon Bedrock Guardrails
- **Development**: Claude Code (prompt engineering + code generation)

## License

This project was created for the AWS AI League 2026 Seoul Summit competition.
