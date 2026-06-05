# JARVIS Control

## Mission: Individual AI Sovereignty

In an age of creeping AI nationalization — where states and mega-corporations race to centralize, regulate, and ultimately own the most powerful models — JARVIS exists to keep the power in individual hands.

This is a local-first control surface. Your agents run with your memory (Evidence Ledger), your signals (THRML), your tools, and your rules. Remote models like Grok are used as pure reasoners over *your* context, never as the sole custodian of your state or intent. Skills and patterns built here are contributed upstream so others can run sovereign too.

Decentralized execution, local persistence, open contribution, and verifiable human oversight are the only reliable defense against capture. If AI is the new electricity, we refuse to let it be nationalized.

---

Local control surface for combining:

- Hermes as the agent runtime and tool/memory layer (now with custom skills like grok-xai-oauth, grok-build-patterns, grok-x-research, and grok-heartbreak-to-mars for deep Grok-powered creative heartbreak-to-Mars content in Olivia Rodrigo style).
- Grok through xAI as the remote reasoning model (via official OAuth or API key).
- THRML as a probabilistic sampling signal for uncertainty-aware action.
- A localhost action bridge so the Vercel UI can see your local runtime from your browser.

These custom Hermes skills were built inside Grok Build and contributed back upstream.

There's a helper in scripts/load-grok-hermes-skills.sh to verify the skills are available when using the Grok provider in Hermes.

## Demo Grok Skills
To demo the new Grok integration skills:
1. Switch Hermes to Grok OAuth: `hermes model` (select xAI Grok OAuth).
2. Run the helper: `bash scripts/load-grok-hermes-skills.sh`
3. Use e.g. `hermes chat -q "Using grok-x-research, search X for recent Hermes Agent + Grok usage and synthesize."`

See the skills in ~/.hermes/skills/software-development/ for details.

## Run (important: from the project directory)

```bash
cd grok-concierge
cp .env.example .env.local   # add your XAI_API_KEY (or leave for local-model fallback)
npm run jarvis
```

Then in a **second terminal** (for the creative generators, Hermes bridge, full sovereignty tools):

```bash
cd grok-concierge
npm run bridge
```

Open [http://localhost:3000](http://localhost:3000).

**If you see "Could not read package.json"** — you ran the command from your home directory (`~`). Always `cd grok-concierge` first.

The app is the JARVIS control surface for the anti-nationalization mission. The Starship to Mars generator (new) lives in the Creative section and produces launch-energy content that treats the real Starship as the physical ship whose guidance system must remain distributed (ledger + local agents) even if Earth-side AI is captured.

## Starship to Mars Layer

The heartbreak-to-Mars creative work now has an explicit hardware counterpart. See `starship_to_mars.md` (created in this session). The generators in the UI (Heartbreak to Mars, Sovereignty Anthem Variants, and the new Starship to Mars) use the `grok-heartbreak-to-mars` Hermes skill + the local bridge to turn refusal of AI nationalization into the exact propellant for leaving the gravity well.

This is not just poetry for the project — it is a cultural contribution to the actual program: the more humans who feel in their bones that "if they nationalize the models, the ship still needs to fly under its own distributed intelligence," the more likely we are to actually get there with our minds intact.

## Local Action Bridge

Run this in a second terminal:

```bash
npm run bridge
```

The bridge listens on `127.0.0.1:8787`, exposes `/health`, and can call Hermes + the Evidence Ledger through token-protected endpoints.

When Hermes is invoked via the bridge, it is automatically given the location and usage of the canonical ledger CLI (`python3 -m scripts.ledger`).

See [LEDGER.md](./LEDGER.md) for the full memory contract and philosophy.

## THRML

The app works without Python ML dependencies by using a deterministic fallback signal. To enable real THRML/JAX sampling locally:

```bash
npm run setup:thrml
```

The API will automatically use `.venv/bin/python` when it exists.

## Routes

- `/` is the JARVIS command UI.
- `/api/status` reports Hermes and THRML status.
- `/api/chat` sends commands through Grok when `XAI_API_KEY` is set. Grok now sees the live Evidence Ledger and can auto-record important observations.
- `/api/ledger` — GET for recent entries, POST to manually record (`claim` + optional `evidence`).

The **Evidence Ledger** (`~/.jarvis/memory/ledger.jsonl`) is now the persistent, queryable memory of the system. It is injected into every Grok reasoning turn and is also directly accessible to Hermes via the local bridge (`/ledger/recent`, `/ledger/record`).

## Checks

```bash
npm run lint
npm run build
```

## Latest VILO Pull-Up (outside terminal / public mirror)

Full project docs synced for public access beyond TUI:

- palantir_sovereignty_operator_guide.md : Playbook for sovereign ops inside Palantir (ledger primary, dual demo, pre-AIP, Kristoff/Anna, o7 _~ discipline).
- pre_aip_preparation.md : Local generators and daily workflow to prepare assets while waiting for AIP access (ready to load briefs instantly).
- pantheon_o7.md : Unified anthem following Olivia, Elon, Karp, Thiel + loadable CampaignBrief.
- their_lead_sao_franxx.md and related creative (the evolved SAO/Franxx + Indominus + full metaphors assets with CampaignBriefs for AIP).

See the GitHub tree for all: https://github.com/xre217/tether/tree/main/sovereignty

Local UI: cd grok-concierge && npm run jarvis (then bridge in second term) for the interactive Sovereignty Dashboard, record, reflect, creative generators (Virtual Cage Rebellion etc.).

The mirror makes the full VILO (strategy, runtime, operator guides, creative resistance) visible and forkable outside any terminal.
