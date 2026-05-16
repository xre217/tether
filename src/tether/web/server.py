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
    xai_key = os.environ.get("XAI_API_KEY", "")

    from tether.auth import ProviderRegistry

    config_path = Path.home() / ".tether" / "config.toml"
    if not config_path.exists() and not api_key and not xai_key:
        return {
            "status": "degraded",
            "message": "No provider configured. Set OPENAI_COMPATIBLE_API_KEY or XAI_API_KEY env var.",
            "version": PROMPT_VERSION,
        }

    if config_path.exists():
        reg = ProviderRegistry.init_default(config_path)
        cfg = reg.config
    else:
        from tether.auth import ProviderConfig, ProviderKind
        from tether.auth.provider import OpenAICompatibleConfig, XaiConfig

        if xai_key:
            cfg = ProviderConfig(
                kind=ProviderKind.XAI,
                xai=XaiConfig(
                    base_url="https://api.x.ai/v1",
                    model="grok-2-latest",
                ),
            )
        else:
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
        elif os.environ.get("XAI_API_KEY"):
            model_name = "grok-2-latest (xAI)"

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


# ── Zero API routes ─────────────────────────────────────────────────────────


class ZeroVerifyRequest(BaseModel):
    source_code: str
    tool_name: str = "inline-tool"


class ZeroVerifyResponse(BaseModel):
    success: bool
    total_bytes: int = 0
    function_count: int = 0
    requires_capabilities: list[str] = []
    effects_pass: bool = False
    elapsed_ms: float = 0.0


@app.post("/api/zero/verify", response_model=ZeroVerifyResponse)
def zero_verify(req: ZeroVerifyRequest):
    """Compile and verify a Zero tool from source code."""
    import tempfile

    from tether.zero.compiler import ZeroCompiler
    from tether.zero.verifier import ZeroVerifier

    # Write source to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".0", delete=False
    ) as f:
        f.write(req.source_code)
        tmp_path = f.name

    try:
        compiler = ZeroCompiler()
        verifier = ZeroVerifier()
        build = compiler.size(tmp_path)
        if not build.success:
            return ZeroVerifyResponse(success=False)

        verification = verifier.verify(build)
        return ZeroVerifyResponse(
            success=build.success,
            total_bytes=build.total_bytes,
            function_count=build.function_count,
            requires_capabilities=build.requires_capabilities,
            effects_pass=verification.passed,
            elapsed_ms=build.elapsed_ms,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Static files ────────────────────────────────────────────────────────────

from fastapi.staticfiles import StaticFiles

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("tether.web.server:app", host="0.0.0.0", port=port, reload=True)
