"""
Unified LLM client factory that routes to the correct SDK based on model name.

Providers:
    - openai_compat: Internal vLLM / open-source endpoint (OpenAI-compatible API)
    - gemini: Google Gemini via google-genai SDK
    - openai: OpenAI proprietary models (GPT-4o, GPT-5.5, etc.)
    - together: Together AI (Qwen, etc.)

Environment variables (loaded from .env at repo root):
    LLM_BASE_URL       – Base URL for the open-source vLLM endpoint
    LLM_API_KEY        – API key for the open-source endpoint
    GEMINI_API_KEY     – Google Gemini API key
    OPENAI_API_KEY     – OpenAI API key
    TOGETHER_API_KEY   – Together AI API key
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from model_config import get_model_config, get_provider

# Load .env from the repo root
_repo_root = Path(__file__).resolve().parent.parent
_env_file = _repo_root / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            if "=" in _line:
                _key, _, _val = _line.partition("=")
                _key = _key.strip()
                _val = _val.strip()
                if _key and _val and _key not in os.environ:
                    os.environ[_key] = _val


_RETRY_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 5


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMChoice:
    message: LLMMessage


@dataclass
class LLMUsage:
    total_tokens: int


@dataclass
class LLMResponse:
    choices: List[LLMChoice]
    usage: Optional[LLMUsage]


class LLMClient:
    """Unified interface for LLM calls across providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.provider = get_provider(model_name)
        self._client = None
        self._init_client()

    def _init_client(self):
        print(f">>>>>>>>>>>>>>>>>> {self.provider}")
        if self.provider == "openai_compat":
            from openai import OpenAI

            self._client = OpenAI(
                base_url=os.getenv("LLM_BASE_URL"),
                api_key=os.getenv("LLM_API_KEY", "unused"),
            )
        elif self.provider == "openai":
            from openai import OpenAI

            self._client = OpenAI(
                api_key=os.environ["OPENAI_API_KEY"],
            )
        elif self.provider == "gemini":
            from google import genai

            self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        elif self.provider == "together":
            from openai import OpenAI

            self._client = OpenAI(
                base_url="https://api.together.xyz/v1",
                api_key=os.environ["TOGETHER_API_KEY"],
            )

    def chat(
        self, messages: List[Dict[str, str]], temperature: float = 0.0, **kwargs
    ) -> LLMResponse:
        """Send a chat completion request with retries.

        For openai_compat (open-source models), includes special handling for
        the Harmony Token Crash (nudges temperature up to break deterministic
        token loops).
        """
        current_temperature = temperature
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                return self._dispatch(messages, current_temperature, **kwargs)
            except Exception as exc:
                err_str = str(exc)

                # Harmony Token Crash — only applies to open-source vLLM endpoints
                if self.provider == "openai_compat" and (
                    "Unexpected token 200002" in err_str
                    or "InternalServerError" in err_str
                ):
                    if attempt == _RETRY_ATTEMPTS:
                        raise
                    new_temp = current_temperature + 0.2
                    print(
                        f"   [WARN] Harmony parser crash hit (attempt {attempt}/{_RETRY_ATTEMPTS}). "
                        f"Nudging temperature from {current_temperature:.1f} to {new_temp:.1f}..."
                    )
                    current_temperature = new_temp
                    time.sleep(2)
                    continue

                # Standard retry for all providers
                if attempt == _RETRY_ATTEMPTS:
                    raise
                print(
                    f"   [WARN] {self.provider} API call failed (attempt {attempt}/{_RETRY_ATTEMPTS}): {exc}. "
                    f"Retrying in {_RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(_RETRY_DELAY_SECONDS)

    def _dispatch(
        self, messages: List[Dict[str, str]], temperature: float, **kwargs
    ) -> LLMResponse:
        if self.provider in ("openai_compat", "openai", "together"):
            return self._call_openai_style(messages, temperature, **kwargs)
        elif self.provider == "gemini":
            return self._call_gemini(messages, temperature, **kwargs)

        raise ValueError(f"Unknown provider: {self.provider}")

    def _call_openai_style(
        self, messages: List[Dict[str, str]], temperature: float, **kwargs
    ) -> LLMResponse:
        # extra_body is only valid for vLLM-compatible endpoints
        if self.provider != "openai_compat":
            kwargs.pop("extra_body", None)
        resp = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        content = resp.choices[0].message.content or ""
        total_tokens = resp.usage.total_tokens if resp.usage else 0
        return LLMResponse(
            choices=[LLMChoice(message=LLMMessage(role="assistant", content=content))],
            usage=LLMUsage(total_tokens=total_tokens),
        )

    def _call_gemini(
        self, messages: List[Dict[str, str]], temperature: float, **kwargs
    ) -> LLMResponse:
        from google.genai import types

        system_instruction = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append(
                    types.Content(
                        role="user", parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
            elif msg["role"] == "assistant":
                contents.append(
                    types.Content(
                        role="model", parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        content = response.text or ""
        total_tokens = 0
        if response.usage_metadata:
            total_tokens = (response.usage_metadata.prompt_token_count or 0) + (
                response.usage_metadata.candidates_token_count or 0
            )

        return LLMResponse(
            choices=[LLMChoice(message=LLMMessage(role="assistant", content=content))],
            usage=LLMUsage(total_tokens=total_tokens),
        )


# Convenience: cache clients per model to avoid re-initializing
_client_cache: Dict[str, LLMClient] = {}


def get_llm_client(model_name: str) -> LLMClient:
    """Get or create a cached LLMClient for the given model name."""
    print(f">>>>>>>>>>>>>>>>>> {model_name}")
    if model_name not in _client_cache:
        _client_cache[model_name] = LLMClient(model_name)
    return _client_cache[model_name]
