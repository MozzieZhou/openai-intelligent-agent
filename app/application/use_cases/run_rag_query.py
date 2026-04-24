class RunRagQueryUseCase:
    async def execute(self, query: str) -> str:
        return f"上下文摘要: {query}"
