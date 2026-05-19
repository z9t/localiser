"""JSON schemas for Regionaliser Hermes plugin and MCP tools."""
from __future__ import annotations

REGION = {"type": "string", "description": "Region code: au, us, uk, or ca."}
TEXT = {"type": "string", "description": "Input text to process."}
LOCALES = {
    "description": "Optional comma-separated string or list of locality labels, e.g. 'NSW,Sydney' or ['Ontario/Toronto'].",
    "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
}
REGIONS = {
    "description": "Optional comma-separated string or list of candidate region codes.",
    "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
}

LOCALISER_REGIONALISE_TEXT = {
    "name": "localiser_regionalise_text",
    "description": "Rewrite English text toward a target regional variety using deterministic Regionaliser CSV/SQLite data. Use for AU/US/UK/CA spelling, vocabulary, and light register shifts; does not call an AI model.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": TEXT,
            "region": REGION,
            "register": {"type": "string", "default": "neutral"},
            "generation": {"type": "string", "default": "neutral"},
            "subregion": {"type": "string", "default": "national"},
            "class_layer": {"type": "string", "default": "neutral"},
            "setting": {"type": "string", "default": "neutral"},
            "density": {"type": "string", "enum": ["none", "light", "medium", "high"], "default": "light"},
            "explain": {"type": "boolean", "default": True},
            "use_stanza": {"type": "boolean", "default": False, "description": "Full localiser only: use optional Stanza NER to protect named entities from rewrite false positives. Requires stanza/models; unavailable Stanza returns notes and keeps deterministic output."},
            "db_path": {"type": "string", "description": "Optional path to regionaliser.sqlite."},
        },
        "required": ["text", "region"],
    },
}

LOCALISER_DETECT_REGION = {
    "name": "localiser_detect_region",
    "description": "Score likely AU/US/UK/CA regional textual signals from spelling, vocabulary, institutions, and cultural references. Evidence scoring only; not proof of nationality or location.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": TEXT,
            "regions": REGIONS,
            "max_evidence": {"type": "integer", "default": 12},
            "db_path": {"type": "string"},
        },
        "required": ["text"],
    },
}

LOCALISER_DETECT_LOCALE = {
    "name": "localiser_detect_locale",
    "description": "Score subnational/state/city textual clues for a region using locale marker data. Useful for Australian state/city clues, US/UK/CA metro/province clues. Evidence only.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": TEXT,
            "region": {"type": "string", "default": "au"},
            "locales": LOCALES,
            "max_evidence": {"type": "integer", "default": 12},
            "db_path": {"type": "string"},
        },
        "required": ["text"],
    },
}

LOCALISER_CULTURAL_CONTEXT = {
    "name": "localiser_cultural_context",
    "description": "Return daily-life institutions, media/reference ecology, and generational cultural quote/reference context for a region/locality. Use to build cultural context trees without stereotype stuffing.",
    "parameters": {
        "type": "object",
        "properties": {
            "region": REGION,
            "locales": LOCALES,
            "generation": {"type": "string", "default": "neutral"},
            "max_rows": {"type": "integer", "default": 24},
            "db_path": {"type": "string"},
        },
        "required": ["region"],
    },
}

LOCALISER_SPORTS_CONTEXT = {
    "name": "localiser_sports_context",
    "description": "Return locality sports-cultural context: top sports/codes, teams, current player seeds, historic players, notes, and cautions. Use explicitly; don't infer allegiance.",
    "parameters": {
        "type": "object",
        "properties": {
            "region": REGION,
            "locales": LOCALES,
            "max_rows": {"type": "integer", "default": 24},
            "db_path": {"type": "string"},
        },
        "required": ["region"],
    },
}

LOCALISER_NAMED_ENTITIES = {
    "name": "localiser_named_entities",
    "description": "Extract named entities with optional Stanford Stanza NER. Use to separate people, places, organisations, and brands from regional vocabulary before detection or lexicon learning. Requires optional stanza install/models.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": TEXT,
            "lang": {"type": "string", "default": "en"},
            "package": {"type": "string"},
            "db_path": {"type": "string"},
        },
        "required": ["text"],
    },
}

TOOLS = [
    LOCALISER_REGIONALISE_TEXT,
    LOCALISER_DETECT_REGION,
    LOCALISER_DETECT_LOCALE,
    LOCALISER_CULTURAL_CONTEXT,
    LOCALISER_SPORTS_CONTEXT,
    LOCALISER_NAMED_ENTITIES,
]

TOOLS_BY_NAME = {tool["name"]: tool for tool in TOOLS}
