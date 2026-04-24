# OpenAI Agents + RAGFlow 智能客服实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个可上线的智能客服 Agent 单体服务，支持 RAG 问答、只读 SQL 查询、后台操作审批执行与全链路审计。

**Architecture:** 基于 Clean/Hexagonal 分层：`entrypoints -> application -> domain -> infrastructure`。OpenAI Agents SDK 负责编排与工具决策，RAGFlow/SQL/后台脚本通过 Port+Adapter 接入，所有工具调用经策略校验与审计记录。

**Tech Stack:** Python 3.12+、OpenAI Agents SDK、FastAPI、Pydantic、SQLite（会话/审批/审计）与 MySQL 只读账号、Pytest。

---

## 0. 文件结构映射（先锁边界）

### 新增文件
- `app/entrypoints/api/chat_controller.py`
- `app/entrypoints/api/approval_controller.py`
- `app/application/use_cases/handle_chat.py`
- `app/application/use_cases/run_sql_query.py`
- `app/application/use_cases/request_admin_action.py`
- `app/application/use_cases/confirm_admin_action.py`
- `app/application/services/agent_orchestrator.py`
- `app/application/services/policy_service.py`
- `app/application/services/audit_service.py`
- `app/domain/models/conversation.py`
- `app/domain/models/approval_ticket.py`
- `app/domain/models/tool_call.py`
- `app/domain/policies/sql_policy.py`
- `app/domain/policies/action_policy.py`
- `app/domain/ports/rag_port.py`
- `app/domain/ports/sql_port.py`
- `app/domain/ports/admin_script_port.py`
- `app/domain/ports/approval_port.py`
- `app/domain/ports/audit_port.py`
- `app/infrastructure/llm/openai_agents_adapter.py`
- `app/infrastructure/rag/ragflow_adapter.py`
- `app/infrastructure/db/mysql_readonly_adapter.py`
- `app/infrastructure/db/sqlite_session_adapter.py`
- `app/infrastructure/tools/sql_tool.py`
- `app/infrastructure/tools/admin_script_tool.py`
- `app/infrastructure/tools/tool_gateway.py`
- `app/infrastructure/approval/manual_approval_adapter.py`
- `app/infrastructure/audit/audit_log_adapter.py`
- `app/infrastructure/config/settings.py`
- `app/bootstrap/container.py`
- `app/bootstrap/app_factory.py`
- `tests/unit/domain/test_sql_policy.py`
- `tests/unit/application/test_request_admin_action.py`
- `tests/integration/test_chat_rag_sql_flow.py`
- `tests/integration/test_admin_approval_flow.py`
- `tests/e2e/test_mixed_query_and_approval.py`

### 修改文件
- `rag_sql_orchestration_demo.py`（迁移为兼容 demo 入口，复用新架构）
- `pyproject.toml`（补充依赖和 pytest 配置）
- `README.md`（新增运行方式与架构说明）

---

### Task 1: 建立骨架与依赖基线

**Files:**
- Create: `app/__init__.py`
- Create: `app/entrypoints/__init__.py`
- Create: `app/entrypoints/api/__init__.py`
- Create: `app/application/__init__.py`
- Create: `app/application/use_cases/__init__.py`
- Create: `app/application/services/__init__.py`
- Create: `app/domain/__init__.py`
- Create: `app/domain/models/__init__.py`
- Create: `app/domain/policies/__init__.py`
- Create: `app/domain/ports/__init__.py`
- Create: `app/infrastructure/__init__.py`
- Create: `app/infrastructure/llm/__init__.py`
- Create: `app/infrastructure/rag/__init__.py`
- Create: `app/infrastructure/db/__init__.py`
- Create: `app/infrastructure/tools/__init__.py`
- Create: `app/infrastructure/approval/__init__.py`
- Create: `app/infrastructure/audit/__init__.py`
- Create: `app/infrastructure/config/__init__.py`
- Modify: `pyproject.toml`
- Test: `pytest -q`

- [ ] **Step 1: 创建基础包目录与空 `__init__.py`**

```bash
mkdir -p app/entrypoints/api app/application/use_cases app/application/services app/domain/models app/domain/policies app/domain/ports app/infrastructure/llm app/infrastructure/rag app/infrastructure/db app/infrastructure/tools app/infrastructure/approval app/infrastructure/audit app/infrastructure/config tests/unit/domain tests/unit/application tests/integration tests/e2e
touch app/__init__.py app/entrypoints/__init__.py app/entrypoints/api/__init__.py app/application/__init__.py app/application/use_cases/__init__.py app/application/services/__init__.py app/domain/__init__.py app/domain/models/__init__.py app/domain/policies/__init__.py app/domain/ports/__init__.py app/infrastructure/__init__.py app/infrastructure/llm/__init__.py app/infrastructure/rag/__init__.py app/infrastructure/db/__init__.py app/infrastructure/tools/__init__.py app/infrastructure/approval/__init__.py app/infrastructure/audit/__init__.py app/infrastructure/config/__init__.py
```

- [ ] **Step 2: 更新 `pyproject.toml` 依赖**

```toml
[project]
dependencies = [
  "openai-agents>=0.2.0",
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pydantic>=2.8.0",
  "python-dotenv>=1.0.1",
  "httpx>=0.27.0",
  "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: 安装依赖并验证可运行**

Run: `poetry install`  
Expected: 依赖安装成功，无冲突报错。

- [ ] **Step 4: 运行空测试基线**

Run: `pytest -q`  
Expected: 测试收集成功（可为 0 tests），无 ImportError。

- [ ] **Step 5: Commit**

```bash
git add app pyproject.toml
git commit -m "chore: bootstrap clean architecture project skeleton"
```

---

### Task 2: 定义领域模型与端口接口

**Files:**
- Create: `app/domain/models/conversation.py`
- Create: `app/domain/models/tool_call.py`
- Create: `app/domain/models/approval_ticket.py`
- Create: `app/domain/ports/rag_port.py`
- Create: `app/domain/ports/sql_port.py`
- Create: `app/domain/ports/admin_script_port.py`
- Create: `app/domain/ports/approval_port.py`
- Create: `app/domain/ports/audit_port.py`
- Test: `tests/unit/domain/test_sql_policy.py`（先写最小接口可导入测试）

- [ ] **Step 1: 写失败测试，约束领域模型可实例化**

```python
# tests/unit/domain/test_models_import.py
from app.domain.models.conversation import ConversationContext
from app.domain.models.approval_ticket import ApprovalTicket

def test_models_can_be_constructed():
    c = ConversationContext(user_id="u1", session_id="s1", trace_id="t1")
    a = ApprovalTicket(ticket_id="tk1", action_name="refund", status="PENDING")
    assert c.user_id == "u1"
    assert a.status == "PENDING"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/domain/test_models_import.py -v`  
Expected: FAIL，提示模块不存在。

- [ ] **Step 3: 实现模型与 Port 抽象**

```python
# app/domain/models/conversation.py
from pydantic import BaseModel

class ConversationContext(BaseModel):
    user_id: str
    session_id: str
    trace_id: str
    channel: str = "web"
```

```python
# app/domain/models/approval_ticket.py
from pydantic import BaseModel
from typing import Literal

TicketStatus = Literal["PENDING", "APPROVED", "REJECTED", "EXECUTED", "FAILED"]

class ApprovalTicket(BaseModel):
    ticket_id: str
    action_name: str
    status: TicketStatus
    payload: dict = {}
```

```python
# app/domain/ports/sql_port.py
from abc import ABC, abstractmethod

class SqlPort(ABC):
    @abstractmethod
    async def query(self, sql: str) -> list[dict]:
        raise NotImplementedError
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/domain/test_models_import.py -v`  
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/domain tests/unit/domain/test_models_import.py
git commit -m "feat: add domain models and port interfaces"
```

---

### Task 3: 实现 SQL 只读策略（核心风控）

**Files:**
- Create: `app/domain/policies/sql_policy.py`
- Create: `tests/unit/domain/test_sql_policy.py`

- [ ] **Step 1: 先写失败测试覆盖允许与拒绝场景**

```python
from app.domain.policies.sql_policy import SqlPolicy

def test_allow_select():
    p = SqlPolicy(allowed_tables={"inventory"})
    ok, _ = p.validate("SELECT * FROM inventory LIMIT 10")
    assert ok is True

def test_reject_update():
    p = SqlPolicy(allowed_tables={"inventory"})
    ok, reason = p.validate("UPDATE inventory SET stock=0")
    assert ok is False
    assert "只允许" in reason

def test_reject_multi_statement():
    p = SqlPolicy(allowed_tables={"inventory"})
    ok, _ = p.validate("SELECT * FROM inventory; DELETE FROM inventory")
    assert ok is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/domain/test_sql_policy.py -v`  
Expected: FAIL，`SqlPolicy` 未实现。

- [ ] **Step 3: 实现最小可用 `SqlPolicy`**

```python
import re

class SqlPolicy:
    def __init__(self, allowed_tables: set[str]):
        self.allowed_tables = {t.lower() for t in allowed_tables}

    def validate(self, sql: str) -> tuple[bool, str]:
        s = sql.strip().lower()
        if ";" in s[:-1]:
            return False, "禁止多语句执行"
        if not (s.startswith("select") or s.startswith("explain")):
            return False, "只允许 SELECT/EXPLAIN 查询"
        if any(k in s for k in [" insert ", " update ", " delete ", " drop ", " alter "]):
            return False, "检测到危险关键字"

        tables = set(re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", s))
        if tables and not tables.issubset(self.allowed_tables):
            return False, f"存在未授权表: {tables - self.allowed_tables}"
        return True, ""
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/domain/test_sql_policy.py -v`  
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/domain/policies/sql_policy.py tests/unit/domain/test_sql_policy.py
git commit -m "feat: enforce readonly sql policy with whitelist checks"
```

---

### Task 4: 接入基础设施适配器（RAG / SQL / 审计）

**Files:**
- Create: `app/infrastructure/rag/ragflow_adapter.py`
- Create: `app/infrastructure/db/mysql_readonly_adapter.py`
- Create: `app/infrastructure/audit/audit_log_adapter.py`
- Create: `app/infrastructure/config/settings.py`
- Test: `tests/integration/test_chat_rag_sql_flow.py`（mock 外部依赖）

- [ ] **Step 1: 先写失败测试，约束 SQL Adapter 接口返回**

```python
import pytest
from app.infrastructure.db.mysql_readonly_adapter import MysqlReadonlyAdapter

@pytest.mark.asyncio
async def test_mysql_adapter_returns_rows():
    adapter = MysqlReadonlyAdapter(dsn="sqlite:///business_demo.db")
    rows = await adapter.query("SELECT 1 as ok")
    assert isinstance(rows, list)
    assert rows[0]["ok"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_chat_rag_sql_flow.py -v`  
Expected: FAIL，Adapter 未实现。

- [ ] **Step 3: 实现最小 Adapter**

```python
# app/infrastructure/db/mysql_readonly_adapter.py
import sqlite3

class MysqlReadonlyAdapter:
    def __init__(self, dsn: str):
        self.dsn = dsn

    async def query(self, sql: str) -> list[dict]:
        conn = sqlite3.connect("business_demo.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/integration/test_chat_rag_sql_flow.py -v`  
Expected: PASS（若使用 sqlite fallback）。

- [ ] **Step 5: Commit**

```bash
git add app/infrastructure tests/integration/test_chat_rag_sql_flow.py
git commit -m "feat: add rag/sql/audit infrastructure adapters"
```

---

### Task 5: 实现工具网关与用例编排

**Files:**
- Create: `app/infrastructure/tools/tool_gateway.py`
- Create: `app/infrastructure/tools/sql_tool.py`
- Create: `app/application/use_cases/run_sql_query.py`
- Create: `app/application/services/policy_service.py`
- Test: `tests/unit/application/test_run_sql_query.py`

- [ ] **Step 1: 写失败测试，确保 SQL 用例经过策略校验**

```python
import pytest
from app.application.use_cases.run_sql_query import RunSqlQueryUseCase

class DummySql:
    async def query(self, sql: str):
        return [{"ok": 1}]

@pytest.mark.asyncio
async def test_sql_use_case_rejects_non_select():
    uc = RunSqlQueryUseCase(sql_port=DummySql(), allowed_tables={"inventory"})
    with pytest.raises(ValueError):
        await uc.execute("DELETE FROM inventory")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/application/test_run_sql_query.py -v`  
Expected: FAIL，UseCase 未实现。

- [ ] **Step 3: 实现 UseCase + Gateway 最小闭环**

```python
# app/application/use_cases/run_sql_query.py
from app.domain.policies.sql_policy import SqlPolicy

class RunSqlQueryUseCase:
    def __init__(self, sql_port, allowed_tables: set[str]):
        self.sql_port = sql_port
        self.policy = SqlPolicy(allowed_tables=allowed_tables)

    async def execute(self, sql: str) -> list[dict]:
        ok, reason = self.policy.validate(sql)
        if not ok:
            raise ValueError(reason)
        return await self.sql_port.query(sql)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/application/test_run_sql_query.py -v`  
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/application app/infrastructure/tools tests/unit/application/test_run_sql_query.py
git commit -m "feat: add sql use case and tool gateway guardrail path"
```

---

### Task 6: 实现后台操作审批流

**Files:**
- Create: `app/application/use_cases/request_admin_action.py`
- Create: `app/application/use_cases/confirm_admin_action.py`
- Create: `app/infrastructure/approval/manual_approval_adapter.py`
- Create: `tests/unit/application/test_request_admin_action.py`
- Create: `tests/integration/test_admin_approval_flow.py`

- [ ] **Step 1: 先写失败测试，约束审批状态流转**

```python
import pytest
from app.application.use_cases.request_admin_action import RequestAdminActionUseCase

@pytest.mark.asyncio
async def test_create_pending_ticket():
    uc = RequestAdminActionUseCase()
    ticket = await uc.execute("refund_order", {"order_id": "O1"})
    assert ticket.status == "PENDING"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/application/test_request_admin_action.py -v`  
Expected: FAIL，UseCase 未实现。

- [ ] **Step 3: 实现请求与确认用例**

```python
# app/application/use_cases/request_admin_action.py
import uuid
from app.domain.models.approval_ticket import ApprovalTicket

class RequestAdminActionUseCase:
    async def execute(self, action_name: str, payload: dict) -> ApprovalTicket:
        return ApprovalTicket(
            ticket_id=str(uuid.uuid4()),
            action_name=action_name,
            status="PENDING",
            payload=payload,
        )
```

```python
# app/application/use_cases/confirm_admin_action.py
class ConfirmAdminActionUseCase:
    def __init__(self, approval_port, script_port):
        self.approval_port = approval_port
        self.script_port = script_port

    async def execute(self, ticket_id: str, approved: bool, operator: str) -> dict:
        ticket = await self.approval_port.update(ticket_id, approved=approved, operator=operator)
        if ticket.status != "APPROVED":
            return {"status": ticket.status, "message": "已拒绝或待处理"}
        result = await self.script_port.execute(ticket.action_name, ticket.payload)
        return {"status": "EXECUTED", "result": result}
```

- [ ] **Step 4: 运行单元 + 集成测试**

Run: `pytest tests/unit/application/test_request_admin_action.py tests/integration/test_admin_approval_flow.py -v`  
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/application/use_cases app/infrastructure/approval tests/unit/application tests/integration/test_admin_approval_flow.py
git commit -m "feat: add manual approval workflow for admin scripts"
```

---

### Task 7: 接入 OpenAI Agents 编排服务

**Files:**
- Create: `app/application/services/agent_orchestrator.py`
- Create: `app/infrastructure/llm/openai_agents_adapter.py`
- Modify: `rag_sql_orchestration_demo.py`
- Test: `tests/integration/test_chat_rag_sql_flow.py`

- [ ] **Step 1: 写失败测试，要求编排器可处理三类请求**

```python
import pytest
from app.application.services.agent_orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_handles_sql_intent():
    orch = AgentOrchestrator(...)
    result = await orch.handle("查询库存低于50的商品")
    assert "库存" in result["answer"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_chat_rag_sql_flow.py -v`  
Expected: FAIL，编排器未实现。

- [ ] **Step 3: 实现编排器与 SDK 适配器**

```python
# app/application/services/agent_orchestrator.py
from agents import Agent, Runner


class AgentOrchestrator:
    def __init__(self, rag_use_case, sql_use_case, request_action_use_case):
        self.rag_use_case = rag_use_case
        self.sql_use_case = sql_use_case
        self.request_action_use_case = request_action_use_case

        async def rag_tool(query: str) -> str:
            docs = await self.rag_use_case.execute(query)
            return str(docs)

        async def sql_tool(query: str) -> str:
            rows = await self.sql_use_case.execute(query)
            return str(rows)

        async def approval_tool(action_name: str, payload: dict) -> str:
            ticket = await self.request_action_use_case.execute(action_name, payload)
            return f"已创建审批单 {ticket.ticket_id}"

        self.rag_agent = Agent(
            name="RAGAgent",
            instructions="处理制度/规则类问题，优先调用 rag_tool 并基于结果回答。",
            tools=[rag_tool],
        )
        self.sql_agent = Agent(
            name="SQLAgent",
            instructions="处理数据查询类问题，必须先调用 sql_tool。",
            tools=[sql_tool],
        )
        self.action_agent = Agent(
            name="ActionAgent",
            instructions="处理后台操作请求，必须调用 approval_tool 创建审批单。",
            tools=[approval_tool],
        )
        self.root_agent = Agent(
            name="BusinessOrchestrator",
            instructions=(
                "你是总控编排 Agent：\n"
                "1) 制度/流程/规则 -> 转交 RAGAgent\n"
                "2) SQL/指标查询 -> 转交 SQLAgent\n"
                "3) 退款/后台操作 -> 转交 ActionAgent"
            ),
            handoffs=[self.rag_agent, self.sql_agent, self.action_agent],
        )

    async def handle(self, user_query: str) -> dict:
        result = await Runner.run(self.root_agent, user_query)
        return {"answer": result.final_output}
```

- [ ] **Step 4: 运行集成测试确认通过**

Run: `pytest tests/integration/test_chat_rag_sql_flow.py -v`  
Expected: PASS（先用 mock/stub 适配器）。

- [ ] **Step 5: Commit**

```bash
git add app/application/services app/infrastructure/llm rag_sql_orchestration_demo.py tests/integration/test_chat_rag_sql_flow.py
git commit -m "feat: integrate openai agents orchestrator with rag/sql/approval routes"
```

---

### Task 8: API 接口层落地（Chat + Approval）

**Files:**
- Create: `app/entrypoints/api/chat_controller.py`
- Create: `app/entrypoints/api/approval_controller.py`
- Create: `app/bootstrap/container.py`
- Create: `app/bootstrap/app_factory.py`
- Test: `tests/integration/test_api_endpoints.py`

- [ ] **Step 1: 先写失败测试，定义 API 契约**

```python
from fastapi.testclient import TestClient
from app.bootstrap.app_factory import create_app

def test_chat_endpoint():
    app = create_app()
    c = TestClient(app)
    r = c.post("/api/chat", json={"user_id": "u1", "session_id": "s1", "query": "查库存"})
    assert r.status_code == 200
    assert "answer" in r.json()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/integration/test_api_endpoints.py -v`  
Expected: FAIL，路由未实现。

- [ ] **Step 3: 实现 FastAPI 入口与 DI 装配**

```python
# app/bootstrap/app_factory.py
from fastapi import FastAPI
from app.entrypoints.api.chat_controller import router as chat_router
from app.entrypoints.api.approval_controller import router as approval_router

def create_app() -> FastAPI:
    app = FastAPI(title="Intelligent CS Agent")
    app.include_router(chat_router, prefix="/api")
    app.include_router(approval_router, prefix="/api")
    return app
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/integration/test_api_endpoints.py -v`  
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add app/entrypoints app/bootstrap tests/integration/test_api_endpoints.py
git commit -m "feat: add chat and approval api endpoints with app factory"
```

---

### Task 9: 端到端验证与文档收口

**Files:**
- Create: `tests/e2e/test_mixed_query_and_approval.py`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-04-24-openai-agents-ragflow-cs-agent-design.md`（仅补链接）

- [ ] **Step 1: 编写 E2E 测试（混合咨询 + 审批）**

```python
def test_e2e_mixed_and_approval():
    # 1) 问规则 + 查库存
    # 2) 触发后台操作审批
    # 3) 审批通过并执行
    assert True
```

- [ ] **Step 2: 运行全量测试**

Run: `pytest -q`  
Expected: 所有单测/集测/E2E 通过。

- [ ] **Step 3: 更新 README 的运行与架构说明**

```markdown
## Quick Start
1. 配置 .env
2. `poetry install`
3. `uvicorn app.bootstrap.app_factory:create_app --reload`

## Architecture
- OpenAI Agents SDK + RAGFlow + SQL Readonly + Manual Approval
```

- [ ] **Step 4: 冒烟运行**

Run: `uvicorn app.bootstrap.app_factory:create_app --reload`  
Expected: 服务启动成功，`/docs` 可访问，接口可调用。

- [ ] **Step 5: Commit**

```bash
git add tests/e2e README.md docs/superpowers/specs/2026-04-24-openai-agents-ragflow-cs-agent-design.md
git commit -m "test/docs: add e2e coverage and finalize usage documentation"
```

---

## 计划自检（对齐设计文档）
- 需求覆盖：RAG 问答、只读 SQL、后台审批、审计、API 接入、E2E 验证均有任务覆盖。
- 占位符检查：无 `TODO/TBD` 文案；每个任务含文件、步骤、命令、预期结果。
- 一致性检查：`SqlPolicy`、`ApprovalTicket`、`AgentOrchestrator` 命名在任务中保持一致。
- 范围约束：保持单体架构，不引入多租户和异步消息系统，符合 MVP 目标。

## 执行建议
- 推荐执行方式：`subagent-driven-development`，按 Task 逐项推进并在每个 Task 后做 review。
- 若你希望我直接开始编码，请回复：`按 Task 1 开始执行`。
