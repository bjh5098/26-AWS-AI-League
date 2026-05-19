# AWS AI League 대회 준비 프로젝트

## 프로젝트 개요
AWS AI League 경쟁형 워크샵 준비. 제한 시간 내 지도를 탐색해 코인을 수집하는 AI 에이전트를 Amazon Bedrock AgentCore로 구성하고, Claude Code가 Lambda 코드를 자동 수정·배포하는 루프를 통해 점수를 극대화한다.

---

## 대회 당일 전략 플레이북

### 핵심 원칙
> **"코드보다 관찰이 먼저다."** 무엇이 점수를 막고 있는지 파악한 뒤에 코드를 수정한다.
> 점수 향상의 80%는 System Prompt 개선과 알고리즘 로직 수정에서 나온다.

---

### Phase 1: 환경 파악 (T+0 ~ T+10분)

```bash
# 1. AWS 자격증명 설정 확인
aws sts get-caller-identity

# 2. 인프라 자동 파악 (가장 먼저 실행!)
python scripts/inspect_infra.py
# → .env 자동 업데이트 + infra_report.md 생성

# 3. 파악 결과 확인
cat infra_report.md
```

**이 단계에서 반드시 파악해야 할 것:**

| 확인 항목 | 확인 방법 | 중요도 |
|---------|---------|-------|
| 게임 규칙 (채점 공식) | 당일 공개 자료 꼼꼼히 읽기 | ⭐⭐⭐ 최우선 |
| 보너스/챌린지 조건 | 당일 공개 자료 | ⭐⭐⭐ |
| 실격 조건 | 당일 공개 자료 | ⭐⭐⭐ 반드시 확인 |
| 사용 가능한 Lambda Tool 목록 | `infra_report.md` | ⭐⭐⭐ |
| 에이전트 System Prompt 내용 | `infra_report.md` | ⭐⭐⭐ |
| 지도 크기 / 코인 종류 / 이동 방식 | 첫 번째 게임 실행 후 로그 | ⭐⭐⭐ |
| Memory ID, Gateway ID | `infra_report.md` → `.env` | ⭐⭐ |

---

### Phase 2: 베이스라인 수립 (T+10 ~ T+20분)

```bash
# .env 확인 및 수동 보완
cat .env
# GAME_API_ENDPOINT, GAME_SESSION_ID 등 당일 공개 값 직접 입력

# 전체 Lambda 배포
./deploy.sh all

# 에이전트 첫 실행 (점수 0점에서 시작)
python agent/invoke_agent.py loop
```

**베이스라인 실행 목표:**
- 에이전트가 적어도 1개 이상 코인을 수집하는 것을 확인
- 에러 없이 Tool이 호출되는지 확인
- 첫 점수(N점) 기록 → 이후 모든 개선의 기준

---

### Phase 3: 반복 개선 루프 (T+20분 ~ 종료)

이 루프가 대회의 핵심이다. **최대한 빠르게 많은 사이클을 돌린다.**

```
관찰(로그/점수) → 병목 파악 → Claude Code에게 수정 지시 → 배포 → 재실행 → 점수 확인
```

#### 병목 진단 의사결정 트리

```
에이전트가 코인을 못 수집하고 있다
├── 같은 자리를 맴돌고 있다
│   └── → Memory 미활용. System Prompt에 "매 턴 시작 전 Memory 조회" 강제 추가
├── 장애물에 계속 부딪힌다
│   └── → pathfinding_tool.py의 장애물 처리 로직 수정 + System Prompt에 "이동 전 find_path 필수 호출" 추가
├── 가까운 코인을 놔두고 먼 곳으로 간다
│   └── → state_query_tool에서 코인 위치 정렬 로직 추가 + System Prompt에 "가장 가까운 코인 우선" 지시
└── Tool을 전혀 호출하지 않는다
    └── → System Prompt에 Tool 호출 시나리오 예시 추가, description 강화

점수는 오르는데 속도가 느리다
├── 턴당 Tool 호출이 3번 이상이다
│   └── → 불필요한 중간 조회 제거. 한 턴에 "탐색+이동+수집"을 하나의 판단으로
├── Lambda 응답이 3초 이상 걸린다
│   └── → Lambda 메모리 256MB → 512MB 증가, 타임아웃 재확인
└── 에이전트 모델이 Sonnet이다
    └── → Haiku로 교체 (응답속도 2-3배 빠름, invoke 비용도 낮음)

점수가 갑자기 0이 됐다
└── → 실격 조건 확인! Guardrails가 응답을 차단했을 가능성
    └── → CloudWatch 로그로 에러 확인: aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow
```

---

### Claude Code 지시 템플릿

#### 시스템 프롬프트 개선 요청
```
현재 상황:
- 점수: {이전 점수} → {현재 점수}
- 문제: 에이전트가 {구체적 문제 행동}
- 로그 요약: {핵심 로그 2-3줄}

agent/system_prompt.txt를 수정해서 에이전트가 다음을 하도록 바꿔줘:
1. {원하는 행동 1}
2. {원하는 행동 2}
수정 후 테스트는 필요없고 파일만 저장해줘.
```

#### Lambda 코드 수정 + 배포 요청
```
현재 상황:
- 점수: {점수}
- 문제: tools/{파일명}.py의 {함수명}이 {구체적 문제}

{파일명}의 {함수명}을 수정해서 {원하는 동작}을 구현하고,
./deploy.sh {tool_name} 까지 실행해줘.
```

#### 빠른 디버깅 요청
```
다음 Lambda 로그를 분석해서 왜 코인을 못 찾는지 이유와 수정 방법을 알려줘:
{CloudWatch 로그 붙여넣기}
```

---

### 점수 극대화 우선순위 전략

대회 시간이 제한되어 있으므로 **임팩트가 큰 것부터** 순서대로 한다.

| 순위 | 개선 영역 | 예상 점수 향상 | 소요 시간 |
|-----|---------|-------------|---------|
| 1 | System Prompt 개선 (역할·우선순위 명확화) | 매우 높음 | 2-3분 |
| 2 | Memory 활용 (재탐색 방지) | 높음 | 3-5분 |
| 3 | 코인 수집 우선순위 로직 (고가치 코인 우선) | 높음 | 5분 |
| 4 | 보너스 조건 충족 (당일 공개 규칙 대응) | 매우 높음 | 가변 |
| 5 | 경로탐색 최적화 (A* 튜닝) | 중간 | 5-10분 |
| 6 | Lambda 성능 최적화 (메모리/타임아웃) | 낮음 | 2분 |

**절대 하지 말아야 할 것:**
- 새로운 AWS 서비스를 처음부터 구성하려는 시도 (시간 낭비)
- 완벽한 알고리즘을 만들려는 perfectionism (80/20 룰 적용)
- 배포 없이 로컬에서만 테스트 (실제 게임 환경과 다를 수 있음)

---

### 시간 배분 가이드 (총 60분 기준)

```
T+00 ~ T+05  인프라 파악 + .env 설정
T+05 ~ T+10  Lambda 배포 + 첫 에이전트 실행
T+10 ~ T+12  베이스라인 점수 확인 + 병목 파악
T+12 ~ T+25  1차 개선 사이클 (System Prompt 중심)
T+25 ~ T+40  2차 개선 사이클 (알고리즘/코드 수정)
T+40 ~ T+55  3차 개선 사이클 (보너스 조건 집중)
T+55 ~ T+60  마지막 배포 + 최종 에이전트 실행
```

시간이 더 주어지면 같은 루프를 계속 반복한다.

---

### 긴급 대응 시나리오

#### "에이전트가 전혀 실행 안 됨"
```bash
# 1. 에이전트 상태 확인
aws bedrock-agent get-agent --agent-id $AGENT_ID

# 2. PREPARED 상태 아니면 재준비
python agent/agent_skeleton.py

# 3. 별칭 확인
aws bedrock-agent list-agent-aliases --agent-id $AGENT_ID
```

#### "Lambda 에러 발생"
```bash
# 실시간 로그 확인
aws logs tail /aws/lambda/$LAMBDA_FUNCTION_NAME --follow

# 빠른 수정 후 재배포
./deploy.sh pathfinding_tool  # 특정 tool만 배포
```

#### "점수가 갑자기 0"
1. Guardrails 차단 여부 확인
2. 실격 조건 재확인
3. GAME_SESSION_ID가 만료됐는지 확인
4. 에이전트를 새 세션 ID로 재실행

#### "게임 규칙을 잘못 이해했음"
→ 당황하지 말고 `agent/system_prompt.txt`만 수정 (배포 불필요, 즉시 반영)

---

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

---

## 파일 구조
```
.
├── CLAUDE.md                    # 이 파일 (Claude Code 프로젝트 컨텍스트)
├── .env.template                # 환경변수 템플릿 (대회 당일 .env로 복사)
├── .env                         # 실제 환경변수 (gitignore)
├── deploy.sh                    # Lambda 빠른 배포 스크립트
│
├── scripts/
│   └── inspect_infra.py         # 대회 당일 인프라 자동 파악
│
├── agent/
│   ├── agent_skeleton.py        # AgentCore 에이전트 생성 코드
│   ├── invoke_agent.py          # 에이전트 실행 래퍼 + 게임 루프
│   └── system_prompt.txt        # 에이전트 System Prompt ← 가장 자주 수정
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

---

## 환경변수 (.env)
- `.env.template` 참고
- `python scripts/inspect_infra.py` 실행 시 자동으로 채워짐
- 수동으로 채울 항목: `GAME_API_ENDPOINT`, `GAME_SESSION_ID` (당일 공개)

## 주의사항
- 실격 조건은 당일 공개 → Guardrails 설정 최소화로 사전 대비
- Lambda 타임아웃 30초 설정 권장
- 모든 코드는 순수 Python (numpy/scipy 의존성 없음)
