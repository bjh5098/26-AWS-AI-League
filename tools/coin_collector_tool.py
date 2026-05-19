"""
coin_collector_tool.py — Lambda Tool: 코인 수집

collect_coin: 현재 위치의 코인을 수집하고 결과 반환
"""

import json


def lambda_handler(event, context):
    action_group = event.get('actionGroup', '')
    function_name = event.get('function', '')
    params = {p['name']: p['value'] for p in event.get('parameters', [])}

    try:
        if function_name == 'collect_coin':
            result = handle_collect_coin(params)
        else:
            result = {'error': f'Unknown function: {function_name}'}
    except Exception as e:
        result = {'error': str(e)}

    return _build_response(action_group, function_name, result)


def handle_collect_coin(params: dict) -> dict:
    """코인 수집 처리."""
    position_x = int(params.get('position_x', 0))
    position_y = int(params.get('position_y', 0))

    # 게임 API 호출 (실제 대회 환경에서 채워넣기)
    # 여기서는 게임 환경 API를 호출하는 패턴 제공
    import os
    import urllib.request

    game_endpoint = os.environ.get('GAME_API_ENDPOINT', '')
    session_id = os.environ.get('GAME_SESSION_ID', '')

    if game_endpoint:
        try:
            payload = json.dumps({
                'action': 'collect_coin',
                'session_id': session_id,
                'position': {'x': position_x, 'y': position_y}
            }).encode()

            req = urllib.request.Request(
                f"{game_endpoint}/collect",
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'position': [position_x, position_y]
            }

    # 게임 API 미설정 시 시뮬레이션 응답
    return {
        'success': True,
        'coins_collected': 1,
        'position': [position_x, position_y],
        'message': f'({position_x},{position_y}) 위치 코인 수집 완료'
    }


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
