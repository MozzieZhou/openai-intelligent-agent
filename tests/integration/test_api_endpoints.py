from pathlib import Path
import os
import sys

from fastapi.testclient import TestClient


def test_chat_endpoint_triggers_mock_sql_and_returns_answer(capsys) -> None:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ["APP_ENV"] = "test"
    from app.bootstrap.app_factory import create_app

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
    assert "SQL 正在调用" in captured.out
