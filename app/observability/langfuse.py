from __future__ import annotations

import os


def setup_observability() -> None:
    """Install OpenInference instrumentation before any agent runs are started."""
    # Langfuse v3 prefers LANGFUSE_BASE_URL; some examples still use LANGFUSE_HOST.
    if "LANGFUSE_BASE_URL" not in os.environ and "LANGFUSE_HOST" in os.environ:
        os.environ["LANGFUSE_BASE_URL"] = os.environ["LANGFUSE_HOST"]

    try:
        from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

        OpenAIAgentsInstrumentor().instrument()
    except Exception as exc:  # pragma: no cover - observability must never stop local dev.
        print(f"[observability] OpenAI Agents instrumentation skipped: {exc}")

    try:
        from langfuse import get_client

        get_client()
    except Exception as exc:  # pragma: no cover - observability must never stop local dev.
        print(f"[observability] Langfuse client initialization skipped: {exc}")


def flush_langfuse() -> None:
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception as exc:  # pragma: no cover - tracing failures should not hide workflow output.
        print(f"[observability] Langfuse flush skipped: {exc}")
