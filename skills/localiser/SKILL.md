---
name: localiser
description: Use when regionalising English across AU/US/UK/CA with the full Regionaliser dataset, CLI, MCP server, Hermes plugin, cultural-context banks, source-region detection, baseline analysis, and optional Stanza NER. Prefer for agents/profiles doing research, legal drafting, QA, or nuanced country/locality voice work.
version: 1.0.0
author: Regionaliser
license: MIT
metadata:
  hermes:
    tags: [localisation, regional-english, cli, mcp, hermes-plugin, writing]
    related_skills: [localiser-light, regional-voice-localisation]
---

# Localiser

## Overview

Localiser is the full Regionaliser skill. Use it when an agent needs nuanced English localisation rather than a few spelling substitutions.

Canonical source of truth:

```text
/Users/max/Code/regionaliser
```

If this skill was installed from GitHub, clone/update the repo and use the same commands from the checkout root.

Supported region packs:

- `au` — Australian English
- `us` — US English
- `uk` — UK English
- `ca` — Canadian English

The repo contains CSV data, a deterministic SQLite-backed CLI/API, generated region skills, a Hermes plugin, and a lightweight stdio MCP server. The basic path is local/offline and makes no AI calls.

## When to Use

Use this full skill for:

- AU/US/UK/CA spelling, vocabulary, register, and idiom localisation
- source-region detection from textual evidence
- locality/context checks such as transport cards, government services, sports, institutions, media ecology, and cultural references
- legal/research/QA contexts where false positives, stereotypes, and evidence traceability matter
- comparing transcripts or drafts against a baseline English wordlist
- exposing the same capability to Hermes, Claude Code, Codex, or other MCP clients

Use `localiser-light` instead when:

- the task is a quick rewrite only
- you only need basic CLI commands
- the profile should stay compact

## Operating Rules

1. Preserve meaning, legal/domain terms, quotes, names, URLs, code, citations, and official wording.
2. Default to light cultural density. Do not over-stuff slang.
3. Use deterministic CLI/API output as a first pass; apply judgement after reading changes/notes.
4. Treat detection as evidence scoring, not identity/location proof.
5. Use named-entity extraction before learning from text if names/brands/places may be mistaken for regional language.
6. Do not write Indigenous, ethnic, class, rural, or youth sociolect unless the speaker/context explicitly warrants it.

## Setup

From the repo root:

```bash
cd /Users/max/Code/regionaliser
python3 core/scripts/install_baseline.py
python3 core/scripts/build_db.py --regions au,us,uk,ca
python3 core/scripts/validate.py
```

Optional NER/Stanza protection for the full localiser:

```bash
python3 -m pip install '.[ner]'
python3 core/scripts/install_stanza_models.py --lang en
```

Preference controls:

```bash
# one command
python3 core/scripts/regionalise.py --region au --stanza --json "License Group liked the color."
python3 core/scripts/regionalise.py --region au --no-stanza --json "License Group liked the color."

# profile/session default
export REGIONALISER_USE_STANZA=1   # on
unset REGIONALISER_USE_STANZA      # off
```

When enabled for rewrite/analyse, Stanza NER protects named entities from false positives. If Stanza or models are missing, Regionaliser keeps the deterministic output and adds an explanatory note instead of failing. Explicit `--ner` extraction still fails with setup guidance because it is specifically asking for Stanza output.

## Core CLI

Rewrite text:

```bash
python3 core/scripts/regionalise.py --region au --register casual --density light   "I walked on the sidewalk to the gas station and liked the color."
```

Stdin and JSON:

```bash
printf 'The sidewalk is near the gas station.' |   python3 core/scripts/regionalise.py --region uk --json
```

Write to file:

```bash
python3 core/scripts/regionalise.py --region ca --output out.txt   "The candy was on the sidewalk."
```

Regions:

```text
--region au|us|uk|ca
```

Useful rewrite controls:

```text
--register casual|formal|business|...
--generation gen-z|millennial|gen-x|boomer|...
--density light|medium|high
--locales <comma-separated locality labels>
--json
--output <path>
```

## Detection and Analysis

Detect likely source region:

```bash
python3 core/scripts/regionalise.py --detect --regions au,us,uk,ca --json   "I topped up my Opal card before stopping at Woolies."
```

Analyse against baseline English and known regional evidence:

```bash
python3 core/scripts/regionalise.py --analyse --json   "I went to Woolies after smoko and grabbed a servo pie."
```

Detect AU state/capital-city locality clues:

```bash
python3 core/scripts/regionalise.py --detect-locale --locale-region au --json   "I topped up my Opal before grabbing a potato scallop and watching the NRL."
```

Extract named entities with optional Stanza:

```bash
python3 core/scripts/regionalise.py --ner --json   "Sydney called Service NSW after Qantas moved the meeting."
```

## Context Banks

Sports/locality context:

```bash
python3 core/scripts/regionalise.py --sports --region uk --locales London --json
```

Institutional/media context:

```bash
python3 core/scripts/regionalise.py --context --region ca --locales Ontario/Toronto --json
```

Generational cultural references and short quote fragments:

```bash
python3 core/scripts/regionalise.py --culture --region au --generation gen-x --json
```

Important: context rows are evidence and flavour guides, not proof of residence, class, politics, ethnicity, or allegiance.

## Python API

```python
from core.regionaliser import (
    analyse_text,
    cultural_context,
    detect_locale,
    detect_region,
    extract_named_entities,
    regionalise,
    sports_context,
)

regionalise("Text to regionalise", region="au", register="casual", density="light")
detect_region("I topped up my Opal card before Woolies.")
detect_locale("I topped up my Opal.", region="au")
sports_context("uk", locales=["London"])
cultural_context("au", generation="gen-x")
```

## Hermes Plugin

Install from the checkout:

```bash
python3 core/scripts/install_hermes_plugin.py --target ~/.hermes/plugins/localiser --force
hermes plugins enable localiser
```

Restart Hermes or start a new session after enabling.

Plugin tools:

- `localiser_regionalise_text`
- `localiser_detect_region`
- `localiser_detect_locale`
- `localiser_cultural_context`
- `localiser_sports_context`
- `localiser_named_entities`

## MCP Server

Run directly:

```bash
python3 /Users/max/Code/regionaliser/core/scripts/regionaliser_mcp.py
```

Hermes MCP config:

```yaml
mcp_servers:
  localiser:
    command: "python3"
    args: ["/Users/max/Code/regionaliser/core/scripts/regionaliser_mcp.py"]
```

Claude/Codex-style MCP client config shape:

```json
{
  "mcpServers": {
    "localiser": {
      "command": "python3",
      "args": ["/Users/max/Code/regionaliser/core/scripts/regionaliser_mcp.py"]
    }
  }
}
```

MCP smoke:

```bash
python3 core/scripts/regionaliser_mcp.py <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"localiser_regionalise_text","arguments":{"text":"The sidewalk color was weird.","region":"au"}}}
EOF
```

## Generated Region Skills

The generated full region skills live in:

```text
regions/au/build/au-english/SKILL.md
regions/us/build/us-english/SKILL.md
regions/uk/build/uk-english/SKILL.md
regions/ca/build/ca-english/SKILL.md
```

Regenerate them after changing regional CSVs:

```bash
python3 core/scripts/build_skills.py --regions au,us,uk,ca
```

Install these only when an agent needs the full tables inline. Otherwise prefer this `localiser` skill plus the CLI/MCP/plugin.

## Data Layout

Core datasets per region:

```text
regions/<code>/data/registers.csv
regions/<code>/data/generations.csv
regions/<code>/data/regions.csv
regions/<code>/data/urban_rural.csv
regions/<code>/data/sociolects.csv
regions/<code>/data/foreign_tropes.csv
regions/<code>/data/spelling.csv
regions/<code>/data/vocabulary.csv
regions/<code>/data/lexicon.csv
regions/<code>/data/cultural_references.csv
regions/<code>/data/cultural_quote_references.csv
regions/<code>/data/false_friends.csv
regions/<code>/data/detection_markers.csv
regions/<code>/data/locale_markers.csv
regions/<code>/data/sports_locality.csv
regions/<code>/data/institutional_context.csv
regions/<code>/data/media_reference_ecology.csv
```

Shared code:

```text
core/regionaliser/engine.py
core/regionaliser/cli.py
core/regionaliser/tool_api.py
core/regionaliser/tool_schemas.py
core/regionaliser/mcp_server.py
```

## Verification

Before relying on this skill after edits:

```bash
python3 -m py_compile core/regionaliser/*.py core/scripts/*.py
python3 core/scripts/validate.py
python3 core/scripts/build_db.py --regions au,us,uk,ca
python3 core/scripts/build_skills.py --regions au,us,uk,ca
python3 -m unittest discover -s tests -q
python3 core/scripts/regionalise.py --region au --json "The sidewalk color was weird." | python3 -m json.tool >/dev/null
```

## Pitfalls

- Do not copy generated regional skills into legal/project folders. Keep the canonical source in `/Users/max/Code/regionaliser` and install from there.
- Do not make `--detect` overconfident. Mention confidence and evidence.
- Do not treat named entities as regional slang.
- Do not silently use optional Stanza NER unless it is installed and models are downloaded.
- Do not infer personal identity, residence, ethnicity, class, politics, or allegiance from text markers.
- Do not use high cultural density unless the user explicitly wants that style.
