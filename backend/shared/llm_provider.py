"""LLM provider factory — OpenRouter (production) vs direct Claude (dev)."""

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Runtime-mutable model selection
_active_model = None

AVAILABLE_MODELS = {
    "anthropic/claude-sonnet-4": "Claude Sonnet 4",
    "openai/gpt-4o": "GPT-4o",
    "google/gemini-2.5-flash-preview": "Gemini 2.5 Flash",
}


def get_active_model_id() -> str:
    """Return the currently active model ID."""
    return _active_model or os.getenv("PRIMARY_MODEL", "anthropic/claude-sonnet-4")


def set_active_model(model_id: str):
    """Set the active model at runtime. Requires agent cache clear to take effect."""
    global _active_model
    _active_model = model_id


def get_model(temperature: float = 0):
    """
    Returns a LangChain chat model.

    USE_OPENROUTER=true (default, production): Routes through OpenRouter.
    Claude primary, can switch to GPT-4o/Gemini at runtime.

    USE_OPENROUTER=false (local dev): Direct Claude API, no routing overhead.
    """
    if os.getenv("USE_OPENROUTER", "true").lower() == "true":
        model_id = get_active_model_id()
        return ChatOpenAI(
            model=model_id,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=temperature,
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "https://qosina-demo-production.up.railway.app"),
                "X-Title": "Qosina Enterprise AI Assistant",
            },
        )
    else:
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=temperature,
        )
