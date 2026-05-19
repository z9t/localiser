# Regionaliser Agent Notes

Regionaliser is data-first.

Rules:

1. Keep executable logic in `core/scripts/` only.
2. Keep shared output structure in `core/templates/` only.
3. Keep region-specific content in `regions/<code>/data/*.csv` and `manifest.json`.
4. Do not hand-edit generated `regions/<code>/build/` files except for debugging; rebuild them with `python3 core/scripts/build_skills.py`.
5. Do not duplicate installer/render/validation logic inside region folders.
6. If a region needs a special rule, add a data field and teach the central script to interpret it.
7. Base region packs are for everyday written/conversational simulation. Put specialist domain packs in future `domains/<domain>/<region>/`, not in base region packs.

Verification before reporting done:

```bash
python3 core/scripts/validate.py
python3 core/scripts/build_skills.py --regions au,us,uk,ca
python3 core/scripts/install_regions.py --regions au --target /tmp/regionaliser-test --dry-run
```
