"""Shared JSON-friendly tool handlers for Localiser integrations.

Used by the Hermes plugin and the lightweight MCP server so both surfaces expose
one stable contract.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import DEFAULT_DB, Localiser
from .profiles import create_profile, mine_profile_from_sources, mine_profile_from_text


def _engine(db_path: str | None = None) -> Localiser:
    return Localiser(Path(db_path) if db_path else DEFAULT_DB)


def _regions(value: str | list[str] | None) -> list[str] | None:
    if value is None or value == "":
        return None
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _locales(value: str | list[str] | None) -> list[str] | None:
    return _regions(value)


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _error(exc: Exception) -> str:
    return json.dumps({"error": str(exc)}, ensure_ascii=False)


def localise_text(args: dict[str, Any], **_: Any) -> str:
    try:
        text = str(args.get("text", ""))
        region = str(args.get("region", "")).strip()
        if not text or not region:
            return _ok({"error": "Both text and region are required."})
        result = _engine(args.get("db_path")).localise(
            text,
            region=region,
            register=str(args.get("register", "neutral")),
            generation=str(args.get("generation", "neutral")),
            subregion=str(args.get("subregion", "national")),
            class_layer=str(args.get("class_layer", "neutral")),
            setting=str(args.get("setting", "neutral")),
            density=str(args.get("density", "light")),
            explain=bool(args.get("explain", True)),
            use_stanza=bool(args.get("use_stanza", False)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def detect_region(args: dict[str, Any], **_: Any) -> str:
    try:
        text = str(args.get("text", ""))
        if not text:
            return _ok({"error": "text is required."})
        result = _engine(args.get("db_path")).detect(
            text,
            regions=_regions(args.get("regions")),
            max_evidence=int(args.get("max_evidence", 12)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def detect_locale(args: dict[str, Any], **_: Any) -> str:
    try:
        text = str(args.get("text", ""))
        if not text:
            return _ok({"error": "text is required."})
        result = _engine(args.get("db_path")).detect_locale(
            text,
            region=str(args.get("region", "au")),
            locales=_locales(args.get("locales")),
            max_evidence=int(args.get("max_evidence", 12)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def cultural_context(args: dict[str, Any], **_: Any) -> str:
    try:
        region = str(args.get("region", "")).strip()
        if not region:
            return _ok({"error": "region is required."})
        result = _engine(args.get("db_path")).cultural_context(
            region,
            locales=_locales(args.get("locales")),
            generation=str(args.get("generation", "neutral")),
            max_rows=int(args.get("max_rows", 24)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def sports_context(args: dict[str, Any], **_: Any) -> str:
    try:
        region = str(args.get("region", "")).strip()
        if not region:
            return _ok({"error": "region is required."})
        result = _engine(args.get("db_path")).sports(
            region,
            locales=_locales(args.get("locales")),
            max_rows=int(args.get("max_rows", 24)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def named_entities(args: dict[str, Any], **_: Any) -> str:
    try:
        text = str(args.get("text", ""))
        if not text:
            return _ok({"error": "text is required."})
        result = _engine(args.get("db_path")).named_entities(
            text,
            lang=str(args.get("lang", "en")),
            package=args.get("package"),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def create_layered_profile(args: dict[str, Any], **_: Any) -> str:
    try:
        name = str(args.get("name", "")).strip()
        if not name:
            return _ok({"error": "name is required."})
        result = create_profile(
            name,
            parent_region=args.get("parent_region"),
            parent_profile=args.get("parent_profile"),
            root=args.get("profile_root", "profiles"),
            description=args.get("description"),
            overwrite=bool(args.get("overwrite", False)),
        )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


def mine_layered_profile(args: dict[str, Any], **_: Any) -> str:
    try:
        name = str(args.get("name", "")).strip()
        if not name:
            return _ok({"error": "name is required."})
        sources = _regions(args.get("sources")) or []
        if sources:
            result = mine_profile_from_sources(
                name,
                sources,
                parent_region=args.get("parent_region"),
                parent_profile=args.get("parent_profile"),
                root=args.get("profile_root", "profiles"),
                min_count=int(args.get("min_count", 2)),
                overwrite=bool(args.get("overwrite", False)),
            )
        else:
            text = str(args.get("text", ""))
            if not text:
                return _ok({"error": "text or sources is required."})
            result = mine_profile_from_text(
                name,
                text,
                parent_region=args.get("parent_region"),
                parent_profile=args.get("parent_profile"),
                root=args.get("profile_root", "profiles"),
                min_count=int(args.get("min_count", 2)),
                overwrite=bool(args.get("overwrite", False)),
                db_path=args.get("db_path"),
            )
        return _ok(result.as_dict())
    except Exception as exc:
        return _error(exc)


HANDLERS = {
    "localiser_localise_text": localise_text,
    "localiser_detect_region": detect_region,
    "localiser_detect_locale": detect_locale,
    "localiser_cultural_context": cultural_context,
    "localiser_sports_context": sports_context,
    "localiser_named_entities": named_entities,
    "localiser_create_layered_profile": create_layered_profile,
    "localiser_mine_layered_profile": mine_layered_profile,
}
