---
name: tracemap-agents
description: Configure and extend TraceMap CrewAI agents, tasks, tools, and process flows. Use when modifying agent behavior, adding tools, changing task prompts, or debugging Ollama/CrewAI pipeline runs.
---

# TraceMap CrewAI Agents

## Layout

- `agents/agents.py` — agent definitions
- `agents/tasks.py` — task definitions
- `agents/tools.py` — `@tool` registry
- `agents/process.py` — pipeline orchestration
- `agents/crew.py` — public entrypoint

## LLM

Ollama at `http://localhost:11434/v1`. Verify: `curl http://localhost:11434/api/tags`

When Ollama is offline, `run_pipeline()` uses deterministic fallback.

## Rules

- Task outputs must use Pydantic models from `agents/schemas.py`
- Tools delegate to `db/repository.py` — no SQL in prompts
- New tools: add to `agents/tools.py`, assign to agent in `agents.py`
