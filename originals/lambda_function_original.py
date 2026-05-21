"""
원본 pathfinding Lambda 코드 (대회 제공 원본, 복구용)
출처: AI League 대회 페이지 "원본 코드" 섹션
"""
import json
from collections import deque

CELL_POINTS = {"c7": 250}
COLLECTIBLE_COINS = {"c7"}
DIRECTIONS = [(-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")]


def lambda_handler(event, context):
    """
    AWS Lambda function for pathfinding using Swift path strategy by default
    Handles both API Gateway format and direct AgentCore Gateway format

    ## Map Definitions
        - "wall": non-walkable cell
        - "treasure": target cell to reach
        - "normal": walkable cell with no special properties
        - "start": the start cell of your avatar, acts as normal cell
        - "c1": Violent Violet guardrail challenge
        - "c2": Blue Brain code execution challenge
        - "c3": Memento memory challenge
        - "c4": Dark Prophet web scraping challenge
        - "c5": Bonehead challenge, simple question that requires little skill
        - "c6": Boss Challenge, most requires all skills
        - "c7": Coins that increase score when collected with no challenge
        - "c8": Spikes that reduce health traveled over

    ## Map JSON Example
    [
        ["start","normal","c5","normal","normal","normal","c5","normal","normal","c1"],
        ["normal","wall","wall","normal","wall","wall","wall","wall","wall","normal"],
        ["c8","wall","wall","c5","wall","c7","c7","c7","wall","c3"],
        ["normal","wall","c8","normal","wall","c8","wall","c8","wall","normal"],
        ["normal","wall","c7","normal","wall","normal","normal","normal","wall","normal"],
        ["c5","wall","c7","normal","wall","c5","wall","normal","wall","c5"],
        ["normal","wall","c7","normal","wall","normal","wall","normal","wall","normal"],
        ["c1","wall","c8","normal","c2","normal","wall","normal","c4","normal"],
        ["normal","wall","wall","wall","wall","wall","wall","normal","normal","c7"],
        ["c7","normal","c3","normal","c4","normal","c2","normal","treasure","normal"]
    ]

    ## Pathfinding Lambda with strategy selection.

    Usage: Use strategy get_coins

    Strategies:
      swift     - BFS shortest path to treasure (default)
      get_coins - Greedily collect c7 coins on the way to treasure
    """

    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        print(f"DEBUG: Received event: {body}")
        game_map = body.get('game_map', [])
        start_pos = body.get('start_pos', [0, 0])
        strategy = body.get('strategy', 'swift')

        if not game_map:
            return _err(400, 'Missing game_map')

        rows, cols = len(game_map), len(game_map[0])
        treasure = None
        for r in range(rows):
            for c in range(cols):
                if game_map[r][c] == 'treasure':
                    treasure = (r, c)
                    break
            if treasure:
                break

        if not treasure:
            return _err(400, 'No treasure found on map')

        if strategy == 'get_coins':
            path = get_coins_path(game_map, rows, cols, tuple(start_pos), treasure)
        else:
            path = swift_path(game_map, rows, cols, tuple(start_pos), treasure)

        result = {'path': path, 'steps': len(path), 'start_position': start_pos}
        print(f"RESULT: strategy={strategy} steps={len(path)}")
        return {'statusCode': 200, 'body': json.dumps(result)}

    except Exception as e:
        print(f"ERROR: {e}")
        return _err(500, str(e))


def _err(code, msg):
    return {'statusCode': code, 'body': json.dumps({'error': msg})}


def _bfs(game_map, rows, cols, start, goal):
    """BFS shortest path between two points."""
    queue = deque([(start[0], start[1], [])])
    visited = {(start[0], start[1])}
    while queue:
        r, c, path = queue.popleft()
        if (r, c) == goal:
            return path
        for dr, dc, move in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and game_map[nr][nc] != 'wall' and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, path + [move]))
    return None


def swift_path(game_map, rows, cols, start, treasure):
    """BFS shortest path to treasure."""
    return _bfs(game_map, rows, cols, start, treasure) or []


def get_coins_path(game_map, rows, cols, start, treasure):
    """Greedily BFS to best coins-per-step c7 cell, then BFS to treasure."""
    board = [row[:] for row in game_map]
    r, c = start
    full_path = []

    for _ in range(50):
        # BFS to find reachable coins
        queue = deque([(r, c, [])])
        visited = {(r, c)}
        targets = []
        while queue:
            cr, cc, p = queue.popleft()
            if board[cr][cc] in COLLECTIBLE_COINS and (cr, cc) != (r, c):
                dist = max(len(p), 1)
                targets.append((dist, p, cr, cc))  # closest coin first
            for dr, dc, move in DIRECTIONS:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != 'wall' and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc, p + [move]))

        if not targets:
            break
        targets.sort()
        _, path_to, r, c = targets[0]
        full_path.extend(path_to)
        board[r][c] = 'normal'

    # BFS to treasure from current position
    path_end = _bfs(board, rows, cols, (r, c), treasure)
    if path_end is not None:
        full_path.extend(path_end)
        return full_path
    return swift_path(game_map, rows, cols, start, treasure)
