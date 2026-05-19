#!/usr/bin/env python3
"""Install selected Regionaliser skills to a target skills directory."""
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'core/scripts/build_skills.py'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regions', required=True, help='comma-separated region codes, e.g. au,ca')
    ap.add_argument('--target', required=True, help='target skills directory')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    subprocess.check_call([sys.executable, str(BUILD), '--regions', args.regions])
    target = Path(args.target).expanduser()
    for code in [x.strip() for x in args.regions.split(',') if x.strip()]:
        manifest_path = ROOT / 'regions' / code / 'manifest.json'
        import json
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        src = ROOT / 'regions' / code / 'build' / manifest['skill_name']
        dst = target / manifest['skill_name']
        if args.dry_run:
            print(f'would install {src} -> {dst}')
            continue
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        print(f'installed {manifest["skill_name"]} -> {dst}')
if __name__ == '__main__':
    main()
