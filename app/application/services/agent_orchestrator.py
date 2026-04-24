class AgentOrchestrator:
    def __init__(self, llm_orchestrator):
        self.llm_orchestrator = llm_orchestrator

    async def handle(self, user_query: str) -> dict:
        result = await self.llm_orchestrator.handle(user_query)
        return {"answer": result}