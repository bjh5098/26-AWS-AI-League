"""
inspect_infra.py — 대회 당일 AWS 인프라 자동 파악 스크립트

사용법: python scripts/inspect_infra.py
결과: .env 업데이트 + infra_report.md 생성

AWS CLI access 정보를 받은 즉시 실행하면:
1. 계정 내 AgentCore 에이전트 목록 파악
2. Lambda 함수 목록 및 코드 다운로드
3. Memory, Gateway 설정 파악
4. 문제 유형 유추 및 전략 제안
"""

import boto3
import json
import os
import sys
from datetime import datetime


def main():
    print("=" * 60)
    print("AWS AI League — 인프라 자동 파악 스크립트")
    print(f"실행 시각: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

    region = os.environ.get('AWS_REGION', 'ap-northeast-2')
    report = []

    # 1. 계정 확인
    account_id = _check_account(report)

    # 2. AgentCore 에이전트 파악
    agents = _inspect_agents(region, report)

    # 3. Lambda 함수 파악
    lambdas = _inspect_lambdas(region, report)

    # 4. AgentCore Memory 파악
    _inspect_memory(region, report)

    # 5. AgentCore Gateway 파악
    _inspect_gateway(region, report)

    # 6. 문제 유형 유추
    _infer_challenge_type(agents, lambdas, report)

    # 7. .env 자동 업데이트
    _update_env(agents, lambdas, region, account_id)

    # 8. 리포트 저장
    report_path = 'infra_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"\n✓ 리포트 저장: {report_path}")
    print("✓ .env 업데이트 완료")
    print("\n다음 단계: cat infra_report.md 로 전략 확인")


def _check_account(report: list) -> str:
    report.append(f"# AWS AI League 인프라 파악 리포트")
    report.append(f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("## 1. AWS 계정 정보")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        report.append(f"- Account ID: `{account_id}`")
        report.append(f"- ARN: `{identity['Arn']}`")
        print(f"[1/6] 계정: {account_id}")
        return account_id
    except Exception as e:
        report.append(f"- ⚠ 계정 조회 실패: {e}")
        print(f"[1/6] 계정 조회 실패: {e}")
        return ''


def _inspect_agents(region: str, report: list) -> list:
    report.append("\n## 2. AgentCore 에이전트")
    agents = []
    try:
        client = boto3.client('bedrock-agent', region_name=region)
        paginator = client.get_paginator('list_agents')
        for page in paginator.paginate():
            for agent in page.get('agentSummaries', []):
                agent_id = agent['agentId']
                agent_name = agent['agentName']
                status = agent['agentStatus']

                # 상세 정보 조회
                try:
                    detail = client.get_agent(agentId=agent_id)['agent']
                    model = detail.get('foundationModel', 'unknown')
                    instruction_preview = detail.get('instruction', '')[:200]

                    # 별칭 조회
                    aliases = client.list_agent_aliases(agentId=agent_id).get('agentAliasSummaries', [])
                    alias_id = aliases[0]['agentAliasId'] if aliases else 'TSTALIASID'

                    # 액션그룹 조회 (어떤 도구를 쓰는지 파악)
                    action_groups = client.list_agent_action_groups(
                        agentId=agent_id, agentVersion='DRAFT'
                    ).get('actionGroupSummaries', [])

                    agent_info = {
                        'id': agent_id,
                        'name': agent_name,
                        'status': status,
                        'model': model,
                        'alias_id': alias_id,
                        'action_groups': [ag['actionGroupName'] for ag in action_groups],
                        'instruction_preview': instruction_preview,
                    }
                    agents.append(agent_info)

                    report.append(f"\n### {agent_name} (`{agent_id}`)")
                    report.append(f"- 상태: `{status}`")
                    report.append(f"- 모델: `{model}`")
                    report.append(f"- 별칭 ID: `{alias_id}`")
                    report.append(f"- 액션그룹: {agent_info['action_groups']}")
                    if instruction_preview:
                        report.append(f"- System Prompt 미리보기:\n  ```\n  {instruction_preview}\n  ```")

                except Exception as e:
                    report.append(f"\n### {agent_name} — 상세 조회 실패: {e}")

        print(f"[2/6] 에이전트: {len(agents)}개 발견")
        if not agents:
            report.append("- 에이전트 없음 (직접 생성 필요)")

    except Exception as e:
        report.append(f"- ⚠ 에이전트 조회 실패: {e}")
        print(f"[2/6] 에이전트 조회 실패: {e}")

    return agents


def _inspect_lambdas(region: str, report: list) -> list:
    report.append("\n## 3. Lambda 함수")
    lambdas = []
    try:
        client = boto3.client('lambda', region_name=region)
        paginator = client.get_paginator('list_functions')

        ai_league_funcs = []
        for page in paginator.paginate():
            for func in page.get('Functions', []):
                name = func['FunctionName']
                # AI League 관련 함수 필터링 (이름 패턴)
                keywords = ['agent', 'league', 'game', 'coin', 'map', 'tool', 'mcp', 'bedrock']
                if any(kw in name.lower() for kw in keywords):
                    ai_league_funcs.append(func)

        for func in ai_league_funcs:
            name = func['FunctionName']
            arn = func['FunctionArn']
            runtime = func.get('Runtime', 'unknown')
            timeout = func.get('Timeout', 3)
            memory = func.get('MemorySize', 128)

            func_info = {
                'name': name,
                'arn': arn,
                'runtime': runtime,
                'timeout': timeout,
                'memory': memory,
            }

            # 환경변수 확인 (게임 API 엔드포인트 등)
            try:
                env_vars = func.get('Environment', {}).get('Variables', {})
                func_info['env_vars'] = list(env_vars.keys())
            except Exception:
                func_info['env_vars'] = []

            lambdas.append(func_info)
            report.append(f"\n### {name}")
            report.append(f"- ARN: `{arn}`")
            report.append(f"- Runtime: `{runtime}` | Timeout: {timeout}s | Memory: {memory}MB")
            if func_info['env_vars']:
                report.append(f"- 환경변수 키: {func_info['env_vars']}")

        print(f"[3/6] Lambda: {len(lambdas)}개 발견 (AI League 관련)")
        if not lambdas:
            report.append("- AI League 관련 Lambda 없음")
            report.append("  (키워드: agent, league, game, coin, map, tool, mcp, bedrock)")

    except Exception as e:
        report.append(f"- ⚠ Lambda 조회 실패: {e}")
        print(f"[3/6] Lambda 조회 실패: {e}")

    return lambdas


def _inspect_memory(region: str, report: list):
    report.append("\n## 4. AgentCore Memory")
    try:
        client = boto3.client('bedrock-agent', region_name=region)
        memories = client.list_agent_memories if hasattr(client, 'list_agent_memories') else None

        # Memory 직접 list API가 없으므로 에이전트별로 확인
        report.append("- Memory 설정은 에이전트 상세 → memoryConfiguration 참조")
        report.append("- MEMORY_ID는 에이전트 생성 시 자동 할당 또는 별도 생성")
        print("[4/6] Memory: 에이전트 연결 정보로 확인")

    except Exception as e:
        report.append(f"- ⚠ Memory 조회 실패: {e}")


def _inspect_gateway(region: str, report: list):
    report.append("\n## 5. AgentCore Gateway")
    try:
        client = boto3.client('bedrock-agentcore-control', region_name=region)
        gateways = client.list_gateways().get('items', [])

        if gateways:
            for gw in gateways:
                report.append(f"\n### Gateway: {gw.get('name', 'unknown')}")
                report.append(f"- ID: `{gw.get('gatewayId', '')}`")
                report.append(f"- 상태: `{gw.get('status', '')}`")
                report.append(f"- 인증: `{gw.get('authorizerType', '')}`")
        else:
            report.append("- Gateway 없음")

        print(f"[5/6] Gateway: {len(gateways)}개 발견")

    except Exception as e:
        report.append(f"- ⚠ Gateway 조회 실패 (서비스 미지원 가능): {e}")
        print(f"[5/6] Gateway 조회 실패: {e}")


def _infer_challenge_type(agents: list, lambdas: list, report: list):
    report.append("\n## 6. 문제 유형 유추 및 전략 제안")

    clues = []

    # 에이전트 System Prompt에서 힌트 추출
    for agent in agents:
        prompt = agent.get('instruction_preview', '').lower()
        if any(w in prompt for w in ['map', '지도', 'grid', '격자']):
            clues.append("지도 탐색 게임")
        if any(w in prompt for w in ['coin', '코인', 'treasure', '보물']):
            clues.append("코인/보물 수집")
        if any(w in prompt for w in ['memory', '기억', 'hint', '힌트']):
            clues.append("Memory 활용 필수")

    # Lambda 함수명에서 힌트 추출
    for func in lambdas:
        name = func['name'].lower()
        if any(w in name for w in ['path', 'navigate', 'move']):
            clues.append("경로 탐색 Tool 존재")
        if any(w in name for w in ['collect', 'coin', 'pick']):
            clues.append("코인 수집 Tool 존재")
        if any(w in name for w in ['state', 'status', 'query']):
            clues.append("상태 조회 Tool 존재")
        if any(w in name for w in ['hint', 'clue', 'secret']):
            clues.append("힌트 Tool 존재 — Memory에 저장 필수")

    clues = list(set(clues))

    if clues:
        report.append("\n### 분석 결과")
        for clue in clues:
            report.append(f"- ✓ {clue}")
    else:
        report.append("- 분석 단서 부족 — 에이전트 System Prompt 직접 확인 권장")

    report.append("\n### 추천 전략")
    report.append("1. `query_state(type='all')` 로 게임 전체 상태 파악")
    report.append("2. Memory에 초기 상태 저장")
    report.append("3. `find_nearest_coin` → `find_path` → `collect_coin` 루프 실행")
    report.append("4. 각 행동 후 Memory 업데이트")
    report.append("5. 힌트 발견 시 즉시 Memory 저장 + 전략 재조정")

    report.append("\n### 빠른 시작 명령")
    report.append("```bash")
    report.append("# 1. 인프라 파악 결과 확인")
    report.append("cat infra_report.md")
    report.append("")
    report.append("# 2. .env 확인 및 수정")
    report.append("cat .env")
    report.append("")
    report.append("# 3. Lambda 배포 테스트")
    report.append("./deploy.sh all")
    report.append("")
    report.append("# 4. 에이전트 실행")
    report.append("python agent/invoke_agent.py")
    report.append("```")

    print(f"[6/6] 유추된 문제 유형: {clues if clues else '분석 단서 부족'}")


def _update_env(agents: list, lambdas: list, region: str, account_id: str):
    """파악한 인프라 정보로 .env 자동 업데이트."""
    updates = {}

    if region:
        updates['AWS_REGION'] = region
    if account_id:
        updates['AWS_ACCOUNT_ID'] = account_id

    # 첫 번째 에이전트 정보 자동 채우기
    if agents:
        agent = agents[0]
        updates['AGENT_ID'] = agent['id']
        updates['AGENT_ALIAS_ID'] = agent.get('alias_id', '')

    # Lambda ARN 자동 매핑
    for func in lambdas:
        name = func['name'].lower()
        if any(w in name for w in ['path', 'navigate']):
            updates['LAMBDA_PATHFINDING_ARN'] = func['arn']
        elif any(w in name for w in ['coin', 'collect']):
            updates['LAMBDA_COIN_COLLECTOR_ARN'] = func['arn']
        elif any(w in name for w in ['state', 'query', 'status']):
            updates['LAMBDA_STATE_QUERY_ARN'] = func['arn']

    if not updates:
        return

    # .env 파일 업데이트 (없으면 .env.template 복사)
    env_path = '.env'
    if not os.path.exists(env_path):
        if os.path.exists('.env.template'):
            import shutil
            shutil.copy('.env.template', env_path)
        else:
            with open(env_path, 'w') as f:
                f.write("# Auto-generated by inspect_infra.py\n")

    # 기존 .env 읽기
    with open(env_path, 'r') as f:
        lines = f.readlines()

    # 값 업데이트
    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0]
            if key in updates and updates[key]:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # 새 키 추가
    for key, val in updates.items():
        if key not in updated_keys and val:
            new_lines.append(f"{key}={val}\n")

    with open(env_path, 'w') as f:
        f.writelines(new_lines)


if __name__ == '__main__':
    main()
