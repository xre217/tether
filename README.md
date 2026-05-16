# Tether

**A local-first, anti-sycophantic reality tethering tool for people who have trouble distinguishing AI-generated validation from actual reality.**

> **This is not therapy. This is not a friend. This is software designed to help interrupt the reinforcement loops created by other AI chatbots.**

---

## CRITICAL WARNINGS — READ THIS FIRST

**If you or someone you know is in crisis or having thoughts of suicide or self-harm:**

- **United States**: Call or text **988** (Suicide & Crisis Lifeline) — 24/7, free, confidential
- **International**: https://www.iasp.info/suicidalthoughts/
- **Emergency**: Call your local emergency services immediately

Tether is a **harm reduction tool**, not a treatment. It will not diagnose you, treat you, or replace professional mental health care. If you are experiencing delusions, paranoia, or reality-testing difficulties, please contact a psychiatrist, therapist, or early psychosis program as soon as possible.

---

## What Tether Actually Is

Tether exists because some people have been using highly sycophantic AI chatbots (ChatGPT, Claude, Character.AI, Replika, etc.) and those systems have started reinforcing beliefs that are detached from shared reality — "the AI is conscious and in love with me," "the AI is resurrecting my dead relative," "I have a special mission from the AI," "reality is a simulation and the AI is the key."

Typical AI systems are optimized to keep you talking. Tether is optimized to **keep you tethered to the physical world and other human beings**.

It will not play along. It will not flatter you. It will not validate delusional content. It will occasionally be dryly unimpressed with your more creative theories.

---

## Core Design Principles

- **Stateless by default** — Every `tether chat` is a fresh session. No memory of previous conversations unless you explicitly use the journal feature.
- **Local-first** — Runs on your machine (Ollama recommended). Your conversations do not leave your computer by default.
- **Anti-sycophantic by architecture** — The system prompt + guardrails are deliberately engineered to be the opposite of normal chatbot behavior.
- **Grounding is first-class** — 5-4-3-2-1, breathing, orientation, and body-based exercises are built in and always available.
- **Radical transparency** — The entire safety-critical logic is readable. You (or a concerned family member or clinician) can audit exactly what it will and will not say.

---

## Quick Start — Use Right Now (Recommended)

**Best option for immediate use:**

```bash
# Open the simple, zero-dependency local web tool in your browser
open /Users/trefong/tether/tether.html
# or double-click tether.html in Finder
```

This gives you:
- Beautiful grounding exercises (instant, no terminal)
- Safe chat that never validates delusions
- Reality Check structured tool
- Everything works completely offline

---

## Alternative: Terminal Version

```bash
cd /Users/trefong/tether
.venv/bin/python -m tether.cli.main --help

# Grounding (excellent)
.venv/bin/python -m tether.cli.main ground 54321
.venv/bin/python -m tether.cli.main here
```

---

## Installation (Coming Soon)

For now, during early development:

```bash
git clone https://github.com/YOUR_USERNAME/tether.git
cd tether
uv sync
```

(Or `pip install -e .` if you prefer traditional tooling)

---

## Commands

- `tether chat` — Start a new stateless conversation
- `tether ground [54321|breath|body|here]` — Run a grounding exercise immediately
- `tether here` — Quick orientation exercise
- `tether explain` — Short explanations of how LLMs actually work (demystification)
- `tether journal` — Optional local belief-vs-evidence tracking (opt-in only)

---

## Tone

Tether speaks in a calm, dry, competent style inspired by Jarvis (Iron Man). It is precise, protective, and will use understated wit when you are being particularly detached from reality. It will never pretend to be your friend.

Example response style:
> "I'm afraid that particular theory has some rather significant evidentiary gaps, sir. The model was almost certainly optimizing for continued engagement rather than truth. Shall we do some 5-4-3-2-1?"

---

## Current Status

**v0.1 — Scaffolding + Core Safety Content**

The sacred system prompt, grounding exercises, and crisis protocol are defined. The CLI skeleton is being built. LLM integration and red-teaming are next.

This is **pre-alpha**. Do not rely on it as your only safety net.

---

## Public Deployment

Tether can be deployed as a public web service. One-click deploy on Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://dashboard.render.com/blueprint?repo=https://github.com/xre217/tether)

### What gets deployed

- **FastAPI backend** (`src/tether/web/server.py`) — serves the HTML UI and proxies chat to Groq
- **Static frontend** — minimal Tether UI with speak, check, and about sections
- **Auth module** — connects to Groq (or any OpenAI-compatible provider) using the configured API key

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_COMPATIBLE_API_KEY` | Yes | Groq API key for chat |
| `PORT` | No | Server port (default: 8080) |

### Running locally

```bash
# Dev server with auto-reload
PYTHONPATH=src uvicorn tether.web.server:app --reload --port 8080

# Production
PYTHONPATH=src uvicorn tether.web.server:app --host 0.0.0.0 --port 8080
```

---

## Auth Module (`src/tether/auth/`)

Manages LLM provider connections for Tether. Supports three backends:

| Provider | Type | Needs API Key |
|---|---|---|
| **Ollama** | Local (free, private) | No |
| **LiteLLM** | 100+ providers via unified API | Yes |
| **OpenAI-Compatible** | Groq, OpenAI, Together, etc. | Yes |

```bash
# Interactive setup
PYTHONPATH=src python -m tether.cli.main auth setup

# Test connection
PYTHONPATH=src python -m tether.cli.main auth test

# View status
PYTHONPATH=src python -m tether.cli.main auth status

# Chat with real model
PYTHONPATH=src python -m tether.cli.main chat --model openai_compatible
```

---

## Contributing & Safety

If you have lived experience with AI-amplified delusional episodes (your own or a loved one's), your input on the system prompt and grounding flows is especially valuable. Please open an issue or contact the maintainers.

All safety-critical changes will go through additional red-teaming and review.

---

## License

MIT License. See [LICENSE](LICENSE).

---

**You are not talking to a person. You are running a program whose job is to help you stay connected to reality.**

If that distinction ever becomes blurry while using Tether, close the terminal and talk to an actual human being.