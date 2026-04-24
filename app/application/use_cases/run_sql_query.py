
from app.domain.policies.sql_policy import SqlPolicy
from app.domain.ports.sql_prot import SqlPort


class RunSqlUseCase:
    def __init__(self, sql_prot: SqlPort, allow_tables:set[str]):
        self.sql_prot = sql_prot
        self.policy = SqlPolicy(allow_tables)

    async def execute(self, sql:str) -> list[dict]:
        """
        执行SQL查询
        """
        valid, msg = self.policy.validate(sql)
        if not valid:
            return [{"error": msg}]
        print(f"SQL 正在调用: {sql}")
        return await self.sql_prot.query(sql)
