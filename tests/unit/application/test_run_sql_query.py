from pathlib import Path
import sys

import pytest


class DummySqlPort:
    async def query(self, sql: str) -> list[dict]:
        return [{"ok": 1, "sql": sql}]


@pytest.mark.asyncio
async def test_run_sql_use_case_prints_sql_call(capsys) -> None:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app.application.use_cases.run_sql_query import RunSqlUseCase

    use_case = RunSqlUseCase(sql_port=DummySqlPort(), allow_tables={"inventory"})
    result = await use_case.execute("SELECT * FROM inventory LIMIT 1")

    assert result[0]["ok"] == 1
    captured = capsys.readouterr()
    assert "SQL 正在调用" in captured.out
