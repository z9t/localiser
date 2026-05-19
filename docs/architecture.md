# Localiser Architecture

## Principle

Keep behaviour central and data regional.

- Central scripts: install, validate, build, render.
- Central templates: SKILL.md structure and common checklists.
- Regional data: vocabulary, spelling, references, humour, sociolects.
- Optional future domains: legal, medical, finance, youth slang, government.

## Why

If each region has its own hand-written script, AU and Canada will eventually
have different capabilities. The installer, validator, and renderer must remain
single-source. Region packs should be data-first.

## Current build model

1. Read `regions/<code>/manifest.json`.
2. Read all CSV files in `regions/<code>/data/`.
3. Render `core/templates/SKILL.md.tpl` with region metadata and compact tables.
4. Copy raw CSVs into the skill's `references/` folder.
5. Install only requested generated skill folders to the requested target.

## Future growth hooks

- `domains/<domain>/<region>/data/*.csv` for specialist vocab without bloating
  base region skills.
- `data/cultural_references.csv` can grow into multiple files:
  `movies.csv`, `tv.csv`, `comedy.csv`, `sport.csv`, `politics.csv`,
  `school.csv`, `food.csv`, `music.csv`, `internet.csv`.
- Add embeddings/search later over region data without changing pack structure.
- Add `tests/examples/*.json` per region for prompt-response smoke tests.

## Avoiding duplicated scripts

All executable logic belongs under `core/scripts/`. Region folders should contain
data and generated build outputs only. If a region needs special handling, add a
field to `manifest.json` and make the central script interpret it.
