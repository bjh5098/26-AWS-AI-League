"""
pathfinding_tool.py — Lambda Tool: 경로탐색

AgentCore가 호출하는 Lambda 핸들러.
find_path: 현재 위치 → 목표 위치 최단 경로 반환
"""

import json
import sys
import os

# Lambda 환경에서 algorithms/ 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathfinder import astar, bfs, find_nearest_coin


def lambda_handler(event, context):
    action_group = event.get('actionGroup', '')
    function_name = event.get('function', '')
    params = {p['name']: p['value'] for p in event.get('parameters', [])}

    try:
        if function_name == 'find_path':
            result = handle_find_path(params)
        elif function_name == 'find_nearest_coin':
            result = handle_find_nearest_coin(params)
        else:
            result = {'error': f'Unknown function: {function_name}'}
    except Exception as e:
        result = {'error': str(e), 'function': function_name}

    return _build_response(action_group, function_name, result)


def handle_find_path(params: dict) -> dict:
    """A*로 start → goal 최단 경로 계산."""
    current_x = int(params.get('current_x', 0))
    current_y = int(params.get('current_y', 0))
    target_x  = int(params.get('target_x', 0))
    target_y  = int(params.get('target_y', 0))

    # 지도 파라미터 (JSON 문자열로 전달될 수 있음)
    grid_raw = params.get('grid', '[]')
    if isinstance(grid_raw, str):
        try:
            grid = json.loads(grid_raw)
        except json.JSONDecodeError:
            grid = []
    else:
        grid = grid_raw

    if not grid:
        # 지도 없으면 직선 이동 경로 반환 (단순화)
        path = _straight_path((current_x, current_y), (target_x, target_y))
        return {
            'path': path,
            'cost': len(path) - 1,
            'algorithm': 'straight',
            'found': True,
            'message': '지도 정보 없음: 직선 경로 반환'
        }

    result = astar(grid, (current_x, current_y), (target_x, target_y))
    result['path'] = [list(p) for p in result['path']]  # tuple → list (JSON 직렬화)
    return result


def handle_find_nearest_coin(params: dict) -> dict:
    """BFS로 가장 가까운 코인 탐색."""
    current_x = int(params.get('current_x', 0))
    current_y = int(params.get('current_y', 0))

    grid_raw = params.get('grid', '[]')
    if isinstance(grid_raw, str):
        try:
            grid = json.loads(grid_raw)
        except json.JSONDecodeError:
            grid = []
    else:
        grid = grid_raw

    if not grid:
        return {'error': '지도 정보가 필요합니다.', 'found': False}

    result = find_nearest_coin(grid, (current_x, current_y))
    result['path'] = [list(p) for p in result.get('path', [])]
    if result.get('target'):
        result['target'] = list(result['target'])
    return result


def _straight_path(start, goal):
    """지도 없을 때 직선(맨해튼) 경로."""
    path = [list(start)]
    x, y = start
    tx, ty = goal
    while x != tx:
        x += 1 if tx > x else -1
        path.append([x, y])
    while y != ty:
        y += 1 if ty > y else -1
        path.append([x, y])
    return path


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
