import os

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.use_cases.request_admin_action import RequestAdminActionUseCase
from app.application.use_cases.run_rag_query import RunRagQueryUseCase
from app.application.use_cases.run_sql_query import RunSqlUseCase
from app.infrastructure.db.mysql_readonly_adapter import MysqlReadonlyAdapter
from app.infrastructure.llm.openai_agents_adapter import OpenAIAgentsLLMOrchestrator


class TestLLMOrchestrator:
    def __init__(self, sql_use_case):
        self.sql_use_case = sql_use_case

    async def handle(self, user_query: str) -> str:
        if "查询" in user_query or "库存" in user_query:
            rows = await self.sql_use_case.execute("SELECT * FROM inventory LIMIT 20")
            return f"SQL结果: {rows}"
        return f"测试模式回复: {user_query}"


def build_agent_orchestrator() -> AgentOrchestrator:
    rag_use_case = RunRagQueryUseCase()
    sql_port = MysqlReadonlyAdapter({"database": "mockdb", "table": ["inventory"]})
    sql_use_case = RunSqlUseCase(sql_prot=sql_port, allow_tables={"inventory"})
    request_action_use_case = RequestAdminActionUseCase()

    if os.getenv("APP_ENV") == "test":
        llm_orchestrator = TestLLMOrchestrator(sql_use_case=sql_use_case)
    else:
        llm_orchestrator = OpenAIAgentsLLMOrchestrator(
            rag_use_case=rag_use_case,
            sql_use_case=sql_use_case,
            request_action_use_case=request_action_use_case,
        )

    return AgentOrchestrator(llm_orchestrator=llm_orchestrator)
