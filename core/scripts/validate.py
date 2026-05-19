#!/usr/bin/env python3
"""Validate Regionaliser manifests and CSV files."""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ['registers','generations','regions','urban_rural','sociolects','foreign_tropes','spelling','vocabulary','lexicon','cultural_references','false_friends','detection_markers']
OPTIONAL = ['locale_markers','sports_locality','institutional_context','media_reference_ecology','cultural_quote_references']
EXPECTED_COLUMNS = {
    'locale_markers': ['marker','scope','locales','weight','meaning','notes','caution'],
    'sports_locality': ['locale','rank','sport','code','team','league','current_players','notable_historic_players','notes','caution','sources'],
    'institutional_context': ['locale','domain','institution_or_term','meaning','typical_context','strength','caution','sources'],
    'media_reference_ecology': ['locale','category','reference','what_it_signals','typical_phrase','generation_or_register','strength','caution','sources'],
    'cultural_quote_references': ['locale','generation','reference_type','reference','era','quote_fragments','how_used','avoid_when','caution','sources'],
}

def fail(msg):
    print('FAIL:', msg)
    return 1

def main():
    status = 0
    for region in sorted((ROOT/'regions').iterdir()):
        if not region.is_dir():
            continue
        mp = region/'manifest.json'
        if not mp.exists():
            status |= fail(f'{region.name}: missing manifest.json'); continue
        m = json.loads(mp.read_text(encoding='utf-8'))
        for k in ['region_code','skill_name','display_name','description','overview']:
            if not m.get(k): status |= fail(f'{region.name}: missing {k}')
        if not re.match(r'^[a-z]{2}-english$', m.get('skill_name','')):
            status |= fail(f'{region.name}: unexpected skill_name {m.get("skill_name")}')
        for ds in REQUIRED:
            p = region/'data'/f'{ds}.csv'
            if not p.exists():
                status |= fail(f'{region.name}: missing {ds}.csv'); continue
            with p.open(newline='', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            if len(rows) < 2:
                status |= fail(f'{region.name}: {ds}.csv has no data rows')
        for ds in OPTIONAL:
            p = region/'data'/f'{ds}.csv'
            if not p.exists():
                continue
            with p.open(newline='', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            if len(rows) < 2:
                status |= fail(f'{region.name}: {ds}.csv has no data rows')
            expected = EXPECTED_COLUMNS.get(ds)
            if expected and rows and rows[0] != expected:
                status |= fail(f'{region.name}: {ds}.csv columns {rows[0]} != {expected}')
            if rows:
                width = len(rows[0])
                for idx, row in enumerate(rows[1:], start=2):
                    if len(row) != width:
                        status |= fail(f'{region.name}: {ds}.csv row {idx} has {len(row)} columns, expected {width}')
    if status == 0:
        print('ok')
    return status
if __name__ == '__main__':
    raise SystemExit(main())
