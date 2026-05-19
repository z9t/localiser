#!/usr/bin/env python3
"""CLI for deterministic local Regionaliser transforms, detection, and lexicon learning."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import DEFAULT_DB, Regionaliser


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="regionalise",
        description="Regionalise, detect, analyse, or learn English regional signals locally. No AI calls.",
    )
    p.add_argument("text", nargs="*", help="Text to process. If omitted, stdin is used.")
    p.add_argument("-r", "--region", help="Target region for regionalise mode.")
    p.add_argument("--detect", action="store_true", help="Detect likely source region instead of rewriting text.")
    p.add_argument("--detect-locale", action="store_true", help="Detect likely subnational/state/capital-city signals, currently strongest for AU.")
    p.add_argument("--ner", action="store_true", help="Extract named entities with optional Stanford Stanza NER.")
    p.add_argument("--analyse", "--analyze", action="store_true", help="Diff text against baseline English and known regional clues.")
    p.add_argument("--learn", metavar="NAME", help="Create a custom lexicon scaffold from non-baseline terms, e.g. 'Oka bogan'.")
    p.add_argument("--sports", action="store_true", help="Include/query locality sports context: top codes, teams, current players, historic players.")
    p.add_argument("--context", action="store_true", help="Include/query daily-life institutions and media/reference ecology for a region/locality.")
    p.add_argument("--culture", action="store_true", help="Include/query generational cultural quote/reference context for a country/locality.")
    p.add_argument("--learn-out", default="custom", help="Directory for --learn output. Default: custom/")
    p.add_argument("--min-count", type=int, default=1, help="Minimum token count for --learn candidates.")
    p.add_argument("--regions", default=None, help="Detect/analyse only: comma-separated candidate regions. Default: all DB manifests.")
    p.add_argument("--locale-region", default="au", help="Region code for --detect-locale. Default: au")
    p.add_argument("--ner-lang", default="en", help="Stanza language for --ner. Default: en")
    p.add_argument("--ner-package", default=None, help="Optional Stanza package/model name for --ner.")
    p.add_argument("--locales", default=None, help="Detect-locale/sports only: comma-separated candidate locale labels, e.g. NSW,Sydney,VIC,Melbourne")
    p.add_argument("--sports-max", type=int, default=24, help="Sports rows to return when --sports is used. Default: 24")
    p.add_argument("--context-max", type=int, default=24, help="Institution/media rows to return per dataset when --context is used. Default: 24")
    p.add_argument("--register", default="neutral", help="neutral, casual, conversational, social-business, formal, institutional")
    p.add_argument("--generation", default="neutral", help="neutral, gen-z, millennial, boomer, older")
    p.add_argument("--subregion", default="national", help="national or a data-backed subregion label")
    p.add_argument("--class", dest="class_layer", default="neutral", help="neutral, lower, middle, upper, or local sociolect label")
    p.add_argument("--setting", default="neutral", help="neutral, capital, suburban, regional-centre, rural, remote")
    p.add_argument("--density", default="light", choices=["none", "light", "medium", "high"], help="How much vernacular to introduce.")
    p.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB path. Default: core/data/regionaliser.sqlite")
    p.add_argument("-o", "--output", help="Write result/report to a file instead of stdout.")
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.add_argument("--explain", action="store_true", help="Include notes/changes; implied by --json, otherwise printed to stderr.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = " ".join(args.text).strip() if args.text else sys.stdin.read()
    if not text.strip() and not (args.sports or args.context or args.culture):
        print("No input text supplied. Pass text args or pipe stdin.", file=sys.stderr)
        return 2
    engine = Regionaliser(args.db)
    regions = [r.strip() for r in args.regions.split(",") if r.strip()] if args.regions else None
    locales = [r.strip() for r in args.locales.split(",") if r.strip()] if args.locales else None

    if (args.sports or args.context or args.culture) and not text.strip():
        if not args.region:
            print("--region is required for --sports/--context/--culture when no text is supplied.", file=sys.stderr)
            return 2
        payload = {}
        parts = []
        if args.sports:
            sports = engine.sports(args.region, locales=locales, max_rows=args.sports_max)
            payload["sports"] = sports.as_dict()
            parts.append(render_sports_text(sports))
        if args.context or args.culture:
            context = engine.cultural_context(args.region, locales=locales, generation=args.generation, max_rows=args.context_max)
            payload["context"] = context.as_dict()
            parts.append(render_context_text(context))
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "\n\n".join(parts)
        return emit(rendered, args.output)

    if args.learn:
        result = engine.learn_lexicon(args.learn, text, out_dir=args.learn_out, min_count=args.min_count)
        rendered = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) if args.json else render_learn_text(result)
        return emit(rendered, args.output)

    if args.analyse:
        result = engine.analyse(text, regions=regions)
        rendered = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) if args.json else render_analysis_text(result)
        return emit(rendered, args.output)

    if args.detect:
        result = engine.detect(text, regions=regions)
        rendered = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) if args.json else render_detection_text(result)
        return emit(rendered, args.output)

    if args.ner:
        try:
            result = engine.named_entities(text, lang=args.ner_lang, package=args.ner_package)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        rendered = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) if args.json else render_ner_text(result)
        return emit(rendered, args.output)

    if args.detect_locale:
        result = engine.detect_locale(text, region=args.locale_region, locales=locales)
        rendered = json.dumps(result.as_dict(), ensure_ascii=False, indent=2) if args.json else render_locale_detection_text(result)
        return emit(rendered, args.output)

    if not args.region:
        print("--region is required unless --detect, --detect-locale, --analyse, --ner, or --learn is used.", file=sys.stderr)
        return 2
    result = engine.regionalise(
        text,
        region=args.region,
        register=args.register,
        generation=args.generation,
        subregion=args.subregion,
        class_layer=args.class_layer,
        setting=args.setting,
        density=args.density,
        explain=args.explain or args.json,
    )
    sports = engine.sports(args.region, locales=locales, max_rows=args.sports_max) if args.sports else None
    context = engine.cultural_context(args.region, locales=locales, generation=args.generation, max_rows=args.context_max) if (args.context or args.culture) else None
    if args.json:
        payload = result.as_dict()
        if sports:
            payload["sports"] = sports.as_dict()
        if context:
            payload["context"] = context.as_dict()
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        rendered = result.text
        if sports:
            rendered = rendered + "\n\n" + render_sports_text(sports)
        if context:
            rendered = rendered + "\n\n" + render_context_text(context)
        if args.explain:
            print(json.dumps({"changes": result.changes, "notes": result.notes}, ensure_ascii=False, indent=2), file=sys.stderr)
    return emit(rendered, args.output)


def emit(rendered: str, output: str | None) -> int:
    if output:
        Path(output).write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        print(rendered)
    return 0


def render_detection_text(result) -> str:
    lines = [f"best={result.region or 'unknown'} confidence={result.confidence:.2f}"]
    for cand in result.candidates:
        bits = ", ".join(f"{e['marker']}({e['kind']} +{e['weight']})" for e in cand.evidence[:5]) or "no evidence"
        lines.append(f"{cand.region}: score={cand.score:.1f} evidence={bits}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_ner_text(result) -> str:
    lines = [f"ner lang={result.lang} entities={len(result.entities)}"]
    for ent in result.entities:
        span = ""
        if ent.get("start_char") is not None and ent.get("end_char") is not None:
            span = f" @{ent.get('start_char')}:{ent.get('end_char')}"
        lines.append(f"- {ent.get('text')} [{ent.get('type')}]{span}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_locale_detection_text(result) -> str:
    lines = [f"best_locale={result.locale or 'unknown'} confidence={result.confidence:.2f}"]
    for cand in result.candidates:
        bits = ", ".join(f"{e['marker']}({e['scope']} +{e['weight']})" for e in cand.evidence[:5]) or "no evidence"
        lines.append(f"{cand.locale}: score={cand.score:.1f} evidence={bits}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_sports_text(result) -> str:
    filters = f" locales={','.join(result.locales)}" if result.locales else ""
    lines = [f"sports region={result.region}{filters} rows={len(result.rows)}"]
    for row in result.rows:
        players = row.get("current_players", "")
        historic = row.get("notable_historic_players", "")
        lines.append(
            f"- {row.get('locale','')} #{row.get('rank','')}: {row.get('sport','')} / {row.get('code','')} — "
            f"{row.get('team','')} ({row.get('league','')}); current: {players}; historic: {historic}"
        )
        caution = row.get("caution", "")
        if caution:
            lines.append(f"  caution: {caution}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_context_text(result) -> str:
    filters = f" locales={','.join(result.locales)}" if result.locales else ""
    lines = [f"context region={result.region}{filters} institutions={len(result.institutions)} media={len(result.media)} cultural_quotes={len(result.cultural_quotes)}"]
    if result.institutions:
        lines.append("institutions:")
        for row in result.institutions:
            lines.append(f"- {row.get('locale','')}: {row.get('institution_or_term','')} ({row.get('domain','')}) — {row.get('typical_context','')}")
            if row.get("caution"):
                lines.append(f"  caution: {row.get('caution')}")
    if result.media:
        lines.append("media/reference ecology:")
        for row in result.media:
            lines.append(f"- {row.get('locale','')}: {row.get('reference','')} ({row.get('category','')}) — {row.get('typical_phrase','')}")
            if row.get("caution"):
                lines.append(f"  caution: {row.get('caution')}")
    if result.cultural_quotes:
        lines.append("cultural quote/reference bank:")
        for row in result.cultural_quotes:
            lines.append(f"- {row.get('locale','')} / {row.get('generation','')}: {row.get('reference','')} ({row.get('reference_type','')}) — {row.get('quote_fragments','')}")
            if row.get("caution"):
                lines.append(f"  caution: {row.get('caution')}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_analysis_text(result) -> str:
    lines = [f"baseline_words={result.baseline_words}"]
    lines.append(render_detection_text(result.known_evidence))
    lines.append("non_baseline:")
    for item in result.non_baseline[:40]:
        extra = f" regions={','.join(item.get('known_regions', []))}" if item.get("known_regions") else ""
        lines.append(f"- {item['term']} x{item['count']} {item['reason']}{extra}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


def render_learn_text(result) -> str:
    lines = [f"learned={result.name} slug={result.slug}"]
    if result.lexicon_path:
        lines.append(f"lexicon={result.lexicon_path}")
    if result.markers_path:
        lines.append(f"markers={result.markers_path}")
    lines.append(f"candidates={len(result.candidates)}")
    for c in result.candidates[:40]:
        lines.append(f"- {c['term']} x{c['count']} {c.get('reason', '')}")
    lines.extend(f"note: {n}" for n in result.notes)
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
