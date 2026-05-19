#!/usr/bin/env python3
"""Run the Localiser stdio MCP server from a repo checkout."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.localiser.mcp_server import main

if __name__ == "__main__":
    raise SystemExit(main())
