#!/usr/bin/env python3
"""Install a baseline English wordlist for Regionaliser diff/analyse mode.

Default order:
1. Copy the host system dictionary if available (/usr/share/dict/words).
2. If --url is provided, download that wordlist instead.

The baseline is deliberately a broad non-regional English wordlist. It is not a
claim that all listed words are region-neutral; it is a practical denominator for
flagging unusual, local, domain, named, or transcript-specific tokens.
"""
from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "core/data/baseline_english_words.txt"
SYSTEM_WORDS = Path("/usr/share/dict/words")
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'’-]{1,}$")


def normalise_words(raw: str) -> list[str]:
    words = set()
    for line in raw.splitlines():
        word = line.strip().lower().replace("’", "'")
        if WORD_RE.match(word) and not word.endswith("'s"):
            words.add(word)
    return sorted(words)


def install(out: Path = DEFAULT_OUT, url: str | None = None, source: Path | None = None) -> Path:
    if url:
        with urllib.request.urlopen(url, timeout=30) as r:  # nosec: user-supplied CLI URL
            raw = r.read().decode("utf-8", errors="ignore")
        source_label = url
    else:
        src = source or SYSTEM_WORDS
        if not src.exists():
            raise FileNotFoundError(
                "No baseline wordlist found. Pass --url or --source, e.g. a SCOWL/wordfreq/plain word list."
            )
        raw = src.read_text(encoding="utf-8", errors="ignore")
        source_label = str(src)
    words = normalise_words(raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(words) + "\n", encoding="utf-8")
    (out.with_suffix(out.suffix + ".meta")).write_text(
        f"source={source_label}\nwords={len(words)}\n",
        encoding="utf-8",
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output baseline wordlist path")
    ap.add_argument("--source", help="Local plain-text wordlist source")
    ap.add_argument("--url", help="Download a plain-text wordlist URL instead of using system dictionary")
    args = ap.parse_args()
    out = install(Path(args.out), url=args.url, source=Path(args.source) if args.source else None)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
