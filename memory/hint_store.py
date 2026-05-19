"""
hint_store.py — 게임 힌트·코인위치·방문경로 저장소

AgentCore Memory를 활용한 고수준 게임 상태 관리.
"""

import json
import os
from typing import List, Tuple, Optional
from datetime import datetime


class HintStore:
    """
    게임 진행 중 수집한 정보를 구조화하여 저장·조회.

    사용 예:
        store = HintStore()
        store.add_coin_location((3, 5), value=10)
        store.add_obstacle((4, 4))
        store.mark_visited((1, 1))

        coins = store.get_unvisited_coins()
        summary = store.to_system_prompt_context()
    """

    def __init__(self):
        self.coin_locations: List[dict] = []      # {"pos": (x,y), "value": int, "collected": bool}
        self.obstacles: List[Tuple[int, int]] = [] # 장애물 위치
        self.visited: set = set()                  # 방문한 위치
        self.hints: List[str] = []                 # 텍스트 힌트
        self.current_score: int = 0

    def add_coin_location(self, position: Tuple[int, int], value: int = 1) -> None:
        """코인 위치 추가."""
        if not any(c['pos'] == position for c in self.coin_locations):
            self.coin_locations.append({
                'pos': position,
                'value': value,
                'collected': False,
                'discovered_at': datetime.now().isoformat()
            })

    def mark_coin_collected(self, position: Tuple[int, int]) -> None:
        """코인 수집 완료 표시."""
        for coin in self.coin_locations:
            if coin['pos'] == position and not coin['collected']:
                coin['collected'] = True
                self.current_score += coin.get('value', 1)
                break

    def add_obstacle(self, position: Tuple[int, int]) -> None:
        """장애물 위치 추가."""
        if position not in self.obstacles:
            self.obstacles.append(position)

    def mark_visited(self, position: Tuple[int, int]) -> None:
        """방문 완료 표시."""
        self.visited.add(position)

    def add_hint(self, hint_text: str) -> None:
        """게임 힌트 추가."""
        self.hints.append({
            'text': hint_text,
            'timestamp': datetime.now().isoformat()
        })

    def get_unvisited_coins(self) -> List[Tuple[int, int]]:
        """아직 수집하지 않은 코인 위치 목록."""
        return [c['pos'] for c in self.coin_locations if not c['collected']]

    def get_high_value_coins(self, min_value: int = 5) -> List[Tuple[int, int]]:
        """고가치 코인 위치 목록."""
        return [c['pos'] for c in self.coin_locations
                if not c['collected'] and c.get('value', 1) >= min_value]

    def get_obstacles(self) -> List[Tuple[int, int]]:
        """알려진 장애물 위치 목록."""
        return list(self.obstacles)

    def is_visited(self, position: Tuple[int, int]) -> bool:
        """위치 방문 여부 확인."""
        return position in self.visited

    def to_system_prompt_context(self) -> str:
        """System Prompt에 주입할 현재 게임 상태 요약."""
        unvisited_coins = self.get_unvisited_coins()
        lines = [
            "=== 현재 게임 상태 (Memory) ===",
            f"현재 점수: {self.current_score}",
            f"발견한 코인: {len(self.coin_locations)}개 (미수집: {len(unvisited_coins)}개)",
        ]

        if unvisited_coins:
            coin_strs = [f"({x},{y})" for x, y in unvisited_coins[:5]]
            lines.append(f"미수집 코인 위치: {', '.join(coin_strs)}")

        if self.obstacles:
            obs_strs = [f"({x},{y})" for x, y in self.obstacles[:5]]
            lines.append(f"알려진 장애물: {', '.join(obs_strs)}")

        if self.hints:
            lines.append(f"수집한 힌트: {len(self.hints)}개")
            for h in self.hints[-3:]:  # 최근 3개만
                lines.append(f"  - {h['text']}")

        lines.append("================================")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """직렬화 (저장용)."""
        return {
            'coin_locations': [
                {**c, 'pos': list(c['pos'])} for c in self.coin_locations
            ],
            'obstacles': [list(o) for o in self.obstacles],
            'visited': [list(v) for v in self.visited],
            'hints': self.hints,
            'current_score': self.current_score,
        }

    def save_to_file(self, filepath: str = '/tmp/hint_store.json') -> None:
        """Lambda /tmp에 상태 저장 (세션 내 재사용)."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str = '/tmp/hint_store.json') -> 'HintStore':
        """저장된 상태 불러오기."""
        store = cls()
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            store.coin_locations = [
                {**c, 'pos': tuple(c['pos'])} for c in data.get('coin_locations', [])
            ]
            store.obstacles = [tuple(o) for o in data.get('obstacles', [])]
            store.visited = {tuple(v) for v in data.get('visited', [])}
            store.hints = data.get('hints', [])
            store.current_score = data.get('current_score', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return store
