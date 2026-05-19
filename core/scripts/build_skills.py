#!/usr/bin/env python3
"""Build Localiser region skills from shared template + regional CSV data."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = (ROOT / 'core/templates/SKILL.md.tpl').read_text(encoding='utf-8')
DATASETS = ['registers','generations','regions','urban_rural','sociolects','foreign_tropes','spelling','vocabulary','lexicon','cultural_references','cultural_quote_references','false_friends','detection_markers','locale_markers','sports_locality','institutional_context','media_reference_ecology']

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def md_table(rows, limit=18):
    if not rows:
        return '_No data yet._'
    cols = list(rows[0].keys())
    out = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(['---']*len(cols)) + ' |']
    for row in rows[:limit]:
        out.append('| ' + ' | '.join(str(row.get(c,'')).replace('\n',' ').replace('|','/') for c in cols) + ' |')
    if len(rows) > limit:
        remaining = len(rows)-limit
        out.append('| ' + ' | '.join([f'… {remaining} more entries in references CSV'] + ['']*(len(cols)-1)) + ' |')
    return '\n'.join(out)

def build_region(code: str) -> Path:
    region = ROOT / 'regions' / code
    manifest = json.loads((region / 'manifest.json').read_text(encoding='utf-8'))
    tables = {}
    for ds in DATASETS:
        path = region / 'data' / f'{ds}.csv'
        tables[f'{ds}_table'] = md_table(read_csv(path)) if path.exists() else '_No data yet._'
    skill = TEMPLATE
    values = {**manifest, **tables}
    for key, val in values.items():
        skill = skill.replace('{{' + key + '}}', str(val))
    outdir = region / 'build' / manifest['skill_name']
    refdir = outdir / 'references'
    refdir.mkdir(parents=True, exist_ok=True)
    (outdir / 'SKILL.md').write_text(skill, encoding='utf-8')
    for csv_path in (region / 'data').glob('*.csv'):
        (refdir / csv_path.name).write_text(csv_path.read_text(encoding='utf-8'), encoding='utf-8')
    return outdir

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regions', default='au,us,uk,ca', help='comma-separated region codes')
    args = ap.parse_args()
    for code in [x.strip() for x in args.regions.split(',') if x.strip()]:
        print(build_region(code))
if __name__ == '__main__':
    main()
