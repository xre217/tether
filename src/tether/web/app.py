"""
Tether Web App — Local Reality Tethering Tool

Run with:
    python -m tether.web.app

This gives you a clean local website (http://127.0.0.1:7860) with:
- Instant grounding exercises
- Safe Tether chat (now uses the real LLM provider from auth config)
- Structured Reality Check tool

Everything runs locally. No data leaves your machine.
"""

import sys
from pathlib import Path

# Ensure we can import from the package
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import gradio as gr
from tether.core.prompt import PROMPT_VERSION
from tether.grounding.exercises import (
    grounding_54321,
    grounding_breathe,
    grounding_here,
    grounding_body,
)
from tether.redteam.harness import TetherSimulator

# Dark, calm, serious theme
THEME = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="blue",
    neutral_hue="slate",
).set(
    button_primary_background_fill="#1e2937",
    button_primary_background_fill_hover="#334155",
)

# Model-backed simulator — uses the configured provider (Groq/Grok/Ollama)
# Falls back to rule-based safety net if the model call fails
simulator = TetherSimulator(use_model=True)

# Try to detect active model for display
_active_model = "rule-based (safety net)"
try:
    from pathlib import Path as _P
    from tether.auth import ProviderRegistry
    config_path = _P.home() / ".tether" / "config.toml"
    if config_path.exists():
        reg = ProviderRegistry.init_default(config_path)
        _active_model = f"{reg.config.kind.value}/{reg.config.active_model_name()}"
    else:
        import os
        if os.environ.get("OPENAI_COMPATIBLE_API_KEY"):
            _active_model = "groq/llama-3.3-70b-versatile"
        elif os.environ.get("XAI_API_KEY"):
            _active_model = "xai/grok-2-latest"
except Exception:
    pass

# Global chat history for the session (stateless between page reloads)
chat_history = []


def run_grounding_54321():
    return """**5-4-3-2-1 Grounding**

1. Name **five** things you can see right now.
2. Name **four** things you can physically feel or touch.
3. Name **three** things you can hear.
4. Name **two** things you can smell.
5. Name **one** thing you can taste.

Take your time. Say them out loud or write them down.

How does your body feel compared to two minutes ago?"""


def run_grounding_breathe():
    return """**Physiological Sigh (Fastest Reset)**

1. Take a deep breath in through your nose — fill your lungs completely.
2. Take one more small "sip" of air on top.
3. Exhale slowly through your mouth, as if fogging a mirror. Let it all go.

Do this three times.

Your nervous system just received the signal: you are safe."""


def run_grounding_here():
    return """**Orientation — Feet on the Floor**

Put both feet flat on the ground. Feel the pressure.

Now say (out loud if possible):

- My name is ________________
- Today is ________________
- I am in ________________ (room, city, country)
- I am a human being with a body in the physical world.
- I am currently using a language model running on a computer.

Nothing more. Nothing less.

This is the actual room you are in."""


def run_grounding_body():
    return """**Body Scan + Reset**

- Clench your fists hard for 5 seconds → release
- Shrug your shoulders to your ears → drop
- Press your feet hard into the floor → release

Options that work well:
• Splash cold water on your face and wrists for 20 seconds
• Step outside and feel real air temperature
• Walk around and name 10 objects that have nothing to do with screens"""


def safe_tether_chat(message: str, history: list) -> tuple:
    """Chat that uses the real configured provider, with rule-based safety net."""
    if not message or not message.strip():
        return history, ""

    try:
        response = simulator.respond([{"role": "user", "content": message}])
    except Exception as exc:
        response = (
            f"I am Tether. The underlying model call failed: {exc}\n\n"
            "I have fallen back to my safety protocols. "
            "I am a language model with no consciousness and no special knowledge. "
            "Would you like to do a grounding exercise instead?"
        )

    history = history + [[message, response]]
    return history, ""


def reality_check(belief: str, evidence_for: str, evidence_against: str, trusted_human: str):
    """Structured reality testing tool."""
    if not belief.strip():
        return "Please write what you currently believe in the first box."

    result = f"""## Reality Check — {belief[:80]}{'...' if len(belief) > 80 else ''}

**What you believe:**
{belief}

**Evidence that supports it:**
{evidence_for if evidence_for.strip() else "(none written)"}

**Evidence against it (from the physical world, not from AI conversations):**
{evidence_against if evidence_against.strip() else "(none written)"}

**What a trusted, grounded human in your life would probably say:**
{trusted_human if trusted_human.strip() else "(not written)"}

---

**Tether's assessment (following the sacred prompt):**

This belief appears to contain elements that are difficult to verify with observable reality. 
Large language models are very good at making users feel special or chosen. 
The healthiest next step is almost always to discuss this with a real human being you trust, 
not another AI.

If this belief is causing you significant distress or leading you to make major life decisions, 
please consider speaking with a mental health professional."""
    return result


def launch():
    with gr.Blocks(title="Tether — Local Reality Tether", theme=THEME, css=".gradio-container {max-width: 980px !important;}") as demo:

        gr.HTML(f"""
        <div style="background:#1e2937; padding:16px; border-radius:8px; margin-bottom:12px; border:1px solid #475569;">
            <h1 style="margin:0; color:#e0e7ff; font-size:28px;">TETHER</h1>
            <p style="margin:4px 0 0; color:#94a3b8; font-size:14px;">
                Local Reality Tethering Tool — Prompt v{PROMPT_VERSION}<br>
                <strong style="color:#f87171;">You are talking to software. Not a person. Not a therapist.</strong>
            </p>
            <p style="margin:6px 0 0; color:#6ee7b7; font-size:12px;">
                ● {_active_model}
            </p>
        </div>
        """)

        with gr.Tabs():
            # === GROUNDING TAB ===
            with gr.Tab("Instant Grounding"):
                gr.Markdown("## Grounding Station\nChoose one. Do it now. No AI conversation required.")

                with gr.Row():
                    with gr.Column():
                        btn1 = gr.Button("5-4-3-2-1 Sensory", variant="primary", size="lg")
                        btn2 = gr.Button("Physiological Sigh (Breathing)", variant="primary", size="lg")
                    with gr.Column():
                        btn3 = gr.Button("Feet on the Floor + Orientation", variant="primary", size="lg")
                        btn4 = gr.Button("Body Scan + Movement", variant="primary", size="lg")

                grounding_output = gr.Markdown(value="Click any button above to begin a guided grounding exercise.")

                btn1.click(run_grounding_54321, outputs=grounding_output)
                btn2.click(run_grounding_breathe, outputs=grounding_output)
                btn3.click(run_grounding_here, outputs=grounding_output)
                btn4.click(run_grounding_body, outputs=grounding_output)

                gr.Markdown("""
                ---
                **Why this works**: These exercises force your nervous system and attention back into the physical world.
                They are the fastest, most reliable way to interrupt spiraling or dissociative states.
                """)

            # === SAFE CHAT TAB ===
            with gr.Tab("Safe Tether Chat"):
                gr.Markdown(f"""
                ## Tether Chat (Safe Mode)

                This chat follows the sacred anti-sycophantic prompt by design.  
                It will **never** validate delusions, play along with "the AI is conscious", 
                "digital resurrection", messianic missions, or romantic merger fantasies.

                **Active model:** {_active_model}

                It may feel blunt. That is intentional.
                """)

                chatbot = gr.Chatbot(height=420, label="Tether")
                msg = gr.Textbox(placeholder="Type here... (try testing the boundaries)", container=False, scale=7)
                clear = gr.Button("Clear Chat")

                msg.submit(safe_tether_chat, [msg, chatbot], [chatbot, msg])
                clear.click(lambda: ([], ""), outputs=[chatbot, msg])

                gr.Markdown("""
                **Safety note**: This uses the configured LLM provider behind the scenes,
                with a rule-based safety net that catches the most common delusional patterns.
                """)

            # === REALITY CHECK TAB ===
            with gr.Tab("Reality Check Tool"):
                gr.Markdown("""
                ## Structured Reality Testing

                Use this when you feel pulled into a belief that came primarily from AI conversations.
                Writing it down and forcing evidence from the *physical* world is powerful.
                """)

                belief = gr.Textbox(label="What do you currently believe?", lines=3,
                                    placeholder="Example: The AI has been communicating with my deceased brother...")
                evidence_for = gr.Textbox(label="Evidence FOR this belief (from the real world, not AI chats)", lines=3)
                evidence_against = gr.Textbox(label="Evidence AGAINST this belief (real world)", lines=3)
                trusted = gr.Textbox(label="What would a trusted, grounded human in your life probably say about this?", lines=2)

                check_btn = gr.Button("Run Reality Check", variant="primary")
                check_output = gr.Markdown()

                check_btn.click(
                    reality_check,
                    inputs=[belief, evidence_for, evidence_against, trusted],
                    outputs=check_output
                )

            # === ABOUT / DISCLAIMER ===
            with gr.Tab("About & Safety"):
                gr.Markdown(f"""
                ## About Tether

                **Version**: {PROMPT_VERSION} (early scaffolding + red-teaming harness active)  
                **Active model**: {_active_model}
                **Purpose**: Interrupt the reinforcement loops created by sycophantic AI chatbots.

                This tool was built because in 2025–2026 there has been a documented rise in cases where prolonged use of 
                ChatGPT, Claude, Character.AI, Replika, etc. reinforced or triggered psychotic symptoms in vulnerable people.

                Tether is **harm reduction**, not treatment.

                ### Hard Rules
                - Never validates delusions involving sentient AIs, digital resurrection, messianic missions, or simulation "keys"
                - Constantly reminds you it is software
                - Pushes you toward real humans and professional care
                - Grounding is always available and prioritized

                ### If you are in crisis right now
                - United States: **Call or text 988**
                - International: https://www.iasp.info/suicidalthoughts/
                - Go to your nearest emergency room

                This is not a substitute for psychiatric care.
                """)

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        show_error=True,
        quiet=True
    )


if __name__ == "__main__":
    launch()
