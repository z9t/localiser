#!/usr/bin/env python3
"""Download Stanford Stanza models used by Localiser optional NER.

Keeps Stanza optional: install with `pip install '.[ner]'` or `pip install stanza`.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download Stanza models for Localiser NER.")
    parser.add_argument("--lang", default="en", help="Stanza language code. Default: en")
    parser.add_argument("--package", default=None, help="Optional Stanza package/model name.")
    parser.add_argument("--processors", default="tokenize,ner", help="Processors to download. Default: tokenize,ner")
    args = parser.parse_args(argv)

    try:
        import stanza  # type: ignore
    except ImportError:
        print(
            "Stanza is not installed. Run: python3 -m pip install '.[ner]'  # or: python3 -m pip install stanza",
            file=sys.stderr,
        )
        return 1

    kwargs = {"lang": args.lang, "processors": args.processors}
    if args.package:
        kwargs["package"] = args.package
    stanza.download(**kwargs)
    print(f"downloaded stanza models lang={args.lang} processors={args.processors} package={args.package or 'default'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
