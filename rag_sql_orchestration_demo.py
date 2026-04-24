import asyncio
import os
import sqlite3
from typing import Any

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
BUSINESS_DB = "business_demo.db"

# Mini "RAG corpus": replace with your vector search in real projects.
KNOWLEDGE_BASE = [
    {
        "id": "doc-1",
        "title": "差旅报销制度",
        "content": "出差餐费单日上限200元，超额部分需主管审批；打车需提供行程截图和发票。",
    },
    {
        "id": "doc-2",
        "title": "采购补货策略",
        "content": "库存低于50定义为低库存，建议按近7日销量的1.5倍进行补货，优先保障核心SKU。",
    },
    {
        "id": "doc-3",
        "title": "活动运营规则",
        "content": "促销期间可临时放宽库存警戒线到40，但需在活动结束后24小时内恢复至50以上。",
    },
]


def _normalize_tokens(text: str) -> list[str]:
    separators = ["，", "。", ",", ".", "；", ";", "：", ":", "\n", "\t"]
    normalized = text.lower()
    for sep in separators:
        normalized = normalized.replace(sep, " ")
    return [t for t in normalized.split() if t]


def _score_doc(query: str, text: str) -> int:
    query_l = query.lower()
    text_l = text.lower()
    score = 0

    # 1) Token substring hit: works for English terms and mixed text.
    for token in _normalize_tokens(query_l):
        if token and token in text_l:
            score += 3

    # 2) Character overlap fallback: helps Chinese lexical matching.
    query_chars = {c for c in query_l if c.strip()}
    text_chars = {c for c in text_l if c.strip()}
    score += len(query_chars & text_chars)
    return score


@function_tool
def rag_search(query: str, top_k: int = 2) -> str:
    """Retrieve policy/knowledge snippets by lexical matching.

    Args:
        query: User question.
        top_k: Max number of docs to return.
    """
    scored: list[tuple[int, dict[str, str]]] = []
    for doc in KNOWLEDGE_BASE:
        score = _score_doc(query, doc["title"] + " " + doc["content"])
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_docs = [doc for score, doc in scored if score > 0][: max(1, top_k)]

    if not top_docs:
        # Demo fallback: return top-1 doc to avoid empty context in tutorials.
        top_docs = [scored[0][1]]

    lines = []
    for i, doc in enumerate(top_docs, start=1):
        lines.append(f"{i}. [{doc['id']}] {doc['title']} - {doc['content']}")
    return "\n".join(lines)


def init_demo_db() -> None:
    conn = sqlite3.connect(BUSINESS_DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            stock INTEGER NOT NULL,
            weekly_sales INTEGER NOT NULL
        )
        """
    )
    cur.execute("SELECT COUNT(*) FROM inventory")
    count = cur.fetchone()[0]
    if count == 0:
        cur.executemany(
            "INSERT INTO inventory (sku, product_name, stock, weekly_sales) VALUES (?, ?, ?, ?)",
            [
                ("SKU-1001", "无线鼠标", 38, 90),
                ("SKU-1002", "机械键盘", 67, 52),
                ("SKU-1003", "USB-C 扩展坞", 29, 41),
                ("SKU-1004", "显示器支架", 85, 24),
                ("SKU-1005", "降噪耳机", 44, 76),
            ],
        )
    conn.commit()
    conn.close()


def _sanitize_sql(sql: str) -> str:
    cleaned = sql.strip()
    cleaned = cleaned.replace("```sql", "").replace("```", "").strip()
    if cleaned.lower().startswith("sql\n"):
        cleaned = cleaned[4:].strip()
    return cleaned


@function_tool
def run_sql(query: str) -> str:
    """Execute read-only SQL on the demo inventory database.

    Args:
        query: SELECT statement only.
    """
    cleaned = _sanitize_sql(query)
    if not cleaned.lower().startswith("select"):
        return "仅允许执行 SELECT 查询。"

    conn = sqlite3.connect(BUSINESS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(cleaned)
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        return f"SQL执行失败: {e}"
    conn.close()

    if not rows:
        return "查询结果为空。"

    result: list[dict[str, Any]] = [dict(row) for row in rows]
    return str(result)


rag_agent = Agent(
    name="RAGAgent",
    instructions=(
        "你是知识库专家。处理制度、规范、策略类问题。"
        "优先调用 rag_search 检索，再基于检索片段作答并标注来源doc id。"
    ),
    model=MODEL,
    tools=[rag_search],
)

sql_agent = Agent(
    name="SQLAgent",
    instructions=(
        "你是数据分析专家。处理库存/销量/指标问题。"
        "必须先调用 run_sql 获取数据，再给出结论。"
        "调用 run_sql 时仅传 SELECT 语句。"
    ),
    model=MODEL,
    tools=[run_sql],
)

orchestrator = Agent(
    name="BusinessOrchestrator",
    instructions=(
        "你是智能编排总控：\n"
        "1) 制度/流程/规则问题 -> 转交 RAGAgent\n"
        "2) 数据查询/统计问题 -> 转交 SQLAgent\n"
        "3) 混合问题可串行转交两个专家，再统一总结为可执行建议。"
    ),
    model=MODEL,
    handoffs=[rag_agent, sql_agent],
)

session = SQLiteSession("rag_sql_demo", "conversations.db")


async def ask(question: str) -> None:
    result = await Runner.run(orchestrator, question, session=session)
    print(f"\nQ: {question}")
    print(f"A: {result.final_output}")


async def main() -> None:
    init_demo_db()

    await ask("根据公司制度，差旅餐费报销有什么限制？")
    await ask("请查询库存低于50的商品，返回 product_name、stock、weekly_sales。")
    await ask("结合前两问，给出三条补货建议。")

    items = await session.get_items()
    print(f"\n[Session Items] 当前会话累计 {len(items)} 条记录")


if __name__ == "__main__":
    asyncio.run(main())
