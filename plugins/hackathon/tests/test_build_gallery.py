"""Regression tests for the standalone gallery builder."""

import base64
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_gallery.py"
SPEC = importlib.util.spec_from_file_location("build_gallery", SCRIPT)
gallery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gallery)
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==")


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name)

    def write(self, data, frame=None):
        (self.run_dir / "results.json").write_text(json.dumps(data), encoding="utf-8")
        if frame is not None:
            (self.run_dir / "frame.html").write_text(frame, encoding="utf-8")

    def build(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = gallery.main([str(self.run_dir)] + list(args))
        page = (self.run_dir / "gallery.html").read_text(encoding="utf-8") if (self.run_dir / "gallery.html").exists() else ""
        return code, page, out.getvalue(), err.getvalue()

    def test_missing_keys_defaults(self):
        self.write({"pitches": [{}]})
        code, page, summary, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn("Untitled pitch 1", page)
        self.assertIn("Unassigned", page)
        self.assertIn("effort ?", page)
        self.assertIn("1 missing", summary)

    def test_none_values_and_types(self):
        self.write({"pitches": [{"name": "Mixed", "feasibility": None, "value": None,
                                 "risks": None, "one_liner": 7, "surface": 3,
                                 "api_used": [1, None]}]})
        code, page, _, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn('<span class="score">–', page)
        self.assertIn('<p class="one">7</p>', page)
        self.assertIn('<code>1</code><code></code>', page)

    def test_pitches_shape_and_missing_teams(self):
        self.write({"pitches": [{"name": "One"}], "teams_missing": ["B", "C"]})
        self.assertIn("Teams with no result: B, C", self.build()[1])

    def test_raw_team_list_joins_by_slug_first(self):
        self.write([{"team": "Alpha", "pitches": [{"name": "A", "slug": "a"}],
                     "feasibility": {"verdicts": [{"slug": "a", "verdict": "Buildable"}]},
                     "value": {"verdicts": [{"slug": "a", "score": 8}]} }])
        code, page, _, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn("Alpha", page)
        self.assertIn('<span class="score">8', page)
        self.assertIn('class="pill ok">buildable', page)

    def test_teams_object_joins_by_trimmed_name(self):
        self.write({"teams": [{"name": "Beta", "pitches": [{"name": "Named"}],
                               "feasibility": {"verdicts": [{"name": " named ", "verdict": "Buildable"}]},
                               "value": {"verdicts": [{"name": "NAMED", "score": "7.5"}]}}]})
        page = self.build()[1]
        self.assertIn("Beta", page)
        self.assertIn('<span class="score">7.5', page)

    def test_top_level_judge_lists_and_pitch_override(self):
        self.write({"pitches": [{"name": "One", "slug": "one", "value": {"score": 9}},
                                {"name": "Two", "slug": "two"}],
                    "feasibility": [{"slug": "one", "verdict": "Buildable"},
                                    {"name": " two ", "verdict": "not_buildable"}],
                    "value": [{"slug": "one", "score": 1}, {"slug": "two", "score": 4}]})
        code, page, summary, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn('<span class="score">9', page)
        self.assertIn("1 parked", summary)

    def test_mockup_file_without_frame(self):
        mockups = self.run_dir / "mockups"
        mockups.mkdir()
        (mockups / "one.html").write_text("<h1>Actual mockup</h1>", encoding="utf-8")
        self.write({"pitches": [{"name": "One", "slug": "one"}]})
        code, page, summary, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn("Actual mockup", page)
        self.assertIn("0 missing", summary)

    def test_relative_path_uses_run_dir_from_other_cwd(self):
        mockups = self.run_dir / "mockups"
        mockups.mkdir()
        (mockups / "custom.html").write_text("relative works", encoding="utf-8")
        self.write({"pitches": [{"name": "One", "mockup_path": "mockups/custom.html"}]})
        old = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            code, page, _, _ = self.build()
        finally:
            os.chdir(old)
        self.assertEqual(code, 0)
        self.assertIn("relative works", page)

    def test_generic_fallback_slots_and_marker_strip(self):
        self.write({"pitches": [{"name": "One", "slug": "one", "slots_fallback": {"novel": "NOVEL", "color": "red"}}]},
                   "<!-- SLOT:title --><!-- SLOT:caption --><!-- SLOT:novel --><!-- SLOT:unused --><style>/* SLOT:color */</style>")
        code, page, summary, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn("NOVEL", page)
        self.assertIn("Team Unassigned", page)
        self.assertIn("1 fallback", summary)
        self.assertNotIn("SLOT:unused", page)

    def test_missing_frame_fallback_becomes_placeholder(self):
        self.write({"pitches": [{"name": "One", "slots_fallback": {"other": "text"}}]})
        code, page, summary, err = self.build()
        self.assertEqual(code, 0)
        self.assertIn("Mockup missing", page)
        self.assertIn("frame.html missing", err)
        self.assertIn("1 missing", summary)

    def test_duplicate_slugs_get_distinct_document_ids(self):
        self.write({"pitches": [{"name": "First", "slug": "same"}, {"name": "Second", "slug": "same"}]})
        page = self.build()[1]
        self.assertEqual(re.findall(r'<template id="doc-(\d+)"', page), ["0", "1"])
        self.assertEqual(re.findall(r'data-doc="(\d+)"', page), ["0", "1"])

    def test_verdict_variants(self):
        cases = {"Buildable with changes": "buildable-with-changes",
                 "buildable (with changes)": "buildable-with-changes",
                 "not_buildable": "not-buildable", "NOT BUILDABLE": "not-buildable",
                 "unbuildable": "not-buildable", "buildable": "buildable", None: "unjudged",
                 "buildable (see note)": "buildable", "Buildable - notes inside": "buildable",
                 "non-buildable": "not-buildable", "not yet judged": "unjudged"}
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(gallery.verdict(raw), expected)

    def test_value_scores_key_joins(self):
        self.write({"pitches": [{"name": "One", "slug": "one"}],
                    "value": {"scores": [{"slug": "one", "score": 6, "note": "fine"}]}})
        code, page, _, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn('<span class="score">6<small>', page)

    def test_score_coercion_and_clamp(self):
        cases = [("7", 7.0), (10.5, 10.0), (-2, 0.0), ("bad", None), (None, None), ("nan", None)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(gallery.numeric_score(raw), expected)
        self.assertEqual(gallery.score_label(7.0), "7")

    def test_ranking_score_verdict_and_original_order(self):
        self.write({"pitches": [
            {"name": "None", "value": None}, {"name": "Change", "value": 8, "feasibility": "buildable with changes"},
            {"name": "First", "value": 8, "feasibility": "buildable"},
            {"name": "Second", "value": 8, "feasibility": "buildable"},
            {"name": "Park", "value": 10, "feasibility": "not buildable"}]})
        page = self.build()[1]
        self.assertLess(page.index("<h2>First"), page.index("<h2>Second"))
        self.assertLess(page.index("<h2>Second"), page.index("<h2>Change"))
        self.assertLess(page.index("<h2>Change"), page.index("<h2>None"))
        self.assertLess(page.index("<h2>None"), page.index("<h2>Park"))

    def test_size_precedence(self):
        mockups = self.run_dir / "mockups"
        mockups.mkdir()
        (mockups / "one.html").write_text('<meta name="hackathon:size" content="320x600">', encoding="utf-8")
        self.write({"pitches": [{"name": "One", "slug": "one"}]},
                   '<meta name="hackathon:size" content="800x500">')
        self.assertIn('data-w="320" data-h="600"', self.build()[1])
        self.assertIn('data-w="900" data-h="700"', self.build("--size", "900x700")[1])
        (mockups / "one.html").write_text("<p>No size</p>", encoding="utf-8")
        self.assertIn('data-w="800" data-h="500"', self.build()[1])
        (self.run_dir / "frame.html").unlink()
        self.assertIn('data-w="1352" data-h="860"', self.build()[1])

    def test_built_screenshot_embedded(self):
        (self.run_dir / "built.png").write_bytes(PNG)
        self.write({"pitches": [{"name": "One", "built_screenshot": "built.png", "status": "built", "built_note": "Done"}]})
        code, page, summary, _ = self.build()
        self.assertEqual(code, 0)
        self.assertIn("data:image/png;base64,", page)
        self.assertIn("<figcaption>Mockup</figcaption>", page)
        self.assertIn("<figcaption>Built</figcaption>", page)
        self.assertIn("1 built", summary)

    def test_artifact_shape(self):
        self.write({"pitches": []})
        self.assertEqual(self.build("Gallery", "--artifact", "Page")[0], 0)
        artifact = (self.run_dir / "gallery.artifact.html").read_text(encoding="utf-8")
        self.assertTrue(artifact.startswith("<title>Page</title>\n<style>"))
        self.assertIn("</style>\n<header>", artifact)
        self.assertNotIn("<body>", artifact)

    def test_sandbox_on_card_and_viewer(self):
        self.write({"pitches": [{"name": "One"}]})
        page = self.build()[1]
        self.assertEqual(page.count('sandbox="allow-scripts"'), 2)
        self.assertNotIn("allow-same-origin", page)

    def test_malicious_name_escaped_and_absent_from_script(self):
        name = '</script><script>alert("bad")</script>'
        self.write({"pitches": [{"name": name}]})
        page = self.build()[1]
        self.assertNotIn(name, page)
        self.assertIn("&lt;/script&gt;", page)
        script = page.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("bad", script)

    def test_missing_results_returns_two(self):
        code, _, summary, err = self.build()
        self.assertEqual(code, 2)
        self.assertEqual(summary, "")
        self.assertIn("results.json", err)

    def test_invalid_results_returns_two(self):
        (self.run_dir / "results.json").write_text("not json", encoding="utf-8")
        self.assertEqual(self.build()[0], 2)

    def test_non_object_pitch_returns_two(self):
        self.write({"pitches": ["not an object"]})
        code, _, _, err = self.build()
        self.assertEqual(code, 2)
        self.assertIn("pitch must be an object", err)

    def test_single_api_string_and_mixed_defaults(self):
        self.write({"pitches": [{"name": "One", "api_used": "API", "risks": 42}]})
        page = self.build()[1]
        self.assertIn("<code>API</code>", page)
        self.assertIn("<b>Risks:</b> 42", page)

    def test_viewer_scales_and_restores_focus(self):
        self.write({"pitches": [{"name": "One"}]})
        page = self.build()[1]
        self.assertIn("stage.clientWidth / w", page)
        self.assertIn("if (opener) opener.focus()", page)
        self.assertIn("e.key === 'Escape'", page)


if __name__ == "__main__":
    unittest.main()
