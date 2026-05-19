"""
pathfinder.py — AWS AI League 경로탐색 알고리즘

A*, BFS, 탐욕적 코인 수집 경로 계산.
순수 Python (numpy/scipy 불필요) — Lambda 환경 호환.
"""

import heapq
from collections import deque
from typing import List, Tuple, Optional, Dict, Any


def astar(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    obstacles: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, Any]:
    """
    A* 알고리즘으로 start → goal 최단 경로 탐색.

    Args:
        grid: 2D 격자 (0=이동가능, 1=장애물, 2=코인)
        start: (x, y) 시작 위치
        goal: (x, y) 목표 위치
        obstacles: 추가 장애물 목록 (동적 장애물용)

    Returns:
        {"path": [(x,y),...], "cost": int, "algorithm": "a_star", "found": bool}
    """
    if not grid or start == goal:
        return {"path": [start], "cost": 0, "algorithm": "a_star", "found": True}

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    extra_obstacles = set(obstacles) if obstacles else set()

    def is_passable(x: int, y: int) -> bool:
        if x < 0 or x >= cols or y < 0 or y >= rows:
            return False
        if (x, y) in extra_obstacles:
            return False
        return grid[y][x] != 1

    def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_heap: List[Tuple[int, Tuple[int, int]]] = []
    heapq.heappush(open_heap, (0, start))
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], int] = {start: 0}
    f_score: Dict[Tuple[int, int], int] = {start: heuristic(start, goal)}

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return {"path": path, "cost": len(path) - 1, "algorithm": "a_star", "found": True}

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if not is_passable(neighbor[0], neighbor[1]):
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score[neighbor], neighbor))

    return {"path": [], "cost": -1, "algorithm": "a_star", "found": False}


def bfs(
    grid: List[List[int]],
    start: Tuple[int, int],
    obstacles: Optional[List[Tuple[int, int]]] = None,
    target_value: int = 2
) -> Dict[str, Any]:
    """
    BFS로 가장 가까운 target_value 셀(기본: 코인=2) 탐색.
    목표가 없으면 미방문 영역 탐색.

    Args:
        grid: 2D 격자
        start: (x, y) 시작 위치
        obstacles: 추가 장애물
        target_value: 찾을 셀 값 (기본 2=코인)

    Returns:
        {"path": [(x,y),...], "cost": int, "algorithm": "bfs", "found": bool, "target": (x,y)|None}
    """
    if not grid:
        return {"path": [], "cost": -1, "algorithm": "bfs", "found": False, "target": None}

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    extra_obstacles = set(obstacles) if obstacles else set()

    def is_passable(x: int, y: int) -> bool:
        if x < 0 or x >= cols or y < 0 or y >= rows:
            return False
        if (x, y) in extra_obstacles:
            return False
        return grid[y][x] != 1

    queue: deque = deque([(start, [start])])
    visited = {start}
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while queue:
        current, path = queue.popleft()
        x, y = current

        if (x, y) != start and grid[y][x] == target_value:
            return {
                "path": path,
                "cost": len(path) - 1,
                "algorithm": "bfs",
                "found": True,
                "target": current,
            }

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            if neighbor not in visited and is_passable(nx, ny):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {"path": [], "cost": -1, "algorithm": "bfs", "found": False, "target": None}


def greedy_coin_route(
    grid: List[List[int]],
    start: Tuple[int, int],
    coin_positions: List[Tuple[int, int]],
    obstacles: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, Any]:
    """
    탐욕적 최근접 이웃 알고리즘으로 여러 코인을 방문하는 경로 계산.

    Args:
        grid: 2D 격자
        start: (x, y) 시작 위치
        coin_positions: 방문할 코인 위치 목록
        obstacles: 추가 장애물

    Returns:
        {"full_path": [(x,y),...], "total_cost": int, "coins_order": [(x,y),...], "algorithm": "greedy"}
    """
    if not coin_positions:
        return {"full_path": [start], "total_cost": 0, "coins_order": [], "algorithm": "greedy"}

    remaining = list(coin_positions)
    current = start
    full_path: List[Tuple[int, int]] = [start]
    coins_order: List[Tuple[int, int]] = []
    total_cost = 0

    while remaining:
        # 현재 위치에서 가장 가까운 코인 선택 (Manhattan 거리 기준)
        nearest = min(
            remaining,
            key=lambda c: abs(c[0] - current[0]) + abs(c[1] - current[1])
        )

        # A*로 실제 경로 계산
        result = astar(grid, current, nearest, obstacles)

        if result["found"] and len(result["path"]) > 1:
            full_path.extend(result["path"][1:])  # 시작점 중복 제거
            total_cost += result["cost"]
            coins_order.append(nearest)
            current = nearest
        # 도달 불가능한 코인은 건너뜀

        remaining.remove(nearest)

    return {
        "full_path": full_path,
        "total_cost": total_cost,
        "coins_order": coins_order,
        "algorithm": "greedy",
    }


def find_nearest_coin(
    grid: List[List[int]],
    start: Tuple[int, int],
    obstacles: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, Any]:
    """
    현재 위치에서 가장 가까운 코인(grid값=2)을 BFS로 탐색.
    코인 위치를 모를 때 사용.
    """
    return bfs(grid, start, obstacles, target_value=2)


def explore_unknown(
    grid: List[List[int]],
    start: Tuple[int, int],
    visited: set,
    obstacles: Optional[List[Tuple[int, int]]] = None
) -> Dict[str, Any]:
    """
    미방문 영역을 향해 BFS 탐색 경로 반환.

    Args:
        grid: 2D 격자
        start: 현재 위치
        visited: 이미 방문한 위치 집합
        obstacles: 추가 장애물
    """
    if not grid:
        return {"path": [], "cost": -1, "algorithm": "bfs_explore", "found": False}

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    extra_obstacles = set(obstacles) if obstacles else set()

    def is_passable(x: int, y: int) -> bool:
        if x < 0 or x >= cols or y < 0 or y >= rows:
            return False
        if (x, y) in extra_obstacles:
            return False
        return grid[y][x] != 1

    queue: deque = deque([(start, [start])])
    seen = {start}
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while queue:
        current, path = queue.popleft()

        if current not in visited and current != start:
            return {
                "path": path,
                "cost": len(path) - 1,
                "algorithm": "bfs_explore",
                "found": True,
                "target": current,
            }

        x, y = current
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            if neighbor not in seen and is_passable(nx, ny):
                seen.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {"path": [], "cost": -1, "algorithm": "bfs_explore", "found": False, "target": None}
