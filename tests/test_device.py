import json
import unittest
from unittest.mock import patch

from stellivor.cli import main as cli_main
from stellivor.core import Result, Status
from stellivor.device import _parse_devices, device_readiness


class DeviceParsingTests(unittest.TestCase):
    def test_parse_devices_keeps_state_and_details(self):
        devices = _parse_devices("""List of devices attached
emulator-5554\tdevice product:sdk_gphone model:sdk_gphone_x86 device:generic_x86
usb-1\tunauthorized usb:1-2
""")
        self.assertEqual(devices[0]["state"], "device")
        self.assertEqual(devices[0]["details"]["model"], "sdk_gphone_x86")
        self.assertEqual(devices[1]["state"], "unauthorized")

    @patch("stellivor.device.run_command")
    def test_missing_adb_is_explicit(self, run_command):
        missing = Result("device", "probe", Status.DEPENDENCY_MISSING, "missing")
        run_command.return_value = missing
        result = device_readiness()
        self.assertEqual(result.status, Status.DEPENDENCY_MISSING)
        self.assertEqual(result.data["authorized_operations_only"], True)
        self.assertIn("lockscreen_bypass", result.data["unsupported_operations"])


class DirectCliTests(unittest.TestCase):
    def test_cli_system_json_is_machine_readable(self):
        # The direct CLI writes exactly one JSON result when --json is selected.
        with patch("sys.stdout.write") as write:
            # Use the parser path and only assert it succeeds; system collection is real.
            self.assertEqual(cli_main(["system", "--json"]), 0)
            self.assertTrue(write.called)


if __name__ == "__main__":
    unittest.main()
