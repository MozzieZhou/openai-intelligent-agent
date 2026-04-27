

class MysqlReadonlyAdapter:
    def __init__(self, meta: dict):
        self.meta = meta
    
    async def query(self, sql:str) -> list[dict]:
        """
        执行SQL查询并返回结果,连接archery-query,登陆信息建议用公共配置账号密码,业务逻辑中控制人的可见度,在sqlPort中实现
        """
        if "SELECT 1" in sql:
            return [{"sql": sql, "rows": [{"test": 1}]}]

        print(
            f"执行SQL查询数据库: {self.meta.get('database', [])}，表：{self.meta.get('table', [])}，SQL语句: {sql}"
        )
        return [{"sql": sql, "rows": [{"id": "T11773902008348624414101079", "movie_name": "寒战1994"}]}]
