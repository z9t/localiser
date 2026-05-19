#!/usr/bin/env python3
"""Install Localiser localiser skills into agent/Hermes skill directories."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills"
FULL_PROFILES = {"seek", "soop", "knowall", "research", "qa-eval", "denuto"}


def copy_skill(name: str, dest_skills_dir: Path) -> Path:
    src = SOURCE / name
    if not (src / "SKILL.md").exists():
        raise SystemExit(f"Missing source skill: {src / 'SKILL.md'}")
    dst = dest_skills_dir / name
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return dst


def hermes_profile_skill_dirs(home: Path) -> list[tuple[str, Path]]:
    dirs: list[tuple[str, Path]] = [("default", home / ".hermes" / "skills")]
    profiles = home / ".hermes" / "profiles"
    if profiles.exists():
        for p in sorted(profiles.iterdir()):
            if p.is_dir():
                dirs.append((p.name, p / "skills"))
    return dirs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--home", default=str(Path.home()))
    ap.add_argument("--full-profiles", default=",".join(sorted(FULL_PROFILES)))
    ap.add_argument("--skip-claude-codex", action="store_true")
    args = ap.parse_args()

    home = Path(args.home).expanduser()
    full_profiles = {x.strip() for x in args.full_profiles.split(",") if x.strip()}
    installed: list[str] = []

    for profile, skills_dir in hermes_profile_skill_dirs(home):
        installed.append(str(copy_skill("localiser-light", skills_dir)))
        if profile in full_profiles:
            installed.append(str(copy_skill("localiser", skills_dir)))

    if not args.skip_claude_codex:
        for skills_dir in [home / ".claude" / "skills", home / ".codex" / "skills"]:
            installed.append(str(copy_skill("localiser-light", skills_dir)))

    print("\n".join(installed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
