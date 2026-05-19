#!/usr/bin/env python3
"""Repo-local wrapper for the Localiser CLI."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.localiser.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
