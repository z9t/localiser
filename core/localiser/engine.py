"""Deterministic local text localisation and region detection engine.

The engine is intentionally conservative: it uses the Localiser CSV data via a
SQLite database, applies spelling/vocabulary substitutions, and can score region
of origin from text clues. It does not call an AI model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
import sqlite3
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "core/data/localiser.sqlite"
REGION_CODES = {"au", "us", "uk", "ca"}


@dataclass
class LocaliseOptions:
    region: str
    register: str = "neutral"
    generation: str = "neutral"
    subregion: str = "national"
    class_layer: str = "neutral"
    setting: str = "neutral"
    density: str = "light"
    explain: bool = False
    use_stanza: bool = False
    protected_spans: list[tuple[int, int]] = field(default_factory=list)
    db_path: Path = DEFAULT_DB


@dataclass
class LocaliseResult:
    text: str
    region: str
    changes: list[dict[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"text": self.text, "region": self.region, "changes": self.changes, "notes": self.notes}


@dataclass
class DetectionCandidate:
    region: str
    score: float
    evidence: list[dict[str, object]] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"region": self.region, "score": round(self.score, 3), "evidence": self.evidence}


@dataclass
class DetectionResult:
    region: str | None
    confidence: float
    candidates: list[DetectionCandidate]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "region": self.region,
            "confidence": round(self.confidence, 3),
            "candidates": [c.as_dict() for c in self.candidates],
            "notes": self.notes,
        }


@dataclass
class LocaleCandidate:
    locale: str
    score: float
    evidence: list[dict[str, object]] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"locale": self.locale, "score": round(self.score, 3), "evidence": self.evidence}


@dataclass
class LocaleDetectionResult:
    locale: str | None
    confidence: float
    candidates: list[LocaleCandidate]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "locale": self.locale,
            "confidence": round(self.confidence, 3),
            "candidates": [c.as_dict() for c in self.candidates],
            "notes": self.notes,
        }


@dataclass
class SportsLocalityResult:
    region: str
    locales: list[str]
    rows: list[dict[str, object]]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {"region": self.region, "locales": self.locales, "sports": self.rows, "notes": self.notes}


@dataclass
class CulturalContextResult:
    region: str
    locales: list[str]
    institutions: list[dict[str, object]] = field(default_factory=list)
    media: list[dict[str, object]] = field(default_factory=list)
    cultural_quotes: list[dict[str, object]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "region": self.region,
            "locales": self.locales,
            "institutions": self.institutions,
            "media": self.media,
            "cultural_quotes": self.cultural_quotes,
            "notes": self.notes,
        }


@dataclass
class AnalyseResult:
    text: str
    tokens: list[str]
    non_baseline: list[dict[str, object]]
    known_evidence: DetectionResult
    baseline_words: int
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "tokens": self.tokens,
            "non_baseline": self.non_baseline,
            "known_evidence": self.known_evidence.as_dict(),
            "baseline_words": self.baseline_words,
            "notes": self.notes,
        }


@dataclass
class NamedEntityResult:
    text: str
    lang: str
    entities: list[dict[str, object]]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "lang": self.lang,
            "entities": self.entities,
            "notes": self.notes,
        }


@dataclass
class LearnedLexiconResult:
    name: str
    slug: str
    lexicon_path: str | None
    markers_path: str | None
    candidates: list[dict[str, object]]
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "slug": self.slug,
            "lexicon_path": self.lexicon_path,
            "markers_path": self.markers_path,
            "candidates": self.candidates,
            "notes": self.notes,
        }


class Localiser:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Localiser DB not found: {self.db_path}. Run: python3 core/scripts/build_db.py"
            )

    def localise(self, text: str, **kwargs) -> LocaliseResult:
        opts = LocaliseOptions(db_path=self.db_path, **kwargs)
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            available = self._region_codes(con)
            if opts.region not in available:
                raise ValueError(f"Unsupported region {opts.region!r}; expected one of {sorted(available)}")
            out = text
            changes: list[dict[str, str]] = []
            stanza_notes: list[str] = []
            if opts.use_stanza:
                opts.protected_spans, stanza_notes = self._stanza_protected_spans(text)
            out = self._apply_vocabulary(con, out, opts, changes)
            out = self._apply_spelling(con, out, opts, changes)
            out = self._apply_register(con, out, opts, changes)
            out = self._apply_light_lexicon(con, out, opts, changes)
            notes = self._notes(con, opts) + stanza_notes
            return LocaliseResult(text=out, region=opts.region, changes=changes, notes=notes)

    def detect(self, text: str, regions: Iterable[str] | None = None, max_evidence: int = 12) -> DetectionResult:
        """Score likely source region from local clues in text.

        This is evidence scoring, not authorship truth. It looks for data-backed
        spellings, vocabulary, lexicon terms, cultural references, and explicit
        geographic/institutional markers. Short generic text should return low
        confidence rather than guessing hard.
        """
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            available = self._region_codes(con)
            wanted = list(regions or sorted(available))
            unknown = [r for r in wanted if r not in available]
            if unknown:
                raise ValueError(f"Unsupported regions {unknown!r}; expected subset of {sorted(available)}")
            candidates: list[DetectionCandidate] = []
            for region in wanted:
                evidence = self._detect_region_evidence(con, text, region)
                evidence.sort(key=lambda e: (-float(str(e["weight"])), str(e["marker"]).lower()))
                score = sum(float(str(e["weight"])) for e in evidence)
                candidates.append(DetectionCandidate(region=region, score=score, evidence=evidence[:max_evidence]))
            candidates.sort(key=lambda c: c.score, reverse=True)
            top = candidates[0] if candidates else None
            second = candidates[1] if len(candidates) > 1 else DetectionCandidate(region="", score=0)
            confidence = confidence_from_scores(top.score if top else 0, second.score if second else 0)
            region = top.region if top and top.score > 0 and confidence >= 0.28 else None
            notes = [
                "Local deterministic detect mode: no AI/model calls; evidence comes from Localiser CSV/SQLite data.",
                "Detection is probabilistic clue scoring, not proof of author nationality or location.",
            ]
            if region is None:
                notes.append("No region cleared the confidence threshold; text may be generic, mixed, or too short.")
            return DetectionResult(region=region, confidence=confidence, candidates=candidates, notes=notes)

    def detect_locale(self, text: str, region: str = "au", locales: Iterable[str] | None = None, max_evidence: int = 12) -> LocaleDetectionResult:
        """Score likely subnational/local textual signals for a region.

        For AU this uses `locale_markers.csv` to score state/capital-city clues
        such as Opal/myki/parma/parmi. This is concept/context clue scoring, not
        a claim about where a writer lives.
        """
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            available = self._region_codes(con)
            if region not in available:
                raise ValueError(f"Unsupported region {region!r}; expected one of {sorted(available)}")
            wanted = {l.strip().lower() for l in locales or [] if l.strip()} if locales else None
            scores: dict[str, float] = {}
            evidence_by_locale: dict[str, list[dict[str, object]]] = {}
            seen: set[tuple[str, str]] = set()
            for raw in self._rows(con, "locale_markers", region):
                row = json.loads(raw["data"])
                marker = clean_term(row.get("marker", ""))
                if not marker or not contains_term(text, marker):
                    continue
                weight = float(row.get("weight") or 2)
                for locale_name in split_locale_list(row.get("locales", "")):
                    if wanted and locale_name.lower() not in wanted:
                        continue
                    key = (locale_name.lower(), marker.lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    scores[locale_name] = scores.get(locale_name, 0.0) + weight
                    evidence_by_locale.setdefault(locale_name, []).append({
                        "marker": marker,
                        "scope": row.get("scope", "locale_marker"),
                        "weight": weight,
                        "meaning": row.get("meaning", ""),
                        "note": row.get("notes", ""),
                        "caution": row.get("caution", ""),
                    })
            candidates = [
                LocaleCandidate(
                    locale=locale_name,
                    score=score,
                    evidence=sorted(
                        evidence_by_locale.get(locale_name, []),
                        key=lambda e: (-float(str(e["weight"])), str(e["marker"]).lower()),
                    )[:max_evidence],
                )
                for locale_name, score in scores.items()
            ]
            candidates.sort(key=lambda c: c.score, reverse=True)
            top = candidates[0] if candidates else None
            second = candidates[1] if len(candidates) > 1 else LocaleCandidate(locale="", score=0)
            confidence = confidence_from_scores(top.score if top else 0, second.score if second else 0)
            locale = top.locale if top and top.score > 0 and confidence >= 0.28 else None
            notes = [
                f"Local deterministic locale detect mode for {region}: no AI/model calls; evidence comes from locale_markers.csv.",
                "Locale detection scores textual signals (transport cards, food terms, sport-code references), not identity or residence.",
                "Shared terms can point to multiple states/cities; combine several independent clues before trusting a result.",
            ]
            if locale is None:
                notes.append("No locale cleared the confidence threshold; evidence may be generic, mixed, or outside the installed locale marker data.")
            return LocaleDetectionResult(locale=locale, confidence=confidence, candidates=candidates, notes=notes)

    def named_entities(self, text: str, lang: str = "en", package: str | None = None, processors: str = "tokenize,ner") -> NamedEntityResult:
        """Extract named entities with optional Stanford Stanza NER.

        Stanza is intentionally optional so Localiser stays dependency-light.
        Install it with `pip install localiser[ner]` or `pip install stanza`,
        then download models via `python3 core/scripts/install_stanza_models.py --lang en`.
        """
        try:
            import stanza  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Stanza is not installed. Install optional NER support with: "
                "python3 -m pip install '.[ner]' && python3 core/scripts/install_stanza_models.py --lang en"
            ) from exc

        pipeline_kwargs: dict[str, object] = {
            "lang": lang,
            "processors": processors,
            "use_gpu": False,
            "verbose": False,
        }
        if package:
            pipeline_kwargs["package"] = package
        try:
            nlp = stanza.Pipeline(**pipeline_kwargs)
            doc = nlp(text)
        except Exception as exc:  # model missing, incompatible package, etc.
            raise RuntimeError(
                f"Stanza NER failed for lang={lang!r}. Try: "
                f"python3 core/scripts/install_stanza_models.py --lang {lang}"
            ) from exc

        entities = []
        for ent in getattr(doc, "ents", []):
            entities.append({
                "text": ent.text,
                "type": ent.type,
                "start_char": getattr(ent, "start_char", None),
                "end_char": getattr(ent, "end_char", None),
            })
        notes = [
            "Named entities are extraction candidates, not identity/location proof.",
            "Use NER to separate names, places, organisations, and brands from regional vocabulary before detection/lexicon learning.",
        ]
        return NamedEntityResult(text=text, lang=lang, entities=entities, notes=notes)

    def analyse(self, text: str, regions: Iterable[str] | None = None, max_terms: int = 80, use_stanza: bool = False) -> AnalyseResult:
        """Diff text against baseline English and known regional evidence."""
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            baseline = self._baseline_words(con)
            tokens = tokenize_words(text)
            counts: dict[str, int] = {}
            first_forms: dict[str, str] = {}
            protected_terms: set[str] = set()
            stanza_notes: list[str] = []
            if use_stanza:
                protected_spans, stanza_notes = self._stanza_protected_spans(text)
                for start, end in protected_spans:
                    protected_terms.update(t.lower().replace("’", "'") for t in tokenize_words(text[start:end]))
            for token in tokens:
                key = token.lower().replace("’", "'")
                counts[key] = counts.get(key, 0) + 1
                first_forms.setdefault(key, token)
            non_baseline = []
            known_terms = self._known_terms(con)
            for word, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                if word in protected_terms:
                    continue
                if word in baseline:
                    continue
                if len(word) < 2 or word.isdigit():
                    continue
                entry = {"term": first_forms[word], "count": count, "reason": "not_in_baseline"}
                if word in known_terms:
                    entry["known_regions"] = sorted(known_terms[word])
                    entry["reason"] = "known_regional_or_custom_term"
                non_baseline.append(entry)
                if len(non_baseline) >= max_terms:
                    break
            evidence = self.detect(text, regions=regions)
            notes = [
                "Baseline diff flags terms absent from the installed broad English wordlist; this includes names, typos, domain terms, slang, transcription artefacts, and localisms.",
                "Use repeated non-baseline terms plus detect evidence as lexicon candidates; do not assume every flagged word is regional.",
            ] + stanza_notes
            return AnalyseResult(text=text, tokens=tokens, non_baseline=non_baseline, known_evidence=evidence, baseline_words=len(baseline), notes=notes)

    def sports(self, region: str, locales: Iterable[str] | None = None, max_rows: int = 24) -> SportsLocalityResult:
        """Return reviewable sports/cultural rows for a country or locality.

        Sports data is a cultural context aid, not a detector of identity,
        residence, politics, class, religion, or ethnicity.
        """
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            available = self._region_codes(con)
            if region not in available:
                raise ValueError(f"Unsupported region {region!r}; expected one of {sorted(available)}")
            wanted = [clean_term(l) for l in locales or [] if clean_term(l)]
            wanted_lower = [l.lower() for l in wanted]
            rows: list[dict[str, object]] = []
            for raw in self._rows(con, "sports_locality", region):
                row = json.loads(raw["data"])
                locale = clean_term(row.get("locale", ""))
                if wanted_lower and not any(locale_matches(locale, w) for w in wanted_lower):
                    continue
                try:
                    row["rank"] = int(row.get("rank") or 0)
                except (TypeError, ValueError):
                    row["rank"] = 0
                rows.append(row)
            rows.sort(key=lambda r: (str(r.get("locale", "")).lower(), int(str(r.get("rank") or 0)), str(r.get("team", "")).lower()))
            notes = [
                "Sports rows are cultural/locality context only; they are weak evidence and never identity or residence proof.",
                "Current-player fields are reviewable seed data and should be refreshed from official rosters before high-stakes/current use.",
                "Local loyalties can be club-, suburb-, family-, class-, school-, or migration-shaped; avoid assuming allegiance from geography.",
            ]
            if not rows:
                notes.append("No sports rows matched the requested region/locality filters.")
            return SportsLocalityResult(region=region, locales=wanted, rows=rows[:max_rows], notes=notes)

    def cultural_context(self, region: str, locales: Iterable[str] | None = None, generation: str = "neutral", max_rows: int = 24) -> CulturalContextResult:
        """Return daily-life institutional, media/reference, and cultural-quote context rows."""
        with sqlite3.connect(self.db_path) as con:
            con.row_factory = sqlite3.Row
            available = self._region_codes(con)
            if region not in available:
                raise ValueError(f"Unsupported region {region!r}; expected one of {sorted(available)}")
            wanted = [clean_term(l) for l in locales or [] if clean_term(l)]
            institutions = self._context_rows(con, region, "institutional_context", wanted, max_rows)
            media = self._context_rows(con, region, "media_reference_ecology", wanted, max_rows)
            cultural_quotes = self._cultural_quote_rows(con, region, wanted, generation, max_rows)
            notes = [
                "Cultural context rows are a map of daily systems, reference ecology, and quote fragments, not proof of identity or residence.",
                "Institutional/service clues are often stronger than slang because they reflect systems people actually navigate.",
                "Media/reference and quote clues are audience-, generation-, taste-, and topic-shaped; use sparingly and avoid fake-local name-dropping.",
                "Quote fragments are short reference handles, not permission to reproduce long copyrighted passages.",
            ]
            if not institutions and not media and not cultural_quotes:
                notes.append("No context rows matched the requested region/locality/generation filters.")
            return CulturalContextResult(region=region, locales=wanted, institutions=institutions, media=media, cultural_quotes=cultural_quotes, notes=notes)

    def learn_lexicon(self, name: str, text: str, out_dir: str | Path | None = None, min_count: int = 1) -> LearnedLexiconResult:
        """Extract non-baseline candidates into a reusable custom lexicon scaffold."""
        slug = slugify(name)
        analysed = self.analyse(text, max_terms=200)
        candidates = [c for c in analysed.non_baseline if int(c.get("count", 0)) >= min_count]
        notes = [
            "Generated from baseline diff; review before treating as authentic regional vocabulary.",
            "For phrases and meanings, add human notes/examples; single-token extraction is only a first pass.",
        ]
        if out_dir is None:
            return LearnedLexiconResult(name=name, slug=slug, lexicon_path=None, markers_path=None, candidates=candidates, notes=notes)
        root = Path(out_dir) / slug
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "display_name": f"{name} Custom Lexicon",
            "description": f"Custom learned lexicon scaffold for {name}.",
            "overview": "Generated from baseline diff of supplied examples; review before use.",
            "region_code": slug,
            "skill_name": f"{slug}-english",
        }
        (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lexicon_path = data_dir / "lexicon.csv"
        markers_path = data_dir / "detection_markers.csv"
        import csv
        with lexicon_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["term","category","register","region_or_group","meaning","usage_notes","avoid_when","source_count"])
            writer.writeheader()
            for c in candidates:
                writer.writerow({
                    "term": c["term"], "category": "candidate", "register": "unknown", "region_or_group": name,
                    "meaning": "TODO", "usage_notes": "Extracted because absent from baseline English wordlist", "avoid_when": "unreviewed", "source_count": c["count"],
                })
        with markers_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["marker","type","weight","notes"])
            writer.writeheader()
            for c in candidates:
                weight = 2 if int(c.get("count", 0)) == 1 else 3
                writer.writerow({"marker": c["term"], "type": "learned_lexicon", "weight": weight, "notes": f"Learned candidate for {name}; review before use"})
        (root / "examples.txt").write_text(text, encoding="utf-8")
        return LearnedLexiconResult(name=name, slug=slug, lexicon_path=str(lexicon_path), markers_path=str(markers_path), candidates=candidates, notes=notes)

    def _region_codes(self, con: sqlite3.Connection) -> set[str]:
        return {str(r["region"]) for r in con.execute("select region from manifests")}

    def _baseline_words(self, con: sqlite3.Connection) -> set[str]:
        return {str(r["word"]) for r in con.execute("select word from baseline_words")}

    def _known_terms(self, con: sqlite3.Connection) -> dict[str, set[str]]:
        terms: dict[str, set[str]] = {}
        for row in con.execute("select region, dataset, data from entries"):
            region = str(row["region"])
            dataset = str(row["dataset"])
            data = json.loads(row["data"])
            fields = []
            if dataset in {"lexicon", "false_friends"}:
                fields.append(data.get("term", ""))
            elif dataset == "vocabulary":
                fields.append(data.get("local", ""))
            elif dataset == "detection_markers":
                fields.append(data.get("marker", ""))
            elif dataset == "cultural_references":
                fields.append(data.get("reference", ""))
            elif dataset == "cultural_quote_references":
                fields.append(data.get("reference", ""))
                fields.extend(split_quote_fragments(data.get("quote_fragments", "")))
            for field in fields:
                key = clean_term(str(field)).lower()
                if key:
                    terms.setdefault(key, set()).add(region)
        return terms

    def _rows(self, con: sqlite3.Connection, dataset: str, region: str) -> list[sqlite3.Row]:
        return list(con.execute("select data from entries where region=? and dataset=?", (region, dataset)))

    def _stanza_protected_spans(self, text: str) -> tuple[list[tuple[int, int]], list[str]]:
        """Return named-entity spans to protect when optional Stanza is enabled.

        This is a preference-driven enhancement for the full localiser skill. If
        Stanza or its models are unavailable, the caller still gets deterministic
        output plus an explanatory note.
        """
        try:
            result = self.named_entities(text)
        except RuntimeError as exc:
            return [], [f"Stanza protection requested but unavailable: {exc}"]
        spans: list[tuple[int, int]] = []
        for ent in result.entities:
            start = ent.get("start_char")
            end = ent.get("end_char")
            if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
                spans.append((start, end))
        if spans:
            return spans, [f"Stanza protection enabled: protected {len(spans)} named-entity span(s) from rewrite/diff false positives."]
        return [], ["Stanza protection enabled: no named-entity spans found."]

    def _context_rows(self, con: sqlite3.Connection, region: str, dataset: str, locales: list[str], max_rows: int) -> list[dict[str, object]]:
        wanted_lower = [l.lower() for l in locales]
        rows: list[dict[str, object]] = []
        for raw in self._rows(con, dataset, region):
            row = json.loads(raw["data"])
            locale = clean_term(row.get("locale", ""))
            if wanted_lower and not any(locale_matches(locale, w) for w in wanted_lower):
                continue
            rows.append(row)
        rows.sort(key=lambda r: (str(r.get("locale", "")).lower(), str(r.get("domain", r.get("category", ""))).lower(), str(r.get("institution_or_term", r.get("reference", ""))).lower()))
        return rows[:max_rows]

    def _cultural_quote_rows(self, con: sqlite3.Connection, region: str, locales: list[str], generation: str, max_rows: int) -> list[dict[str, object]]:
        wanted_lower = [l.lower() for l in locales]
        generation = clean_term(generation or "neutral").lower()
        rows: list[dict[str, object]] = []
        for raw in self._rows(con, "cultural_quote_references", region):
            row = json.loads(raw["data"])
            locale = clean_term(row.get("locale", ""))
            if wanted_lower and not (any(locale_matches(locale, w) for w in wanted_lower) or locale.lower() in national_locale_names(region)):
                continue
            row_generation = clean_term(row.get("generation", "")).lower()
            if generation not in {"", "neutral", "all", "all-age"} and row_generation not in {generation, "all-age", "all"}:
                continue
            rows.append(row)
        order = {"all-age": 0, "older": 1, "gen-x": 2, "millennial": 3, "gen-z": 4}
        rows.sort(key=lambda r: (order.get(str(r.get("generation", "")).lower(), 9), str(r.get("reference", "")).lower()))
        return rows[:max_rows]

    def _apply_vocabulary(self, con, text: str, opts: LocaliseOptions, changes):
        rows = self._rows(con, "vocabulary", opts.region)
        pairs: list[tuple[str, str, str]] = []
        for row in rows:
            data = json.loads(row["data"])
            local = clean_term(data.get("local", ""))
            if not local:
                continue
            for key, value in data.items():
                if key.lower() in {"local", "notes"}:
                    continue
                for source in split_terms(value):
                    if source and source.lower() != local.lower():
                        pairs.append((source, local, "vocabulary"))
        return replace_pairs(text, pairs, changes, protected_spans=opts.protected_spans)

    def _apply_spelling(self, con, text: str, opts: LocaliseOptions, changes):
        pairs: list[tuple[str, str, str]] = []
        for row in self._rows(con, "spelling", opts.region):
            data = json.loads(row["data"])
            guarded = apply_contextual_spelling_rule(text, data, changes, protected_spans=opts.protected_spans)
            if guarded is not None:
                text = guarded
                continue
            uses = split_terms(data.get("use", ""))
            avoids = split_terms(data.get("avoid", ""))
            if len(uses) == len(avoids):
                pairs.extend((avoid, use, "spelling") for use, avoid in zip(uses, avoids))
            elif uses and avoids:
                pairs.extend((avoid, uses[0], "spelling") for avoid in avoids)
        return replace_pairs(text, pairs, changes, protected_spans=opts.protected_spans)

    def _apply_register(self, con, text: str, opts: LocaliseOptions, changes):
        register = opts.register.lower()
        if register in {"neutral", "none"}:
            return text
        # These are safe, broad, reversible register edits; not slang stuffing.
        formal_pairs = [("get", "receive"), ("help", "assist"), ("buy", "purchase"), ("kids", "children")]
        casual_pairs = [("children", "kids"), ("purchase", "buy"), ("receive", "get")]
        if register in {"formal", "institutional"}:
            return replace_pairs(text, [(a, b, "register") for a, b in formal_pairs], changes, protected_spans=opts.protected_spans)
        if register in {"casual", "conversational"}:
            return replace_pairs(text, [(a, b, "register") for a, b in casual_pairs], changes, protected_spans=opts.protected_spans)
        return text

    def _apply_light_lexicon(self, con, text: str, opts: LocaliseOptions, changes):
        if opts.density == "none" or opts.register in {"formal", "institutional"}:
            return text
        rows = [json.loads(r["data"]) for r in self._rows(con, "lexicon", opts.region)]
        wanted = []
        for row in rows:
            reg = (row.get("register") or "").lower()
            area = (row.get("region_or_group") or "").lower()
            avoid = (row.get("avoid_when") or "").lower()
            if "formal" in avoid and opts.register in {"formal", "institutional"}:
                continue
            if opts.register not in {"neutral", "casual", "conversational"} and "casual" in reg:
                continue
            if opts.subregion != "national" and area not in {"national", opts.subregion.lower()}:
                continue
            meaning = row.get("meaning", "")
            term = row.get("term", "")
            if meaning and term:
                wanted.append((meaning, term, "lexicon"))
        # Keep lexicon additions restrained: first applicable change for light, three for medium/high.
        limit = {"light": 1, "medium": 3, "high": 5}.get(opts.density, 1)
        before_count = len(changes)
        out = text
        for src, dst, kind in wanted:
            if len(changes) - before_count >= limit:
                break
            out = replace_pairs(out, [(src, dst, kind)], changes, max_replacements=1, protected_spans=opts.protected_spans)
        return out

    def _detect_region_evidence(self, con, text: str, region: str) -> list[dict[str, object]]:
        evidence: list[dict[str, object]] = []
        seen: set[tuple[str, str]] = set()

        def add(marker: str, kind: str, weight: float, source: str, note: str = ""):
            marker = clean_term(marker)
            if not marker or len(marker) < 2:
                return
            key = (kind, marker.lower())
            if key in seen:
                return
            if contains_term(text, marker):
                seen.add(key)
                evidence.append({"marker": marker, "kind": kind, "weight": weight, "source": source, "note": note})

        for row in self._rows(con, "detection_markers", region):
            data = json.loads(row["data"])
            add(data.get("marker", ""), data.get("type", "marker"), float(data.get("weight") or 2), "detection_markers", data.get("notes", ""))

        for row in self._rows(con, "lexicon", region):
            data = json.loads(row["data"])
            reg = (data.get("register") or "").lower()
            weight = 3.0 if any(x in reg for x in ["casual", "common", "media"]) else 2.0
            add(data.get("term", ""), "lexicon", weight, "lexicon", data.get("meaning", ""))

        for row in self._rows(con, "vocabulary", region):
            data = json.loads(row["data"])
            local = data.get("local", "")
            add(local, "vocabulary", 2.0, "vocabulary", data.get("notes", ""))

        for row in self._rows(con, "spelling", region):
            data = json.loads(row["data"])
            for term in split_terms(data.get("use", "")):
                # Spelling conventions are useful but weak; many are shared across Commonwealth regions.
                add(term, "spelling", 1.0, "spelling", data.get("notes", ""))

        for row in self._rows(con, "false_friends", region):
            data = json.loads(row["data"])
            add(data.get("term", ""), "false_friend", 1.5, "false_friends", data.get("trap", ""))

        for row in self._rows(con, "cultural_references", region):
            data = json.loads(row["data"])
            add(data.get("reference", ""), "cultural_reference", 2.5, "cultural_references", data.get("caution", ""))

        for row in self._rows(con, "cultural_quote_references", region):
            data = json.loads(row["data"])
            add(data.get("reference", ""), "cultural_quote_reference", 2.0, "cultural_quote_references", data.get("caution", ""))
            for fragment in split_quote_fragments(data.get("quote_fragments", "")):
                add(fragment, "quote_fragment", 2.5, "cultural_quote_references", data.get("reference", ""))

        return evidence

    def _notes(self, con, opts: LocaliseOptions) -> list[str]:
        notes = ["Local deterministic mode: no AI/model calls; CSV data loaded from SQLite."]
        if opts.class_layer != "neutral":
            notes.append("Class/sociolect options are intentionally conservative; no caricature markers are inserted automatically.")
        if opts.setting != "neutral":
            notes.append(f"Setting requested: {opts.setting}; use generated skill references for deeper judgement-heavy edits.")
        return notes


def localise(text: str, region: str, **kwargs) -> str:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).localise(text, region=region, **kwargs).text


def detect_region(text: str, **kwargs) -> DetectionResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).detect(text, **kwargs)


def extract_named_entities(text: str, **kwargs) -> NamedEntityResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).named_entities(text, **kwargs)


def detect_locale(text: str, **kwargs) -> LocaleDetectionResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).detect_locale(text, **kwargs)


def sports_context(region: str, **kwargs) -> SportsLocalityResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).sports(region=region, **kwargs)


def cultural_context(region: str, **kwargs) -> CulturalContextResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).cultural_context(region=region, **kwargs)


def analyse_text(text: str, **kwargs) -> AnalyseResult:
    return Localiser(kwargs.pop("db_path", DEFAULT_DB)).analyse(text, **kwargs)


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", text)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "custom"


def split_terms(value: str) -> list[str]:
    value = str(value or "").strip()
    if not value:
        return []
    # Remove explanatory clauses that are not replacement tokens.
    value = re.sub(r"\bfor\b.*$", "", value, flags=re.I).strip(" ;,")
    parts = re.split(r"\s*/\s*|\s*;\s*|\s*,\s*", value)
    return [clean_term(p) for p in parts if clean_term(p)]


def split_locale_list(value: str) -> list[str]:
    value = str(value or "").strip()
    if not value:
        return []
    parts = re.split(r"\s*;\s*|\s*,\s*", value)
    return [clean_term(p) for p in parts if clean_term(p)]


def split_quote_fragments(value: str) -> list[str]:
    value = str(value or "").strip()
    if not value:
        return []
    parts = re.split(r"\s*\|\s*|\s*;\s*", value)
    return [clean_term(p) for p in parts if clean_term(p)]


def national_locale_names(region: str) -> set[str]:
    return {
        "au": {"australia"},
        "us": {"united states", "usa", "us"},
        "uk": {"united kingdom", "uk", "britain", "great britain"},
        "ca": {"canada"},
    }.get(region, {region.lower()})


def locale_matches(locale: str, wanted_lower: str) -> bool:
    locale_lower = locale.lower()
    parts = [p.strip() for p in re.split(r"\s*/\s*|\s*;\s*|\s*,\s*", locale_lower) if p.strip()]
    return wanted_lower == locale_lower or wanted_lower in parts or wanted_lower in locale_lower


def clean_term(value: str) -> str:
    return str(value or "").strip().strip('"“”')


def replace_pairs(
    text: str,
    pairs: Iterable[tuple[str, str, str]],
    changes: list[dict[str, str]],
    max_replacements: int | None = None,
    protected_spans: list[tuple[int, int]] | None = None,
) -> str:
    out = text
    made = 0
    # Longest first avoids replacing "gas" before "gas station".
    for source, target, kind in sorted(pairs, key=lambda p: len(p[0]), reverse=True):
        source = clean_term(source)
        target = clean_term(target)
        if not source or not target or source.lower() == target.lower():
            continue
        pattern = re.compile(r"(?<![\w’'-])" + re.escape(source) + r"(?![\w’'-])", re.IGNORECASE)
        def repl(match):
            nonlocal made
            if max_replacements is not None and made >= max_replacements:
                return match.group(0)
            if span_overlaps(match.start(), match.end(), protected_spans or []):
                return match.group(0)
            made += 1
            replacement = preserve_case(match.group(0), target)
            changes.append({"kind": kind, "from": match.group(0), "to": replacement})
            return replacement
        out = pattern.sub(repl, out)
        if max_replacements is not None and made >= max_replacements:
            break
    return out


def contains_term(text: str, term: str) -> bool:
    term = clean_term(term)
    if not term:
        return False
    pattern = re.compile(r"(?<![\w’'-])" + re.escape(term) + r"(?![\w’'-])", re.IGNORECASE)
    return bool(pattern.search(text))


def apply_contextual_spelling_rule(
    text: str,
    data: dict[str, object],
    changes: list[dict[str, str]],
    protected_spans: list[tuple[int, int]] | None = None,
) -> str | None:
    """Apply guarded spelling rules for forms that need syntax/meaning.

    Some Commonwealth spellings are not simple US<->AU/UK replacements:
    practice/practise and licence/license depend on noun vs verb, while
    cheque/check depends on banking sense. A broad word replacement creates
    legal false positives such as "practice areas" -> "practise areas" and
    "check defences" -> "cheque defences". The safe default is to skip
    uncertain cases rather than guessing.
    """
    use_raw = clean_term(str(data.get("use", ""))).lower()
    avoid_raw = clean_term(str(data.get("avoid", ""))).lower()
    notes = clean_term(str(data.get("notes", ""))).lower()

    if "practise verb/practice noun" in use_raw and "practice" in avoid_raw:
        return replace_contextual_word(
            text,
            "practice",
            "practise",
            "spelling_contextual",
            changes,
            allow_next=VERB_PRACTICE_NEXT,
            block_next=NOUN_PRACTICE_NEXT,
            note="AU/UK noun/verb split: changed only high-confidence verb use; noun uses such as practice areas stay practice.",
            protected_spans=protected_spans,
        )

    if "licence noun/license verb" in use_raw and "license" in avoid_raw:
        return replace_contextual_word(
            text,
            "license",
            "licence",
            "spelling_contextual",
            changes,
            allow_next=NOUN_LICENSE_NEXT,
            block_next=VERB_LICENSE_NEXT,
            allow_boundary=True,
            note="AU/UK noun/verb split: changed only high-confidence noun use; verb uses stay license.",
            protected_spans=protected_spans,
        )

    if ("cheque" in use_raw and "check" in avoid_raw) and ("bank" in notes or "bank" in use_raw or "bank" in avoid_raw):
        return replace_contextual_word(
            text,
            "check",
            "cheque",
            "spelling_contextual",
            changes,
            allow_prev=BANK_CHEQUE_PREV,
            allow_next=BANK_CHEQUE_NEXT,
            block_next=VERIFY_CHECK_NEXT,
            note="AU/UK/CA cheque/check split: changed only banking-instrument contexts; verify/check uses stay check.",
            protected_spans=protected_spans,
        )

    return None


NOUN_PRACTICE_NEXT = {
    "area", "areas", "group", "groups", "manager", "management", "note", "notes",
    "direction", "directions", "owner", "owners", "leader", "leaders", "team", "teams",
    "guide", "guides", "manual", "manuals", "standard", "standards", "certificate",
    "certificates", "exam", "exams", "policy", "policies", "website", "websites",
}
VERB_PRACTICE_NEXT = {"law", "medicine", "midwifery", "nursing", "dentistry", "psychology", "as", "in"}
NOUN_LICENSE_NEXT = {
    "agreement", "agreements", "fee", "fees", "holder", "holders", "number", "numbers",
    "plate", "plates", "renewal", "renewals", "terms", "key", "keys", "file", "files",
}
VERB_LICENSE_NEXT = {"to", "for", "under", "as"}
BANK_CHEQUE_PREV = {"bank", "blank", "cashier", "cashier's", "personal", "certified", "pay", "paid", "paper"}
BANK_CHEQUE_NEXT = {"book", "books", "account", "accounts", "deposit", "deposits", "payment", "payments"}
VERIFY_CHECK_NEXT = {
    "defence", "defences", "defense", "defenses", "whether", "if", "that", "this", "it", "the",
    "a", "an", "for", "with", "against", "status", "statuses", "box", "boxes", "list", "lists",
}


def replace_contextual_word(
    text: str,
    source: str,
    target: str,
    kind: str,
    changes: list[dict[str, str]],
    *,
    allow_prev: set[str] | None = None,
    allow_next: set[str] | None = None,
    block_next: set[str] | None = None,
    allow_boundary: bool = False,
    protected_spans: list[tuple[int, int]] | None = None,
    note: str = "",
) -> str:
    token_re = re.compile(r"(?<![\w’'-])" + re.escape(source) + r"(?![\w’'-])", re.IGNORECASE)

    def word_before(pos: int) -> str:
        before = text[:pos]
        words = re.findall(r"[A-Za-z][A-Za-z'’.-]*", before)
        return words[-1].lower().strip(".,”“\"'") if words else ""

    def word_after(pos: int) -> str:
        after = text[pos:]
        match = re.search(r"[A-Za-z][A-Za-z'’.-]*", after)
        return match.group(0).lower().strip(".,”“\"'") if match else ""

    def repl(match: re.Match[str]) -> str:
        prev_word = word_before(match.start())
        next_word = word_after(match.end())
        if block_next and next_word in block_next:
            return match.group(0)
        if span_overlaps(match.start(), match.end(), protected_spans or []):
            return match.group(0)
        prev_ok = bool(allow_prev and prev_word in allow_prev)
        next_ok = bool(allow_next and next_word in allow_next)
        boundary_ok = allow_boundary and at_clause_or_line_boundary(text[match.end():])
        if not (prev_ok or next_ok or boundary_ok):
            return match.group(0)
        replacement = preserve_case(match.group(0), target)
        change = {"kind": kind, "from": match.group(0), "to": replacement}
        if note:
            change["note"] = note
        changes.append(change)
        return replacement

    return token_re.sub(repl, text)


def at_clause_or_line_boundary(after: str) -> bool:
    """True when the matched word is acting as a standalone heading/label."""
    if not after:
        return True
    # Treat punctuation or a line break before the next word as a noun-heading boundary.
    return bool(re.match(r"^[\s\.:;!?)\]}>#-]*(?:\n|$)", after))


def span_overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < span_end and end > span_start for span_start, span_end in spans)


def confidence_from_scores(top: float, second: float) -> float:
    if top <= 0:
        return 0.0
    # Blend absolute evidence with margin. This deliberately stays cautious for
    # tiny texts with one weak clue, and rises when top evidence beats runner-up.
    margin = max(0.0, top - second)
    absolute = min(1.0, top / 12.0)
    separation = margin / (top + second + 1.0)
    return max(0.0, min(1.0, (absolute * 0.55) + (separation * 0.45)))


def preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target
