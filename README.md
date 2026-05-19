# Localiser

Region-specific English simulation packs for AI agents.

Goal: install only the English region packs you need — AU, US, UK, Canada now;
more regions later — without duplicating central scripts or letting capability
split across copies.

Localiser is not an agent. It is the information substrate an agent needs to
sound local: spelling, vocabulary, register, generation, regional differences,
class/sociolect notes, cultural references, humour, quotes, taboo traps, and
example transformations.

## Design

```
localiser/
├── core/
│   ├── scripts/              # shared installers/builders/validators
│   └── templates/            # shared skill templates
├── regions/
│   ├── au/                   # Australian English pack
│   ├── us/                   # US English pack
│   ├── uk/                   # UK English pack
│   └── ca/                   # Canadian English pack
└── docs/
```

Each region is standalone from the installer's point of view. You can install
one region or several. Shared code lives in `core/scripts/`; regional data lives
under `regions/<code>/data/`. Generated SKILL.md files are built from shared
templates plus region data, so the regions do not drift in capability.

## Local CLI / API

Install a baseline English wordlist, then build the local SQLite database from
CSV region packs plus the baseline:

```bash
python3 core/scripts/install_baseline.py
python3 core/scripts/build_db.py --regions au,us,uk,ca
```

`install_baseline.py` uses the host system dictionary when present
(`/usr/share/dict/words` on macOS) or can download/copy another plain-text
wordlist with `--url` or `--source`. This keeps the package lean: the baseline
is pulled at install/build time rather than vendored into the repo.

Regionalise a paragraph with no AI/model calls:

```bash
python3 core/scripts/regionalise.py --region au --register casual --density light \
  "I walked on the sidewalk to the gas station and liked the color."
```

The CLI accepts stdin and can write text or JSON:

```bash
printf 'The sidewalk is near the gas station.' | \
  python3 core/scripts/regionalise.py --region uk --json

python3 core/scripts/regionalise.py --region ca --output out.txt "The candy was on the sidewalk."
```

It can also run in detect mode, scoring the likely source region from spelling,
vocabulary, lexicon, cultural, institutional, and geographic clues:

```bash
python3 core/scripts/regionalise.py --detect --json \
  "I topped up my Opal card before stopping at Woolies."
```

Detect mode is deterministic evidence scoring, not proof of author nationality
or location. Short generic text should return low confidence.

AU locale detect mode scores state/capital-city clues such as Opal/myki,
parma/parmi, potato cake/potato scallop, AFL/NRL, and transport/admin labels:

```bash
python3 core/scripts/regionalise.py --detect-locale --json \
  "I topped up my Opal before grabbing a potato scallop and watching the NRL."
```

Sports context mode exposes reviewable sports-cultural rows by country/locality:
top local codes, locally salient teams, current player seeds, and notable
historic players. It can be queried alone or attached to a rewrite request:

```bash
python3 core/scripts/regionalise.py --sports --region uk --locales London --json

python3 core/scripts/regionalise.py --region au --sports --locales VIC/Melbourne \
  "I liked the color of the sidewalk."
```

Sports rows are cultural context only. They are weak evidence and should not be
used to infer residence, class, religion, ethnicity, politics, or allegiance.
Refresh current-player fields from official rosters before high-stakes/current
use.

Context mode exposes the two less performative locality layers: daily-life
institutions/services and media/reference ecology. `--culture` adds a country-
level generational quote/reference bank: films, TV, comedy, internet references,
and short quotable fragments useful for detection or restrained local flavour.
These are useful for building a cultural context tree without stuffing slang into
prose:

```bash
python3 core/scripts/regionalise.py --context --region ca --locales Ontario/Toronto --json

python3 core/scripts/regionalise.py --culture --region au --generation gen-x --json

python3 core/scripts/regionalise.py --region uk --context --locales London \
  "The sidewalk color was unusual."
```

Context/culture rows are still evidence, not proof: people can quote a service,
paper, broadcaster, film, or meme without being from that place. Quote fragments
are short reference handles, not permission to reproduce long copyrighted
passages.

Analyse/diff mode compares text against the installed baseline dictionary and
known regional/custom evidence. This is useful for transcripts and YouTube text:

```bash
python3 core/scripts/regionalise.py --analyse --json \
  "I went to Woolies after smoko with the Oka crew and grabbed a servo pie."
```

Optional Stanford Stanza NER can extract names, places, organisations, and
brands before regional detection or lexicon learning. It is not installed by
default:

```bash
python3 -m pip install '.[ner]'
python3 core/scripts/install_stanza_models.py --lang en
python3 core/scripts/regionalise.py --ner --json \
  "Sydney called Service NSW after Qantas moved the meeting."
```

NER output is candidate structure only; it should help avoid treating names and
organisations as slang or locality proof.

Learn mode creates a reviewable custom lexicon scaffold from non-baseline terms,
e.g. for an Oka bogan pack:

```bash
python3 core/scripts/regionalise.py --learn "Oka bogan" --learn-out custom \
  "Paste examples or a transcript here"
```

This writes `custom/oka-bogan/data/lexicon.csv` and
`custom/oka-bogan/data/detection_markers.csv`. Re-run `build_db.py` afterwards
to include custom packs in detection. If the pack lives outside the repo, pass
`--custom-dir /path/to/custom`. The generated candidates must be reviewed:
baseline diff also catches names, typos, transcription artefacts, and specialist
terms.

Options include `--register`, `--generation`, `--subregion`, `--class`,
`--setting`, and `--density`. The basic version is deterministic and local:
CSV data is compiled into `core/data/localiser.sqlite`; the Python API and
CLI read that DB and do not call an AI service.

Python API:

```python
from core.localiser import analyse_text, cultural_context, detect_locale, detect_region, extract_named_entities, regionalise, sports_context

text = regionalise(
    "I walked on the sidewalk to the gas station.",
    region="au",
    register="casual",
    density="light",
)
report = analyse_text("I went to Woolies after smoko.")
region = detect_region("I topped up my Opal card.")
locale = detect_locale("I topped up my Opal before the NRL.", region="au")
sports = sports_context("uk", locales=["London"])
context = cultural_context("ca", locales=["Ontario/Toronto"])
culture = cultural_context("au", generation="gen-x")
entities = extract_named_entities("Sydney called Service NSW.")
```

## Hermes plugin and MCP server

Hermes plugin install from this checkout:

```bash
python3 core/scripts/install_hermes_plugin.py --target ~/.hermes/plugins/localiser --force
hermes plugins enable localiser
# restart Hermes or start a new session
```

The plugin exposes six tools in the `localiser` toolset:

- `localiser_regionalise_text`
- `localiser_detect_region`
- `localiser_detect_locale`
- `localiser_cultural_context`
- `localiser_sports_context`
- `localiser_named_entities`

Lightweight stdio MCP server for Claude Code, Codex, Hermes, and other MCP
clients:

```bash
python3 core/scripts/localiser_mcp.py
```

Hermes MCP config example:

```yaml
mcp_servers:
  localiser:
    command: "python3"
    args: ["/Users/max/Code/localiser/core/scripts/localiser_mcp.py"]
```

Claude/Codex-style clients should point their stdio MCP command to the same
script. The server is dependency-free and implements `initialize`, `tools/list`,
`tools/call`, and `ping`. Stanza NER remains optional; the NER tool returns an
actionable install/model-download error until configured.

The deterministic rewrite path is deliberately conservative around context-sensitive spellings:

- `practice` stays `practice` in noun compounds such as `practice areas`, but can become `practise` in high-confidence verb contexts such as `practise law`.
- `check` stays `check` for verify/test senses such as `check defences`, but can become `cheque` in banking-instrument contexts such as `bank cheque`.
- `license` can become noun `licence` in headings/labels and noun compounds, while likely verb contexts stay `license`.

Stanza is optional and currently exposed for named-entity extraction (`--ner`) and as a preference-controlled full-localiser protection layer:

```bash
python3 core/scripts/regionalise.py --region au --stanza --json "License Group liked the color."
python3 core/scripts/regionalise.py --analyse --stanza --json "Qantas mentioned smoko."
export LOCALISER_USE_STANZA=1   # default on for this shell/profile
```

Use `--no-stanza` to turn the preference off for a command. When Stanza protection is enabled, named-entity spans are protected from rewrite/diff false positives; if Stanza/models are unavailable, the deterministic output still completes with a setup note. Keep the default path deterministic and conservative; Stanza should increase confidence/protection, not force uncertain rewrites.

## Install localiser skills

Canonical localiser skills live under this repo's `skills/` directory:

- `skills/localiser-light/SKILL.md` — compact default skill for quick AU/US/UK/CA rewrites, detection, and CLI guardrails.
- `skills/localiser/SKILL.md` — full skill for nuanced localisation, context banks, MCP/plugin integration, detection, and optional NER.

Install them into local agent skill directories:

```bash
python3 core/scripts/install_agent_skills.py
```

The installer puts `localiser-light` into every Hermes profile plus Claude/Codex skill dirs, and also puts full `localiser` into Hermes profiles that need the heavier version: seek, soop, knowall, research, qa-eval, and denuto.

## Install one or more generated region skills

Dry run:

```bash
python3 core/scripts/install_regions.py --regions au --target ~/.hermes/skills/localiser --dry-run
```

Install selected regions:

```bash
python3 core/scripts/install_regions.py --regions au,ca --target ~/.hermes/skills/localiser
```

Build generated skills inside this repo for review:

```bash
python3 core/scripts/build_skills.py --regions au,us,uk,ca
```

Validate manifests and CSVs:

```bash
python3 core/scripts/validate.py
```

## Region pack contract

Every `regions/<code>/` contains:

- `manifest.json` — metadata and install name.
- `data/spelling.csv` — spelling conventions and notes.
- `data/vocabulary.csv` — everyday vocabulary comparisons.
- `data/registers.csv` — casual / social-business / formal guidance.
- `data/generations.csv` — Gen Z / Millennial / Boomer guidance.
- `data/regions.csv` — internal regional differences.
- `data/sociolects.csv` — ocker/bogan/redneck/chav/hoser etc. where relevant.
- `data/cultural_references.csv` — broad films, TV, comedy, humour, shared references.
- `data/cultural_quote_references.csv` — optional country-level generational reference bank with short quote fragments and cautions.
- `data/false_friends.csv` — cross-jurisdiction traps.
- `data/foreign_tropes.csv` — foreign tropes/projections versus real local signals.
- `data/urban_rural.csv` — city, suburban, regional, and rural differences.
- `data/detection_markers.csv` — landmarks, institutions, transport, retail, and cultural clues for deterministic detect mode.
- `data/locale_markers.csv` — optional subnational/city clues for deterministic locale scoring.
- `data/sports_locality.csv` — optional sports-cultural locality rows: top codes, teams, current players, historic players, notes, cautions.
- `data/institutional_context.csv` — optional daily-life systems: public services, utilities, schools/exams, health, transport, admin terms.
- `data/media_reference_ecology.csv` — optional media/reference layer: broadcasters, local papers, radio, weather/emergency, civic/event references.

Generated output:

- `regions/<code>/build/<skill-name>/SKILL.md`
- copied references under `regions/<code>/build/<skill-name>/references/`

## Scope

Localiser focuses on lived language and cultural simulation, not specialist
legal vocabulary. Specialist packs can be added later as separate domains, e.g.
`domains/legal/au`, using the same core scripts.
