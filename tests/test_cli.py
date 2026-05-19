from pathlib import Path
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest

from core.localiser.engine import Localiser
from core.localiser import mcp_server, tool_api

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "core/scripts/regionalise.py"
MCP = ROOT / "core/scripts/localiser_mcp.py"


class LocaliserCliTests(unittest.TestCase):
    def run_cli(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            input=input_text,
            text=True,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def test_au_replaces_vocabulary_and_spelling(self):
        result = self.run_cli(
            "--region", "au", "--density", "none",
            "I walked on the sidewalk to the gas station and liked the color.",
        )
        self.assertIn("footpath", result.stdout)
        self.assertIn("servo", result.stdout)
        self.assertIn("colour", result.stdout)

    def test_au_contextual_spelling_avoids_legal_false_positives(self):
        result = self.run_cli(
            "--region", "au", "--density", "none", "--json",
            "## License\n\nOur practice areas include criminal law. Check defences before filing.",
        )
        payload = json.loads(result.stdout)
        self.assertIn("## Licence", payload["text"])
        self.assertIn("practice areas", payload["text"])
        self.assertIn("Check defences", payload["text"])
        self.assertNotIn("practise areas", payload["text"])
        self.assertNotIn("Cheque defences", payload["text"])

    def test_au_contextual_spelling_changes_only_high_confidence_senses(self):
        result = self.run_cli(
            "--region", "au", "--density", "none", "--json",
            "She plans to practice law and paid by bank check.",
        )
        payload = json.loads(result.stdout)
        self.assertIn("practise law", payload["text"])
        self.assertIn("bank cheque", payload["text"])

    def test_stanza_preference_protects_named_entities_when_enabled(self):
        class FakeEntity:
            def __init__(self, text, typ, start, end):
                self.text = text
                self.type = typ
                self.start_char = start
                self.end_char = end

        class FakeDoc:
            ents = [FakeEntity("License Group", "ORG", 0, 13)]

        class FakePipeline:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __call__(self, text):
                return FakeDoc()

        previous = sys.modules.get("stanza")
        fake_stanza = types.ModuleType("stanza")
        setattr(fake_stanza, "Pipeline", FakePipeline)
        sys.modules["stanza"] = fake_stanza
        try:
            result = Localiser().regionalise("License Group liked the color.", region="au", density="none", use_stanza=True)
        finally:
            if previous is None:
                sys.modules.pop("stanza", None)
            else:
                sys.modules["stanza"] = previous
        self.assertIn("License Group", result.text)
        self.assertIn("colour", result.text)
        self.assertTrue(any("Stanza" in note for note in result.notes))

    def test_stanza_preference_filters_named_entities_from_analysis(self):
        class FakeEntity:
            def __init__(self, text, typ, start, end):
                self.text = text
                self.type = typ
                self.start_char = start
                self.end_char = end

        class FakeDoc:
            ents = [FakeEntity("Qantas", "ORG", 0, 6)]

        class FakePipeline:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __call__(self, text):
                return FakeDoc()

        previous = sys.modules.get("stanza")
        fake_stanza = types.ModuleType("stanza")
        setattr(fake_stanza, "Pipeline", FakePipeline)
        sys.modules["stanza"] = fake_stanza
        try:
            result = Localiser().analyse("Qantas mentioned smoko.", use_stanza=True)
        finally:
            if previous is None:
                sys.modules.pop("stanza", None)
            else:
                sys.modules["stanza"] = previous
        terms = {item["term"] for item in result.non_baseline}
        self.assertNotIn("Qantas", terms)
        self.assertIn("smoko", terms)
        self.assertTrue(any("Stanza" in note for note in result.notes))

    def test_stdin_and_json_changes(self):
        result = self.run_cli("--region", "uk", "--json", input_text="The sidewalk is near the gas station.")
        self.assertIn('"text"', result.stdout)
        self.assertIn("pavement", result.stdout)

    def test_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "regionalised.txt"
            self.run_cli("--region", "ca", "--output", str(out), "The candy was on the sidewalk.")
            self.assertTrue(out.exists())
            self.assertTrue(out.read_text(encoding="utf-8").strip())

    def test_detect_mode_scores_region_from_markers(self):
        result = self.run_cli(
            "--detect", "--json",
            "I topped up my Opal card before stopping at Woolies and checking Centrelink.",
        )
        self.assertIn('"region": "au"', result.stdout)
        self.assertIn("Opal card", result.stdout)

    def test_detect_locale_scores_au_state_and_city_markers(self):
        result = self.run_cli(
            "--detect-locale", "--json",
            "I topped up my Opal before grabbing a potato scallop and watching the NRL.",
        )
        self.assertIn('"locale": "NSW"', result.stdout)
        self.assertIn("Sydney", result.stdout)
        self.assertIn("Opal", result.stdout)

    def test_detect_locale_scores_vic_markers(self):
        result = self.run_cli(
            "--detect-locale", "--json",
            "I tapped on with my myki, grabbed a potato cake and called it a parma before the AFL.",
        )
        self.assertIn('"locale": "VIC"', result.stdout)
        self.assertIn("Melbourne", result.stdout)
        self.assertIn("myki", result.stdout)

    def test_detect_locale_scores_us_markers(self):
        result = self.run_cli(
            "--detect-locale", "--locale-region", "us", "--json",
            "I put money on my Clipper card before taking BART and Muni across the Bay.",
        )
        self.assertIn('"locale": "San Francisco Bay Area"', result.stdout)
        self.assertIn("BART", result.stdout)

    def test_detect_locale_scores_uk_markers(self):
        result = self.run_cli(
            "--detect-locale", "--locale-region", "uk", "--json",
            "I checked my Oyster card, the Tube delays and the ULEZ map before crossing the borough.",
        )
        self.assertIn('"locale": "London"', result.stdout)
        self.assertIn("Oyster card", result.stdout)

    def test_detect_locale_scores_ca_markers(self):
        result = self.run_cli(
            "--detect-locale", "--locale-region", "ca", "--json",
            "I used my Presto card on the TTC after checking the LCBO hours near the 401.",
        )
        self.assertIn('"locale": "Ontario"', result.stdout)
        self.assertIn("TTC", result.stdout)

    def test_sports_mode_filters_by_locale(self):
        result = self.run_cli(
            "--sports", "--region", "uk", "--locales", "London", "--json",
        )
        self.assertIn('"team": "Arsenal"', result.stdout)
        self.assertIn('"locale": "London"', result.stdout)
        self.assertIn('"sports"', result.stdout)

    def test_rewrite_can_include_sports_context(self):
        result = self.run_cli(
            "--region", "au", "--sports", "--locales", "VIC/Melbourne",
            "I liked the color of the sidewalk.",
        )
        self.assertIn("colour", result.stdout)
        self.assertIn("sports region=au", result.stdout)
        self.assertIn("Collingwood Magpies", result.stdout)

    def test_context_mode_returns_institutions_and_media(self):
        result = self.run_cli(
            "--context", "--region", "ca", "--locales", "Ontario/Toronto", "--json",
        )
        self.assertIn('"context"', result.stdout)
        self.assertIn("ServiceOntario", result.stdout)
        self.assertIn("CBC Toronto", result.stdout)
        self.assertIn("Schitt", result.stdout)

    def test_culture_mode_filters_generation(self):
        result = self.run_cli(
            "--culture", "--region", "au", "--generation", "gen-x", "--json",
        )
        self.assertIn("The Castle", result.stdout)
        self.assertIn("it’s the vibe", result.stdout)
        self.assertNotIn("Bluey", result.stdout)

    def test_detect_mode_uses_quote_fragments(self):
        result = self.run_cli("--detect", "--regions", "au,us", "--json", "Honestly, it’s the vibe of the whole thing.")
        self.assertIn('"region": "au"', result.stdout)
        self.assertIn("quote_fragment", result.stdout)

    def test_named_entities_uses_optional_stanza_pipeline(self):
        class FakeEntity:
            def __init__(self, text, typ, start, end):
                self.text = text
                self.type = typ
                self.start_char = start
                self.end_char = end

        class FakeDoc:
            ents = [FakeEntity("Sydney", "GPE", 0, 6), FakeEntity("Service NSW", "ORG", 14, 25)]

        class FakePipeline:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __call__(self, text):
                return FakeDoc()

        previous = sys.modules.get("stanza")
        fake_stanza = types.ModuleType("stanza")
        setattr(fake_stanza, "Pipeline", FakePipeline)
        sys.modules["stanza"] = fake_stanza
        try:
            result = Localiser().named_entities("Sydney called Service NSW.")
        finally:
            if previous is None:
                sys.modules.pop("stanza", None)
            else:
                sys.modules["stanza"] = previous
        self.assertEqual(result.entities[0]["type"], "GPE")
        self.assertEqual(result.entities[1]["text"], "Service NSW")

    def test_tool_api_regionalise_handler_returns_json(self):
        payload = json.loads(tool_api.regionalise_text({"text": "The sidewalk color", "region": "au", "density": "none"}))
        self.assertIn("footpath", payload["text"])
        self.assertIn("colour", payload["text"])

    def test_mcp_tools_list_and_call(self):
        listed = mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertIsNotNone(listed)
        assert listed is not None
        self.assertIn("tools", listed["result"])
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertIn("localiser_detect_region", names)
        called = mcp_server.handle({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "localiser_detect_region", "arguments": {"text": "I tapped my Opal card at Woolies."}},
        })
        self.assertIsNotNone(called)
        assert called is not None
        text = called["result"]["content"][0]["text"]
        self.assertIn('"region": "au"', text)

    def test_mcp_stdio_smoke(self):
        messages = "\n".join([
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            "",
        ])
        result = subprocess.run(
            [sys.executable, str(MCP)],
            input=messages,
            text=True,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertIn("localiser", result.stdout)
        self.assertIn("localiser_regionalise_text", result.stdout)

    def test_rewrite_can_include_context_tree(self):
        result = self.run_cli(
            "--region", "uk", "--context", "--locales", "London",
            "The sidewalk color was unusual.",
        )
        self.assertIn("pavement", result.stdout)
        self.assertIn("context region=uk", result.stdout)
        self.assertIn("TfL", result.stdout)

    def test_detect_mode_can_return_unknown_for_generic_text(self):
        result = self.run_cli("--detect", "--json", "We went to the meeting and discussed the project.")
        self.assertIn('"region": null', result.stdout)

    def test_analyse_mode_flags_non_baseline_and_known_terms(self):
        result = self.run_cli(
            "--analyse", "--json",
            "I went to Woolies after smoko with the Oka crew and grabbed a servo pie.",
        )
        self.assertIn('"non_baseline"', result.stdout)
        self.assertIn("smoko", result.stdout)
        self.assertIn('"known_regions"', result.stdout)

    def test_learn_mode_writes_custom_lexicon_scaffold(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.run_cli("--learn", "Oka bogan", "--learn-out", td, "Oka yarning at the ridgy-didge camp.")
            self.assertIn("slug=oka-bogan", result.stdout)
            self.assertTrue((Path(td) / "oka-bogan" / "data" / "lexicon.csv").exists())
            self.assertTrue((Path(td) / "oka-bogan" / "data" / "detection_markers.csv").exists())


if __name__ == "__main__":
    unittest.main()
