import json
import tempfile
import unittest
from pathlib import Path

from stellivor.core import Result, Status
from stellivor.reports import build_report, render_markdown, save_report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.results = [
            Result("test", "observation", Status.SUCCESS, "Observed a test value.", data={"value": 42}),
            Result("test", "failure", Status.FAILURE, "Failed honestly.", errors=["expected test error"], warnings=["test limitation"]),
        ]

    def tearDown(self):
        self.temporary.cleanup()

    def test_report_preserves_results_and_errors(self):
        report = build_report(self.results)
        self.assertEqual(report["result_count"], 2)
        self.assertEqual(report["results"][1]["errors"], ["expected test error"])
        self.assertFalse(report["uploaded"])

    def test_credential_output_is_excluded_from_reports_by_default(self):
        secret = "alice:Recovered-Local-Password"
        result = Result("credential_audit", "john_run", Status.SUCCESS, "Completed locally.",
                        data={"returncode": 0, "output": secret, "mode": "single", "network_used": False})
        report = build_report([result])
        serialized = json.dumps(report)
        self.assertNotIn(secret, serialized)
        self.assertNotIn('"output"', serialized)
        self.assertTrue(report["results"][0]["sensitive_output_excluded"])
        self.assertEqual(report["results"][0]["data"]["mode"], "single")

    def test_credential_output_can_be_explicitly_included_for_private_reports(self):
        secret = "alice:Recovered-Local-Password"
        result = Result("credential_audit", "john_show", Status.SUCCESS, "Local results.",
                        data={"output": secret})
        report = build_report([result], include_sensitive=True)
        self.assertIn(secret, json.dumps(report))
        self.assertTrue(report["sensitive_output_included"])

    def test_save_json_and_markdown(self):
        result = save_report(self.results, self.root, stem="test-report")
        self.assertEqual(result.status, Status.SUCCESS)
        json_path = self.root / "test-report.json"
        markdown_path = self.root / "test-report.md"
        self.assertTrue(json_path.is_file())
        self.assertTrue(markdown_path.is_file())
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema"], "stellivor.report.v1")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("expected test error", markdown)
        self.assertIn("Privacy notice", markdown)

    def test_markdown_contains_status(self):
        text = render_markdown(build_report(self.results))
        self.assertIn("**failure**", text)
        self.assertIn("**success**", text)

    def test_path_like_stem_is_sanitized(self):
        result = save_report(self.results, self.root, stem="../unsafe name")
        self.assertEqual(result.status, Status.SUCCESS)
        for filename in result.data["files"]:
            self.assertEqual(Path(filename).parent, self.root)
            self.assertNotIn("..", Path(filename).name)

    def test_invalid_format_and_empty_results(self):
        self.assertEqual(save_report(self.results, self.root, formats=["html"]).status, Status.FAILURE)
        self.assertEqual(save_report([], self.root).status, Status.FAILURE)


if __name__ == "__main__":
    unittest.main()
