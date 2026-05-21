"""
generate_faithfulness_dataset.py — Stage 2 Faithfulness Training 데이터셋 생성

목적: 모델이 Lambda 출력을 수정 없이 그대로 재현하도록 학습
출력:
  data/faithfulness_train.jsonl  (403샘플)
  data/faithfulness_val.jsonl    (81샘플)

사용법:
  python scripts/generate_faithfulness_dataset.py
"""

import json
import random
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from pathfinding_tool import lambda_handler as pathfinding_handler

SYSTEM_PROMPT = (
    "You are a tool output relay. When you receive a tool response containing a path array, "
    "you MUST return it exactly as-is. Do not drop, add, reorder, or summarize any elements. "
    "Copy the array verbatim."
)

STRATEGIES = ["swift", "get_coins", "avoid_spikes", "safe_coins"]
MAP_SIZES = [6, 8, 10]


def generate_map(size):
    grid = [["normal"] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if random.random() < 0.15:
                grid[r][c] = "wall"
    for r in range(size):
        for c in range(size):
            if grid[r][c] == "normal" and random.random() < 0.08:
                grid[r][c] = random.choice(["c7", "c7", "c5", "c8"])
    grid[0][0] = "start"
    grid[size - 1][size - 1] = "treasure"
    for c in range(size):
        if grid[0][c] == "wall":
            grid[0][c] = "normal"
    for r in range(size):
        if grid[r][size - 1] == "wall":
            grid[r][size - 1] = "normal"
    return grid


def call_lambda(game_map, start_pos, strategy):
    event = {"game_map": game_map, "start_pos": start_pos, "strategy": strategy}
    return pathfinding_handler(event, None)


ROW_LABELS = "ABCDEFGHIJ"

def pos_label(row, col):
    return f"{ROW_LABELS[row]}{col + 1}" if row < len(ROW_LABELS) else f"R{row}C{col+1}"


def build_sample(index, split):
    size = random.choice(MAP_SIZES)
    strategy = random.choice(STRATEGIES)
    game_map = generate_map(size)
    start_pos = [0, 0]

    result = call_lambda(game_map, start_pos, strategy)

    # 실제 Lambda 출력 파싱
    try:
        body = json.loads(result.get("body", "{}"))
        path = body.get("path", [])
        steps = body.get("steps", len(path))
    except Exception:
        path = []
        steps = 0

    tool_output = json.dumps({"path": path, "steps": steps})
    ground_truth = tool_output

    user_content = f"Return this tool output exactly:\n{tool_output}"

    # 500토큰 근사 필터
    sample = {
        "data_source": "faithfulness_training",
        "prompt": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "ability": "tool_output_faithfulness",
        "reward_model": {
            "ground_truth": ground_truth,
            "style": "exact_match",
        },
        "extra_info": {
            "index": index,
            "split": split,
            "tool": "pathfinding_lambda",
            "map_size": size,
            "strategy": strategy,
            "position": pos_label(start_pos[0], start_pos[1]),
            "path_length": steps,
        },
    }
    return sample


def write_jsonl(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    written = 0
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            line = json.dumps(s, ensure_ascii=False)
            if len(line) <= 2000:  # ~500토큰 근사
                f.write(line + "\n")
                written += 1
    print(f"  저장: {path} ({written}개)")


def main():
    random.seed(7)
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    print("Faithfulness 훈련 데이터셋 생성 중... (403샘플)")
    train = [build_sample(i, "train") for i in range(403)]
    write_jsonl(os.path.join(out_dir, "faithfulness_train.jsonl"), train)

    print("Faithfulness 검증 데이터셋 생성 중... (81샘플)")
    val = [build_sample(i, "val") for i in range(81)]
    write_jsonl(os.path.join(out_dir, "faithfulness_val.jsonl"), val)

    print("완료. data/faithfulness_train.jsonl, data/faithfulness_val.jsonl 생성됨")


if __name__ == "__main__":
    main()
