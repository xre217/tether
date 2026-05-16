"""Zero effect verifier — the 'Tether verifies' layer.

Takes a Zero build result and checks it against a set of expectations:
- Required capabilities must match allowed sets
- Memory footprint must be within budget
- No hidden network, filesystem, or process effects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from tether.zero.compiler import ZeroBuildResult


@dataclass
class VerificationResult:
    """Result of verifying a Zero program's declared effects."""

    passed: bool
    program: str
    target: str
    checks: Dict[str, bool] = field(default_factory=dict)
    details: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"[{status}] {self.program} ({self.target})"]
        for check, ok in self.checks.items():
            icon = "✓" if ok else "✗"
            lines.append(f"  {icon} {check}")
        for err in self.errors:
            lines.append(f"  ! {err}")
        return "\n".join(lines)


class ZeroVerifier:
    """Verifies that a compiled Zero program meets Tether's safety standards.

    Default policy: no network, no filesystem writes, no process spawning
    unless explicitly allowed.
    """

    DEFAULT_ALLOWED_CAPABILITIES = {"world", "stdio", "memory", "alloc"}
    DEFAULT_BLOCKED_CAPABILITIES = {"net", "fs", "proc", "env"}

    def __init__(
        self,
        allowed_caps: Optional[List[str]] = None,
        blocked_caps: Optional[List[str]] = None,
        max_binary_bytes: int = 1024 * 1024,  # 1MB
    ) -> None:
        self.allowed = set(allowed_caps) if allowed_caps else self.DEFAULT_ALLOWED_CAPABILITIES
        self.blocked = set(blocked_caps) if blocked_caps else self.DEFAULT_BLOCKED_CAPABILITIES
        self.max_bytes = max_binary_bytes

    def verify(self, build: ZeroBuildResult) -> VerificationResult:
        """Run all checks against a build result."""
        result = VerificationResult(
            passed=True,
            program=build.source_file,
            target=build.target,
        )

        # 1. Check compilation succeeded
        result.checks["compilation_success"] = build.success
        if not build.success:
            result.passed = False
            result.errors.append(f"Compilation failed: {build.error}")
            return result

        # 2. Check capabilities are within allowed set
        required = set(build.requires_capabilities)
        disallowed = required - self.allowed
        result.checks["capabilities_allowed"] = len(disallowed) == 0
        if disallowed:
            result.passed = False
            result.errors.append(
                f"Requires blocked capabilities: {', '.join(sorted(disallowed))}"
            )
        else:
            result.details.append(f"Capabilities: {', '.join(sorted(required))}")

        # 3. Check no blocked capabilities are used
        blocked_used = required & self.blocked
        result.checks["no_blocked_capabilities"] = len(blocked_used) == 0
        if blocked_used:
            result.passed = False
            result.errors.append(
                f"Uses blocked capabilities: {', '.join(sorted(blocked_used))}"
            )

        # 4. Check binary size is within budget
        result.checks["binary_size_ok"] = build.total_bytes <= self.max_bytes
        if build.total_bytes > self.max_bytes:
            result.passed = False
            result.errors.append(
                f"Binary too large: {build.total_bytes}B (max {self.max_bytes}B)"
            )
        else:
            result.details.append(f"Binary size: {build.total_bytes}B")

        # 5. Check function count is reasonable
        result.checks["function_count_ok"] = build.function_count <= 100
        if build.function_count > 100:
            result.passed = False
            result.errors.append(
                f"Too many functions: {build.function_count} (max 100)"
            )
        else:
            result.details.append(f"Functions: {build.function_count}")

        # 6. Detailed capability restrictions (from portableRuntime)
        restrictions = build.capability_restrictions
        for cap, status in restrictions.items():
            if status == "unavailable":
                # Already guaranteed by Zero's compiler — extra safety net
                result.details.append(f"Zero-blocked capability: {cap}")

        return result
