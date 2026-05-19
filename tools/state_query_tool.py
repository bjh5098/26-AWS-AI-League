"""
state_query_tool.py — Lambda Tool: 게임 상태 조회

query_state: 현재 게임 상태(위치, 점수, 지도, 남은 코인) 조회
"""

import json
import os
import urllib.request


def lambda_handler(event, context):
    action_group = event.get('actionGroup', '')
    function_name = event.get('function', '')
    params = {p['name']: p['value'] for p in event.get('parameters', [])}

    try:
        if function_name == 'query_state':
            result = handle_query_state(params)
        else:
            result = {'error': f'Unknown function: {function_name}'}
    except Exception as e:
        result = {'error': str(e)}

    return _build_response(action_group, function_name, result)


def handle_query_state(params: dict) -> dict:
    """게임 상태 조회."""
    query_type = params.get('query_type', 'all')

    game_endpoint = os.environ.get('GAME_API_ENDPOINT', '')
    session_id = os.environ.get('GAME_SESSION_ID', '')

    if game_endpoint:
        try:
            url = f"{game_endpoint}/state?session_id={session_id}&type={query_type}"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {'error': str(e), 'query_type': query_type}

    # 게임 API 미설정 시 시뮬레이션 응답
    mock_states = {
        'map': {
            'grid': [[0,0,2,0,1],[0,1,0,2,0],[0,0,0,0,0],[2,0,1,0,2],[0,0,0,0,0]],
            'width': 5, 'height': 5,
            'description': '5x5 테스트 지도. 0=이동가능, 1=장애물, 2=코인'
        },
        'score': {
            'current_score': 0,
            'coins_collected': 0,
            'time_remaining': 300
        },
        'coins_remaining': {
            'positions': [[0,2],[1,3],[3,0],[3,4]],
            'count': 4
        },
        'agent_status': {
            'position': [0, 0],
            'direction': 'none',
            'status': 'idle'
        }
    }

    if query_type == 'all':
        return {k: v for k, v in mock_states.items()}
    return mock_states.get(query_type, {'error': f'Unknown query_type: {query_type}'})


def _build_response(action_group, function_name, result):
    return {
        'response': {
            'actionGroup': action_group,
            'function': function_name,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {'body': json.dumps(result, ensure_ascii=False)}
                }
            }
        }
    }
