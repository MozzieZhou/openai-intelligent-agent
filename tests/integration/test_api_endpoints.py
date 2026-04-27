from pathlib import Path
import os
import sys

from fastapi.testclient import TestClient


def test_chat_endpoint_returns_answer_and_prints_thinking(capsys, monkeypatch) -> None:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ["APP_ENV"] = "test"
    from app.bootstrap.app_factory import create_app
    from app.entrypoints.api import chat_controller

    async def fake_handle(query: str) -> dict:
        print("[Thinking][BusinessOrchestrator] 先判断用户问题应该转给哪个 Agent")
        print("[Thinking][SQLAgent] 需要生成只读 SQL 并调用 sql_tool")
        print("SQL 正在调用: SELECT * FROM inventory LIMIT 20")
        return {"answer": "SQL结果: []"}

    monkeypatch.setattr(chat_controller.orchestrator, "handle", fake_handle)

    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={"user_id": "u1", "session_id": "s1", "query": "请查询库存低于50的商品"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "SQL结果" in body["answer"]

    captured = capsys.readouterr()
    assert "[Thinking][BusinessOrchestrator]" in captured.out
    assert "[Thinking][SQLAgent]" in captured.out
    assert "SQL 正在调用" in captured.out
