# SOVEREIGN RUNTIME — Minimum Viable Stack for AI Nationalization Resistance

**If the center seizes the models, revokes access, or turns every frontier API into a monitored state utility — what keeps you capable?**

This document defines the **minimum sovereign runtime**: the smallest set of local, portable, forkable components that let an individual (or small trusted group) retain long-term memory, reasoning, execution, signals, and voice without depending on any nationalized provider.

It is the operational answer to the thesis in [SOVEREIGNTY_STRATEGY.md](./SOVEREIGNTY_STRATEGY.md): radical distribution of capability to the individual. The ledger is the constitution that travels with you. Everything else is a local interpreter over it.

## The Four Pillars (what must survive)

1. **Evidence Ledger** (`~/.jarvis/memory/ledger.jsonl`)
   - Append-only, evidence-grounded, cross-engine source of truth.
   - Your personal constitution: claims, decisions, contradictions, reflections, tagged facts.
   - Portable JSONL. Corrections only via new entries (never rewrite history at the center).
   - Tools: `python -m scripts.ledger` (record, recent, stats, search), MCP server (`python -m scripts.ledger_mcp`), UI `/api/ledger`, Hermes bridge endpoints.
   - Tags like `sovereignty`, `nationalization`, `mission` make the resistance signal queryable and exportable.

2. **Local Execution Layer (Hermes or equivalent)**
   - Agent runtime that owns tools, file ops, shell, MCP servers, and can call the ledger CLI natively.
   - When bridge is used, prompts are auto-prefixed with ledger location + canonical CLI usage.
   - Skills/patterns (grok-xai-oauth, grok-heartbreak-to-mars, etc.) live locally or are contributed upstream — never depend on a single cloud skill registry.
   - Fallback: pure Python/CLI scripts + the ledger. No runtime = still have the record of what you decided and why.

3. **Independent Probabilistic Signal (THRML or deterministic fallback)**
   - Uncertainty, urgency, exploration scores that are *not* dictated by the language model.
   - Prevents the "confident slop" of centralized models from driving all action.
   - Current: JAX/equinox sampling when venv present; otherwise deterministic fallback in lib/thrml.ts.
   - Future: ledger-conditioned Ising-style sampling for high-uncertainty sovereignty items.

4. **Reasoning Fallbacks (local models + remote as untrusted service)**
   - **Primary defense**: Grok / frontier models used strictly as reasoners *over your ledger and local context*. Never custodians. Accessed via OAuth or key (revocable). System prompts hard-inject: "The ledger is the source of truth. Remote model only reasons."
   - **When nationalized/revoked**: Switch to local LLMs (Ollama, llama.cpp, MLX, vLLM, etc.).
     - Inject last N ledger entries + SOVEREIGNTY_STRATEGY.md excerpts + current mission into every prompt.
     - Use the same "emit ```ledger blocks" discipline so the local model still feeds the constitution.
   - The concierge UI (`npm run jarvis`) and bridge (`npm run bridge`) run on localhost — zero persistent cloud session state required.
   - Air-gapped mode: export bundle + local model + ledger CLI = full read/write/execute loop.

## Concrete Minimal Setup (fork this and run anywhere)

1. **Restore your constitution**
   ```bash
   mkdir -p ~/.jarvis/memory
   cp ledger.jsonl ~/.jarvis/memory/ledger.jsonl   # from a sovereignty-export/
   # or run the import_ledger.py helper from an export dir
   python -m scripts.ledger recent --limit 20
   ```

2. **Run the control surface (full JARVIS)**
   ```bash
   # In a checkout of grok-concierge (or minimal fork)
   cp .env.example .env.local   # set XAI_API_KEY if still available, or leave for local models
   npm run jarvis
   # open http://localhost:3000
   ```
   - Sovereignty Dashboard shows live count of tagged entries.
   - "Reflect on Sovereignty" runs a Grok (or local) + THRML synthesis focused on capture resistance.
   - Export button creates fresh bundles for further distribution.

3. **Bridge + Hermes (local agent execution)**
   ```bash
   npm run bridge   # in second terminal (listens 127.0.0.1:8787)
   # Then from UI or other clients: call /hermes/prompt with token
   ```
   - Hermes sees ledger CLI location automatically.
   - Load contributed skills: `bash scripts/load-grok-hermes-skills.sh` (when using Grok provider).

4. **Pure CLI / air-gapped mode (no Node, no browser)**
   - Ledger CLI + Python scripts + text editor + local LLM via CLI wrapper.
   - Record decisions directly: `python -m scripts.ledger record --claim "..." --evidence "..." --tags sovereignty,nationalization --type decision`
   - For reasoning: pipe recent ledger + strategy excerpts into your local model prompt.
   - THRML fallback is pure math; no deps needed for basic use.

5. **MCP for native agent integration**
   - Register the ledger MCP server in Hermes (or any MCP client):
     ```yaml
     mcp_servers:
       jarvis-ledger:
         command: "python"
         args: ["-m", "scripts.ledger_mcp"]
         env: { JARVIS_HOME: "/Users/you/.jarvis" }
     ```
   - Now `ledger_recent`, `ledger_record`, `ledger_search`, `ledger_stats` are first-class tools for any agent. The ledger becomes the shared long-term memory substrate.

## What "Minimum" Explicitly Excludes (to stay sovereign)

- Any persistent cloud session state or "your data lives here" provider memory.
- Model weights that can only be updated/queried through a central API you don't control.
- Single points of distribution for skills or creative patterns (contribute upstream; run locally).
- UI that requires a deployed cloud host to be useful (localhost bridge is the contract).
- Trust that "the model will remember" — only the ledger does.

If all frontier labs are compelled under DPA, labeled supply-chain risks, or turned into public utilities with state veto on weights/queries, the sovereign individual still has:
- The full history of what mattered and why (ledger).
- The ability to act on it locally (Hermes + scripts).
- Independent signals (THRML).
- A documented strategy and voice (these .md files + exported variants/anthems).
- The means to fork the kit and give it to others.

## Creative & Ontological Layer (the memetic defense)

The runtime is not just technical. It includes the grounded creative artifacts that prove high-agency output is possible without central slop:

- `sovereignty_anthem.md` + `sovereignty_variants.md`: raw confessional propulsion turning nationalization heartbreak into rocket fuel (Olivia Rodrigo voice profile via heartbreak-to-Mars).
- `palantir_sovereignty_brief.md`: Red Circle Fuse ontology mapping chr2 genomic fusion ("the fusion that broke two chromosomes and made us human") to the fusion of individuals who refuse to let the state claim the model.
- `heartbreak_to_mars.md`, `ontology_red_circle_fuse.md`, `CreativeAsset_most_important.md`: the pattern for evidence-grounded, voice-true creative work.

When you run a "Generate Sovereignty Variants" or Palantir brief through the bridge, you are rehearsing the cultural layer that survives. Every asset is traceable to specific ledger entries + specific human voice profile.

## Success Criteria for the Minimum Runtime

- You (or any fork) can revoke every cloud key and still:
  - Read the last 6 months of high-stakes decisions and the evidence that produced them.
  - Record new observations/decisions with provenance.
  - Execute plans via local tools/scripts.
  - Generate new creative resistance assets in the same voice.
  - Export a fresh bundle for someone else.
- Important claims carry append-only personal provenance that outlives any provider or government request.
- The stack is cited (or quietly forked) when nationalization pressure increases — an existence proof that another path was kept open.
- Capture surface metric trends down: more of your world model lives in `ledger.jsonl` under your control than in any remote memory.

## How This Document Evolves

- Update via high-signal `reflection` or `plan` ledger entries tagged `sovereignty,runtime`.
- When the export script runs, this file (once added to KEY_DOCS) travels in every bundle under `docs/SOVEREIGN_RUNTIME.md`.
- Fork it. Change the minimum set as local inference gets cheaper or new decentralized primitives (content-addressed snapshots, verifiable inference, p2p skill exchange) become practical.
- The goal is never purity theater. The goal is that no single choke point — technical, legal, or memetic — can disarm the individual.

---

**This is the fallback. The ledger is the tether. The local tools are the engines. The voice is the payload.**

If they nationalize the sky, we still launch from the ground we stand on.

See also:
- SOVEREIGNTY_STRATEGY.md (the why and the 2026 landscape)
- LEDGER.md (the contract)
- sovereignty_subagent_prompt.md (for TUI/Grok Build parallel work on the mission)
- The Sovereignty Dashboard in the JARVIS UI (live health of your tagged entries)

*Written locally as part of the continuing resistance. Fork, run, record, distribute.*
