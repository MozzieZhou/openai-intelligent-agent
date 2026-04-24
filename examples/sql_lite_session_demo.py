import os
from agents import Agent, SQLiteSession, set_tracing_disabled,Runner
import asyncio
from dotenv import load_dotenv

set_tracing_disabled(True)

load_dotenv()

OPENROUTER_API_KEY = os.getenv("LLM_API_KEY")
OPENROUTER_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENROUTER_API_BASE"] = OPENROUTER_BASE_URL


agent = Agent(
    name="Assistant",
    instructions="你是一个简洁的中文助手。",
    model="litellm/openrouter/stepfun/step-3.5-flash",  # 通过 LiteLLM 路由到 OpenRouter
)

session = SQLiteSession("conversation_123")

async def main():
    result = await Runner.run(
        agent,
        "What city is the Golden Gate Bridge in?",
        session=session,
    )
    print(result.final_output)

    result = await Runner.run(
        agent,
        "What state is it in?",
        session=session,
    )
    print(result.final_output)

    result = await Runner.run(
        agent,
        "What's the population?",
        session=session,
    )
    print(result.final_output)

    items = await session.get_items()
    print(items)


if __name__ == "__main__":
    asyncio.run(main())
