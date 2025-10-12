# Location: /src/ice_lightrag/model_provider.py
# Purpose: Model provider factory for LightRAG supporting OpenAI and Ollama
# Why: Enables user choice between paid OpenAI API ($5/mo) and free local Ollama ($0/mo)
# Relevant Files: ice_rag_fixed.py, LOCAL_LLM_GUIDE.md, CLAUDE.md

import os
import logging
import requests
from typing import Tuple, Dict, Any, Callable
from lightrag.utils import EmbeddingFunc

logger = logging.getLogger(__name__)

# Try importing LightRAG providers
try:
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI provider not available - lightrag.llm.openai import failed")

try:
    from lightrag.llm.ollama import ollama_model_complete, ollama_embed
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama provider not available - lightrag.llm.ollama import failed")


def check_ollama_service(host: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama service is running

    Args:
        host: Ollama service URL

    Returns:
        True if service is healthy, False otherwise
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama service check failed: {e}")
        return False


def check_ollama_model_available(model_name: str, host: str = "http://localhost:11434") -> bool:
    """
    Check if specific Ollama model is pulled and available

    Args:
        model_name: Model name (e.g., "qwen3:30b-32k")
        host: Ollama service URL

    Returns:
        True if model is available, False otherwise
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [m.get("name", "") for m in models]
            return model_name in available_models
        return False
    except Exception as e:
        logger.debug(f"Ollama model check failed: {e}")
        return False


def get_llm_provider() -> Tuple[Callable, Callable, Dict[str, Any]]:
    """
    Factory function to get LLM provider based on environment configuration

    Supports two providers:
    - OpenAI (default): Paid API, high quality
    - Ollama: Free local models, requires setup

    Environment Variables:
        LLM_PROVIDER: "openai" (default) or "ollama"
        LLM_MODEL: Model name (default: "gpt-4o-mini" for openai, "qwen3:30b-32k" for ollama)
        OLLAMA_HOST: Ollama service URL (default: "http://localhost:11434")
        OLLAMA_NUM_CTX: Context window size (default: 32768)
        EMBEDDING_PROVIDER: "openai" (default) or "ollama"
        EMBEDDING_MODEL: Embedding model (default: "nomic-embed-text" for ollama)
        EMBEDDING_DIM: Embedding dimension (default: 1536 for openai, 768 for ollama)

    Returns:
        Tuple of (llm_func, embed_func, model_config)
        - llm_func: LLM completion function
        - embed_func: Embedding function
        - model_config: Dict with llm_model_name, llm_model_kwargs (empty for OpenAI)

    Fallback:
        If Ollama requested but unavailable, falls back to OpenAI with warning
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", provider).lower()

    # OpenAI provider (default)
    if provider == "openai":
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI provider not available. Install lightrag with OpenAI support."
            )

        logger.info("✅ Using OpenAI provider (gpt-4o-mini)")
        return (
            gpt_4o_mini_complete,
            openai_embed,
            {}  # OpenAI uses defaults, no extra config needed
        )

    # Ollama provider (local)
    elif provider == "ollama":
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama provider not available - lightrag.llm.ollama import failed")
            return _fallback_to_openai("Ollama imports not available")

        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model_name = os.getenv("LLM_MODEL", "qwen3:30b-32k")
        num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "32768"))

        # Health checks
        if not check_ollama_service(ollama_host):
            logger.warning(f"Ollama service not running at {ollama_host}")
            return _fallback_to_openai(
                f"Ollama service not running. Start with: ollama serve"
            )

        if not check_ollama_model_available(model_name, ollama_host):
            logger.warning(f"Ollama model '{model_name}' not available")
            return _fallback_to_openai(
                f"Model not found. Pull with: ollama pull {model_name}"
            )

        # Embedding configuration
        if embedding_provider == "ollama":
            # Default embedding model (nomic-embed-text:latest is the full name)
            embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
            embedding_dim = int(os.getenv("EMBEDDING_DIM", "768"))

            # Check embedding model availability
            if not check_ollama_model_available(embedding_model, ollama_host):
                logger.warning(f"Ollama embedding model '{embedding_model}' not available")
                logger.info(f"Pull with: ollama pull {embedding_model}")
                return _fallback_to_openai(f"Embedding model not found: {embedding_model}")

            embed_func = EmbeddingFunc(
                embedding_dim=embedding_dim,
                max_token_size=8192,
                func=lambda texts: ollama_embed(
                    texts,
                    embed_model=embedding_model,
                    host=ollama_host
                )
            )
            logger.info(f"✅ Using Ollama embeddings ({embedding_model}, {embedding_dim}-dim)")
        else:
            # Hybrid: Ollama LLM + OpenAI embeddings
            if not OPENAI_AVAILABLE:
                logger.error("OpenAI embeddings requested but not available")
                return _fallback_to_openai("OpenAI not available for embeddings")

            embed_func = openai_embed
            logger.info("✅ Using hybrid: Ollama LLM + OpenAI embeddings")

        logger.info(f"✅ Using Ollama provider ({model_name}, {num_ctx} context)")

        return (
            ollama_model_complete,
            embed_func,
            {
                "llm_model_name": model_name,
                "llm_model_kwargs": {
                    "host": ollama_host,
                    "options": {"num_ctx": num_ctx},
                    "timeout": 300
                }
            }
        )

    else:
        logger.error(f"Unknown LLM_PROVIDER: {provider}. Use 'openai' or 'ollama'")
        return _fallback_to_openai("Invalid provider")


def _fallback_to_openai(reason: str) -> Tuple[Callable, Callable, Dict[str, Any]]:
    """
    Fallback to OpenAI when Ollama unavailable

    Args:
        reason: Reason for fallback (logged as warning)

    Returns:
        OpenAI provider tuple

    Raises:
        RuntimeError: If OpenAI also unavailable
    """
    logger.warning(f"⚠️  Falling back to OpenAI: {reason}")

    if not OPENAI_AVAILABLE:
        raise RuntimeError(
            f"Fallback failed: {reason}\n"
            "OpenAI also unavailable. Either:\n"
            "1. Fix Ollama setup, or\n"
            "2. Set OPENAI_API_KEY for fallback"
        )

    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            f"Fallback failed: {reason}\n"
            "OPENAI_API_KEY not set. Either:\n"
            "1. Fix Ollama setup, or\n"
            "2. Set OPENAI_API_KEY environment variable"
        )

    logger.info("✅ Using OpenAI provider (fallback from Ollama)")
    return (
        gpt_4o_mini_complete,
        openai_embed,
        {}
    )


# Export for testing
__all__ = [
    'get_llm_provider',
    'check_ollama_service',
    'check_ollama_model_available'
]
