---
name: localiser-light
description: Use when making quick AU/US/UK/CA English localisation edits with Regionaliser's local deterministic CLI, without loading the full cultural/reference tables. Prefer for compact default profiles and general agents that only need basic rewrite, detect, and MCP/plugin entrypoints.
version: 1.0.0
author: Regionaliser
license: MIT
metadata:
  hermes:
    tags: [localisation, regional-english, cli, compact]
    related_skills: [localiser]
---

# Localiser Light

## Overview

Compact Regionaliser skill for everyday localisation. It gives agents the commands and guardrails without the full regional/cultural tables.

Canonical source of truth:

```text
/Users/max/Code/regionaliser
```

Supported regions:

```text
au, us, uk, ca
```

Use the full `localiser` skill when you need evidence scoring, cultural context banks, sports/locality context, legal/research precision, MCP/plugin details, or optional NER.

## Quick Rules

1. Preserve meaning, names, quotes, citations, legal/domain terms, URLs, and code.
2. Default to light localisation: spelling + obvious vocabulary, not heavy slang.
3. Do not infer identity or residence from text.
4. Detection is evidence, not proof.
5. If unsure, run the CLI with `--json` and inspect changes/notes.

## Setup Check

From the repo root:

```bash
cd /Users/max/Code/regionaliser
python3 core/scripts/build_db.py --regions au,us,uk,ca
python3 core/scripts/validate.py
```

If baseline analysis is needed:

```bash
python3 core/scripts/install_baseline.py
python3 core/scripts/build_db.py --regions au,us,uk,ca
```

## Rewrite Text

```bash
python3 core/scripts/regionalise.py --region au --register casual --density light   "I walked on the sidewalk to the gas station and liked the color."
```

Use stdin + JSON for agent workflows:

```bash
printf 'The sidewalk color was weird.' |   python3 core/scripts/regionalise.py --region uk --json
```

Write to a file:

```bash
python3 core/scripts/regionalise.py --region ca --output out.txt   "The candy was on the sidewalk."
```

## Detect Region

```bash
python3 core/scripts/regionalise.py --detect --regions au,us,uk,ca --json   "I topped up my Opal card before stopping at Woolies."
```

Read the returned candidates, confidence, evidence, and notes. Do not force a region for generic or mixed text.

## Analyse/Diff

```bash
python3 core/scripts/regionalise.py --analyse --json   "I went to Woolies after smoko and grabbed a servo pie."
```

Use this to find non-baseline words and known regional clues. Treat names, typos, brands, and jargon as candidates only.

## Python API

```python
from core.regionaliser import analyse_text, detect_region, regionalise

regionalise("Text to regionalise", region="au", register="casual", density="light")
detect_region("I topped up my Opal card before Woolies.")
analyse_text("I went to Woolies after smoko.")
```

## Hermes Plugin / MCP Pointers

If tool integration is needed, install from the repo:

```bash
python3 core/scripts/install_hermes_plugin.py --target ~/.hermes/plugins/localiser --force
hermes plugins enable localiser
```

Stdio MCP command for Claude/Codex/Hermes clients:

```bash
python3 /Users/max/Code/regionaliser/core/scripts/regionaliser_mcp.py
```

Use full `localiser` for the complete tool list and config examples.

## Verification

```bash
python3 core/scripts/validate.py
python3 core/scripts/build_db.py --regions au,us,uk,ca
python3 -m unittest discover -s tests -q
python3 core/scripts/regionalise.py --region au --json "The sidewalk color was weird." | python3 -m json.tool >/dev/null
```

## Common Pitfalls

- Do not copy old generated regional skills into legal/project folders; install from the canonical Regionaliser repo.
- Do not overdo slang or cultural references.
- Do not claim a writer is Australian/American/British/Canadian; say the text has evidence for a region.
- Do not use this light skill for nuanced subregional/legal/research questions; load `localiser` instead.
