import sys
import unittest

from stellivor.core import PlatformInfo, Result, Status, aggregate_status, detect_platform, run_command


class ResultTests(unittest.TestCase):
    def test_result_serializes_status(self):
        result = Result("test", "operation", Status.SUCCESS, "worked", data={"value": 1})
        self.assertEqual(result.to_dict()["status"], "success")
        self.assertTrue(result.succeeded)

    def test_aggregate_does_not_hide_partial_failure(self):
        results = [
            Result("test", "one", Status.SUCCESS, "ok"),
            Result("test", "two", Status.DEPENDENCY_MISSING, "missing"),
        ]
        self.assertEqual(aggregate_status(results), Status.WARNING)


class PlatformTests(unittest.TestCase):
    def test_windows(self):
        self.assertEqual(detect_platform({}, "Windows").name, "windows")

    def test_macos(self):
        self.assertEqual(detect_platform({}, "Darwin").name, "macos")

    def test_termux(self):
        info = detect_platform({"TERMUX_VERSION": "0.119", "PREFIX": "/data/data/com.termux/files/usr"}, "Linux")
        self.assertEqual(info.name, "termux")
        self.assertTrue(info.is_android)

    def test_android_without_termux(self):
        info = detect_platform({"ANDROID_ROOT": "/system", "ANDROID_DATA": "/data"}, "Linux")
        self.assertEqual(info.name, "android")


class CommandTests(unittest.TestCase):
    def test_missing_executable(self):
        result = run_command(["stellivor-command-that-does-not-exist"], module="test", operation="missing")
        self.assertEqual(result.status, Status.DEPENDENCY_MISSING)
        self.assertFalse(result.data["found"])

    def test_real_successful_command(self):
        result = run_command([sys.executable, "-c", "print('actual output')"], module="test", operation="success")
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.data["stdout"].strip(), "actual output")
        self.assertEqual(result.data["returncode"], 0)

    def test_nonzero_exit_is_failure(self):
        result = run_command([sys.executable, "-c", "raise SystemExit(7)"], module="test", operation="failure")
        self.assertEqual(result.status, Status.FAILURE)
        self.assertEqual(result.data["returncode"], 7)

    def test_output_is_bounded(self):
        code = "import sys; print('x' * 5000); print('e' * 5000, file=sys.stderr)"
        result = run_command([sys.executable, "-c", code], module="test", operation="bounded", max_output_bytes=1024)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertTrue(result.data["stdout_truncated"])
        self.assertTrue(result.data["stderr_truncated"])
        self.assertEqual(len(result.data["stdout"].encode()), 1024)
        self.assertEqual(len(result.data["stderr"].encode()), 1024)

    def test_timeout_is_failure(self):
        result = run_command([sys.executable, "-c", "import time; time.sleep(3)"], module="test", operation="timeout", timeout=0.1)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertTrue(result.data["timed_out"])

    def test_invalid_command_is_rejected(self):
        result = run_command([], module="test", operation="invalid")
        self.assertEqual(result.status, Status.FAILURE)


if __name__ == "__main__":
    unittest.main()
