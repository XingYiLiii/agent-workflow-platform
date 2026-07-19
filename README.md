# Agent Workflow Platform

A runnable, inspectable AI Agent Workflow platform built to demonstrate agent engineering, not a conversational ChatBot. A task is planned, executed through controlled tools, reviewed, finalized, and persisted as a trace that can be inspected or recovered after failure.

## Why this is an Agent Workflow platform

The platform turns a goal into an explicit execution lifecycle:

```text
Task -> Planner -> Executor -> Tool Calling -> Reviewer -> Finalizer -> Persisted result
```

It exposes the state around that lifecycle: workflow node history, tool-call input/output, task-step results, checkpoints, retry count, errors, and final output. This makes an execution observable and recoverable instead of treating an LLM response as a black box.

## Architecture

```mermaid
flowchart TD
    UI["Dashboard / API Consumer"] --> API["FastAPI"]
    API --> Tasks["Task Service"]
    Tasks --> Runtime["Workflow Runtime"]
    Runtime --> Graph["LangGraph: Planner -> Executor -> Reviewer -> Finalizer"]
    Graph --> Tools["Tool Registry: Calculator / CSV File Reader"]
    Runtime --> DB[("PostgreSQL: Tasks, Runs, Steps, Tool Calls, Checkpoints")]
    Graph --> LLM["LLM Provider Interface: FakeProvider for deterministic demos"]
```

## Agent execution flow

```mermaid
flowchart LR
    A["Create task"] --> B["Planner: structured ExecutionPlan"]
    B --> C["Executor: selects tool by step type"]
    C --> D["Tool Registry: file_reader or calculator"]
    D --> E["Reviewer: validates results"]
    E --> F["Finalizer: creates output"]
    F --> G["Persist workflow run, steps, calls and checkpoints"]
```

## Reliability and traceability

- **Structured workflow:** Pydantic models define plan, step, review, final output, and workflow state.
- **Tool tracing:** Every tool call persists its name, validated input, output, status, and failure message.
- **Error and retry controls:** Tasks support `failed` state, classified errors, retry counters, and retry limits.
- **Checkpoint recovery:** A snapshot is stored after every key node. A failed task resumes from the next unfinished node, avoiding completed work.
- **Versioned prompts and providers:** In-memory `PromptRegistry` provides planner/reviewer/finalizer v1 templates. `BaseLLMProvider` separates runtime logic from model implementations; the shipped FakeProvider makes the demo deterministic without API keys.

## Technology stack

| Area | Technology |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy |
| Agent workflow | LangGraph, Pydantic |
| Storage | PostgreSQL, Alembic |
| Engineering | Docker Compose, pytest, Ruff |
| Demo UI | Server-rendered lightweight HTML plus browser fetch |

## Run the demo

### Docker Compose

```bash
docker compose up --build
```

Open the lightweight execution dashboard at [http://localhost:8000/dashboard](http://localhost:8000/dashboard), and interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

The API container runs `alembic upgrade head` before starting Uvicorn. The compose file provides the PostgreSQL connection automatically.

### Local development

1. Start PostgreSQL and copy `.env.example` to `.env` if you need a custom database URL.
2. Create and activate a Python 3.11+ virtual environment.
3. Install the service and development tools:

```bash
cd backend
pip install -e .
pip install pytest ruff httpx
alembic upgrade head
uvicorn app.main:app --reload
```

Environment variables use the `AWP_` prefix:

```env
AWP_ENVIRONMENT=development
AWP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agent_workflow
```

## API quickstart

Create and run a calculation task:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Calculate discount","input":"calculate: 100*0.8"}'

curl -X POST http://localhost:8000/tasks/<task_id>/run
curl http://localhost:8000/tasks/<task_id>/details
```

`GET /tasks/{task_id}/details` returns the task, latest workflow run and node history, task steps, tool traces, checkpoint records, and final output in one response. It is intended for the dashboard or a portfolio demo.

## Demo data

[examples/sales.csv](examples/sales.csv) is a small CSV fixture for the File Reader tool. To run it locally, create a task with input `analyze csv: examples/sales.csv`; the File Reader reports rows, columns, and basic type analysis. The Docker image does not copy repository-level examples, so use a mounted or managed upload path when demonstrating CSV analysis in containers.

Example workflow outcome:

```text
Planner: create a file_analysis step
Executor: invoke file_reader with the CSV path
Reviewer: verify a non-empty result
Finalizer: produce the persisted final output
```

## Quality checks

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python -m ruff format --check app tests
```

## Project layout

```text
backend/app/
|-- api/          # FastAPI task, health, and dashboard routes
|-- agent/        # Workflow state and structured schemas
|-- workflow/     # LangGraph graph, execution, retry support
|-- tools/        # Registry plus Calculator and CSV File Reader
|-- llm/          # Provider interface and deterministic FakeProvider
|-- prompts/      # Versioned in-memory prompt registry
|-- models/       # SQLAlchemy persistence models
`-- services/     # Workflow run and checkpoint recovery services
```

## Scope

This repository intentionally focuses on a single-agent, deterministic workflow foundation. Distributed queues, Redis, memory, additional tools, and multi-agent coordination are outside the current scope.