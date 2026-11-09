import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "korea-job-search" / "cli.py"
SPEC = importlib.util.spec_from_file_location("korea_job_search", MODULE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = bridge
SPEC.loader.exec_module(bridge)


def args(**overrides):
    values = dict(
        query="데이터 엔지니어", limit=20, timeout=25, region=["서울"],
        occupation=["133200"], employment=["permanent"], career="experienced",
        min_career_months=24, max_career_months=120, education="bachelor",
        jobage=14, source=None, allow_public_pages=False, format="json",
    )
    values.update(overrides)
    return argparse.Namespace(**values)


class KoreaJobSearchBridgeTests(unittest.TestCase):
    def test_defaults_to_official_first_sources(self):
        self.assertEqual(bridge.parse_sources(None), list(bridge.DEFAULT_SOURCES))

    def test_builds_work24_specific_filters_without_a_secret(self):
        command = bridge.collector_command(Path("integration"), "work24", args())
        self.assertIn("--region", command)
        self.assertIn("--occupation", command)
        self.assertIn("--min-career-months", command)
        self.assertNotIn("WORK24_API_KEY", " ".join(command))

    def test_normalizes_job_searcher_schema(self):
        result = bridge.normalize({
            "external_id": "123", "title": "데이터 엔지니어", "url": "https://example.test/job/123",
            "company": "예시회사", "location": "서울", "posted_at": "2026-11-08T10:00:00Z",
            "deadline": "2026-11-30", "status": "open", "snippet": "Python",
        }, "work24")
        self.assertEqual(result["id"], "work24:123")
        self.assertEqual(result["date"], "2026-11-08")
        self.assertEqual(result["description"], "Python")

    def test_public_pages_need_explicit_opt_in(self):
        selected = bridge.parse_sources(["jobkorea,saramin"])
        self.assertEqual(selected, ["jobkorea", "saramin"])
        self.assertTrue(all(bridge.SOURCES[name]["mode"] in bridge.OPT_IN_MODES for name in selected))

    def test_unknown_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "지원하지 않는 소스"):
            bridge.parse_sources(["unknown"])


if __name__ == "__main__":
    unittest.main()
