

class MysqlReadonlyAdapter:
    def __init__(self, dict:dict):
        self.dict = dict
    
    async def query(self, sql:str) -> list[dict]:
        """
        执行SQL查询并返回结果,连接archery-query,登陆信息建议用公共配置账号密码,业务逻辑中控制人的可见度,在sqlPort中实现
        """
        print(f"执行SQL查询数据库: {self.dict.get('database', [])}，表：{self.dict.get('table', [])}，SQL语句: {sql}")

        return self.dict[sql]