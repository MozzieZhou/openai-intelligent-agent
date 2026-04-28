import importlib
import os
from pathlib import Path
import sys

import litellm


def test_openai_agents_adapter_enables_langfuse_callback_for_compatible_sdk(monkeypatch) -> None:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("LANGFUSE_OTEL_HOST", raising=False)
    litellm.callbacks = []
    litellm.success_callback = []

    from app.infrastructure.llm import openai_agents_adapter

    importlib.reload(openai_agents_adapter)

    assert os.environ["LANGFUSE_HOST"] == "https://us.cloud.langfuse.com"
    assert os.environ["LANGFUSE_OTEL_HOST"] == "https://us.cloud.langfuse.com"
    assert "langfuse" not in litellm.success_callback
    assert "langfuse_otel" in litellm.callbacks
