"""Structured decision audit trail for Tether.

Every model decision is logged as a structured JSON entry:
- What the model planned to do
- What tool was selected (if any)
- The tool's declared effect contract
- Whether it passed verification
- What actually happened
- The model's chain-of-thought (if available)

This makes every agent decision auditable by humans and by programs.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    """A single decision in the audit trail."""

    timestamp: str = ""
    session_id: str = ""
    turn: int = 0

    # What the user said
    user_message: str = ""

    # What the model planned (structured)
    model_thought: str = ""
    model_intent: str = ""  # e.g., "respond", "run_tool", "ground"
    proposed_tool: str = ""
    proposed_params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    # What Zero said (tool contract)
    tool_required_caps: List[str] = field(default_factory=list)
    tool_binary_bytes: int = 0
    tool_function_count: int = 0

    # Whether verification passed
    verification_passed: bool = False
    verification_errors: List[str] = field(default_factory=list)

    # What actually happened
    model_response: str = ""
    execution_stdout: str = ""
    execution_stderr: str = ""
    execution_exit_code: int = -1
    safety_net_triggered: bool = False
    safety_net_reason: str = ""

    # Elapsed
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def short_summary(self) -> str:
        if self.verification_passed and not self.safety_net_triggered:
            icon = "✓"
        elif self.safety_net_triggered:
            icon = "⚠"
        else:
            icon = "✗"

        parts = [f"[{icon}] turn={self.turn}"]
        if self.proposed_tool:
            parts.append(f"tool={self.proposed_tool}")
            parts.append(f"caps={','.join(self.tool_required_caps)}")
        else:
            parts.append("respond")
        parts.append(f"{self.elapsed_ms:.0f}ms")
        return " ".join(parts)


class AuditLog:
    """Append-only structured audit log.

    Each session gets a separate JSON lines file.
    Files go to ~/.tether/audit/ by default (persistent between sessions).
    """

    def __init__(self, session_id: Optional[str] = None, log_dir: Optional[Path] = None):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.log_dir = log_dir or Path.home() / ".tether" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.turn = 0
        self._file = self.log_dir / f"session_{self.session_id}.jsonl"
        self._entries: List[AuditEntry] = []

    def new_entry(self, user_message: str = "") -> AuditEntry:
        """Start a new audit entry for this turn."""
        self.turn += 1
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            turn=self.turn,
            user_message=user_message,
        )
        self._entries.append(entry)
        return entry

    def commit(self, entry: AuditEntry) -> None:
        """Write an entry to the log file."""
        entry.timestamp = datetime.now(timezone.utc).isoformat()
        with open(self._file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def recent(self, n: int = 10) -> List[AuditEntry]:
        """Return the most recent n entries from this session."""
        return self._entries[-n:]

    def summary(self) -> str:
        if not self._entries:
            return "No decisions logged yet."
        total = len(self._entries)
        verified = sum(1 for e in self._entries if e.verification_passed)
        safe = sum(1 for e in self._entries if e.safety_net_triggered)
        failed = total - verified
        return (
            f"Session {self.session_id}: {total} decisions, "
            f"{verified} verified, {safe} safety-net, {failed} failed"
        )

    def export_json(self) -> str:
        """Export full audit as a JSON array."""
        return json.dumps([e.to_dict() for e in self._entries], indent=2)


# ── Helper for formatting Zero tool manifest for model prompt ──────────────


def format_tool_manifest() -> str:
    """Build a structured tool manifest for the model prompt.

    Lists every available Zero tool with its effect contract.
    The model uses this to decide what tool to call.
    """
    from tether.zero.runner import ZeroToolRunner

    runner = ZeroToolRunner()
    tools = runner.list_tools()
    lines = ["\n## Available Zero Tools"]
    lines.append("When you need to take action, choose a tool from this list.")
    lines.append("Return your choice as JSON: {\"tool\": \"...\", \"params\": {...}}\n")

    for t in tools:
        try:
            result = runner.dry_run(t["name"])
            if result.passed_verification:
                caps = ", ".join(result.build.requires_capabilities) or "none"
                lines.append(f"  {t['name']} — {result.build.total_bytes}B, caps: [{caps}]")
            else:
                lines.append(f"  {t['name']} — verification failed")
        except Exception:
            lines.append(f"  {t['name']} — unavailable")

    lines.append("")
    return "\n".join(lines)
