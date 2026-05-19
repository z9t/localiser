#!/usr/bin/env python3
"""Build a local SQLite database from Regionaliser region CSV files."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "core/data/regionaliser.sqlite"
DEFAULT_BASELINE = ROOT / "core/data/baseline_english_words.txt"


def build_db(regions: list[str], out: Path = DEFAULT_DB, baseline: Path = DEFAULT_BASELINE, custom_root: Path | None = None) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.execute("create table entries (region text not null, dataset text not null, rowid_in_csv integer not null, data text not null)")
    con.execute("create index idx_entries_region_dataset on entries(region, dataset)")
    con.execute("create table manifests (region text primary key, data text not null)")
    con.execute("create table baseline_words (word text primary key)")
    con.execute("create table baseline_meta (key text primary key, value text not null)")
    if baseline.exists():
        words = [(w.strip().lower(),) for w in baseline.read_text(encoding="utf-8", errors="ignore").splitlines() if w.strip()]
        con.executemany("insert or ignore into baseline_words(word) values (?)", words)
        con.execute("insert into baseline_meta(key, value) values (?, ?)", ("baseline_path", str(baseline)))
        con.execute("insert into baseline_meta(key, value) values (?, ?)", ("baseline_words", str(len(words))))
    else:
        con.execute("insert into baseline_meta(key, value) values (?, ?)", ("baseline_path", "missing"))
        con.execute("insert into baseline_meta(key, value) values (?, ?)", ("baseline_words", "0"))
    for code in regions:
        region_dir = ROOT / "regions" / code
        manifest = json.loads((region_dir / "manifest.json").read_text(encoding="utf-8"))
        con.execute("insert into manifests(region, data) values (?, ?)", (code, json.dumps(manifest, ensure_ascii=False)))
        for csv_path in sorted((region_dir / "data").glob("*.csv")):
            load_csv(con, code, csv_path)
    custom_base = custom_root or (ROOT / "custom")
    for custom_dir in sorted(custom_base.glob("*")) if custom_base.exists() else []:
        if not custom_dir.is_dir():
            continue
        mp = custom_dir / "manifest.json"
        if not mp.exists():
            continue
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        code = manifest.get("region_code") or custom_dir.name
        con.execute("insert or replace into manifests(region, data) values (?, ?)", (code, json.dumps(manifest, ensure_ascii=False)))
        for csv_path in sorted((custom_dir / "data").glob("*.csv")):
            load_csv(con, code, csv_path)
    con.commit()
    con.close()
    return out


def load_csv(con: sqlite3.Connection, code: str, csv_path: Path) -> None:
    with csv_path.open(newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f), start=1):
            con.execute(
                "insert into entries(region, dataset, rowid_in_csv, data) values (?, ?, ?, ?)",
                (code, csv_path.stem, idx, json.dumps(row, ensure_ascii=False)),
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default="au,us,uk,ca", help="comma-separated region codes")
    ap.add_argument("--out", default=str(DEFAULT_DB), help="output SQLite path")
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="baseline English wordlist path")
    ap.add_argument("--custom-dir", default=str(ROOT / "custom"), help="directory containing custom learned lexicon packs")
    args = ap.parse_args()
    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    out = build_db(regions, Path(args.out), Path(args.baseline), Path(args.custom_dir))
    print(out)


if __name__ == "__main__":
    main()
