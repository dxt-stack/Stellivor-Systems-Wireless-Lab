import hashlib
import tempfile
import unittest
from pathlib import Path

from stellivor.core import Status
from stellivor.file_intel import calculate_sha256, extract_printable_strings, inspect_file, signature_hint, verify_sha256


class FileIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_sha256_empty_known_vector(self):
        path = self.write("empty.bin", b"")
        result = calculate_sha256(path)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.data["digest"], hashlib.sha256(b"").hexdigest())
        self.assertTrue(result.data["covers_entire_file"])

    def test_sha256_abc_known_vector(self):
        path = self.write("abc.bin", b"abc")
        result = calculate_sha256(path)
        self.assertEqual(result.data["digest"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_partial_hash_is_explicit(self):
        path = self.write("large.bin", b"abcdefgh")
        result = calculate_sha256(path, max_bytes=4)
        self.assertEqual(result.status, Status.WARNING)
        self.assertEqual(result.data["digest"], hashlib.sha256(b"abcd").hexdigest())
        self.assertEqual(result.data["hashed_bytes"], 4)
        self.assertFalse(result.data["covers_entire_file"])

    def test_signature_hints(self):
        self.assertEqual(signature_hint(b"\x7fELFrest")["name"], "ELF")
        self.assertEqual(signature_hint(b"MZrest")["name"], "Possible PE")
        self.assertEqual(signature_hint(b"unknown")["name"], "Unknown")

    def test_file_inspection_reads_strings_and_does_not_execute(self):
        marker = self.root / "should-not-exist"
        script = self.write("inspect-only.sh", f"#!/bin/sh\ntouch '{marker}'\necho printable-string\n".encode())
        result = inspect_file(script)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertFalse(marker.exists())
        self.assertFalse(result.data["executed"])
        values = [item["value"] for item in result.data["strings"]["items"]]
        self.assertTrue(any("printable-string" in value for value in values))

    def test_string_offsets_and_limit(self):
        strings, truncated = extract_printable_strings(b"\x00hello\x00world", max_strings=1)
        self.assertEqual(strings[0]["offset"], 1)
        self.assertEqual(strings[0]["value"], "hello")
        self.assertTrue(truncated)

    def test_string_length_limit_is_validated(self):
        for value in (True, 3, 4097, "10"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    extract_printable_strings(b"hello world", max_string_length=value)

    def test_bounded_string_scan(self):
        path = self.write("strings.bin", b"abcd" * 100)
        result = inspect_file(path, max_strings_bytes=16)
        self.assertEqual(result.data["strings"]["bytes_scanned"], 16)
        self.assertTrue(result.data["strings"]["truncated"])

    def test_verification_match(self):
        path = self.write("abc.bin", b"abc")
        digest = hashlib.sha256(b"abc").hexdigest().upper()
        result = verify_sha256(path, digest)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertTrue(result.data["match"])
        self.assertFalse(result.data["reference_is_trusted"])

    def test_verification_mismatch(self):
        path = self.write("abc.bin", b"abc")
        result = verify_sha256(path, "0" * 64)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertFalse(result.data["match"])
        self.assertTrue(result.data["verification_completed"])

    def test_verification_rejects_invalid_digest(self):
        path = self.write("abc.bin", b"abc")
        result = verify_sha256(path, "not-a-hash")
        self.assertEqual(result.status, Status.FAILURE)
        self.assertFalse(result.data["verification_completed"])

    def test_verification_never_compares_partial_hash(self):
        path = self.write("abc.bin", b"abc")
        result = verify_sha256(path, hashlib.sha256(b"ab").hexdigest(), max_bytes=2)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertFalse(result.data["verification_completed"])

    def test_missing_file_and_directory_fail(self):
        self.assertEqual(inspect_file(self.root / "missing").status, Status.FAILURE)
        self.assertEqual(inspect_file(self.root).status, Status.FAILURE)


if __name__ == "__main__":
    unittest.main()
