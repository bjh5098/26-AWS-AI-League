# AWS AI League 준비 문서 인덱스

## 대회 관련 문서

| 파일 | 내용 | 우선순위 |
|------|------|---------|
| [01-workshop-guide.md](01-workshop-guide.md) | 워크샵 사전 안내자료 (게임 규칙, 서비스 개요 4.1~4.6) | ⭐⭐⭐ 필독 |
| [../cheatsheets/4.1-agentcore.md](../cheatsheets/4.1-agentcore.md) | AgentCore 핵심 패턴 & 코드 | ⭐⭐⭐ |
| [../cheatsheets/4.2-memory.md](../cheatsheets/4.2-memory.md) | Memory 활용 패턴 | ⭐⭐⭐ |
| [../cheatsheets/4.3-tools-gateway.md](../cheatsheets/4.3-tools-gateway.md) | Tools/Gateway 패턴 | ⭐⭐⭐ |
| [../cheatsheets/4.4-guardrails.md](../cheatsheets/4.4-guardrails.md) | Guardrails 기본 패턴 | ⭐⭐ |
| [../cheatsheets/4.5-lambda.md](../cheatsheets/4.5-lambda.md) | Lambda 최적화 패턴 | ⭐⭐⭐ |

## 핵심 코드 파일

| 파일 | 역할 |
|------|------|
| [../.env.template](../.env.template) | 대회 당일 환경변수 주입 템플릿 |
| [../deploy.sh](../deploy.sh) | Lambda 배포 자동화 스크립트 |
| [../agent/agent_skeleton.py](../agent/agent_skeleton.py) | AgentCore 에이전트 뼈대 |
| [../algorithms/pathfinder.py](../algorithms/pathfinder.py) | A* + BFS 경로탐색 알고리즘 |
| [../tools/pathfinding_tool.py](../tools/pathfinding_tool.py) | Lambda 경로탐색 Tool |

## 대회 당일 체크리스트

- [ ] `.env` 파일에 환경변수 주입 (ARN, region, account-id)
- [ ] `./deploy.sh` 동작 확인
- [ ] AgentCore 에이전트 생성 확인
- [ ] Lambda Tool 연결 확인
- [ ] Memory 저장/조회 테스트
- [ ] Claude Code → AWS CLI 접근 확인
