# AWS AI League 대회 준비 프로젝트

## 프로젝트 개요
AWS AI League 경쟁형 워크샵 준비. 제한 시간 내 지도를 탐색해 코인을 수집하는 AI 에이전트를 Amazon Bedrock AgentCore로 구성하고, Claude Code가 Lambda 코드를 자동 수정·배포하는 루프를 통해 점수를 극대화한다.

## 대회 당일 즉시 실행 순서

```bash
# 1. AWS 자격증명 설정 후 인프라 파악
python scripts/inspect_infra.py
# → .env 자동 업데이트 + infra_report.md 생성

# 2. 파악 결과 및 전략 확인
cat infra_report.md

# 3. .env 수동 보완 (inspect가 못 채운 값)
vi .env  # 또는 nano .env

# 4. Lambda 배포
./deploy.sh all

# 5. 에이전트 실행
python agent/invoke_agent.py loop
```

## 핵심 전략
- **Claude Code 주력**: Lambda 코드 수정 → `./deploy.sh` → 점수 확인 → 반복
- **Memory 우선**: 매 턴 시작 전 Memory 조회로 불필요한 재탐색 방지
- **Haiku 모델**: 속도 우선 (더 많은 행동 = 더 많은 코인)
- **코인 우선순위**: 고가치 코인 → 가까운 코인 → 미탐색 영역

## 인프라 파악 (`scripts/inspect_infra.py`)

대회 당일 AWS CLI access 정보를 받으면 **가장 먼저 실행**할 스크립트.

### 파악 항목
| 항목 | 방법 | 자동화 |
|------|------|--------|
| AgentCore 에이전트 목록 | `list_agents` → 상세 조회 | ✅ AGENT_ID/.env 자동 |
| 에이전트 System Prompt | `get_agent` | ✅ infra_report.md 저장 |
| Lambda 함수 목록 | `list_functions` (AI League 키워드 필터) | ✅ Lambda ARN/.env 자동 |
| Lambda 환경변수 키 | `get_function_configuration` | ✅ infra_report.md 저장 |
| AgentCore Gateway | `list_gateways` | ✅ infra_report.md 저장 |
| 문제 유형 유추 | System Prompt + Lambda명 분석 | ✅ 전략 제안 자동 생성 |

### 유추 로직
- **System Prompt 키워드** → 게임 타입 파악 (지도탐색, 코인수집, Memory활용 등)
- **Lambda 함수명** → 사용 가능한 Tool 파악 (path/navigate, coin/collect, state/query 등)
- **환경변수 키** → GAME_API_ENDPOINT 등 게임 연결 정보 위치 파악
- → 자동으로 `infra_report.md`에 전략 제안 작성

## 파일 구조
```
.
├── CLAUDE.md                    # 이 파일 (Claude Code 프로젝트 컨텍스트)
├── .env.template                # 환경변수 템플릿 (대회 당일 .env로 복사)
├── .env                         # 실제 환경변수 (gitignore)
├── deploy.sh                    # Lambda 빠른 배포 스크립트
├── infra_report.md              # inspect_infra.py 실행 결과 (gitignore 아님)
│
├── scripts/
│   └── inspect_infra.py         # 대회 당일 인프라 자동 파악
│
├── agent/
│   ├── agent_skeleton.py        # AgentCore 에이전트 생성 코드
│   ├── invoke_agent.py          # 에이전트 실행 래퍼 + 게임 루프
│   └── system_prompt.txt        # 에이전트 System Prompt
│
├── tools/
│   ├── pathfinding_tool.py      # Lambda Tool: A*/BFS 경로탐색
│   ├── coin_collector_tool.py   # Lambda Tool: 코인 수집
│   └── state_query_tool.py      # Lambda Tool: 게임 상태 조회
│
├── algorithms/
│   └── pathfinder.py            # A*, BFS, 탐욕 코인 수집 알고리즘
│
├── memory/
│   ├── memory_patterns.py       # AgentCore Memory API 래퍼
│   └── hint_store.py            # 게임 상태 로컬 추적 (HintStore)
│
├── cheatsheets/                 # 각 서비스별 핵심 패턴 (대회 중 참고)
│   ├── 4.1-agentcore.md
│   ├── 4.2-memory.md
│   ├── 4.3-tools-gateway.md
│   ├── 4.4-guardrails.md
│   └── 4.5-lambda.md
│
└── docs/
    ├── 00-INDEX.md
    └── 01-workshop-guide.md     # 워크샵 사전 안내 (4.1~4.6 정리)
```

## Lambda 수정 → 배포 패턴 (Claude Code 자동화)

Claude Code에게 다음과 같이 지시:
```
현재 점수: {score}
에이전트 로그 요약: {log}

tools/pathfinding_tool.py의 handle_find_path 함수를 수정해서
더 효율적인 경로탐색이 되도록 개선한 후 ./deploy.sh pathfinding_tool 실행해줘.
```

## 환경변수 (.env)
- `.env.template` 참고
- `python scripts/inspect_infra.py` 실행 시 자동으로 채워짐
- 수동으로 채울 항목: `GAME_API_ENDPOINT`, `GAME_SESSION_ID` (당일 공개)

## 주의사항
- 실격 조건은 당일 공개 → Guardrails 설정 최소화로 사전 대비
- Lambda 타임아웃 30초 설정 권장
- 모든 코드는 순수 Python (numpy/scipy 의존성 없음)
