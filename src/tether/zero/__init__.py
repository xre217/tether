"""Tether Zero Integration — Grok reasons, Zero compiles, Tether verifies.

The three-layer architecture:
1. Grok/xAI reasons about which tool to use
2. Zero compiles a native binary with explicit effect declarations
3. Tether verifies the tool's declared effects match expectations
"""

from tether.zero.compiler import ZeroCompiler, ZeroBuildResult
from tether.zero.verifier import ZeroVerifier, VerificationResult

__all__ = [
    "ZeroCompiler",
    "ZeroBuildResult",
    "ZeroVerifier",
    "VerificationResult",
]
