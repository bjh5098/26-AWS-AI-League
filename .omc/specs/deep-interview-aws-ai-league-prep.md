# Deep Interview Spec: AWS AI League 대회 사전 준비 전략

## Metadata
- Interview ID: aws-ai-league-prep-001
- Rounds: 6
- Final Ambiguity Score: 20%
- Type: greenfield
- Generated: 2026-05-19
- Threshold: 20%
- Initial Context Summarized: no
- Status: PASSED

## Clarity Breakdown
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Goal Clarity | 0.85 | ×0.40 | 0.34 |
| Constraint Clarity | 0.75 | ×0.30 | 0.23 |
| Success Criteria | 0.78 | ×0.30 | 0.23 |
| **Total Clarity** | | | **0.80** |
| **Ambiguity** | | | **20%** |

## Topology
| Component | Status | Description | Coverage |
|-----------|--------|-------------|----------|
| 경쟁 전략 수립 | active | 게임 규칙 분석, 채점 패턴 예측, 최적 접근법 문서화 | 코인 극대화 전략, Claude Code 자동 배포 루프 |
| AWS 환경 사전구성 | active | AWS MCP Server 설정, AgentCore 패턴/템플릿 준비 | Workshop Studio AWS CLI 접근 가능 예상 |
| 멀티에이전트 실행 워크플로우 | active | Claude Code 주력 전략, 빠른 수정/배포 분업 | Claude Code 단독 주력으로 단순화 |
| 도메인 지식 정리 | active | 4.1~4.6 각 서비스별 핵심 팁 & 예상 패턴 | 모든 서비스에 퀘스트 존재, 균형 준비 필요 |

## Goal
**AWS AI League 경쟁형 워크샵에서 최고 점수를 얻기 위한 사전 준비를 완료한다.**

구체적으로:
1. 제한 시간 내 지도 탐색 AI 에이전트가 최대한 많은 코인을 수집하도록 AgentCore 기반 에이전트를 사전에 설계한다
2. 대회 당일 Claude Code가 Lambda 코드를 자동 수정 → 배포 → 점수 확인하는 루프를 즉시 가동할 수 있도록 준비한다
3. 4.1 AgentCore ~ 4.5 Lambda 모든 서비스에 퀘스트가 존재하므로 균형 있는 사전 지식을 갖춘다

## Constraints
- **사전 준비 가능 범위**: 코드, 프롬프트, 템플릿 모두 사전 작성 가능. 단 AgentCore ARN/Lambda ARN 등 환경 변수는 당일 주어짐
- **실행 환경**: Workshop Studio 제공 AWS 계정 + AWS CLI 접근 가능 예상 (당일 확인 필요)
- **AI Assistant**: Claude Code 주력 사용 (Claude Code가 AWS CLI 접근 가능 전제)
- **게임 규칙**: 세부 규칙(실격 조건, 보너스, 챌린지)은 당일 공개 — 유연한 전략 필요
- **코딩 환경**: SageMaker AI 코드 에디터 내장, Amazon Q 기본 제공, Kiro/Claude Code 보조 허용
- **서비스 범위**: AgentCore(4.1), Memory(4.2), Tools/Gateway(4.3), Guardrails(4.4), Lambda(4.5) — 전 영역 퀘스트 존재

## Non-Goals
- Kiro 활용 전략 (Claude Code 주력으로 단순화)
- AWS MCP Server 온사이트 구성 (워크샵 환경이 외부 MCP 허용 여부 미확인)
- 멀티플레이어 협력 전략 (개인 경쟁 전제)
- Guardrails(4.4) 깊은 최적화 (점수 영향도 상대적으로 낮을 것으로 예상)

## Acceptance Criteria
- [ ] AgentCore 에이전트 뼈대 코드 (Python) 사전 작성 완료
- [ ] Lambda Tool 템플릿 (경로탐색 / 코인 수집 / 상태 조회) 사전 작성 완료
- [ ] AgentCore Memory 활용 패턴 (힌트 저장 → 재사용) 코드 준비
- [ ] Claude Code → AWS CLI → Lambda deploy 자동화 스크립트 준비
- [ ] 4.1~4.5 각 서비스별 핵심 패턴 치트시트 문서 작성
- [ ] 당일 환경 변수(ARN, region, account-id) 즉시 주입할 수 있는 `.env.template` 준비
- [ ] 코인 수집 알고리즘 (A* 또는 BFS 기반) Lambda 코드 사전 구현

## Assumptions Exposed & Resolved
| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| 코드는 당일 만들어야 한다 | 사전 안내자료에 당일 환경 공개라고 함 | 코드/프롬프트는 사전 가능, ARN 등 환경값만 당일 주입 |
| AWS CLI 접근 불가 | Workshop Studio 환경이 브라우저 전용일 수 있음 | AWS CLI 접근 가능 예상, 로컬 Claude Code에서 제어 |
| Kiro가 필수 | Kiro 사전 설치 권장이라고 안내 | Claude Code 주력으로 단순화, Kiro 보조 역할 |
| 특정 서비스만 중요 | Memory 또는 Tools만 집중하면 됨 | 4.1~4.5 전 서비스에 퀘스트 존재, 균형 준비 필요 |

## Technical Context
### 게임 구조 (Notion 안내자료 기반)
- **형식**: 제한 시간 내 지도 탐색 → 보물(코인) 수집 AI 에이전트 경쟁
- **환경**: Amazon Bedrock AgentCore 중심, SageMaker AI 코드 에디터 내장
- **채점**: 코인 수집량 기반, 챌린지/보너스 당일 공개

### 핵심 아키텍처 패턴
```
Claude Code (로컬)
  → AWS CLI (Lambda update-function-code)
    → AgentCore Agent (Bedrock)
      → Tool 호출 (Lambda)
        → 지도 탐색 / 코인 수집
          → Memory 저장 (힌트, 방문 경로)
```

### 사용자 기존 지식 (Notion 리서치 기반)
- AgentCore Gateway + MCP Hub 실전 검증 완료
- LiteLLM + SigV4 + Interceptor Lambda + DynamoDB ACL 패턴 검증
- IAM 인증 vs JWT 인증 trade-off 이해
- Claude Code + MCP 연동 패턴 실전 경험

## Ontology (Key Entities)
| Entity | Type | Fields | Relationships |
|--------|------|--------|---------------|
| Agent | core domain | id, role, system_prompt, tools, memory_id | uses Lambda Tools, stores in Memory |
| Coin/Treasure | core domain | position, value, collected | collected by Agent |
| Map | core domain | grid, obstacles, coin_positions | navigated by Agent |
| Lambda Tool | supporting | function_name, ARN, code, handler | called by Agent via Gateway |
| AgentCore Memory | supporting | memory_id, entries | read/write by Agent |
| Gateway | supporting | id, targets, auth_type | routes Tool calls |
| Guardrails | supporting | id, rules | constrains Agent output |
| Claude Code | external system | model, tools, mcp_servers | modifies Lambda code, deploys |
| Workshop Studio | external system | aws_account, credentials | provides runtime environment |

## Ontology Convergence
| Round | Entity Count | New | Changed | Stable | Stability Ratio |
|-------|-------------|-----|---------|--------|----------------|
| 1 | 5 | 5 | - | - | N/A |
| 2 | 7 | 2 | 0 | 5 | 71% |
| 3 | 8 | 1 | 0 | 7 | 88% |
| 4-6 | 9 | 1 | 0 | 8 | 89% |

## Implementation Plan

### Phase 1: 도메인 지식 정리 (즉시 시작)
각 서비스별 치트시트 작성:

**4.1 AgentCore 핵심 패턴**
- Agent 생성 API (boto3)
- System Prompt 설계 원칙 (역할 명시, 도구 사용 지침)
- invoke_agent() 호출 패턴

**4.2 Memory 핵심 패턴**
- 힌트/코인 위치 저장
- 세션 간 상태 유지
- System Prompt에서 Memory 참조 방법

**4.3 Tools/Gateway 핵심 패턴**
- Lambda Tool 등록 (schema 정의)
- Gateway ARN 설정
- Tool 호출 결과 파싱

**4.4 Guardrails**
- 기본 설정으로 충분, 과도한 제한 회피

**4.5 Lambda 코드 최적화**
- A*/BFS 경로 탐색 알고리즘
- 코인 수집 우선순위 로직
- 실행 시간 최적화 (타임아웃 회피)

### Phase 2: AWS 환경 사전구성
```python
# .env.template (당일 주입용)
AGENT_ID=
AGENT_ALIAS_ID=
LAMBDA_FUNCTION_NAME=
AWS_REGION=ap-northeast-2
AWS_ACCOUNT_ID=
MEMORY_ID=
GATEWAY_ID=
```

```bash
# deploy.sh (Claude Code 자동 실행용)
#!/bin/bash
zip -r function.zip lambda_function.py
aws lambda update-function-code \
  --function-name $LAMBDA_FUNCTION_NAME \
  --zip-file fileb://function.zip
```

### Phase 3: 멀티에이전트 워크플로우 구성
Claude Code에 지시할 핵심 프롬프트 템플릿:
```
현재 점수: {score}
에이전트 로그: {log}

다음을 수행하세요:
1. 로그에서 실패 패턴 분석
2. lambda_function.py의 {specific_function} 수정
3. deploy.sh 실행하여 배포
4. 30초 후 점수 재확인
```

## Interview Transcript
<details>
<summary>Full Q&A (6 rounds)</summary>

### Round 0
**Q:** Topology 확인 — 4개 컴포넌트 (경쟁전략/AWS환경/멀티에이전트/도메인지식)
**A:** 맞습니다 (잘못 누른 수정 포함)

### Round 1
**Q:** 고득점의 핵심이 완료율 vs 속도 vs 효율성 중 무엇인가?
**A:** 코인 수집 극대화. 게임가이드에 규칙/도구/보너스/챌린지 항목 존재, 실격조건 미공개
**Ambiguity:** 58%

### Round 2
**Q:** 사전 준비 가능 범위 (코드 사전작성 가능 vs 당일 환경만 주어짐)
**A:** 코드/프롬프트는 사전 준비 가능
**Ambiguity:** 47%

### Round 3
**Q:** "준비가 맞다"고 느끼는 구체적 장면
**A:** Claude Code가 자동으로 AgentCore 코드를 수정 + 배포
**Ambiguity:** 35%

### Round 4 (Contrarian Mode)
**Q:** AWS CLI 접근 불가 환경이라면 대안 전략은?
**A:** Workshop Studio가 AWS CLI 접근 가능한 환경 제공 예상
**Ambiguity:** 28%

### Round 5
**Q:** Claude Code + Kiro 역할 분담
**A:** Claude Code를 주력으로 사용할 예정
**Ambiguity:** 22%

### Round 6
**Q:** 4.1~4.6 중 가장 큰 변수가 될 서비스
**A:** 모두 중요하고 각 항목에 대한 퀘스트가 나올 것으로 예상
**Ambiguity:** 20%
</details>
