"""LLM provider factory — OpenRouter (production) vs direct Claude (dev)."""

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


def get_model(temperature: float = 0):
    """
    Returns a LangChain chat model.

    USE_OPENROUTER=true (default, production): Routes through OpenRouter.
    Claude primary, automatic failover to GPT-4o/Gemini if Claude is down.

    USE_OPENROUTER=false (local dev): Direct Claude API, no routing overhead.
    """
    if os.getenv("USE_OPENROUTER", "true").lower() == "true":
        return ChatOpenAI(
            model=os.getenv("PRIMARY_MODEL", "anthropic/claude-sonnet-4"),
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
