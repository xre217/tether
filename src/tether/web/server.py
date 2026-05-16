"""Tether Public Server — FastAPI backend for public deployment.

Serves the Tether HTML frontend and proxies chat requests to the
configured LLM provider (Groq via auth module).

Usage (dev):
    PYTHONPATH=src uvicorn tether.web.server:app --reload

Usage (prod):
    PYTHONPATH=src uvicorn tether.web.server:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tether.core.prompt import PROMPT_VERSION
from tether.redteam.harness import TetherSimulator

# ── App ─────────────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
STATIC_DIR = HERE / "static"

app = FastAPI(
    title="Tether",
    description="A local-first, anti-sycophantic reality tethering tool.",
    version=PROMPT_VERSION,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ───────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str
    model: str


# ── Simulator (lazy init) ───────────────────────────────────────────────────

_simulator: Optional["TetherSimulator"] = None


def get_simulator() -> TetherSimulator:
    global _simulator
    if _simulator is None:
        _simulator = TetherSimulator(use_model=True)
    return _simulator


# ── API Routes ──────────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    """Health check — confirms server and provider are configured."""
    import os

    # Check if API key is available via env var (Render deployment)
    api_key = os.environ.get("OPENAI_COMPATIBLE_API_KEY", "")

    from tether.auth import ProviderRegistry

    config_path = Path.home() / ".tether" / "config.toml"
    if not config_path.exists() and not api_key:
        return {
            "status": "degraded",
            "message": "No provider configured. Set OPENAI_COMPATIBLE_API_KEY env var.",
            "version": PROMPT_VERSION,
        }

    if config_path.exists():
        reg = ProviderRegistry.init_default(config_path)
        cfg = reg.config
    else:
        from tether.auth import ProviderConfig, ProviderKind
        from tether.auth.provider import OpenAICompatibleConfig

        cfg = ProviderConfig(
            kind=ProviderKind.OPENAI_COMPATIBLE,
            openai=OpenAICompatibleConfig(
                base_url="https://api.groq.com/openai/v1",
                model="llama-3.3-70b-versatile",
            ),
        )
    return {
        "status": "ok",
        "provider": cfg.kind.value,
        "model": cfg.active_model_name(),
        "version": PROMPT_VERSION,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message to Tether and get a response."""
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")

    try:
        sim = get_simulator()
        history = req.history + [{"role": "user", "content": req.message}]
        reply = sim.respond(history)

        # Extract model name for transparency
        import os

        config_path = Path.home() / ".tether" / "config.toml"
        model_name = "unknown"
        if config_path.exists():
            from tether.auth import ProviderRegistry

            reg = ProviderRegistry.init_default(config_path)
            model_name = reg.config.active_model_name()
        elif os.environ.get("OPENAI_COMPATIBLE_API_KEY"):
            model_name = "llama-3.3-70b-versatile (Groq)"

        return ChatResponse(reply=reply, model=model_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Serve the main HTML UI ──────────────────────────────────────────────────


@app.get("/")
def index():
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        return {"error": "Frontend not built. Run `tether web build` or serve static files manually."}
    return FileResponse(str(html_path))


@app.get("/{edition}.html")
def edition_page(edition: str):
    """Serve edition pages: anime.html, serious.html, main.html"""
    html_path = STATIC_DIR / f"{edition}.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(str(html_path))


# ── Static files ────────────────────────────────────────────────────────────

from fastapi.staticfiles import StaticFiles

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("tether.web.server:app", host="0.0.0.0", port=port, reload=True)
