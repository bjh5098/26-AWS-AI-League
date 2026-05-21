"""
generate_dataset.py — RLVR Tool Calling 훈련 데이터셋 생성

출력:
  data/train.jsonl  (500샘플)
  data/val.jsonl    (100샘플)

사용법:
  python scripts/generate_dataset.py
"""

import json
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from pathfinding_tool import lambda_handler as pathfinding_handler

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "pathfinding_lambda",
        "description": "AWS Lambda function for pathfinding with multiple strategies on a 2D game map.",
        "parameters": {
            "type": "object",
            "properties": {
                "game_map": {
                    "type": "array",
                    "description": "2D array representing the game map. Each cell is a string: wall, normal, start, treasure, c1-c8."
                },
                "start_pos": {
                    "type": "array",
                    "description": "Starting position as [row, column] (0-indexed)."
                },
                "strategy": {
                    "type": "string",
                    "description": "quickest (BFS shortest path) or coins_first (collect c7 coins first)."
                }
            },
            "required": ["game_map", "start_pos", "strategy"]
        }
    }
}

SYSTEM_PROMPT = """Output ONLY a tool call to find a path on the map:

<tool_call>
{"name": "pathfinding_lambda", "arguments": {"game_map": <2d_array>, "start_pos": [row,col], "strategy": "quickest|coins_first"}}
</tool_call>"""

CELL_TYPES = ["normal", "wall", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"]
STRATEGIES = ["quickest", "coins_first"]
MAP_SIZES = [6, 8, 10]

ROW_LABELS = "ABCDEFGHIJ"


def _pos_label(row, col, size):
    """(row, col) → 'A1' 형식 레이블."""
    return f"{ROW_LABELS[row]}{col + 1}" if row < len(ROW_LABELS) else f"R{row}C{col+1}"


def generate_map(size):
    """랜덤 맵 생성. start·treasure 보장, wall로 막히지 않도록 단순 구조."""
    grid = [["normal"] * size for _ in range(size)]

    # 벽 랜덤 배치 (약 15%)
    for r in range(size):
        for c in range(size):
            if random.random() < 0.15:
                grid[r][c] = "wall"

    # 코인·챌린지 랜덤 배치
    for r in range(size):
        for c in range(size):
            if grid[r][c] == "normal" and random.random() < 0.1:
                grid[r][c] = random.choice(["c7", "c7", "c5", "c8"])

    # start: 좌상단 부근
    start_r, start_c = 0, 0
    grid[start_r][start_c] = "start"

    # treasure: 우하단 부근
    tr, tc = size - 1, size - 1
    grid[tr][tc] = "treasure"

    # start~treasure 사이 최소 경로 확보 (중간 행 벽 제거)
    for c in range(size):
        if grid[0][c] == "wall":
            grid[0][c] = "normal"
    for r in range(size):
        if grid[r][size - 1] == "wall":
            grid[r][size - 1] = "normal"

    return grid, [start_r, start_c], [tr, tc]


def call_lambda(game_map, start_pos, strategy):
    """로컬 pathfinding_tool.lambda_handler 직접 호출."""
    event = {
        "game_map": game_map,
        "start_pos": start_pos,
        "strategy": strategy,
    }
    return pathfinding_handler(event, None)


def build_sample(index, split):
    size = random.choice(MAP_SIZES)
    strategy = random.choice(STRATEGIES)
    game_map, start_pos, treasure_pos = generate_map(size)

    pos_label = _pos_label(start_pos[0], start_pos[1], size)

    user_content = (
        f"Find a path from position {pos_label} to the treasure. "
        f"The map: {json.dumps(game_map)}. "
        f"Use strategy: {strategy}."
    )

    # 실제 Lambda 호출로 ground truth 생성
    lambda_result = call_lambda(game_map, start_pos, strategy)

    ground_truth = json.dumps({
        "function": {
            "name": "pathfinding_lambda",
            "arguments": json.dumps({
                "game_map": game_map,
                "start_pos": start_pos,
                "strategy": strategy,
            })
        },
        "output": lambda_result
    })

    return {
        "prompt": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "tools": [TOOL_SCHEMA],
        "reward_model": {
            "ground_truth": ground_truth,
            "style": "rule",
        },
        "extra_info": {
            "index": index,
            "split": split,
            "tool": "pathfinding_lambda",
            "map_size": size,
            "strategy": strategy,
            "position": pos_label,
        },
        "ability": "tool_use",
    }


def write_jsonl(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            line = json.dumps(s, ensure_ascii=False)
            # 500토큰 근사 필터 (문자 수 기준 ~2000자)
            if len(line) <= 2000:
                f.write(line + "\n")
    print(f"  저장: {path} ({len(samples)}개 시도)")


def main():
    random.seed(42)
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    print("훈련 데이터셋 생성 중... (500샘플)")
    train = [build_sample(i, "train") for i in range(500)]
    write_jsonl(os.path.join(out_dir, "train.jsonl"), train)

    print("검증 데이터셋 생성 중... (100샘플)")
    val = [build_sample(i, "val") for i in range(100)]
    write_jsonl(os.path.join(out_dir, "val.jsonl"), val)

    print("완료. data/train.jsonl, data/val.jsonl 생성됨")


if __name__ == "__main__":
    main()
