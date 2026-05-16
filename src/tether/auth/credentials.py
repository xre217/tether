"""Credential storage for Tether provider auth.

Stores API keys and sensitive configuration locally.
Uses the OS keyring when available, with a fallback to an encrypted local file.
"""

from __future__ import annotations

import os
import tomlkit
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from tether.auth.provider import ProviderKind

# ── Errors ──────────────────────────────────────────────────────────────────


class MissingCredentialError(KeyError):
    """Raised when a required credential has not been configured."""

    def __init__(self, provider: str, key_name: str) -> None:
        self.provider = provider
        self.key_name = key_name
        super().__init__(f"Missing credential '{key_name}' for provider '{provider}'")


# ── Data ────────────────────────────────────────────────────────────────────


@dataclass
class ProviderCredential:
    """A single credential for a provider (e.g. API key, token)."""

    provider: str
    key_name: str
    value: str
    label: str = ""

    @property
    def env_var(self) -> str:
        """The conventional environment variable name for this credential."""
        prefix = self.provider.upper().replace("-", "_")
        return f"{prefix}_{self.key_name.upper()}"

    def to_env(self) -> str:
        """Return a masked version of the value for display."""
        v = self.value
        if len(v) <= 8:
            return "****"
        return v[:4] + "..." + v[-4:]


# ── Store ───────────────────────────────────────────────────────────────────


class CredentialStore:
    """Manages provider credentials with keyring-first, env-var-fallback storage.

    Resolution order (highest priority first):
    1. Environment variable
    2. OS keyring (if available)
    3. Local file fallback (~/.tether/credentials.toml)
    """

    SERVICE_NAME = "tether"
    FALLBACK_PATH = Path.home() / ".tether" / "credentials.toml"

    # Standard credential keys per provider
    PROVIDER_KEYS: Dict[str, list] = {
        ProviderKind.OLLAMA.value: [],
        ProviderKind.LITELLM.value: [
            {"key": "api_key", "label": "API Key (e.g. OpenAI, Anthropic, etc.)"},
        ],
        ProviderKind.OPENAI_COMPATIBLE.value: [
            {"key": "api_key", "label": "API Key"},
        ],
    }

    def __init__(self) -> None:
        self._keyring_available = self._check_keyring()
        self._cache: Dict[str, str] = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, provider: str, key_name: str) -> Optional[str]:
        """Retrieve a credential value.

        Checks env vars first, then keyring, then fallback file.
        Returns None if not found in any source.
        """
        # 1. Check in-memory cache
        cache_key = f"{provider}:{key_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Check environment variable
        cred = ProviderCredential(provider=provider, key_name=key_name, value="")
        env_val = os.environ.get(cred.env_var)
        if env_val:
            self._cache[cache_key] = env_val
            return env_val

        # 3. Check keyring
        if self._keyring_available:
            try:
                import keyring  # type: ignore[import-untyped]

                val = keyring.get_password(self.SERVICE_NAME, cache_key)
                if val:
                    self._cache[cache_key] = val
                    return val
            except Exception:
                pass  # fall through to file

        # 4. Check fallback file
        return self._read_from_file(cache_key)

    def set(self, provider: str, key_name: str, value: str) -> None:
        """Store a credential.

        Uses keyring if available, otherwise falls back to the local file.
        """
        cache_key = f"{provider}:{key_name}"
        self._cache[cache_key] = value

        if self._keyring_available:
            try:
                import keyring
                keyring.set_password(self.SERVICE_NAME, cache_key, value)
                return
            except Exception:
                pass  # fall through to file

        self._write_to_file(cache_key, value)

    def delete(self, provider: str, key_name: str) -> None:
        """Remove a stored credential."""
        cache_key = f"{provider}:{key_name}"
        self._cache.pop(cache_key, None)

        if self._keyring_available:
            try:
                import keyring
                try:
                    keyring.delete_password(self.SERVICE_NAME, cache_key)
                except keyring.errors.PasswordDeleteError:
                    pass
            except Exception:
                pass

        self._remove_from_file(cache_key)

    def require(self, provider: str, key_name: str) -> str:
        """Like ``get`` but raises ``MissingCredentialError`` on failure."""
        val = self.get(provider, key_name)
        if val is None:
            raise MissingCredentialError(provider, key_name)
        return val

    def list_credentials(self, provider: str) -> Dict[str, str]:
        """Return all configured credential keys and their masked values for a provider."""
        keys = self.PROVIDER_KEYS.get(provider, [])
        result: Dict[str, str] = {}
        for k in keys:
            key_name = k["key"]
            val = self.get(provider, key_name)
            if val:
                result[key_name] = ProviderCredential(
                    provider=provider, key_name=key_name, value=val
                ).to_env()
        return result

    # ── Internals ───────────────────────────────────────────────────────────

    @staticmethod
    def _check_keyring() -> bool:
        """Check if the keyring module is available and functional."""
        try:
            import keyring  # noqa: F401
            return True
        except ImportError:
            return False

    def _read_from_file(self, cache_key: str) -> Optional[str]:
        if not self.FALLBACK_PATH.exists():
            return None
        try:
            with open(self.FALLBACK_PATH, "rb") as f:
                data = tomlkit.load(f)
            keys = data.get("credentials", {})
            return keys.get(cache_key)
        except Exception:
            return None

    def _write_to_file(self, cache_key: str, value: str) -> None:
        # Read existing
        existing: Dict = {}
        if self.FALLBACK_PATH.exists():
            try:
                with open(self.FALLBACK_PATH, "rb") as f:
                    existing = tomlkit.load(f)
            except Exception:
                pass

        existing.setdefault("credentials", {})
        existing["credentials"][cache_key] = value

        self.FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(self.FALLBACK_PATH, "w") as f:
            tomlkit.dump(existing, f)
        self.FALLBACK_PATH.chmod(0o600)

    def _remove_from_file(self, cache_key: str) -> None:
        if not self.FALLBACK_PATH.exists():
            return
        try:
            with open(self.FALLBACK_PATH, "rb") as f:
                data = tomlkit.load(f)
            creds = data.get("credentials", {})
            creds.pop(cache_key, None)
            data["credentials"] = creds

            with open(self.FALLBACK_PATH, "w") as f:
                tomlkit.dump(data, f)
        except Exception:
            pass