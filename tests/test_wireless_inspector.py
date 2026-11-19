import unittest
from unittest.mock import patch

from stellivor.core import PlatformInfo, Result, Status
from stellivor.wireless_inspector import (
    current_connection, inspect_saved_profile, network_configuration,
    refresh_wireless_information, saved_profile_names,
)


class SavedProfileTests(unittest.TestCase):
    @patch("stellivor.wireless_inspector.run_command")
    def test_windows_lists_names_without_requesting_keys(self, command):
        command.return_value = Result(
            "wireless_inspector", "saved_profiles", Status.SUCCESS, "ok",
            data={"stdout": "    All User Profile     : HomeNet\n    All User Profile     : Lab"},
        )
        result = saved_profile_names(PlatformInfo("windows", "Windows"))
        self.assertEqual(result.data["profiles"], ["HomeNet", "Lab"])
        self.assertFalse(result.data["key_material_requested"])
        self.assertNotIn("key=clear", command.call_args.args[0])

    @patch("stellivor.wireless_inspector.run_command")
    def test_termux_saved_profiles_are_explicitly_unsupported(self, command):
        result = saved_profile_names(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.UNSUPPORTED)
        command.assert_not_called()

    @patch("stellivor.wireless_inspector.run_command")
    def test_windows_profile_inspection_never_requests_key_clear(self, command):
        command.return_value = Result("wireless_inspector", "profile_inspection", Status.SUCCESS, "ok")
        inspect_saved_profile("HomeNet", PlatformInfo("windows", "Windows"))
        arguments = command.call_args.args[0]
        self.assertIn("show", arguments)
        self.assertNotIn("key=clear", arguments)

    @patch("stellivor.wireless_inspector.run_command")
    def test_linux_profile_listing_parses_wifi_only(self, command):
        command.return_value = Result(
            "wireless_inspector", "saved_profiles", Status.SUCCESS, "ok",
            data={"stdout": "Home:802-11-wireless\nOffice:802-11-wireless\nVPN:vpn"},
        )
        result = saved_profile_names(PlatformInfo("linux", "Linux"))
        self.assertEqual(result.data["profiles"], ["Home", "Office"])

    @patch("stellivor.wireless_inspector.wireless_snapshot")
    def test_nearby_refresh_and_connection_keep_platform_status(self, snapshot):
        snapshot.return_value = Result("wireless", "wireless_snapshot", Status.WARNING, "limited")
        result = refresh_wireless_information(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.WARNING)
        self.assertIn("nearby_networks", result.data)
        self.assertIn("saved_profiles", result.data)

    @patch("stellivor.network.route_information")
    @patch("stellivor.network.interface_information")
    def test_network_configuration_preserves_partial_failure(self, interfaces, routes):
        interfaces.return_value = Result("network", "interfaces", Status.SUCCESS, "ok")
        routes.return_value = Result("network", "routes", Status.UNSUPPORTED, "no adapter")
        result = network_configuration(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.WARNING)
        self.assertEqual(result.data["routes"]["status"], "unsupported")



class TermuxConnectionStateTests(unittest.TestCase):
    @patch("stellivor.wireless_inspector.run_command")
    def test_disconnected_android_wifi_is_warning_not_success(self, command):
        command.return_value = Result(
            "wireless_inspector", "current_connection", Status.SUCCESS, "command ok",
            data={"stdout": '{"ssid":"<unknown ssid>","ip":"0.0.0.0",'
                  '"frequency_mhz":-1,"supplicant_state":"UNINITIALIZED",'
                  '"mac_address":"02:00:00:00:00:00"}'},
        )
        result = current_connection(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.WARNING)
        self.assertIn("no active Wi-Fi connection", result.summary)
        self.assertNotIn("stdout", result.data)
        self.assertNotIn("mac_address", result.data)
        self.assertEqual(result.data["connection"]["ssid"], "<unknown ssid>")

    @patch("stellivor.wireless_inspector.run_command")
    def test_completed_android_wifi_is_success(self, command):
        command.return_value = Result(
            "wireless_inspector", "current_connection", Status.SUCCESS, "command ok",
            data={"stdout": '{"ssid":"LabNet","ip":"192.0.2.10",'
                  '"frequency_mhz":2412,"supplicant_state":"COMPLETED",'
                  '"mac_address":"02:00:00:00:00:00"}'},
        )
        result = current_connection(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.summary, "Active Wi-Fi connection detected.")
        self.assertEqual(result.data["connection"]["ssid"], "LabNet")
        self.assertNotIn("stdout", result.data)
        self.assertNotIn("mac_address", result.data["connection"])

    @patch("stellivor.wireless_inspector.run_command")
    def test_malformed_android_connection_json_fails_and_is_redacted(self, command):
        command.return_value = Result(
            "wireless_inspector", "current_connection", Status.SUCCESS, "command ok",
            data={"stdout": "not-json"},
        )
        result = current_connection(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.FAILURE)
        self.assertNotIn("stdout", result.data)
        self.assertTrue(result.errors)


if __name__ == "__main__":
    unittest.main()
