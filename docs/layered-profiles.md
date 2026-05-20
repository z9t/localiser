# Layered Profiles and Corpus Mining

Localiser profiles are reviewable data packs that sit on top of a broader language layer.

They are for cases like:

- country root variations: Australian English, Canadian English
- state/city layers: NSW/Sydney, London, Toronto
- smaller reviewed groups: a workplace, fandom, regional town, show/movie corpus, or community of practice

They are not identity classifiers. A profile captures text evidence from a corpus and reviewed human notes; it must not claim a writer's nationality, ethnicity, residence, class, or group membership.

## Layer model

Each profile has exactly one parent:

- `parent_region`: use for a country/root-level profile that sits on top of an existing region such as `au`, `us`, `uk`, or `ca`.
- `parent_profile`: use for a narrower layer that sits on top of another profile.

Examples:

```text
au
└── western-sydney
    └── western-sydney-teens
        └── one-school-or-show-corpus
```

A country/root profile can be reused by many narrower profiles. A narrow profile should not pretend to generalise back upward.

## Create an empty profile

```bash
python3 core/scripts/localise.py \
  --profile-create "Western Sydney Teens" \
  --parent-region au
```

This creates:

```text
profiles/western-sydney-teens/
  manifest.json
  data/lexicon.csv
  data/detection_markers.csv
  data/phrases.csv
  sources/README.md
```

## Mine from supplied text

```bash
python3 core/scripts/localise.py \
  --profile-mine "Remote Oka Crew" \
  --parent-region au \
  --min-count 2 \
  "Oka yarning ridgydidge ridgydidge smoko..."
```

Mining uses baseline dictionary diffing. It creates candidate rows only. Review before use.

## Mine from subtitle/transcript files

Supported local inputs:

- `.srt`
- `.vtt`
- `.txt`
- simple transcript `.json`

```bash
python3 core/scripts/localise.py \
  --profile-mine "Show Corpus" \
  --parent-region au \
  --source ~/Downloads/episode1.srt \
  --source ~/Downloads/episode2.vtt \
  --min-count 3
```

## Mine from YouTube transcripts

If `youtube-transcript-api` is installed, Localiser uses it first. Otherwise it tries `yt-dlp` subtitle extraction.

```bash
python3 -m pip install youtube-transcript-api

python3 core/scripts/localise.py \
  --profile-mine "Creator Corpus" \
  --parent-region au \
  --source "https://www.youtube.com/watch?v=VIDEO_ID" \
  --min-count 3
```

If transcripts are disabled, provide downloaded subtitles or plain text instead.

## Build profiles into the DB

```bash
python3 core/scripts/build_db.py --regions au,us,uk,ca --profiles-dir profiles
```

Profile codes become selectable like region codes:

```bash
python3 core/scripts/localise.py --detect --regions remote-oka-crew --json "ridgydidge smoko"
```

## Review rules

Before treating mined rows as real local language:

1. Remove names, brands, typos, ASR errors, OCR artefacts, and one-off jokes.
2. Add meanings and usage notes manually.
3. Add source notes and as-of dates in `sources/README.md`.
4. Keep weights conservative in `detection_markers.csv`.
5. Keep narrow profiles narrow; do not promote them to country-level evidence unless the corpus supports it.

## Current limitations

- Mining is token-first. Phrase mining is scaffolded via `phrases.csv` but still needs human review.
- YouTube transcript availability depends on subtitles being public.
- The miner does not automatically know whether a term is regional, fandom-specific, a name, a mistake, or a domain term.
