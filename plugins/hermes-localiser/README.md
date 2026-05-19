# Hermes Localiser Plugin

Exposes Regionaliser as Hermes tools.

Install from this checkout:

```bash
python3 core/scripts/install_hermes_plugin.py --target ~/.hermes/plugins/localiser
hermes plugins enable localiser
# restart Hermes or /reset a session
```

If copied outside the repo, set `REGIONALISER_ROOT=/Users/max/Code/regionaliser` in the plugin environment.

Tools:

- `localiser_regionalise_text`
- `localiser_detect_region`
- `localiser_detect_locale`
- `localiser_cultural_context`
- `localiser_sports_context`
- `localiser_named_entities` optional Stanza NER

All tools return JSON strings and use the local SQLite DB at `core/data/regionaliser.sqlite` unless `db_path` is passed.
