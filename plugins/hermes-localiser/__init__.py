"""Hermes Localiser plugin.

Install/copy this directory to ~/.hermes/plugins/localiser and enable it with:
  hermes plugins enable localiser

The plugin imports the repo-local Regionaliser package by locating this checkout
relative to the plugin directory, or via REGIONALISER_ROOT when copied elsewhere.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _add_regionaliser_root() -> None:
    env_root = os.getenv("REGIONALISER_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    root_file = Path(__file__).resolve().parent / "regionaliser_root.txt"
    if root_file.exists():
        candidates.append(Path(root_file.read_text(encoding="utf-8").strip()).expanduser())
    here = Path(__file__).resolve()
    candidates.extend([
        here.parents[2] if len(here.parents) > 2 else here.parent,
        Path.cwd(),
    ])
    for root in candidates:
        if (root / "core" / "regionaliser" / "engine.py").exists():
            sys.path.insert(0, str(root))
            return


_add_regionaliser_root()

from core.regionaliser import tool_api, tool_schemas  # noqa: E402


def register(ctx):
    """Register Regionaliser tools with Hermes."""
    for schema in tool_schemas.TOOLS:
        ctx.register_tool(
            name=schema["name"],
            toolset="localiser",
            schema=schema,
            handler=tool_api.HANDLERS[schema["name"]],
        )
