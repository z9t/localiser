# Sources and discussion types used

This expansion prioritises regional self-description, dialect documentation and anti-stereotype guidance rather than foreign pop-culture tropes.

- Our Dialects / English Dialect App, University of Leeds: regional lexical variation and self-reported dialect data. https://www.ourdialects.uk/
- Dictionaries of the Scots Language: Scots vocabulary and usage context; used as a caution not to fake Scots spelling or collapse Scotland into generic UK English. https://dsl.ac.uk/
- Accent Bias Britain: evidence that accent/class stereotypes are socially loaded; used for cautions around RP, regional accents and class-coded voices. https://accentbiasbritain.org/
- British Library Sounds / archival accents and dialects collection: dialect diversity and locality-oriented recordings; used as background for avoiding a single “British accent”.
- BBC Voices / regional language discussions: public-facing regional word and accent discussions; used for lived local signals and regional variation.
- Local UK self-description patterns from council, transport, NHS-style, university, local news, football-club, community-centre and high-street contexts; used for everyday institutional and place cues.
- Locale marker seed set added 2026-05-19: devolved institutions, transport authorities/cards, local rail/bus systems, education/admin terms, and cautious food/place markers. Avoids fake dialect spelling and treats England/Scotland/Wales/Northern Ireland and English regions separately.
- Anti-trope review lens: avoid monarchy/tea/posh/London-only defaults; treat England, Scotland, Wales and Northern Ireland as distinct contexts; avoid phonetic parody and racialised/class-coded sociolect borrowing.

## Sports locality data

Added `data/sports_locality.csv` as a reviewable sports-cultural context layer for UK localities. Rows cover top local sports/codes, locally salient teams, a few current roster/player names, and notable historic players. Sources are primarily official league/team roster pages and established historical/team pages listed in the CSV `sources` column.

Caution: sports references are weak cultural evidence, not identity proof. Do not infer residence, class, ethnicity, religion, politics, or exact local allegiance from a team, code, or player mention. Current-player fields should be refreshed from official rosters before high-stakes or current-events use.

## Daily-life institutions and media ecology

Added `data/institutional_context.csv` and `data/media_reference_ecology.csv` for UK locality context. Institutional rows favour public-service, utility, health, education, transport, and admin systems that locals actually navigate. Media/reference rows map public broadcasters, local news, weather/emergency channels, and civic/event reference layers.

Caution: these rows are context-tree evidence, not identity proof. A person can mention a service, broadcaster, newspaper, or event because they visited, read about it, worked on it, or are helping someone else. Use several independent clues before trusting a locality inference, and avoid fake-local name-dropping.

## Generational cultural quote/reference bank

Added `data/cultural_quote_references.csv` for UK country-level cultural reference context. Rows are organised by generation and include films, TV, comedy, internet references, civic/sport references, short quote fragments, usage notes, avoid-when guidance, cautions, and source hints.

Caution: these references are weak cultural evidence, not identity or nationality proof. They are taste-, age-, class-, media-diet-, and community-shaped. Quote fragments are intentionally short reference handles; do not reproduce long copyrighted passages or force catchphrases into serious writing.
