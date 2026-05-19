# AWS AI League 대회 사전 준비 — Implementation Plan

## Directory Structure

```
/Users/bae/project/aws_ai_league/
├── .env.template
├── CLAUDE.md
├── deploy.sh
├── deploy-loop.sh
├── agent/
│   ├── agent_skeleton.py
│   ├── system_prompt.txt
│   └── invoke_agent.py
├── tools/
│   ├── pathfinding_tool.py
│   ├── coin_collector_tool.py
│   ├── state_query_tool.py
│   └── tool_schemas/
│       ├── pathfinding_schema.json
│       ├── coin_collector_schema.json
│       └── state_query_schema.json
├── memory/
│   ├── memory_patterns.py
│   └── hint_store.py
├── algorithms/
│   └── pathfinder.py
├── cheatsheets/
│   ├── 4.1-agentcore.md
│   ├── 4.2-memory.md
│   ├── 4.3-tools-gateway.md
│   ├── 4.4-guardrails.md
│   └── 4.5-lambda.md
└── prompts/
    ├── claude_code_loop.md
    └── agent_debug_prompt.md
```

## Build Order (Dependency Graph)

Phase 0 — Foundation (parallel):
- AC-6: .env.template
- AC-5: cheatsheets/ (5 docs)
- AC-7: algorithms/pathfinder.py

Phase 1 — Core tools (depends on Phase 0):
- AC-2: tools/*.py + tool_schemas/*.json (depends on AC-7)
- AC-3: memory/*.py (depends on AC-6)

Phase 2 — Agent (depends on Phase 1):
- AC-1: agent/*.py + system_prompt.txt (depends on AC-2 schemas, AC-3, AC-6)

Phase 3 — Automation (depends on Phase 2):
- AC-4: deploy.sh, deploy-loop.sh, CLAUDE.md (depends on AC-1, AC-2)

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Foundation model | Claude 3 Haiku (default) | Faster invocation = more turns |
| Algorithm primary | A* with Manhattan heuristic | Optimal for grid with known targets |
| Exploration fallback | BFS frontier expansion | Guarantees unknown territory coverage |
| Coin routing | Greedy nearest-neighbor | Real-time viable; TSP too slow |
| Lambda packaging | Single-file with pathfinder inlined | No Lambda layer complexity |
| Memory strategy | Retrieve-first every turn | Prevents redundant exploration |
| Deploy method | AWS CLI update-function-code | Fastest iteration, no SAM/CDK |
| Variable injection | .env sourced by shell | Instant fill-in on competition day |
