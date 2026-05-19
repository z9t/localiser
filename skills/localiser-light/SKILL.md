---
name: localiser-light
description: Use for quick dependency-free AU/US/UK/CA English localisation edits with the standalone localiser-light CLI. Prefer for compact default profiles and general agents that only need basic rewrite, detect, and analyse.
version: 0.1.0
author: Regionaliser
license: MIT
metadata:
  hermes:
    tags: [localisation, regional-english, cli, compact]
    related_skills: [localiser]
---

# Localiser Light

Compact dependency-free localiser for everyday AU/US/UK/CA English edits.

## Setup

Install the standalone package:

```bash
python3 -m pip install --user git+https://github.com/z9t/localiser-light.git
```

Install this skill into common agent dirs:

```bash
localiser-light install-skill --all
```

One-shot installer after the repo is public:

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/z9t/localiser-light/main/install.py)"
```

Supported regions:

```text
au, us, uk, ca
```

Use the full `localiser`/Regionaliser repo when you need cultural/context datasets, locality/sports context, custom lexicons, Hermes plugin/MCP, or optional Stanza NER protection.

## Quick Rules

1. Preserve meaning, names, quotes, citations, legal/domain terms, URLs, and code.
2. Default to light localisation: spelling + obvious vocabulary, not heavy slang.
3. Do not infer identity or residence from text.
4. Detection is evidence, not proof.
5. If unsure, run the CLI with `--json` and inspect changes/notes.

## Rewrite Text

```bash
localiser-light --region au "I walked on the sidewalk to the gas station and liked the color."
```

Use stdin + JSON for agent workflows:

```bash
printf 'The sidewalk color was weird.' | localiser-light --region uk --json
```

Write to a file:

```bash
localiser-light --region ca --output out.txt "The candy was on the sidewalk."
```

## Detect Region

```bash
localiser-light --detect --regions au,us,uk,ca --json "I topped up my Opal card before stopping at Woolies."
```

Read candidates, confidence, evidence, and notes. Do not force a region for generic or mixed text.

## Analyse/Diff

```bash
localiser-light --analyse --json "I went to Woolies after smoko and grabbed a servo pie."
```

Use this to find non-baseline words and known regional clues. The built-in baseline is tiny; treat names, typos, brands, and jargon as candidates only.

## Python API

```python
from localiser_light import analyse, detect_region, regionalise

regionalise("Text to regionalise", region="au")
detect_region("I topped up my Opal card before Woolies.")
analyse("I went to Woolies after smoko.")
```

## Verification

```bash
localiser-light --region au --json "The sidewalk color was weird." | python3 -m json.tool >/dev/null
localiser-light --detect --json "I topped up my Opal card before Woolies."
```

## Common Pitfalls

- Do not overdo slang or cultural references.
- Do not claim a writer is Australian/American/British/Canadian; say the text has evidence for a region.
- Do not use this light skill for nuanced subregional/legal/research questions; load full `localiser` instead.
- Do not expect Stanza here; optional NLP stays in the full localiser.
