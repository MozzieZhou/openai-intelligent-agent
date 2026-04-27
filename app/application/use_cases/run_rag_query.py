class RunRagQueryUseCase:
    async def execute(self, query: str) -> str:
        """
        执行RAG查询
        """
        print(f"RAG 正在调用: {query},电影查订单信息需要查dffl_movie数据库的t_new_order表，查询条件为Str的sn")
        return "电影查订单信息需要查dffl_movie数据库的t_new_order表，查询条件为Str的sn"
