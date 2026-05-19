# United States English source notes

Used to add anti-trope, locally grounded examples. Sources were used for broad vernacular and regional self-description patterns, not for specialist-domain content.

- Dictionary of American Regional English (DARE) — regional vocabulary, lexical variation, and evidence against one-size-fits-all American English: https://www.daredictionary.com/
- American Dialect Society — dialect scholarship and public discussion of American English variation: https://americandialect.org/
- Bert Vaux / Harvard Dialect Survey maps — self-reported terms such as soda/pop/coke, sneakers/tennis shoes, and regional usage contrasts: https://www4.uwm.edu/FLL/linguistics/dialect/
- Joshua Katz / NC State dialect visualisations derived from survey data — accessible maps for regional lexical differences: https://www4.ncsu.edu/~jakatz2/project-dialect.html
- Aschmann North American English Dialects map — high-level regional dialect geography reference: https://aschmann.net/AmEng/
- U.S. Census urban/rural and metro discussion pages — distinction between urban, suburban, exurban, small-town, and rural contexts: https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural.html
- Local self-description discussion types reviewed conceptually: city/state subreddits and local forums for New England, Appalachia, Great Plains, Pacific Northwest, Mountain West, Hawaiʻi, Alaska, college towns, exurbs, and inner suburbs; used only for recurring everyday signals such as weather, commute, county/school identity, local chains, sports, and distance.
- Locale marker seed set added 2026-05-19: transit/fare systems, state admin labels, local chains, food-ordering terms, and infrastructure phrases. Weights are intentionally conservative for terms that travel through tourism, migration, media, or chain expansion.

Anti-trope guidance applied: choose region and setting before idiom; avoid Hollywood-only school/college cues, generic NYC/LA/Texas framing, redneck caricature, fake cheerfulness, and phonetic eye-dialect.

## Sports locality data

Added `data/sports_locality.csv` as a reviewable sports-cultural context layer for US localities. Rows cover top local sports/codes, locally salient teams, a few current roster/player names, and notable historic players. Sources are primarily official league/team roster pages and established historical/team pages listed in the CSV `sources` column.

Caution: sports references are weak cultural evidence, not identity proof. Do not infer residence, class, ethnicity, religion, politics, or exact local allegiance from a team, code, or player mention. Current-player fields should be refreshed from official rosters before high-stakes or current-events use.

## Daily-life institutions and media ecology

Added `data/institutional_context.csv` and `data/media_reference_ecology.csv` for US locality context. Institutional rows favour public-service, utility, health, education, transport, and admin systems that locals actually navigate. Media/reference rows map public broadcasters, local news, weather/emergency channels, and civic/event reference layers.

Caution: these rows are context-tree evidence, not identity proof. A person can mention a service, broadcaster, newspaper, or event because they visited, read about it, worked on it, or are helping someone else. Use several independent clues before trusting a locality inference, and avoid fake-local name-dropping.

## Generational cultural quote/reference bank

Added `data/cultural_quote_references.csv` for US country-level cultural reference context. Rows are organised by generation and include films, TV, comedy, internet references, civic/sport references, short quote fragments, usage notes, avoid-when guidance, cautions, and source hints.

Caution: these references are weak cultural evidence, not identity or nationality proof. They are taste-, age-, class-, media-diet-, and community-shaped. Quote fragments are intentionally short reference handles; do not reproduce long copyrighted passages or force catchphrases into serious writing.
