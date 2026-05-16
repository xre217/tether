"""Zero compiler wrapper — compiles .0 files and parses structured JSON output.

Every Zero compilation produces a machine-readable contract:
- requiresCapabilities: what system effects the program needs
- capabilityRestrictions: what's explicitly blocked
- sizeBreakdown: exact binary footprint
- stdlibHelpers: each std call with its effects and allocation behavior
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ZeroBuildResult:
    """Result of a Zero compilation with parsed contract metadata."""

    success: bool
    source_file: str
    target: str
    requires_capabilities: List[str] = field(default_factory=list)
    capability_restrictions: Dict[str, str] = field(default_factory=dict)
    function_count: int = 0
    total_bytes: int = 0
    artifact_path: Optional[Path] = None
    elapsed_ms: float = 0.0
    raw_json: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def from_check_json(cls, data: Dict[str, Any]) -> "ZeroBuildResult":
        """Parse a `zero check --json` response."""
        return cls(
            success=data.get("ok", False),
            source_file=data.get("sourceFile", ""),
            target=data.get("target", ""),
            requires_capabilities=data.get("requiresCapabilities", []),
            raw_json=data,
        )

    @classmethod
    def from_size_json(cls, data: Dict[str, Any]) -> "ZeroBuildResult":
        """Parse a `zero size --json` response."""
        breakdown = data.get("sizeBreakdown", {})
        summary = breakdown.get("summary", {})
        sections = breakdown.get("sections", [])
        total = sum(s.get("bytes", 0) for s in sections)

        caps = data.get("requiresCapabilities", [])
        port = data.get("portableRuntime", {})
        restrictions = port.get("capabilityRestrictions", {})

        funcs = summary.get("functionCount", 0)

        return cls(
            success=True,
            source_file=data.get("sourceFile", ""),
            target=data.get("target", ""),
            requires_capabilities=caps,
            capability_restrictions=restrictions,
            function_count=funcs,
            total_bytes=total,
            raw_json=data,
        )


class ZeroCompiler:
    """Wrapper around the `zero` CLI tool.

    Finds the binary at ~/.zero/bin/zero or $PATH.
    """

    def __init__(self, zero_path: Optional[str] = None) -> None:
        if zero_path:
            self._binary = zero_path
        else:
            default = Path.home() / ".zero" / "bin" / "zero"
            self._binary = str(default) if default.exists() else "zero"

    @property
    def binary(self) -> str:
        return self._binary

    def version(self) -> str:
        """Return the installed Zero version string."""
        result = subprocess.run(
            [self._binary, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() or result.stderr.strip()

    def check(self, source: str, workdir: Optional[Path] = None) -> ZeroBuildResult:
        """Run `zero check --json` on a .0 file.

        Returns parsed contract metadata without building an executable.
        Fast — typically <50ms.
        """
        cmd = [self._binary, "check", "--json", source]
        start = time.monotonic()
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
            cwd=str(workdir) if workdir else None,
        )
        elapsed = (time.monotonic() - start) * 1000

        if result.returncode != 0:
            return ZeroBuildResult(
                success=False,
                source_file=source,
                target="",
                error=result.stderr.strip() or result.stdout.strip(),
                elapsed_ms=round(elapsed, 1),
            )

        try:
            data = json.loads(result.stdout)
            build = ZeroBuildResult.from_check_json(data)
            build.elapsed_ms = round(elapsed, 1)
            return build
        except json.JSONDecodeError as exc:
            return ZeroBuildResult(
                success=False,
                source_file=source,
                target="",
                error=f"JSON parse error: {exc}",
                elapsed_ms=round(elapsed, 1),
            )

    def size(self, source: str, workdir: Optional[Path] = None) -> ZeroBuildResult:
        """Run `zero size --json` on a .0 file.

        Returns detailed size breakdown, retention reasons, and optimization hints.
        """
        cmd = [self._binary, "size", "--json", source]
        start = time.monotonic()
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
            cwd=str(workdir) if workdir else None,
        )
        elapsed = (time.monotonic() - start) * 1000

        if result.returncode != 0:
            return ZeroBuildResult(
                success=False,
                source_file=source,
                target="",
                error=result.stderr.strip() or result.stdout.strip(),
                elapsed_ms=round(elapsed, 1),
            )

        try:
            data = json.loads(result.stdout)
            build = ZeroBuildResult.from_size_json(data)
            build.elapsed_ms = round(elapsed, 1)
            return build
        except json.JSONDecodeError as exc:
            return ZeroBuildResult(
                success=False,
                source_file=source,
                target="",
                error=f"JSON parse error: {exc}",
                elapsed_ms=round(elapsed, 1),
            )

    def build(
        self,
        source: str,
        target: str = "darwin-arm64",
        profile: str = "small",
        out_dir: Optional[Path] = None,
        workdir: Optional[Path] = None,
    ) -> ZeroBuildResult:
        """Build a .0 file into a native executable.

        Returns the build result with artifact path and size breakdown.
        """
        out = out_dir or Path(".zero") / "out"
        exe_name = Path(source).stem
        exe_path = out / exe_name

        cmd = [
            self._binary, "build",
            f"--profile", profile,
            f"--target", target,
            source,
            "--out", str(exe_path),
        ]

        start = time.monotonic()
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60,
            cwd=str(workdir) if workdir else None,
        )
        elapsed = (time.monotonic() - start) * 1000

        if result.returncode != 0:
            return ZeroBuildResult(
                success=False,
                source_file=source,
                target=target,
                error=result.stderr.strip() or result.stdout.strip(),
                elapsed_ms=round(elapsed, 1),
            )

        # Then get size metadata
        size_result = self.size(source, workdir=workdir)
        size_result.artifact_path = exe_path.resolve() if exe_path.exists() else None
        size_result.elapsed_ms = round(elapsed, 1)
        return size_result

    def run(
        self,
        source: str,
        workdir: Optional[Path] = None,
    ) -> str:
        """Run a .0 file with `zero run`.

        Returns stdout output.
        """
        cmd = [self._binary, "run", source]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
            cwd=str(workdir) if workdir else None,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"zero run failed (exit {result.returncode}):\n"
                f"{result.stderr.strip()}"
            )
        return result.stdout.strip()

    def verify_effects(
        self,
        source: str,
        allowed_capabilities: Optional[List[str]] = None,
        workdir: Optional[Path] = None,
    ) -> ZeroBuildResult:
        """Check a .0 file and verify its required capabilities are acceptable.

        Returns the check result; raises if disallowed capabilities are found.
        """
        build = self.check(source, workdir=workdir)
        if not build.success:
            return build

        if allowed_capabilities is None:
            allowed_capabilities = ["world", "stdio", "memory"]

        required = set(build.requires_capabilities)
        allowed = set(allowed_capabilities)

        disallowed = required - allowed
        if disallowed:
            build.error = (
                f"Disallowed capabilities: {', '.join(sorted(disallowed))}. "
                f"Allowed: {', '.join(sorted(allowed))}."
            )
            build.success = False

        return build
