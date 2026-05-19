# Growth Plan

Regionaliser should grow as simulation packs, not monolithic prose.

## Next data expansions

For each region, split `data/cultural_references.csv` once it gets large:

- `culture/movies.csv`
- `culture/tv.csv`
- `culture/comedy.csv`
- `culture/music.csv`
- `culture/sport.csv`
- `culture/food.csv`
- `culture/politics.csv`
- `culture/school.csv`
- `culture/internet.csv`
- `culture/quotes.csv`

The builder should merge these into the generated skill and copy raw references.

## Future region packs

Likely next regions:

- `nz` — New Zealand English
- `ie` — Irish English
- `za` — South African English
- `sg` — Singapore English
- `in` — Indian English

## Domain overlays

Keep base region packs conversational/general. Add specialist overlays later:

```text
domains/
  legal/
    au/data/*.csv
    uk/data/*.csv
    us/data/*.csv
    ca/data/*.csv
  medical/
  finance/
  government/
```

Installer shape to aim for:

```bash
python3 core/scripts/install_regions.py --regions au,ca --target ~/.hermes/skills/regionaliser
python3 core/scripts/install_domain.py --domain legal --regions au --target ~/.hermes/skills/regionaliser
```

## Capability sync principle

If a capability appears in one region, it should usually appear as a column/table
in every region, even if the data is initially sparse. Sparse aligned data beats
rich unaligned data because the renderer and agent instructions stay consistent.
