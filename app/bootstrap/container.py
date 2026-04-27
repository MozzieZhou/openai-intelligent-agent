import os

from app.application.services.agent_orchestrator import AgentOrchestrator
from app.application.use_cases.request_admin_action import RequestAdminActionUseCase
from app.application.use_cases.run_rag_query import RunRagQueryUseCase
from app.application.use_cases.run_sql_query import RunSqlUseCase
from app.infrastructure.db.mysql_readonly_adapter import MysqlReadonlyAdapter
from app.infrastructure.llm.openai_agents_adapter import OpenAIAgentsLLMOrchestrator



def build_agent_orchestrator() -> AgentOrchestrator:
    rag_use_case = RunRagQueryUseCase()
    sql_port = MysqlReadonlyAdapter({"database": "mockdb", "table": ["inventory", "t_new_order"]})
    sql_use_case = RunSqlUseCase(sql_port=sql_port, allow_tables={"inventory"})
    request_action_use_case = RequestAdminActionUseCase()


    llm_orchestrator = OpenAIAgentsLLMOrchestrator(
        rag_use_case=rag_use_case,
        sql_use_case=sql_use_case,
        request_action_use_case=request_action_use_case,
    )

    return AgentOrchestrator(llm_orchestrator=llm_orchestrator)
