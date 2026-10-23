"""
Per-model inference constants loaded by run_simulation and conversation_generator.

Each entry in MODEL_CONFIGS maps a substring (matched case-insensitively against
the model name) to the sampling parameters that should be used for that model family.
Entries are checked in order; the first match wins.

Fields:
    temperature   – sampling temperature (float)
    extra_kwargs  – additional keyword args forwarded to client.chat.completions.create
                    (e.g. top_p, extra_body)
    provider      – "openai_compat" (default, uses internal vLLM endpoint),
                    "gemini", "openai", or "together"
"""

from typing import Any, Dict, List, Tuple

# (substring, config) pairs — checked in order, first match wins.
MODEL_CONFIGS: List[Tuple[str, Dict[str, Any]]] = [
    (
        "claude",
        {
            "temperature": 0.0,
            "extra_kwargs": {},
            "provider": "claude",
        },
    ),
    (
        "gemma",
        {
            "temperature": 1.0,
            "extra_kwargs": {"top_p": 0.95, "extra_body": {"top_k": 64}},
            "provider": "openai_compat",
        },
    ),
    (
        "gpt-oss",
        {
            "temperature": 1.0,
            "extra_kwargs": {"top_p": 1.0, "extra_body": {"reasoning_effort": "high"}},
            "provider": "openai_compat",
        },
    ),
    (
        "nemotron",
        {
            "temperature": 1.0,
            "extra_kwargs": {"top_p": 0.95},
            "provider": "openai_compat",
        },
    ),
    (
        "llama",
        {
            "temperature": 0.6,
            "extra_kwargs": {"top_p": 0.9},
            "provider": "openai_compat",
        },
    ),
    (
        "gemini",
        {
            "temperature": 1.0,
            "extra_kwargs": {},
            "provider": "gemini",
        },
    ),
    (
        "gpt-",
        {
            "temperature": 1.0,
            "extra_kwargs": {},
            "provider": "openai",
        },
    ),
    (
        "qwen",
        {
            "temperature": 0.7,
            "extra_kwargs": {},
            "provider": "together",
        },
    ),
]

# Fallback used when no entry in MODEL_CONFIGS matches.
DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "temperature": 0.0,
    "extra_kwargs": {},
    "provider": "openai_compat",
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Return the config dict for *model_name*, falling back to DEFAULT_MODEL_CONFIG."""
    lower = model_name.lower()
    for substring, config in MODEL_CONFIGS:
        if substring in lower:
            return config
    return DEFAULT_MODEL_CONFIG


def get_provider(model_name: str) -> str:
    """Return the provider string for a model name."""
    return get_model_config(model_name).get("provider", "openai_compat")
