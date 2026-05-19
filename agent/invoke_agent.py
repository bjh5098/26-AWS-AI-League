"""
invoke_agent.py — AgentCore 에이전트 실행 래퍼

대회 당일 이 파일로 에이전트 실행 + 응답 파싱.
"""

import os
import boto3
import uuid
from typing import Optional


def invoke_agent(
    input_text: str,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_alias_id: Optional[str] = None,
) -> dict:
    """
    AgentCore 에이전트 호출.

    Args:
        input_text: 에이전트에게 전달할 지시문
        session_id: 세션 ID (없으면 자동 생성). 같은 세션 유지 시 재사용.
        agent_id: 에이전트 ID (.env의 AGENT_ID)
        agent_alias_id: 에이전트 별칭 ID (.env의 AGENT_ALIAS_ID)

    Returns:
        {"response": str, "trace": list, "session_id": str}
    """
    _agent_id = agent_id or os.environ['AGENT_ID']
    _alias_id = agent_alias_id or os.environ['AGENT_ALIAS_ID']
    _session_id = session_id or str(uuid.uuid4())

    client = boto3.client(
        'bedrock-agent-runtime',
        region_name=os.environ.get('AWS_REGION', 'ap-northeast-2')
    )

    response = client.invoke_agent(
        agentId=_agent_id,
        agentAliasId=_alias_id,
        sessionId=_session_id,
        inputText=input_text,
        enableTrace=True,
        memoryId=os.environ.get('MEMORY_ID', ''),
    )

    # 스트리밍 응답 수집
    output_text = ''
    trace_events = []

    for event in response['completion']:
        if 'chunk' in event:
            output_text += event['chunk']['bytes'].decode('utf-8')
        if 'trace' in event:
            trace = event['trace'].get('trace', {})
            if trace:
                trace_events.append(trace)

    return {
        'response': output_text,
        'trace': trace_events,
        'session_id': _session_id,
    }


def run_game_loop(max_turns: int = 20):
    """
    게임 루프: 에이전트가 자율적으로 코인 수집.
    에이전트가 '완료' 또는 '코인 없음'을 응답할 때까지 반복.
    """
    session_id = str(uuid.uuid4())
    print(f"게임 시작 (session: {session_id})")
    print("=" * 50)

    # 초기 지시
    initial_prompt = """
게임을 시작합니다.
1. query_state(type='all')로 현재 게임 상태를 파악하세요.
2. 코인을 최대한 많이 수집하세요.
3. 각 행동 후 결과를 간략히 요약해주세요.
지금 시작하세요.
"""
    for turn in range(1, max_turns + 1):
        print(f"\n[Turn {turn}/{max_turns}]")

        prompt = initial_prompt if turn == 1 else "계속 진행하세요. 남은 코인을 수집하세요."

        result = invoke_agent(prompt, session_id=session_id)
        response = result['response']

        print(f"에이전트: {response[:300]}{'...' if len(response) > 300 else ''}")

        # 종료 조건
        done_keywords = ['모든 코인', '코인 없음', '완료', '게임 종료', '더 이상']
        if any(kw in response for kw in done_keywords):
            print(f"\n게임 완료! (Turn {turn})")
            break

    print("\n" + "=" * 50)
    print("게임 루프 종료")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'loop':
        run_game_loop()
    else:
        # 단일 호출 테스트
        result = invoke_agent("현재 게임 상태를 확인하고 첫 번째 코인을 수집하세요.")
        print(result['response'])
