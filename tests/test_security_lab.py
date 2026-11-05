import unittest

from stellivor.core import Status
from stellivor.security_lab import HARDENING_CHECKLIST, estimate_passphrase_strength


class PassphraseEstimateTests(unittest.TestCase):
    def test_estimate_returns_derived_metadata_not_secret(self):
        secret = "Correct-Horse-Test-Only-42!"
        result = estimate_passphrase_strength(secret)
        self.assertEqual(result.status, Status.WARNING)
        self.assertEqual(result.data["character_count"], len(secret))
        self.assertFalse(result.data["secret_stored"])
        self.assertFalse(result.data["secret_logged"])
        self.assertNotIn(secret, repr(result.to_dict()))
        self.assertFalse(result.data["network_used"])

    def test_invalid_inputs_fail_without_exposing_input(self):
        self.assertEqual(estimate_passphrase_strength("").status, Status.FAILURE)
        long_secret = "x" * 257
        result = estimate_passphrase_strength(long_secret)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertNotIn(long_secret, repr(result.to_dict()))

    def test_checklist_is_defensive_and_nonempty(self):
        self.assertGreaterEqual(len(HARDENING_CHECKLIST), 5)
        self.assertTrue(all(isinstance(item, str) and item for item in HARDENING_CHECKLIST))
        self.assertTrue(any("WPA" in item for item in HARDENING_CHECKLIST))


if __name__ == "__main__":
    unittest.main()
