#!/usr/bin/env python3
"""Install the Localiser Hermes plugin into a Hermes plugins directory."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "plugins" / "hermes-localiser"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/copy the Localiser Hermes plugin.")
    parser.add_argument("--target", default="~/.hermes/plugins/localiser", help="Plugin directory target. Default: ~/.hermes/plugins/localiser")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target directory.")
    args = parser.parse_args()
    target = Path(args.target).expanduser()
    if target.exists():
        if not args.force:
            raise SystemExit(f"Target exists: {target}. Pass --force to overwrite.")
        shutil.rmtree(target)
    shutil.copytree(SRC, target)
    (target / "localiser_root.txt").write_text(str(ROOT) + "\n", encoding="utf-8")
    print(target)
    print("Next: hermes plugins enable localiser  # then restart Hermes or /reset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
