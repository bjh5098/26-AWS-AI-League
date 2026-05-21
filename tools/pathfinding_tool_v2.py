"""
pathfinding_tool_v2.py — Pathfinding Lambda (클러스터 기반 최적 경로)

맵 셀 키:
  c1: Violent Violet (+400, 가드레일 챌린지)
  c2: Blue Brain (+600, 코드 실행)
  c3: Memento (+550, 기억력)
  c4: Dark Prophet (+800, 웹 검색)
  c5: Bonehead (+250, 간단 질문)
  c6: Boss (+1000, 모든 스킬)
  c7: 코인 (+250, 퀴즈 없음)
  c8: 스파이크 (-1 생명, 회피 필수)
  c18: 의료 API (+500)
  c30: 빨간 문 (+1000, 열쇠 없으면 -5 생명)
  c40: 빨간 열쇠 (+50, c30 전에 반드시 방문)
  treasure: 최종 목표
"""
import json
import re
from collections import deque

DIRECTIONS = [(-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")]
AVOID_CELLS = {"wall", "c8", "treasure"}

TARGET_CELLS = {'c7', 'c4', 'c2', 'c3', 'c18', 'c1', 'c5', 'c6'}


def _parse_start(pos):
    try:
        if isinstance(pos, (list, tuple)):
            if len(pos) == 1:
                return _parse_start(pos[0])
            if len(pos) >= 2:
                a = re.sub(r'[^A-Za-z0-9]', '', str(pos[0]))
                b = re.sub(r'[^A-Za-z0-9]', '', str(pos[1]))
                if a.isalpha():
                    return (int(b) - 1, ord(a.upper()) - ord('A'))
                return (int(a), int(b))
        s = re.sub(r'[^A-Za-z0-9]', '', str(pos))
        m = re.match(r'([A-Za-z])(\d+)', s)
        if m:
            return (int(m.group(2)) - 1, ord(m.group(1).upper()) - ord('A'))
        nums = re.findall(r'\d+', s)
        if len(nums) >= 2:
            return (int(nums[0]), int(nums[1]))
    except Exception:
        pass
    return (0, 0)


def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event and isinstance(event['body'], str) else event

        game_map = body.get('game_map', [])

        if game_map:
            max_cols = max(len(row) for row in game_map)
            game_map = [row + ['normal'] * (max_cols - len(row)) for row in game_map]

        map_config = body.get('map_config', {})
        player_start = map_config.get('playerStart') or body.get('playerStart') or {}
        if isinstance(player_start, str):
            start_pos = _parse_start(player_start)
        elif isinstance(player_start, dict) and player_start:
            start_pos = (player_start.get('row', 0), player_start.get('col', 0))
        else:
            raw = body.get('start_pos') or body.get('start') or body.get('position') or [0, 0]
            start_pos = _parse_start(raw)

        if not game_map:
            return _err(400, 'Missing game_map')

        rows, cols = len(game_map), len(game_map[0])
        if start_pos[0] >= rows or start_pos[1] >= cols:
            start_pos = (0, 0)

        treasure = next(
            ((r, c) for r in range(rows) for c in range(cols) if game_map[r][c] == 'treasure'),
            None
        )
        if not treasure:
            return _err(400, 'No treasure found on map')

        strategy = str(body.get('strategy', 'smart')).lower().strip()
        if 'key' in strategy or 'chain' in strategy:
            strategy = 'key_chain'
        elif 'max' in strategy:
            strategy = 'smart'
        elif 'all' in strategy or 'challenge' in strategy:
            strategy = 'all_challenges'
        elif 'safe' in strategy:
            strategy = 'safe_coins'
        elif 'avoid' in strategy or 'spike' in strategy:
            strategy = 'avoid_spikes'
        elif 'coin' in strategy:
            strategy = 'get_coins'
        elif 'swift' in strategy or 'fast' in strategy:
            strategy = 'swift'
        else:
            strategy = 'smart'

        map_info = _analyze_map(game_map, rows, cols)

        fn_map = {
            'smart': smart_path,
            'key_chain': key_chain_path,
            'avoid_spikes': avoid_spikes_path,
            'safe_coins': safe_coins_path,
            'all_challenges': all_challenges_path,
            'get_coins': get_coins_path,
            'swift': swift_path,
        }
        path = fn_map.get(strategy, smart_path)(game_map, rows, cols, start_pos, treasure)

        result = {
            'path': path,
            'steps': len(path),
            'start_position': list(start_pos),
            'strategy': strategy,
            'map_analysis': map_info,
        }
        return {'statusCode': 200, 'body': json.dumps(result)}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return _err(500, str(e))


def _err(code, msg):
    return {'statusCode': code, 'body': json.dumps({'error': msg})}


def _analyze_map(game_map, rows, cols):
    info = {}
    for r in range(rows):
        for c in range(cols):
            cell = game_map[r][c]
            if cell not in ('normal', 'wall', 'start'):
                if cell not in info:
                    info[cell] = []
                info[cell].append([r, c])
    return info


def _bfs(game_map, rows, cols, start, goal, blocked=None):
    if blocked is None:
        blocked = {'wall'}
    else:
        blocked = set(blocked) | {'wall'}
    queue = deque([(start[0], start[1], [])])
    visited = {(start[0], start[1])}
    while queue:
        r, c, path = queue.popleft()
        if (r, c) == goal:
            return path
        for dr, dc, move in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and game_map[nr][nc] not in blocked
                    and (nr, nc) not in visited):
                visited.add((nr, nc))
                queue.append((nr, nc, path + [move]))
    return None


def _bfs_dist(game_map, rows, cols, start, goal, blocked=None):
    p = _bfs(game_map, rows, cols, start, goal, blocked)
    return len(p) if p is not None else 9999


def smart_path(game_map, rows, cols, start, treasure):
    """
    Top-first 전략: 시작점 근처(상단) 먼저 수집 → c40 → 하단 수집 → c30 → treasure
    모든 타겟 방문, c8 회피, c40→c30 순서 보장, treasure 맨 마지막
    """
    board = [row[:] for row in game_map]
    r, c = start
    full_path = []

    c40_pos = next(((ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c40'), None)
    c30_pos = next(((ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c30'), None)

    remaining = {}
    for ri in range(rows):
        for ci in range(cols):
            if board[ri][ci] in TARGET_CELLS:
                remaining[(ri, ci)] = board[ri][ci]

    # c40 미방문 상태에서는 c30도 회피 (통과 시 챌린지 발동 → 열쇠 없으면 -5생명)
    avoid_before_key = AVOID_CELLS | ({'c30'} if c30_pos else set())

    def visit(pos, blocked):
        nonlocal r, c
        p = _bfs(board, rows, cols, (r, c), pos, blocked)
        if p is None:
            p = _bfs(board, rows, cols, (r, c), pos, blocked - {'c8'})
        if p is not None:
            full_path.extend(p)
            r, c = pos
            board[r][c] = 'normal'
            return True
        return False

    def greedy_nearest(targets, blocked):
        while targets:
            best, best_dist = None, 9999
            for pos in list(targets.keys()):
                p = _bfs(board, rows, cols, (r, c), pos, blocked)
                if p is None:
                    p = _bfs(board, rows, cols, (r, c), pos, blocked - {'c8'})
                if p and len(p) < best_dist:
                    best, best_dist = pos, len(p)
            if best is None:
                break
            targets.pop(best)
            remaining.pop(best, None)
            visit(best, blocked)

    # 타겟 분류: c30 없이 도달 가능 vs c30 통과 필수
    before_key_targets = {}
    after_key_targets = {}
    for pos, cell in remaining.items():
        if pos == c30_pos:
            continue
        p = _bfs(board, rows, cols, start, pos, avoid_before_key)
        if p is not None:
            before_key_targets[pos] = cell
        else:
            after_key_targets[pos] = cell

    # Phase 1: c30 없이 도달 가능한 타겟 수집
    greedy_nearest(before_key_targets, avoid_before_key)

    # Phase 2: c40 방문
    if c40_pos:
        remaining.pop(c40_pos, None)
        visit(c40_pos, avoid_before_key)

    # Phase 3: c30 통과 필수 타겟 수집 (이제 c40 획득 후 c30 통과 안전)
    greedy_nearest(after_key_targets, AVOID_CELLS)

    # Phase 4: 혹시 남은 타겟 처리
    leftover = {pos: cell for pos, cell in remaining.items() if pos != c30_pos}
    greedy_nearest(leftover, AVOID_CELLS)

    # Phase 5: c30
    if c30_pos and board[c30_pos[0]][c30_pos[1]] == 'c30':
        visit(c30_pos, AVOID_CELLS)

    # Phase 6: treasure (맨 마지막)
    p = _bfs(board, rows, cols, (r, c), treasure, AVOID_CELLS)
    if p is None:
        p = _bfs(board, rows, cols, (r, c), treasure, {'wall'}) or []
    full_path.extend(p)
    return full_path


def key_chain_path(game_map, rows, cols, start, treasure):
    board = [row[:] for row in game_map]
    r, c = start
    full_path = []

    c40_pos = next(((ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c40'), None)
    c30_pos = next(((ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c30'), None)

    if c40_pos:
        p = _bfs(board, rows, cols, (r, c), c40_pos, AVOID_CELLS)
        if p is None:
            p = _bfs(board, rows, cols, (r, c), c40_pos, {'wall'}) or []
        full_path.extend(p)
        r, c = c40_pos
        board[r][c] = 'normal'

    if c30_pos:
        p = _bfs(board, rows, cols, (r, c), c30_pos, AVOID_CELLS)
        if p is None:
            p = _bfs(board, rows, cols, (r, c), c30_pos, {'wall'}) or []
        full_path.extend(p)
        r, c = c30_pos
        board[r][c] = 'normal'

    p = _bfs(board, rows, cols, (r, c), treasure, AVOID_CELLS)
    if p is None:
        p = _bfs(board, rows, cols, (r, c), treasure, {'wall'}) or []
    full_path.extend(p)
    return full_path


def avoid_spikes_path(game_map, rows, cols, start, treasure):
    p = _bfs(game_map, rows, cols, start, treasure, AVOID_CELLS)
    return p if p is not None else swift_path(game_map, rows, cols, start, treasure)


def safe_coins_path(game_map, rows, cols, start, treasure):
    board = [row[:] for row in game_map]
    coins = [(ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c7']
    path, pos, board = _greedy_cluster(board, rows, cols, start, coins, AVOID_CELLS)
    p = _bfs(board, rows, cols, pos, treasure, AVOID_CELLS)
    if p is None:
        p = _bfs(board, rows, cols, pos, treasure, {'wall'}) or []
    return path + p


def all_challenges_path(game_map, rows, cols, start, treasure):
    CHALLENGE = {'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c18'}
    board = [row[:] for row in game_map]
    targets = [(ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] in CHALLENGE]
    path, pos, board = _greedy_cluster(board, rows, cols, start, targets, AVOID_CELLS)
    p = _bfs(board, rows, cols, pos, treasure, AVOID_CELLS)
    if p is None:
        p = _bfs(board, rows, cols, pos, treasure, {'wall'}) or []
    return path + p


def swift_path(game_map, rows, cols, start, treasure):
    return _bfs(game_map, rows, cols, start, treasure, {'wall'}) or []


def get_coins_path(game_map, rows, cols, start, treasure):
    board = [row[:] for row in game_map]
    coins = [(ri, ci) for ri in range(rows) for ci in range(cols) if board[ri][ci] == 'c7']
    path, pos, board = _greedy_cluster(board, rows, cols, start, coins, {'wall'})
    p = _bfs(board, rows, cols, pos, treasure, {'wall'}) or []
    return path + p


def _greedy_cluster(game_map, rows, cols, start, targets, blocked=None):
    if blocked is None:
        blocked = {'wall'}
    board = [row[:] for row in game_map]
    r, c = start
    full_path = []
    remaining = list(targets)
    CLUSTER_RADIUS = 4

    while remaining:
        nearby = []
        far_best, far_best_dist = None, 9999

        for target in remaining:
            p = _bfs(board, rows, cols, (r, c), target, blocked)
            if p is None:
                p = _bfs(board, rows, cols, (r, c), target, {'wall'})
            if p is None:
                continue
            dist = len(p)
            if dist <= CLUSTER_RADIUS:
                nearby.append((target, dist, p))
            elif dist < far_best_dist:
                far_best, far_best_dist = target, dist

        if nearby:
            nearby.sort(key=lambda x: x[1])
            target, _, p = nearby[0]
            full_path.extend(p)
            r, c = target
            board[r][c] = 'normal'
            remaining.remove(target)
        elif far_best:
            p = _bfs(board, rows, cols, (r, c), far_best, blocked)
            if p is None:
                p = _bfs(board, rows, cols, (r, c), far_best, {'wall'})
            if p:
                full_path.extend(p)
                r, c = far_best
                board[r][c] = 'normal'
            remaining.remove(far_best)
        else:
            break

    return full_path, (r, c), board
