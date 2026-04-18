import os


def init_langsmith_observability() -> bool:
    """
    Enables LangSmith tracing when LANGSMITH_API_KEY is available.

    Returns:
        bool: True when tracing is enabled, else False.
    """
    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    if not api_key:
        print("[OBSERVABILITY] LangSmith disabled (LANGSMITH_API_KEY not set).")
        return False

    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "AI-SPY")

    print(
        f"[OBSERVABILITY] LangSmith tracing enabled for project: {os.getenv('LANGSMITH_PROJECT', 'AI-SPY')}"
    )
    return True
