"""Layered profile and corpus-mining helpers for Localiser.

Profiles are reviewable packs under ``profiles/<slug>/`` or any custom root.
They can sit at a country root (``parent_region=au``) or on top of another
profile (``parent_profile=western-sydney-youth``). Build/load order is captured
in each manifest so agents can reason about inheritance without guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import csv
import json
import re
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

from .engine import Localiser, slugify

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_ROOT = ROOT / "profiles"
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'’_-]*")


@dataclass
class ProfileResult:
    name: str
    slug: str
    root: str
    parent_region: str | None = None
    parent_profile: str | None = None
    layer_depth: int = 0
    files: list[str] = field(default_factory=list)
    candidates: list[dict[str, object]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "slug": self.slug,
            "root": self.root,
            "parent_region": self.parent_region,
            "parent_profile": self.parent_profile,
            "layer_depth": self.layer_depth,
            "files": self.files,
            "candidates": self.candidates,
            "notes": self.notes,
        }


def create_profile(
    name: str,
    parent_region: str | None = None,
    parent_profile: str | None = None,
    root: str | Path = DEFAULT_PROFILE_ROOT,
    description: str | None = None,
    overwrite: bool = False,
) -> ProfileResult:
    if bool(parent_region) == bool(parent_profile):
        raise ValueError("Set exactly one of parent_region or parent_profile.")
    slug = slugify(name)
    base = Path(root) / slug
    if base.exists() and not overwrite:
        raise FileExistsError(f"Profile already exists: {base}; pass overwrite=True to replace")
    if base.exists():
        import shutil
        shutil.rmtree(base)
    data = base / "data"
    sources = base / "sources"
    data.mkdir(parents=True, exist_ok=True)
    sources.mkdir(parents=True, exist_ok=True)
    depth = _layer_depth(Path(root), parent_profile)
    manifest = {
        "profile_name": name,
        "profile_code": slug,
        "display_name": f"{name} Localiser Profile",
        "description": description or f"Layered localiser profile for {name}.",
        "parent_region": parent_region,
        "parent_profile": parent_profile,
        "layer_depth": depth,
        "kind": "layered_profile",
        "review_status": "draft",
        "notes": [
            "Layered profile: apply parent country/profile first, then this profile's reviewed variations.",
            "Evidence is linguistic/corpus context, not identity, ethnicity, residence, or class proof.",
        ],
    }
    _write_json(base / "manifest.json", manifest)
    _write_csv(data / "lexicon.csv", ["term", "category", "register", "region_or_group", "meaning", "usage_notes", "avoid_when", "source_count", "sources"], [])
    _write_csv(data / "detection_markers.csv", ["marker", "type", "weight", "notes", "sources"], [])
    _write_csv(data / "phrases.csv", ["phrase", "category", "meaning", "usage_notes", "avoid_when", "source_count", "sources"], [])
    (sources / "README.md").write_text(
        "# Sources\n\nAdd reviewed YouTube transcript URLs, subtitle file names, corpus notes, and as-of dates here.\n",
        encoding="utf-8",
    )
    notes = [
        "Created empty layered profile scaffold.",
        "Country/root profiles should set parent_region. Narrow/local/community profiles should set parent_profile so they layer on top of a reviewed parent.",
    ]
    return ProfileResult(name=name, slug=slug, root=str(base), parent_region=parent_region, parent_profile=parent_profile, layer_depth=depth, files=[str(p) for p in sorted(base.rglob("*")) if p.is_file()], notes=notes)


def mine_profile_from_text(
    name: str,
    text: str,
    parent_region: str | None = None,
    parent_profile: str | None = None,
    root: str | Path = DEFAULT_PROFILE_ROOT,
    min_count: int = 2,
    source: str = "manual corpus",
    overwrite: bool = False,
    db_path: str | Path | None = None,
) -> ProfileResult:
    result = create_profile(name, parent_region=parent_region, parent_profile=parent_profile, root=root, overwrite=overwrite)
    base = Path(result.root)
    engine = Localiser(db_path or (ROOT / "core/data/localiser.sqlite"))
    analysis = engine.analyse(text, regions=[parent_region] if parent_region else None, max_terms=300)
    candidates = [c for c in analysis.non_baseline if int(str(c.get("count", 0))) >= min_count]
    _append_candidates(base, result.name, candidates, source)
    corpus_path = base / "sources" / "corpus.txt"
    corpus_path.write_text(text, encoding="utf-8")
    result.candidates = candidates
    result.files = [str(p) for p in sorted(base.rglob("*")) if p.is_file()]
    result.notes.extend([
        "Mined non-baseline token candidates from supplied corpus; review lexicon.csv before trusting.",
        "Subtitle/transcript artefacts, names, OCR/ASR errors, fandom terms, and domain jargon may be present.",
    ])
    return result


def mine_profile_from_sources(
    name: str,
    sources: list[str],
    parent_region: str | None = None,
    parent_profile: str | None = None,
    root: str | Path = DEFAULT_PROFILE_ROOT,
    min_count: int = 2,
    overwrite: bool = False,
) -> ProfileResult:
    texts: list[str] = []
    source_labels: list[str] = []
    for item in sources:
        text, label = source_to_text(item)
        if text.strip():
            texts.append(text)
            source_labels.append(label)
    if not texts:
        raise ValueError("No transcript/subtitle/plain-text content could be read from sources.")
    return mine_profile_from_text(
        name,
        "\n\n".join(texts),
        parent_region=parent_region,
        parent_profile=parent_profile,
        root=root,
        min_count=min_count,
        source="; ".join(source_labels),
        overwrite=overwrite,
    )


def source_to_text(source: str) -> tuple[str, str]:
    p = Path(source).expanduser()
    if p.exists():
        return subtitle_or_text_to_plain(p), str(p)
    if is_youtube_url(source):
        return fetch_youtube_transcript(source), source
    raise FileNotFoundError(f"Source is not a readable file or YouTube URL: {source}")


def subtitle_or_text_to_plain(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return "\n".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in data)
            if isinstance(data, dict):
                return "\n".join(str(v) for v in data.values() if isinstance(v, str))
        except json.JSONDecodeError:
            pass
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.isdigit() or "-->" in s or s.upper().startswith(("WEBVTT", "NOTE")):
            continue
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"\{\\.*?\}", "", s)
        lines.append(s)
    return "\n".join(lines)


def fetch_youtube_transcript(url: str, languages: str = "en") -> str:
    video_id = youtube_id(url)
    # Prefer youtube-transcript-api when available; otherwise try yt-dlp subtitles.
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[x.strip() for x in languages.split(",") if x.strip()])
        return "\n".join(str(row.get("text", "")) for row in transcript)
    except Exception as first_error:
        cmd = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--skip-download", "--write-auto-subs", "--write-subs", "--sub-lang", languages, "--sub-format", "vtt", "--print", "after_move:filepath", url]
        try:
            proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
            paths = [Path(x.strip()) for x in proc.stdout.splitlines() if x.strip()]
            for candidate in paths + list(Path.cwd().glob(f"*{video_id}*.vtt")):
                if candidate.exists():
                    return subtitle_or_text_to_plain(candidate)
        except Exception:
            pass
        raise RuntimeError("Could not fetch YouTube transcript. Install youtube-transcript-api or yt-dlp, or provide a subtitle/text file. Original error: " + str(first_error))


def is_youtube_url(value: str) -> bool:
    host = urlparse(value).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower().endswith("youtu.be"):
        return parsed.path.strip("/").split("/")[0]
    qs = parse_qs(parsed.query)
    if qs.get("v"):
        return qs["v"][0]
    parts = [p for p in parsed.path.split("/") if p]
    if parts:
        return parts[-1]
    return url


def _append_candidates(base: Path, group: str, candidates: list[dict[str, object]], source: str) -> None:
    lexicon = base / "data" / "lexicon.csv"
    markers = base / "data" / "detection_markers.csv"
    with lexicon.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["term", "category", "register", "region_or_group", "meaning", "usage_notes", "avoid_when", "source_count", "sources"])
        for c in candidates:
            writer.writerow({
                "term": c["term"],
                "category": "candidate",
                "register": "unknown",
                "region_or_group": group,
                "meaning": "TODO",
                "usage_notes": "Mined from transcript/subtitle corpus because absent from baseline English wordlist",
                "avoid_when": "unreviewed",
                "source_count": c.get("count", 0),
                "sources": source,
            })
    with markers.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["marker", "type", "weight", "notes", "sources"])
        for c in candidates:
            count = int(str(c.get("count", 0)))
            writer.writerow({"marker": c["term"], "type": "profile_candidate", "weight": 2 if count < 3 else 3, "notes": f"Mined candidate for {group}; review before use", "sources": source})


def _layer_depth(root: Path, parent_profile: str | None) -> int:
    if not parent_profile:
        return 0
    parent = root / slugify(parent_profile) / "manifest.json"
    if not parent.exists():
        return 1
    try:
        data = json.loads(parent.read_text(encoding="utf-8"))
        return int(data.get("layer_depth", 0)) + 1
    except Exception:
        return 1


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
