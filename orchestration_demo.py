import asyncio
import os

from agents import Agent, Runner, SQLiteSession, function_tool, set_tracing_disabled
from dotenv import load_dotenv

set_tracing_disabled(True)
load_dotenv()

OPENROUTER_API_KEY = os.getenv("LLM_API_KEY")
OPENROUTER_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

if not OPENROUTER_API_KEY:
    raise ValueError("LLM_API_KEY is missing. Please set it in .env or environment variables.")

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENROUTER_API_BASE"] = OPENROUTER_BASE_URL

MODEL = "litellm/openrouter/stepfun/step-3.5-flash"


@function_tool
def get_weather(city: str) -> str:
    """Get simple weather info by city.

    Args:
        city: City name, e.g. Beijing.
    """
    weather_map = {
        "beijing": "晴，18C，北风2级",
        "shanghai": "多云，22C，东风3级",
        "guangzhou": "小雨，26C，南风2级",
    }
    return weather_map.get(city.lower(), f"{city}：暂无天气数据")


@function_tool
def calc(expr: str) -> str:
    """Evaluate a basic arithmetic expression safely.

    Args:
        expr: Expression with digits and + - * / ( ) . only.
    """
    safe_chars = set("0123456789+-*/(). ")
    if not expr or any(ch not in safe_chars for ch in expr):
        return "表达式包含不支持字符，仅允许数字和 + - * / ( ) ."
    try:
        value = eval(expr, {"__builtins__": {}}, {})
    except Exception as e:
        return f"计算失败: {e}"
    return f"{expr} = {value}"


weather_agent = Agent(
    name="WeatherAgent",
    instructions="你是天气专家。只回答天气相关问题，必要时调用 get_weather 工具。",
    model=MODEL,
    tools=[get_weather],
)

math_agent = Agent(
    name="MathAgent",
    instructions="你是计算专家。遇到数学计算问题时，优先调用 calc 工具给出结果。",
    model=MODEL,
    tools=[calc],
)

orchestrator = Agent(
    name="Orchestrator",
    instructions=(
        "你是总控编排 Agent。根据用户意图在下列专家间进行路由：\n"
        "1) 天气问题 -> 转交给 WeatherAgent\n"
        "2) 计算问题 -> 转交给 MathAgent\n"
        "3) 混合问题可先后转交多个专家，最后统一用中文总结。"
    ),
    model=MODEL,
    handoffs=[weather_agent, math_agent],
)

session = SQLiteSession("orchestration_demo", "conversations.db")


async def ask(question: str) -> None:
    result = await Runner.run(orchestrator, question, session=session)
    print(f"\nQ: {question}")
    print(f"A: {result.final_output}")


async def main() -> None:
    await ask("北京今天什么天气？")
    await ask("顺便算一下 (23.5 * 4 - 18) / 2")
    await ask("把前两问的结论合并成一段简短建议")

    items = await session.get_items()
    print(f"\n[Session Items] 当前会话累计 {len(items)} 条记录")


if __name__ == "__main__":
    asyncio.run(main())
