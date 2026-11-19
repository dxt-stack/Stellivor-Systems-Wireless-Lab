import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stellivor.core import Status
from stellivor.credential_audit import audit_tool_status, run_local_audit


class CredentialAuditTests(unittest.TestCase):
    def test_tool_status_is_detection_only(self):
        with patch("stellivor.credential_audit.find_john", return_value=None), \
             patch("stellivor.credential_audit.find_hashcat", return_value="/usr/bin/hashcat"):
            result = audit_tool_status()
        self.assertFalse(result.data["john_found"])
        self.assertTrue(result.data["hashcat_found"])
        self.assertFalse(result.data["installation_attempted"])
        self.assertFalse(result.data["network_used"])

    def test_requires_explicit_authorization(self):
        result = run_local_audit("single", "/tmp/hashfile", authorized=False)
        self.assertEqual(result.status, Status.PERMISSION_RESTRICTED)

    def test_rejects_missing_files_and_invalid_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "hashes.txt"
            file.write_text("sample-hash")
            with patch("stellivor.credential_audit.find_john", return_value="/usr/bin/john"):
                result = run_local_audit("unsupported", file, authorized=True)
                self.assertEqual(result.status, Status.FAILURE)
                result = run_local_audit("single", Path(directory) / "missing", authorized=True)
                self.assertEqual(result.status, Status.FAILURE)

    def test_single_mode_uses_argument_array_and_no_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "hashes.txt"
            file.write_text("sample-hash")
            with patch("stellivor.credential_audit.find_john", return_value="/usr/bin/john"), \
                 patch("stellivor.credential_audit.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = "audit complete"
                run.return_value.stderr = ""
                result = run_local_audit("single", file, session="lab_01", authorized=True)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(run.call_args.args[0][1], "--single")
        self.assertIn("--session=lab_01", run.call_args.args[0])

    def test_wordlist_mode_requires_existing_wordlist(self):
        with tempfile.TemporaryDirectory() as directory:
            hashes = Path(directory) / "hashes.txt"
            hashes.write_text("sample-hash")
            with patch("stellivor.credential_audit.find_john", return_value="/usr/bin/john"):
                result = run_local_audit("wordlist", hashes, wordlist=Path(directory) / "missing",
                                         authorized=True)
        self.assertEqual(result.status, Status.FAILURE)


if __name__ == "__main__":
    unittest.main()
