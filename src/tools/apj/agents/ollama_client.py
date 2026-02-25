"""
ollama_client.py — APJ Agent Ollama Connection

Single responsibility: configure and return a pydantic_ai OpenAIModel
pointed at the local Ollama OpenAI-compatible endpoint.

Connection pattern (mirrors dgt_engine/game_engine/model_factory.py):
  - Base URL: http://localhost:11434/v1
  - Auth:     OPENAI_API_KEY = "ollama" (dummy)
  - Keep-alive: -1 (Iron Frame — model stays loaded)
"""

import os

from loguru import logger
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings

# Default model for the Archivist — 3b chosen for coherence reasoning quality
ARCHIVIST_MODEL = "llama3.2:3b"
OLLAMA_BASE_URL = "http://localhost:11434"


def get_ollama_model(
    model_name: str = ARCHIVIST_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    timeout: float = 60.0,
) -> OpenAIModel:
    """
    Configure and return an OpenAIModel backed by local Ollama.

    Args:
        model_name:  Ollama model tag (e.g. "llama3.2:3b").
        temperature: Sampling temperature. 0.3 = analytical, 0.8 = creative.
        max_tokens:  Max response tokens.
        timeout:     Request timeout in seconds.

    Returns:
        Configured OpenAIModel instance ready for pydantic_ai Agent use.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_BASE_URL)

    # Wire pydantic_ai to use Ollama's OpenAI-compat endpoint
    os.environ.setdefault("OLLAMA_BASE_URL", base_url)
    os.environ["OPENAI_BASE_URL"] = f"{base_url}/v1"
    os.environ["OPENAI_API_KEY"] = "ollama"

    settings = ModelSettings(
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body={"keep_alive": -1},  # Iron Frame — keep model loaded
        timeout=timeout,
    )

    # Strip "ollama:" prefix if caller passes the full tag style
    actual_model = model_name.replace("ollama:", "")

    logger.debug(
        f"OllamaClient configured: model={actual_model}, "
        f"base_url={base_url}, temp={temperature}"
    )

    return OpenAIModel(actual_model, settings=settings)
