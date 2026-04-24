import os

from agents import Agent, Runner, function_tool, set_tracing_disabled
from dotenv import load_dotenv

load_dotenv()

set_tracing_disabled(True)

OPENROUTER_API_KEY = os.getenv("LLM_API_KEY")
OPENROUTER_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENROUTER_API_BASE"] = OPENROUTER_BASE_URL

def _resolve_model_name() -> str:
    configured = os.getenv("DEFAULT_MODEL", "stepfun/step-3.5-flash")
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

        rag_agent = Agent(
            name="RAGAgent",
            instructions="处理上下文与知识问答，必须先调用 rag_tool。",
            model=self.model,
            tools=[rag_tool],
        )
        sql_agent = Agent(
            name="SQLAgent",
            instructions=(
                "处理 SQL/指标查询。"
                "当用户提问涉及库存、销量、查询等数据问题时，必须先调用 sql_tool，"
                "若用户给出自然语言，先生成只读 SELECT 语句再调用。"
            ),
            model=self.model,
            tools=[sql_tool],
        )
        action_agent = Agent(
            name="ActionAgent",
            instructions="处理后台操作请求，必须调用 approval_tool 创建审批单。",
            model=self.model,
            tools=[approval_tool],
        )

        self.root_agent = Agent(
            name="BusinessOrchestrator",
            instructions=(
                "你是总控编排 Agent：\n"
                "1) 用户提出问题，先转交 RAGAgent 获取上下文\n"
                "2) 若是 SQL/指标查询，转交 SQLAgent 并调用 sql_tool\n"
                "3) 若是后台操作，转交 ActionAgent 创建审批单"
            ),
            model=self.model,
            handoffs=[rag_agent, sql_agent, action_agent],
        )

    async def handle(self, user_query: str) -> str:
        result = await Runner.run(self.root_agent, user_query)
        return str(result.final_output)
