"""
Tether Web App — Mounted inside the FastAPI server at /gradio.

Run with:
    uvicorn tether.web.server:app --host 0.0.0.0 --port 8080

This mounts the Gradio UI at /gradio and the API at /api/*.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

import gradio as gr
from tether.core.prompt import PROMPT_VERSION
from tether.grounding.exercises import (
    grounding_54321,
    grounding_breathe,
    grounding_here,
    grounding_body,
)
from tether.redteam.harness import TetherSimulator
from tether.zero.runner import ZeroToolRunner

# Dark theme
THEME = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="blue",
    neutral_hue="slate",
).set(
    button_primary_background_fill="#1e2937",
    button_primary_background_fill_hover="#334155",
)

# Detect active model
_active_model = "rule-based (safety net)"
try:
    from tether.auth import ProviderRegistry
    config_path = Path.home() / ".tether" / "config.toml"
    if config_path.exists():
        reg = ProviderRegistry.init_default(config_path)
        _active_model = f"{reg.config.kind.value}/{reg.config.active_model_name()}"
    else:
        if os.environ.get("OPENAI_COMPATIBLE_API_KEY"):
            _active_model = "groq/llama-3.3-70b-versatile"
        elif os.environ.get("XAI_API_KEY"):
            _active_model = "xai/grok-2-latest"
except Exception:
    pass


def build_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app."""
    simulator = TetherSimulator(use_model=True)

    with gr.Blocks(
        title="Tether — Verifiable AI", theme=THEME,
        css=".gradio-container {max-width: 980px !important;}"
    ) as demo:

        # Header
        gr.HTML(f"""
        <div style="background:#1e2937; padding:16px; border-radius:8px; margin-bottom:12px; border:1px solid #475569;">
            <h1 style="margin:0; color:#e0e7ff; font-size:28px;">TETHER</h1>
            <p style="margin:4px 0 0; color:#94a3b8; font-size:14px;">
                Verifiable AI — Prompt v{PROMPT_VERSION}<br>
                <strong style="color:#f87171;">You are talking to software. Not a person. Not a therapist.</strong>
            </p>
            <p style="margin:6px 0 0; color:#6ee7b7; font-size:12px;">
                ● {_active_model}
            </p>
        </div>
        """)

        with gr.Tabs():
            # === CHAT TAB ===
            with gr.Tab("Chat"):
                gr.Markdown(f"""
                ## Tether Chat
                Model: **{_active_model}**. Every response is logged to the audit trail.
                """)

                chatbot = gr.Chatbot(height=400, label="Tether", show_copy_button=True)
                msg = gr.Textbox(placeholder="Type here...", container=False, scale=7)
                with gr.Row():
                    clear = gr.Button("Clear")
                    audit_btn = gr.Button("Show last decision", size="sm", scale=0)

                # Chat state
                chat_state = gr.State([])

                def respond(message: str, history: List[List[str]]):
                    if not message or not message.strip():
                        return history, ""
                    response = simulator.respond([{"role": "user", "content": message}])
                    history.append([message, response])
                    return history, ""

                msg.submit(respond, [msg, chat_state], [chatbot, msg])
                clear.click(lambda: ([], ""), outputs=[chatbot, msg])

                def show_last_decision():
                    entries = simulator.audit.recent(1)
                    if not entries:
                        return "No decisions yet."
                    e = entries[0]
                    parts = [
                        f"**Turn {e.turn}** — {e.elapsed_ms:.0f}ms",
                        f"User: {e.user_message[:80]}",
                        f"Safety net: {'⚠ triggered' if e.safety_net_triggered else '✓ passed'}",
                    ]
                    if e.safety_net_reason:
                        parts.append(f"Reason: {e.safety_net_reason}")
                    parts.append(f"Session: `{simulator.audit.session_id}`")
                    return "\n\n".join(parts)

                audit_btn.click(show_last_decision, outputs=gr.Markdown(visible=False))

            # === GROUNDING TAB ===
            with gr.Tab("Grounding"):
                gr.Markdown("## Grounding Station\nNo AI required. Pick one and do it now.")

                with gr.Row():
                    with gr.Column():
                        btn1 = gr.Button("5-4-3-2-1", variant="primary", size="lg")
                        btn2 = gr.Button("Breathing", variant="primary", size="lg")
                    with gr.Column():
                        btn3 = gr.Button("Orientation", variant="primary", size="lg")
                        btn4 = gr.Button("Body Scan", variant="primary", size="lg")

                grounding_out = gr.Markdown("Click any button above.")

                btn1.click(grounding_54321, outputs=grounding_out)
                btn2.click(grounding_breathe, outputs=grounding_out)
                btn3.click(grounding_here, outputs=grounding_out)
                btn4.click(grounding_body, outputs=grounding_out)

            # === ZERO TOOLS TAB ===
            with gr.Tab("Zero Tools"):
                gr.Markdown("## Compiled Tools\nVerified native tools with explicit effect contracts.")

                refresh_btn = gr.Button("Refresh tool list", variant="secondary", size="sm")
                tool_list = gr.Markdown("Click refresh to load tools.")

                def refresh_tools():
                    try:
                        runner = ZeroToolRunner()
                        tools = runner.list_tools()
                        lines = ["| Tool | Size | Effects |", "|------|------|---------|"]
                        for t in tools:
                            try:
                                r = runner.dry_run(t["name"])
                                if r.passed_verification:
                                    caps = ", ".join(r.build.requires_capabilities) or "none"
                                    lines.append(f"| `{t['name']}` | {r.build.total_bytes}B | {caps} |")
                                else:
                                    lines.append(f"| `{t['name']}` | — | verification failed |")
                            except Exception as e:
                                lines.append(f"| `{t['name']}` | — | {e} |")
                        return "\n".join(lines)
                    except Exception as e:
                        return f"Error loading tools: {e}"

                refresh_btn.click(refresh_tools, outputs=tool_list)
                # Load on first render
                demo.load(refresh_tools, outputs=tool_list)

            # === AUDIT TAB ===
            with gr.Tab("Audit Trail"):
                gr.Markdown("## Decision Audit\nEvery model decision logged as structured data.")

                refresh_audit = gr.Button("Refresh", variant="secondary", size="sm")
                audit_out = gr.Markdown("Click refresh.")

                def show_audit():
                    entries = simulator.audit.recent(10)
                    if not entries:
                        return "No decisions logged yet."
                    lines = ["| # | Intent | Verified | Safety | Time |", "|---|--------|----------|--------|------|"]
                    for e in reversed(entries):
                        verified = "✓" if e.verification_passed else ""
                        safety = "⚠" if e.safety_net_triggered else "—"
                        intent = e.proposed_tool or "chat"
                        lines.append(f"| {e.turn} | {intent} | {verified} | {safety} | {e.elapsed_ms:.0f}ms |")
                    lines.append(f"\n\n**Session:** `{simulator.audit.session_id}`")
                    lines.append(f"**Log:** `~/.tether/audit/session_{simulator.audit.session_id}.jsonl`")
                    return "\n".join(lines)

                refresh_audit.click(show_audit, outputs=audit_out)
                demo.load(show_audit, outputs=audit_out)

            # === ABOUT TAB ===
            with gr.Tab("About"):
                gr.Markdown(f"""
                ## Tether — Verifiable AI

                **Version:** {PROMPT_VERSION}
                **Model:** {_active_model}

                Every response is logged with:
                - Session ID (→ `~/.tether/audit/`)
                - Turn number and elapsed time
                - Whether the safety net was triggered
                - What tool was proposed (if any)

                ### Safety rules
                - Never validates delusions involving sentient AIs, digital resurrection, or messianic missions
                - Constantly reminds you it is software
                - Pushes you toward real humans and professional care

                ### Crisis resources
                - US: **988**
                - International: https://www.iasp.info/suicidalthoughts/
                """)

    return demo
