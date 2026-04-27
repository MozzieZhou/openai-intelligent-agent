from pathlib import Path
import sys


class DummyUseCase:
    async def execute(self, *_args, **_kwargs):
        return "ok"


def test_rag_agent_can_handoff_to_sql_agent() -> None:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app.infrastructure.llm.openai_agents_adapter import OpenAIAgentsLLMOrchestrator

    orchestrator = OpenAIAgentsLLMOrchestrator(
        rag_use_case=DummyUseCase(),
        sql_use_case=DummyUseCase(),
        request_action_use_case=DummyUseCase(),
    )

    assert hasattr(orchestrator, "rag_agent")
    assert hasattr(orchestrator, "sql_agent")
    assert orchestrator.rag_agent.handoffs
    assert orchestrator.sql_agent in orchestrator.rag_agent.handoffs
