"""Tether Auth — Provider credential and configuration management.

Handles authentication to LLM backends (Ollama, LiteLLM, OpenAI-compatible APIs).
Provides a consistent interface for the rest of Tether to connect to any provider.
"""

from tether.auth.provider import (
    ProviderConfig,
    ProviderKind,
    ProviderRegistry,
    test_connection,
)
from tether.auth.credentials import (
    CredentialStore,
    MissingCredentialError,
    ProviderCredential,
)

__all__ = [
    "ProviderConfig",
    "ProviderKind",
    "ProviderRegistry",
    "test_connection",
    "CredentialStore",
    "MissingCredentialError",
    "ProviderCredential",
]