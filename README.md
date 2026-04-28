# OpenAI Intelligent Agent

基于 OpenAI Agents SDK 的智能客服实验项目，当前聚焦于以下能力：

- 基于 `FastAPI` 提供对话 API
- 基于 OpenAI Agents SDK 做多 Agent 编排
- 先经 `RAGAgent` 获取上下文，再按需转交 `SQLAgent` 或 `ActionAgent`
- SQL 查询经过 `RunSqlUseCase`，当前底层数据库适配器为 mock 实现，会直接打印 SQL
- 后台操作当前先走审批单创建流程的最小实现

## 当前状态

项目目前处于 MVP 骨架阶段，已经打通了从 `app_factory` 到 `chat_controller` 再到 OpenAI Agents 编排器的最小闭环。

当前已验证的链路：

- 启动 FastAPI 服务
- 调用 `/api/chat`
- 进入 Agent 编排
- 在 SQL 路径中调用 `RunSqlUseCase.execute()`
- 在控制台打印 SQL 调用日志

当前 SQL 底层不是实际数据库查询，而是通过 `MysqlReadonlyAdapter` 返回 mock 结果，用于先打通整体流程。

## 技术栈

- Python 3.12+
- FastAPI
- OpenAI Agents SDK
- LiteLLM / OpenRouter
- Langfuse
- Pydantic
- Pytest

## 项目结构

```text
openai-intelligent-agent/
├── app/
│   ├── application/         # 应用服务与 use case
│   ├── bootstrap/           # 应用启动与依赖装配
│   ├── domain/              # 领域模型、策略、端口
│   ├── entrypoints/         # API 入口层
│   └── infrastructure/      # LLM / DB / 外部适配器
├── docs/                    # 设计文档与实施计划
├── tests/                   # 单元测试与集成测试
├── pyproject.toml
└── README.md
```

## 环境准备

### 1. 安装依赖

```bash
poetry install
```

### 2. 配置环境变量

在项目根目录创建 `.env`，至少包含：

```env
LLM_API_KEY="your-api-key"
LLM_BASE_URL="https://openrouter.ai/api/v1"
DEFAULT_MODEL="stepfun/step-3.5-flash"
```

如果需要把 LiteLLM / OpenAI Agents 的调用链路上报到 Langfuse Tracing，额外配置：

```env
LANGFUSE_PUBLIC_KEY="your-langfuse-public-key"
LANGFUSE_SECRET_KEY="your-langfuse-secret-key"
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

说明：

- 项目启动时会先 `load_dotenv()`
- `DEFAULT_MODEL` 会自动转换成 `litellm/openrouter/...` 前缀
- `LANGFUSE_BASE_URL` 会在启动时自动映射到 `LANGFUSE_HOST` 和 `LANGFUSE_OTEL_HOST`
- `.env` 已被 `.gitignore` 忽略，不会自动提交

## 启动方式

### 启动 API 服务

```bash
poetry run uvicorn app.bootstrap.app_factory:create_app --reload --factory
```

启动成功后默认访问：

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## 快速验证

### 调用聊天接口

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u1",
    "session_id": "s1",
    "query": "请查询库存低于50的商品"
  }'
```

预期现象：

- 接口返回包含 `answer`
- 控制台打印类似内容：

```text
SQL 正在调用: SELECT * FROM inventory LIMIT 20
执行SQL查询数据库: mockdb，表：['inventory']，SQL语句: SELECT * FROM inventory LIMIT 20
```

如果已配置 Langfuse，调用 `/api/chat` 后还应在 Langfuse 的 `Tracing` 页面看到对应 trace。修改 `.env` 或 tracing 配置后，需要重启 FastAPI 进程。

## 测试

### 运行全部测试

```bash
poetry run pytest -q
```

### 运行 API 集成测试

```bash
poetry run pytest tests/integration/test_api_endpoints.py -q
```

说明：

- 测试环境下会设置 `APP_ENV=test`
- `container.py` 会注入轻量测试编排器，避免真实模型调用影响测试稳定性

## 核心代码说明

### 1. 应用启动层

- `app/bootstrap/app_factory.py`
- 负责创建 `FastAPI` 应用并注册路由

### 2. 依赖装配层

- `app/bootstrap/container.py`
- 负责组装：
  - `RunRagQueryUseCase`
  - `RunSqlUseCase`
  - `RequestAdminActionUseCase`
  - `OpenAIAgentsLLMOrchestrator`

### 3. 应用服务层

- `app/application/services/agent_orchestrator.py`
- 负责把上层请求转发给 LLM 编排器

### 4. OpenAI Agents 编排层

- `app/infrastructure/llm/openai_agents_adapter.py`
- 包含：
  - `RAGAgent`
  - `SQLAgent`
  - `ActionAgent`
  - `BusinessOrchestrator`

### 4.1 Langfuse Tracing 配置

- 项目当前使用 `litellm.callbacks = ["langfuse_otel"]` 上报 Langfuse
- 不再使用旧式 `litellm.success_callback = ["langfuse"]`
- Langfuse 版本固定在 `>=2.60.10,<3.0.0`，见 `pyproject.toml`
- 相关初始化代码位于 `app/infrastructure/llm/openai_agents_adapter.py`

### 5. SQL 执行层

- `app/application/use_cases/run_sql_query.py`
- 当前会在 `execute()` 中打印 SQL 调用日志
- 调用前会经过 `SqlPolicy` 做只读校验

## 当前限制

- RAG 目前仍是最小示例实现，不是真实向量检索
- SQL Agent 虽然走真实模型编排，但底层数据库查询仍是 mock 返回
- 后台操作目前只完成“创建审批单”的最小链路
- 审计、持久化、真实审批流还未完全落地

## 后续计划

后续将逐步补齐：

- 真实 RAGFlow 检索适配器
- 真实只读 SQL 查询链路
- 后台操作审批流与执行回传
- 审计日志与链路追踪
- 更多集成测试与 E2E 测试

## Langfuse 踩坑记录

### 1. `langfuse` 版本不能随便升

项目当前 `litellm` 版本为 `1.82.6`，实际验证可兼容的 `langfuse` 版本范围是：

```toml
langfuse = ">=2.60.10,<3.0.0"
```

踩过的坑：

- `langfuse 4.x` 会报：

```text
AttributeError: module 'langfuse' has no attribute 'version'
```

- `langfuse 3.x` 虽然有 `langfuse.version.__version__`，但仍可能报：

```text
TypeError: Langfuse.__init__() got an unexpected keyword argument 'sdk_integration'
```

根因是当前 `litellm` 的 Langfuse 集成代码同时依赖：

- `langfuse.version.__version__`
- `Langfuse.__init__(..., sdk_integration=...)`

因此不要升级到 `3.x` 或 `4.x`，除非同时升级并验证 `litellm`。

### 2. Tracing 控制台为空，不一定是 key 错

如果 Langfuse 后台没有任何 trace，优先检查下面几项：

- 是否使用了 `litellm.callbacks = ["langfuse_otel"]`
- 是否仍在使用旧式 `litellm.success_callback = ["langfuse"]`
- 是否配置了 `LANGFUSE_BASE_URL`，并在进程启动后映射成了 `LANGFUSE_OTEL_HOST`
- 修改 `.env` 后是否重启了 FastAPI 进程
- 请求是否真的走到了 LiteLLM 模型调用，而不是测试 stub / mock

### 3. 推荐环境变量

推荐至少配置以下变量：

```env
LANGFUSE_PUBLIC_KEY="..."
LANGFUSE_SECRET_KEY="..."
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

项目启动时会自动把：

- `LANGFUSE_BASE_URL -> LANGFUSE_HOST`
- `LANGFUSE_BASE_URL -> LANGFUSE_OTEL_HOST`

### 4. 不要把真实密钥提交到仓库或发到聊天记录

如果 `LANGFUSE_SECRET_KEY` 已经暴露，应该立即在 Langfuse 后台 rotate。

## 相关文档

- 架构设计文档：
  [2026-04-24-openai-agents-ragflow-cs-agent-design.md](file:///Users/mozzie/pythonProjects/openai-intelligent-agent/docs/superpowers/specs/2026-04-24-openai-agents-ragflow-cs-agent-design.md)
- 实施计划文档：
  [2026-04-24-openai-agents-ragflow-cs-agent-implementation-plan.md](file:///Users/mozzie/pythonProjects/openai-intelligent-agent/docs/superpowers/plans/2026-04-24-openai-agents-ragflow-cs-agent-implementation-plan.md)
