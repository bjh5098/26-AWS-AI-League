"""
agent_skeleton.py — AgentCore 에이전트 생성 및 설정

대회 당일: .env 파일에 환경변수 채우고 create_agent() 실행
"""

import os
import time
import boto3
from typing import Optional


def get_agent_client():
    return boto3.client('bedrock-agent', region_name=os.environ.get('AWS_REGION', 'ap-northeast-2'))


def create_agent(agent_name: str = 'ai-league-agent') -> dict:
    """
    AgentCore 에이전트 생성 + Lambda Tool 연결 + prepare

    Returns:
        {"agent_id": str, "agent_alias_id": str}
    """
    client = get_agent_client()

    # 1. 에이전트 생성
    print(f"[1/4] 에이전트 생성 중: {agent_name}")
    resp = client.create_agent(
        agentName=agent_name,
        foundationModel='anthropic.claude-3-haiku-20240307-v1:0',  # 속도 우선
        instruction=open(os.path.join(os.path.dirname(__file__), 'system_prompt.txt')).read(),
        agentResourceRoleArn=os.environ['AGENT_ROLE_ARN'],
        idleSessionTTLInSeconds=600,
    )
    agent_id = resp['agent']['agentId']
    print(f"    agent_id: {agent_id}")

    # 2. Lambda Tool 연결 (경로탐색 + 코인수집 + 상태조회)
    print("[2/4] Lambda Tool 연결 중...")
    _register_tools(client, agent_id)

    # 3. prepare
    print("[3/4] 에이전트 준비 중...")
    client.prepare_agent(agentId=agent_id)
    _wait_for_status(client, agent_id, 'PREPARED')

    # 4. 별칭 생성
    print("[4/4] 별칭 생성 중...")
    alias_resp = client.create_agent_alias(
        agentId=agent_id,
        agentAliasName='competition',
    )
    agent_alias_id = alias_resp['agentAlias']['agentAliasId']
    print(f"    alias_id: {agent_alias_id}")

    print(f"\n✓ 에이전트 준비 완료!")
    print(f"  AGENT_ID={agent_id}")
    print(f"  AGENT_ALIAS_ID={agent_alias_id}")
    print(f"  .env 파일에 위 값을 저장하세요.")

    return {"agent_id": agent_id, "agent_alias_id": agent_alias_id}


def _register_tools(client, agent_id: str):
    """Lambda Tool 3개를 AgentCore에 등록."""

    tools = [
        {
            'name': 'MapNavigation',
            'lambda_env': 'LAMBDA_PATHFINDING_ARN',
            'functions': [
                {
                    'name': 'find_path',
                    'description': '현재 위치에서 목표 위치까지 장애물을 피한 최단 경로를 반환합니다. 이동 전에 반드시 호출하세요.',
                    'parameters': {
                        'current_x': {'type': 'integer', 'description': '현재 X 좌표', 'required': True},
                        'current_y': {'type': 'integer', 'description': '현재 Y 좌표', 'required': True},
                        'target_x':  {'type': 'integer', 'description': '목표 X 좌표', 'required': True},
                        'target_y':  {'type': 'integer', 'description': '목표 Y 좌표', 'required': True},
                    }
                }
            ]
        },
        {
            'name': 'CoinCollection',
            'lambda_env': 'LAMBDA_COIN_COLLECTOR_ARN',
            'functions': [
                {
                    'name': 'collect_coin',
                    'description': '현재 위치의 코인을 수집합니다. 코인이 있는 위치에 도달했을 때만 호출하세요.',
                    'parameters': {
                        'position_x': {'type': 'integer', 'description': '현재 X 좌표', 'required': True},
                        'position_y': {'type': 'integer', 'description': '현재 Y 좌표', 'required': True},
                    }
                }
            ]
        },
        {
            'name': 'GameState',
            'lambda_env': 'LAMBDA_STATE_QUERY_ARN',
            'functions': [
                {
                    'name': 'query_state',
                    'description': '현재 게임 상태(위치, 점수, 지도, 남은 코인)를 조회합니다.',
                    'parameters': {
                        'query_type': {
                            'type': 'string',
                            'description': '조회 유형: map | score | coins_remaining | agent_status | all',
                            'required': True
                        }
                    }
                }
            ]
        },
    ]

    for tool in tools:
        lambda_arn = os.environ.get(tool['lambda_env'], '')
        if not lambda_arn:
            print(f"    ⚠ {tool['name']}: {tool['lambda_env']} 환경변수 없음 (스킵)")
            continue

        client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=tool['name'],
            actionGroupExecutor={'lambda': lambda_arn},
            functionSchema={'functions': [
                {
                    'name': f['name'],
                    'description': f['description'],
                    'parameters': f['parameters'],
                }
                for f in tool['functions']
            ]}
        )
        print(f"    ✓ {tool['name']} 등록 완료")


def _wait_for_status(client, agent_id: str, target_status: str, timeout: int = 60):
    """에이전트 상태가 target_status가 될 때까지 대기."""
    start = time.time()
    while time.time() - start < timeout:
        status = client.get_agent(agentId=agent_id)['agent']['agentStatus']
        if status == target_status:
            return
        if 'FAILED' in status:
            raise RuntimeError(f"에이전트 상태 오류: {status}")
        time.sleep(2)
    raise TimeoutError(f"{timeout}초 내에 {target_status} 상태 미달성")


if __name__ == '__main__':
    # 대회 당일 실행: python agent/agent_skeleton.py
    result = create_agent()
    print(f"\n.env에 추가할 내용:")
    print(f"AGENT_ID={result['agent_id']}")
    print(f"AGENT_ALIAS_ID={result['agent_alias_id']}")
