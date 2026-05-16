"""Provider configuration and registry for LLM backends.

Defines supported provider types, their config schemas, and connection testing.
"""

from __future__ import annotations

import enum
import tomlkit
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, field_validator


class ProviderKind(str, enum.Enum):
    """Supported LLM provider backends."""

    OLLAMA = "ollama"
    LITELLM = "litellm"
    OPENAI_COMPATIBLE = "openai_compatible"


# ── Config schemas ──────────────────────────────────────────────────────────


class OllamaConfig(BaseModel):
    """Configuration for a local Ollama instance."""

    base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama server base URL",
    )
    model: str = Field(
        default="llama3.2",
        description="Default model to use",
    )
    timeout_seconds: int = Field(default=60, ge=1, le=300)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, v: str) -> str:
        v = v.rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v


class LiteLLMConfig(BaseModel):
    """Configuration for LiteLLM proxy or direct API."""

    model: str = Field(
        default="gpt-4o",
        description="Model identifier passed to LiteLLM",
    )
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    custom_llm_provider: Optional[str] = Field(
        default=None,
        description="Optional provider override (e.g. 'openai', 'anthropic')",
    )


class OpenAICompatibleConfig(BaseModel):
    """Configuration for any OpenAI-compatible API endpoint."""

    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="API base URL (must end in /v1)",
    )
    model: str = Field(default="gpt-4o", description="Model name")
    timeout_seconds: int = Field(default=120, ge=1, le=600)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, v: str) -> str:
        v = v.rstrip("/")
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v


# ── Runtime config ──────────────────────────────────────────────────────────


@dataclass
class ProviderConfig:
    """Complete provider configuration for use at runtime."""

    kind: ProviderKind = ProviderKind.OLLAMA
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    litellm: LiteLLMConfig = field(default_factory=LiteLLMConfig)
    openai: OpenAICompatibleConfig = field(default_factory=OpenAICompatibleConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """Parse from a dictionary (e.g. from TOML config)."""
        kind_str = data.get("kind", "ollama")
        try:
            kind = ProviderKind(kind_str)
        except ValueError:
            kind = ProviderKind.OLLAMA

        ollama_data = data.get("ollama", {})
        litellm_data = data.get("litellm", {})
        openai_data = data.get("openai_compatible", {})

        return cls(
            kind=kind,
            ollama=OllamaConfig(**ollama_data) if ollama_data else OllamaConfig(),
            litellm=LiteLLMConfig(**litellm_data) if litellm_data else LiteLLMConfig(),
            openai=OpenAICompatibleConfig(**openai_data) if openai_data else OpenAICompatibleConfig(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary for storage."""
        return {
            "kind": self.kind.value,
            "ollama": self.ollama.model_dump(exclude_none=True),
            "litellm": self.litellm.model_dump(exclude_none=True),
            "openai_compatible": self.openai.model_dump(exclude_none=True),
        }

    def active_model_name(self) -> str:
        """Return the model name for the currently active provider."""
        if self.kind == ProviderKind.OLLAMA:
            return self.ollama.model
        elif self.kind == ProviderKind.LITELLM:
            return self.litellm.model
        else:
            return self.openai.model

    def active_base_url(self) -> Optional[str]:
        """Return the base URL for the active provider, if applicable."""
        if self.kind == ProviderKind.OLLAMA:
            return self.ollama.base_url
        elif self.kind == ProviderKind.OPENAI_COMPATIBLE:
            return self.openai.base_url
        return None


# ── Registry ────────────────────────────────────────────────────────────────


class ProviderRegistry:
    """Loads, stores, and serves the current provider configuration."""

    _instance: Optional["ProviderRegistry"] = None

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        self._config = config or ProviderConfig()

    @classmethod
    def get_default(cls) -> "ProviderRegistry":
        """Return the singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def init_default(cls, config_path: Optional[Path] = None) -> "ProviderRegistry":
        """Initialize the singleton from a config file path."""
        if config_path and config_path.exists():
            with open(config_path, "rb") as f:
                data = tomlkit.load(f)
            provider_data = data.get("provider", {})
            config = ProviderConfig.from_dict(provider_data)
        else:
            config = ProviderConfig()
        cls._instance = cls(config)
        return cls._instance

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @config.setter
    def config(self, value: ProviderConfig) -> None:
        self._config = value

    def save(self, path: Path) -> None:
        """Write the current config to a TOML file."""
        data = {"provider": self._config.to_dict()}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            tomlkit.dump(data, f)

    @staticmethod
    def list_supported() -> List[Dict[str, Any]]:
        """List all supported providers with descriptions."""
        return [
            {
                "id": ProviderKind.OLLAMA.value,
                "name": "Ollama",
                "description": "Local LLM server (free, private, offline)",
                "url": "https://ollama.com/download",
                "needs_api_key": False,
            },
            {
                "id": ProviderKind.LITELLM.value,
                "name": "LiteLLM",
                "description": "Unified API for 100+ LLM providers",
                "url": "https://docs.litellm.ai/docs/proxy/config",
                "needs_api_key": True,
            },
            {
                "id": ProviderKind.OPENAI_COMPATIBLE.value,
                "name": "OpenAI-Compatible",
                "description": "Any OpenAI API-compatible endpoint (OpenAI, Groq, Together, etc.)",
                "url": "https://platform.openai.com/api-keys",
                "needs_api_key": True,
            },
        ]


# ── Connection testing ──────────────────────────────────────────────────────


def test_connection(config: ProviderConfig, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connectivity to the configured provider.

    Returns a dict with keys:
        success (bool)
        message (str) — human-readable result
        latency_ms (float) — round-trip time in milliseconds
    """
    import time

    start = time.monotonic()
    result: Dict[str, Any] = {"success": False, "message": "", "latency_ms": 0.0}

    try:
        if config.kind == ProviderKind.OLLAMA:
            result = _test_ollama(config.ollama)
        elif config.kind == ProviderKind.LITELLM:
            result = _test_litellm(config.litellm, api_key)
        elif config.kind == ProviderKind.OPENAI_COMPATIBLE:
            result = _test_openai_compatible(config.openai, api_key)

        elapsed = (time.monotonic() - start) * 1000
        result["latency_ms"] = round(elapsed, 1)

    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        result = {
            "success": False,
            "message": f"Connection failed: {exc}",
            "latency_ms": round(elapsed, 1),
        }

    return result


def _test_ollama(config: OllamaConfig) -> Dict[str, Any]:
    """Ping the Ollama server and list available models."""
    try:
        resp = httpx.get(
            f"{config.base_url}/api/tags",
            timeout=config.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        model_available = config.model in models

        return {
            "success": True,
            "message": (
                f"✓ Ollama reachable at {config.base_url}\n"
                f"  Server version: {data.get('version', 'unknown')}\n"
                f"  Available: {len(models)} model(s)\n"
                f"  Requested model '{config.model}': "
                f"{'✓ available' if model_available else '✗ not pulled yet (run: ollama pull ' + config.model + ')'}"
            ),
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": (
                f"✗ Could not connect to Ollama at {config.base_url}\n"
                "  Start Ollama with:  ollama serve\n"
                "  Or install from: https://ollama.com/download"
            ),
        }


def _test_litellm(config: LiteLLMConfig, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Verify LiteLLM is importable and configured."""
    try:
        import litellm  # type: ignore[import-untyped]
    except ImportError:
        return {
            "success": False,
            "message": (
                "✗ LiteLLM not installed.\n"
                "  Install with:  pip install 'tether[litellm]'"
            ),
        }

    if not api_key:
        return {
            "success": False,
            "message": (
                "✗ No API key configured for LiteLLM.\n"
                "  Set one with:  tether auth setup"
            ),
        }

    return {
        "success": True,
        "message": (
            f"✓ LiteLLM is installed and configured.\n"
            f"  Model: {config.model}\n"
            f"  Custom provider: {config.custom_llm_provider or '(none)'}\n"
            f"  (Full end-to-end test will run on first chat.)"
        ),
    }


def _test_openai_compatible(config: OpenAICompatibleConfig, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test connection to an OpenAI-compatible endpoint."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = httpx.get(
            f"{config.base_url}/models",
            headers=headers,
            timeout=config.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        model_available = config.model in models

        return {
            "success": True,
            "message": (
                f"✓ Connected to {config.base_url}\n"
                f"  Available: {len(models)} model(s)\n"
                f"  Requested model '{config.model}': "
                f"{'✓ available' if model_available else '✗ not found (available: ' + ', '.join(models[:10]) + '...)'}"
            ),
        }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            return {
                "success": False,
                "message": "✗ Authentication failed (401 Unauthorized). Check your API key.",
            }
        return {
            "success": False,
            "message": f"✗ API error {exc.response.status_code}: {exc.response.text[:200]}",
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "message": f"✗ Could not connect to {config.base_url}. Check the URL and your network.",
        }