---
name: {{skill_name}}
description: {{description}}
argument-hint: "[text to localise, register/generation/region to target, or cultural localness question]"
---

# {{display_name}}

## Overview

{{overview}}

This is a general written and conversational English simulation pack. It is not
a specialist legal, medical, financial, or technical vocabulary pack. If the text
contains specialist terms, preserve domain accuracy while applying local spelling,
register, idiom, and cultural expectations.

## Operating Mode

Before writing, choose:

1. Register: casual/conversational, social-business/middle-class dinner, or formal/institutional.
2. Generation: broad neutral, Gen Z, Millennial, or Boomer/older.
3. Region: national default or a specific subregion.
4. Sociolect: only if requested; do not caricature class or rural identity.
5. Cultural density: light, medium, or high. Default to light.

## Local CLI / API

For deterministic baseline edits, use the repo-local Localiser CLI/API rather
than improvising from memory. The basic version is local, script/SQLite-backed,
and makes no AI calls.

CLI:

```bash
python3 core/scripts/localise.py --region {{region_code}} --register casual --density light "Text to localise"
```

Stdin / JSON:

```bash
printf 'Text to localise' | python3 core/scripts/localise.py --region {{region_code}} --json
```

Detect likely source region instead of rewriting:

```bash
python3 core/scripts/localise.py --detect --json "Text to classify"
```

Diff against baseline English and known regional clues:

```bash
python3 core/scripts/localise.py --analyse --json "Text or transcript to inspect"
```

Detect AU state/capital-city locale clues:

```bash
python3 core/scripts/localise.py --detect-locale --json "I topped up my Opal before grabbing a potato scallop."
```

Create a reviewable custom lexicon scaffold from examples:

```bash
python3 core/scripts/localise.py --learn "Oka bogan" --learn-out custom "Example text"
```

Python API used by the CLI:

```python
from core.localiser import analyse_text, detect_region, localise
localise("Text to localise", region="{{region_code}}", register="casual", density="light")
```

Use CLI/API output as the first pass, then apply judgement with this skill's
tables for class, subregion, generation, setting, and anti-trope constraints.
Do not over-stuff slang; preserve quotes, names, titles, URLs, code, and
official wording.

## Register Levels

{{registers_table}}

## Generational Layer

{{generations_table}}

## Regional Differences

{{regions_table}}

## City, Regional, and Rural Differences

{{urban_rural_table}}

## Sociolect / Class-Coded Voice

{{sociolects_table}}

Use sociolect markers only when requested for character voice, quoted speech,
humour, or analysis. Do not use them as a default and do not punch down.

## Foreign Tropes vs Real Local Signals

{{foreign_tropes_table}}

Foreign projections can be useful as warnings: they show what *not* to do. A convincing local voice usually comes from boring everyday details, not the export stereotype.

## Spelling Conventions

{{spelling_table}}

## Everyday Vocabulary

{{vocabulary_table}}

## Vernacular Lexicon

{{lexicon_table}}

## Cultural References and Humour

{{cultural_references_table}}

## Generational Cultural Quote / Reference Bank

{{cultural_quote_references_table}}

Use quote fragments as detection/context evidence or as light inspiration only.
Do not paste long copyrighted quotes into output. Match generation, topic, and
register; one apt reference is better than name-dropping a list.

## Detection Markers

{{detection_markers_table}}

## State / Provincial / Capital-City Locale Markers

{{locale_markers_table}}

## Sports Locality Data

{{sports_locality_table}}

Sports references are useful cultural evidence but weak identity evidence. Use
team/code/player rows only when the user's text or requested locality warrants
it. Do not infer politics, class, ethnicity, religion, or residence from a team
mention. Current-player fields are intentionally reviewable and should be
refreshed before high-stakes/current-events use.

## Daily-Life Institutions / Services

{{institutional_context_table}}

Institutional/service rows are often better locality evidence than slang: people
mention the agencies, utilities, exams, health systems, portals, and forms they
actually deal with. Use them as context-tree nodes and detection evidence, not
identity proof.

## Media / Reference Ecology

{{media_reference_ecology_table}}

Media/reference rows describe the local information layer: public broadcasters,
local papers, radio, weather/emergency channels, annual events, and civic
reference points. Use sparingly and only where topic, locality, generation, and
register fit.

Use these as evidence for detect mode, not as proof. Geographic, institutional,
transport, retail, and cultural clues are strongest when several independent
signals point the same way. Major city names alone are weak.

Cultural references are optional seasoning, not proof of localness. Prefer one
well-placed reference over a pile of obvious stereotypes.

## False Friends and Traps

{{false_friends_table}}

## Localness Checklist

- [ ] Register matches the setting.
- [ ] Generation layer is intentional or neutral.
- [ ] Region is national-default unless a subregion was requested.
- [ ] Sociolect is respectful and not caricatured.
- [ ] Foreign tropes have been avoided unless deliberately discussed.
- [ ] City/regional/rural setting is represented with real details, not stereotypes.
- [ ] Vocabulary and spelling match the region.
- [ ] Cultural references are accurate and not overused.
- [ ] No specialist-domain scope creep unless requested.
- [ ] Quotes, names, titles, URLs, code, and official wording are preserved.
