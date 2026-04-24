import os
from agents import Agent, SQLiteSession, set_tracing_disabled,Runner
from openai.types.responses import ResponseTextDeltaEvent
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
    instructions="You are a stupid assistant.",
    model="litellm/openrouter/stepfun/step-3.5-flash",  # 通过 LiteLLM 路由到 OpenRouter
)

async def main():
    result = Runner.run_streamed(agent, "tell me 5 jokes.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())




