# Agent Workflow Platform

面向 AI Agent 工程岗位设计的可运行项目：将用户任务转化为可规划、可执行、可追踪、可恢复的 **Agent Workflow**。项目重点不在于实现一个普通 ChatBot，而在于展示 AI Agent 在任务拆解、Tool Calling、执行状态持久化、失败处理与恢复上的工程化能力。

## 项目解决的问题

真实业务中的 AI 任务往往包含多个步骤，例如“分析 CSV 并输出结论”或“计算折扣并生成结果”。单次对话式 LLM 调用存在几个问题：

- 任务过程不可见，无法确认执行了哪些步骤；
- Tool Calling 缺少统一入口和调用记录；
- 执行失败后容易丢失上下文，只能从头再来；
- 结果缺少校验，无法区分“模型已回复”和“任务已完成”。

本项目通过状态化 **Workflow** 解决这些问题：任务由 Planner 生成结构化计划，Executor 调用受控工具，Reviewer 校验结果，Finalizer 输出最终结论；每次运行的节点轨迹、工具输入输出、Checkpoint 和最终结果都会持久化。

## Agent Workflow 架构

```mermaid
flowchart TD
    UI["Dashboard / API Consumer"] --> API["FastAPI"]
    API --> TaskService["Task Service"]
    TaskService --> Runtime["Workflow Runtime"]
    Runtime --> Graph["LangGraph: Planner -> Executor -> Reviewer -> Finalizer"]
    Graph --> Tools["Tool Registry: Calculator / CSV File Reader"]
    Runtime --> DB[("PostgreSQL: Tasks, Runs, Steps, Tool Calls, Checkpoints")]
    Graph --> LLM["LLM Provider Interface: FakeProvider"]
```

## Agent 执行流程

```mermaid
flowchart LR
    A["创建任务"] --> B["Planner: 生成结构化 ExecutionPlan"]
    B --> C["Executor: 按步骤选择 Tool"]
    C --> D["Tool Calling: file_reader / calculator"]
    D --> E["Reviewer: 校验执行结果"]
    E --> F["Finalizer: 生成最终输出"]
    F --> G["持久化运行记录、步骤、工具调用与 Checkpoint"]
```

核心节点职责：

- **Planner**：基于任务目标输出 Pydantic 约束的 `ExecutionPlan`，而非难以解析的自由文本。
- **Executor**：读取计划步骤，根据 `step.type` 从 Tool Registry 中选择工具并执行。
- **Reviewer**：检查每个步骤是否成功、结果是否为空，输出结构化审核结果。
- **Finalizer**：仅在审核通过后汇总步骤结果，生成最终输出。

## Tool Calling 设计

当前实现两个受控工具，并通过统一 Tool Registry 管理：

| 工具 | 场景 | 安全与输出 |
| --- | --- | --- |
| `file_reader` | CSV 文件读取与字段分析 | 统计行数、列名和基础数据类型；处理文件不存在、空文件、格式异常 |
| `calculator` | 基础数值计算 | 基于 AST 解析，只允许数字、四则运算和括号，不使用 `eval` |

每次 Tool Calling 均会写入 `tool_calls`：工具名称、输入参数、输出结果、执行状态、错误信息和创建时间。这使得 Dashboard、API 消费方或面试演示都能查看 Agent 的实际执行证据。

## Reliability：失败处理与恢复

项目通过以下机制提升 Agent Workflow 的可靠性：

- **Error Handling**：统一错误分类，覆盖参数校验、工具执行、模型、超时与权限问题。
- **Task Failed 状态**：任务保存 `error_type`、`error_message`、失败节点、失败时间和重试次数。
- **Retry**：限制最大重试次数，避免无限循环。
- **Checkpoint**：每个关键节点执行后保存 WorkflowState 快照、已完成步骤、工具结果和节点位置。
- **Recovery**：失败任务可从最后一个 Checkpoint 继续，已成功节点不会重复执行。
- **Prompt Registry**：内存式版本化 Prompt Registry，内置 planner/reviewer/finalizer 的 v1 模板。
- **LLM Provider**：通过 `BaseLLMProvider` 抽象模型调用；默认 `FakeProvider` 保证测试和 Demo 不依赖外部 API。`OpenAICompatibleProvider` 为后续接入兼容 API 预留接口。

## 技术栈

| 领域 | 技术 |
| --- | --- |
| Backend | Python、FastAPI、SQLAlchemy |
| Agent Workflow | LangGraph、Pydantic |
| 数据存储 | PostgreSQL、Alembic |
| 工程化 | Docker Compose、pytest、Ruff |
| Demo 页面 | 轻量 HTML + 浏览器原生 fetch |

## Demo 流程

1. 调用 `POST /tasks` 创建任务，例如 `calculate: 100*0.8`。
2. 调用 `POST /tasks/{task_id}/run` 启动 LangGraph Workflow。
3. Planner 生成 calculation 步骤，Executor 通过 Tool Calling 调用 `calculator`。
4. Reviewer 校验计算结果，Finalizer 生成最终输出。
5. 访问 `GET /tasks/{task_id}/details` 查看完整执行详情：任务、节点历史、步骤、工具记录、Checkpoint 与最终结果。
6. 访问 `/dashboard` 查看轻量可视化页面。

CSV Demo 数据位于 [examples/sales.csv](examples/sales.csv)。本地创建任务时输入 `analyze csv: examples/sales.csv`，即可演示 File Reader Tool 的字段分析流程。

## 启动方式

### Docker Compose

```bash
docker compose up --build
```

启动后访问：

- Dashboard：[http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- Swagger API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

容器启动时会自动执行 `alembic upgrade head`，并使用 Docker Compose 提供的 PostgreSQL。

### 本地开发

1. 启动 PostgreSQL；如需修改连接信息，将 `.env.example` 复制为 `.env`。
2. 创建并激活 Python 3.11+ 虚拟环境。
3. 安装依赖并启动服务：

```bash
cd backend
pip install -e .
pip install pytest ruff httpx
alembic upgrade head
uvicorn app.main:app --reload
```

环境变量使用 `AWP_` 前缀：

```env
AWP_ENVIRONMENT=development
AWP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agent_workflow
```

## API 快速体验

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"计算折扣","input":"calculate: 100*0.8"}'

curl -X POST http://localhost:8000/tasks/<task_id>/run
curl http://localhost:8000/tasks/<task_id>/details
```

`GET /tasks/{task_id}/details` 将一次性返回：Task 信息、最新 Workflow 状态、节点执行历史、Task Steps、Tool Calling 记录、Checkpoint 记录和最终输出，便于前端展示与面试讲解。

## 测试结果

当前项目质量检查命令：

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python -m ruff format --check app tests
```

最近一次完整回归结果：

```text
29 passed
Ruff check passed
Ruff format check passed
```

## 项目结构

```text
backend/app/
|-- api/          # FastAPI 的任务、健康检查与 Dashboard 路由
|-- agent/        # Workflow 状态与结构化 Schema
|-- workflow/     # LangGraph Graph、执行器与 Retry 支持
|-- tools/        # Tool Registry、Calculator、CSV File Reader
|-- llm/          # LLM Provider 抽象与 FakeProvider
|-- prompts/      # 版本化 Prompt Registry
|-- models/       # SQLAlchemy 持久化模型
`-- services/     # Workflow 执行与 Checkpoint Recovery 服务
```

## 当前边界

项目当前聚焦单 Agent、确定性 Workflow 的工程基础能力；Redis、Celery、Memory、多 Agent 协作及更多外部工具不在当前版本范围内。
