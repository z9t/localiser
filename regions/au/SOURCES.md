# Australian English source notes

Used to add anti-trope, locally grounded examples. Sources were used for broad vernacular and regional self-description patterns, not for specialist-domain content.

- Australian National Dictionary Centre, Australian National University — Australian words, meanings, origins, and regional vocabulary: https://slll.cass.anu.edu.au/centres/andc
- Macquarie Dictionary Australian Word Map — state/regional term variation such as swimmers/togs/bathers and other local vocabulary (site may block automated fetches): https://www.macquariedictionary.com.au/resources/aus/word/map/
- ABC Everyday / ABC local-life explainers — mundane suburban, regional, weather, school, shopping, and service-context language rather than export stereotypes: https://www.abc.net.au/everyday/
- SBS Voices / SBS Language community stories — multicultural Australian self-description, code-switching awareness, and caution against treating one ethnicity or suburb as a single voice: https://www.sbs.com.au/language/
- State/region discussion types reviewed conceptually: local subreddit and forum discussions for Brisbane/SE QLD, Western Sydney, regional Victoria, Perth/WA, Darwin/Top End, and Far North Queensland; used only for recurring self-described everyday signals such as commute, weather, sport code, shopping, school, services, and distance.
- AU locale marker seed set added 2026-05-19: user-provided contrasts for Opal/myki, parma/parmi, potato cake/potato scallop, AFL/NRL, plus stable public transport/admin labels. These are detection clues, not proof; many can be visitor/travel/media mentions.

Anti-trope guidance applied: prefer practical everyday cues, state/city/suburb specificity, and register control; avoid Crocodile Dundee/Steve Irwin cosplay, universal beach/outback framing, and class-coded sneering.

## Sports locality data

Added `data/sports_locality.csv` as a reviewable sports-cultural context layer for AU localities. Rows cover top local sports/codes, locally salient teams, a few current roster/player names, and notable historic players. Sources are primarily official league/team roster pages and established historical/team pages listed in the CSV `sources` column.

Caution: sports references are weak cultural evidence, not identity proof. Do not infer residence, class, ethnicity, religion, politics, or exact local allegiance from a team, code, or player mention. Current-player fields should be refreshed from official rosters before high-stakes or current-events use.

## Daily-life institutions and media ecology

Added `data/institutional_context.csv` and `data/media_reference_ecology.csv` for AU locality context. Institutional rows favour public-service, utility, health, education, transport, and admin systems that locals actually navigate. Media/reference rows map public broadcasters, local news, weather/emergency channels, and civic/event reference layers.

Caution: these rows are context-tree evidence, not identity proof. A person can mention a service, broadcaster, newspaper, or event because they visited, read about it, worked on it, or are helping someone else. Use several independent clues before trusting a locality inference, and avoid fake-local name-dropping.

## Generational cultural quote/reference bank

Added `data/cultural_quote_references.csv` for AU country-level cultural reference context. Rows are organised by generation and include films, TV, comedy, internet references, civic/sport references, short quote fragments, usage notes, avoid-when guidance, cautions, and source hints.

Caution: these references are weak cultural evidence, not identity or nationality proof. They are taste-, age-, class-, media-diet-, and community-shaped. Quote fragments are intentionally short reference handles; do not reproduce long copyrighted passages or force catchphrases into serious writing.
