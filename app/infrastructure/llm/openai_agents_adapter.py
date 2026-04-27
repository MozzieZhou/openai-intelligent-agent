import os
from datetime import datetime

from agents import Agent, Runner, function_tool, set_tracing_disabled
from dotenv import load_dotenv

load_dotenv()

set_tracing_disabled(False)

OPENROUTER_API_KEY = os.getenv("LLM_API_KEY")
OPENROUTER_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENROUTER_API_BASE"] = OPENROUTER_BASE_URL

def _resolve_model_name() -> str:
    configured = os.getenv("DEFAULT_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    if configured.startswith("litellm/"):
        return configured
    return f"litellm/openrouter/{configured}"


class OpenAIAgentsLLMOrchestrator:
    def __init__(self, rag_use_case, sql_use_case, request_action_use_case):
        self.rag_use_case = rag_use_case
        self.sql_use_case = sql_use_case
        self.request_action_use_case = request_action_use_case
        self.model = _resolve_model_name()

        @function_tool
        async def rag_tool(query: str) -> str:
            docs = await self.rag_use_case.execute(query)
            return str(docs)

        @function_tool
        async def sql_tool(query: str) -> str:
            rows = await self.sql_use_case.execute(query)
            return str(rows)

        @function_tool(strict_mode=False)
        async def approval_tool(action_name: str, payload: dict) -> str:
            ticket = await self.request_action_use_case.execute(action_name, payload)
            ticket_id = getattr(ticket, "ticket_id", ticket.get("ticket_id", "UNKNOWN"))
            return f"已创建审批单 {ticket_id}"

        self.rag_agent = Agent(
            name="RAGAgent",
            instructions=(
                "处理上下文与知识问答，必须先调用 rag_tool。"
                "如果问题需要数据库字段级结果（如订单详情、库存明细、指标数值），"
                "先输出可执行查询意图，再转交 SQLAgent，不要继续重复调用 rag_tool。"
            ),
            model=self.model,
            tools=[rag_tool],
            handoffs=[],
        )
        self.sql_agent = Agent(
            name="SQLAgent",
            instructions=(
                "处理 SQL/指标查询。"
                "当用户提问涉及库存、销量、查询等数据问题时，必须先调用 sql_tool，"
                "若用户给出自然语言，先生成只读 SELECT 语句再调用。"
                "严格遵守用户给出的数据库信息、表信息进行查询，禁止超出范围查询。"
            ),
            model=self.model,
            tools=[sql_tool],
        )
        self.action_agent = Agent(
            name="ActionAgent",
            instructions="处理后台操作请求，必须调用 approval_tool 创建审批单。",
            model=self.model,
            tools=[approval_tool],
        )

        # Allow multi-step chain: RAG context -> SQL data query.
        self.rag_agent.handoffs = [self.sql_agent, self.action_agent]

        self.root_agent = Agent(
            name="BusinessOrchestrator",
            instructions=(
                "你是总控编排 Agent：\n"
                "1) 如果用户已明确给出数据库/表名/字段/查询条件，直接转交 SQLAgent 并调用 sql_tool，不必先走 RAG\n"
                "2) 如果用户问题缺少结构化查询信息，先转交 RAGAgent 获取上下文，再按需转交 SQLAgent\n"
                "3) 若是后台操作，转交 ActionAgent 创建审批单"
            ),
            model=self.model,
            handoffs=[self.rag_agent, self.sql_agent, self.action_agent],
        )

    async def handle(self, user_query: str) -> str:
        _debug_print("RootAgent.input", user_query)
        result = await Runner.run(self.root_agent, user_query)
        final_output = str(result.final_output)
        _debug_print("RootAgent.output", final_output)
        return final_output
