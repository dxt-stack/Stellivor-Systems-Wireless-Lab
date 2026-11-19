from contextlib import ExitStack
import io
import json
import re
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from stellivor.connections import list_listening_tcp
from stellivor.core import PlatformInfo, Result, Status
from stellivor.system_info import collect_system_info
from stellivor.tools import discover_tools
from stellivor.ui import StellivorUI
from stellivor.wireless import wireless_snapshot


class SystemAndToolTests(unittest.TestCase):
    def test_system_profile_is_real_runtime_data(self):
        result = collect_system_info()
        self.assertIn(result.status, (Status.SUCCESS, Status.WARNING))
        self.assertEqual(result.data["observation_source"], "local Python runtime and operating system")
        self.assertIsInstance(result.data["python_version"], str)
        self.assertIn("live_rtl_sdr", result.data["capabilities"])
        self.assertIn("resources", result.data)
        self.assertIn("termux_home_storage", result.data["resources"])

    @patch("stellivor.system_info.run_command")
    def test_termux_battery_snapshot_filters_api_response(self, command):
        command.return_value = Result(
            "system", "termux_battery_status", Status.SUCCESS, "test",
            data={"stdout": json.dumps({"percentage": 73, "status": "DISCHARGING", "health": "GOOD", "serial": "must-not-leak"})},
        )
        result = collect_system_info(PlatformInfo("termux", "Linux", True, True))
        battery = result.data["resources"]["battery"]
        self.assertEqual(battery["availability"], "available")
        self.assertEqual(battery["data"], {"percentage": 73, "status": "DISCHARGING", "health": "GOOD"})

    @patch("stellivor.tools.shutil.which")
    def test_tool_discovery_presence_not_verification(self, which):
        which.side_effect = lambda name: "/usr/bin/ip" if name == "ip" else None
        result = discover_tools(PlatformInfo("linux", "Linux"))
        ip_entry = next(item for item in result.data["tools"] if item["name"] == "ip")
        self.assertTrue(ip_entry["executable_present"])
        self.assertFalse(ip_entry["functionality_verified"])
        self.assertFalse(result.data["installation_attempted"])


class AdapterTests(unittest.TestCase):
    def test_unknown_wireless_and_connections(self):
        info = PlatformInfo("unknown", "Plan9")
        self.assertEqual(wireless_snapshot(info).status, Status.UNSUPPORTED)
        self.assertEqual(list_listening_tcp(info).status, Status.UNSUPPORTED)

    @patch("stellivor.wireless.shutil.which", return_value=None)
    @patch("stellivor.wireless.run_command")
    def test_linux_nmcli_parsing_without_real_scan(self, command, _which):
        def fake(arguments, **kwargs):
            outputs = {
                "nearby_networks": r"*:Home:AA\:BB\:CC\:DD\:EE\:FF:36:5180 MHz:80:WPA2",
                "active_connections": "Home:uuid:802-11-wireless:wlan0",
                "saved_profile_names": "Home:802-11-wireless\nOther:vpn",
            }
            operation = kwargs["operation"]
            return Result("wireless", operation, Status.SUCCESS, "test", data={"stdout": outputs[operation]})
        command.side_effect = fake
        result = wireless_snapshot(PlatformInfo("linux", "Linux"))
        self.assertEqual(result.status, Status.SUCCESS)
        nearby = result.data["sections"]["nearby_networks"]
        self.assertEqual(nearby["data"]["networks"][0]["ssid"], "Home")
        self.assertEqual(nearby["data"]["networks"][0]["bssid"], "AA:BB:CC:DD:EE:FF")
        self.assertFalse(result.data["passwords_extracted"])

    @patch("stellivor.wireless.run_command")
    def test_termux_json_scan_is_labeled_real_command_result(self, command):
        def fake(arguments, **kwargs):
            payload = [] if kwargs["operation"] == "nearby_networks" else {"ssid": "test"}
            return Result("wireless", kwargs["operation"], Status.SUCCESS, "test", data={"stdout": json.dumps(payload)})
        command.side_effect = fake
        result = wireless_snapshot(PlatformInfo("termux", "Linux", True, True))
        self.assertEqual(result.status, Status.WARNING)  # saved profiles are explicitly unsupported
        self.assertEqual(result.data["sections"]["nearby_networks"]["data"]["parsed"], [])
        self.assertEqual(result.data["sections"]["saved_profile_names"]["status"], "unsupported")


class UITests(unittest.TestCase):
    def test_menu_exit_without_network_or_tools(self):
        output = io.StringIO()
        ui = StellivorUI(input_fn=lambda _prompt: "0", output=output, use_color=False)
        self.assertEqual(ui.run(), 0)
        self.assertIn("STELLIVOR closed", output.getvalue())
        self.assertEqual(ui.results, [])

    def test_quick_local_audit_is_read_only_and_does_not_probe(self):
        output = io.StringIO()
        ui = StellivorUI(output=output, use_color=False)
        results = {
            "system": Result("system", "profile", Status.SUCCESS, "ok"),
            "interfaces": Result("network", "interfaces", Status.SUCCESS, "ok"),
            "routes": Result("network", "routes", Status.SUCCESS, "ok"),
            "listeners": Result("connections", "listeners", Status.SUCCESS, "ok"),
            "tools": Result("tools", "catalog", Status.SUCCESS, "ok"),
        }
        with ExitStack() as stack:
            system = stack.enter_context(patch("stellivor.ui.collect_system_info", return_value=results["system"]))
            interfaces = stack.enter_context(patch("stellivor.ui.interface_information", return_value=results["interfaces"]))
            routes = stack.enter_context(patch("stellivor.ui.route_information", return_value=results["routes"]))
            listeners = stack.enter_context(patch("stellivor.ui.list_listening_tcp", return_value=results["listeners"]))
            tools = stack.enter_context(patch("stellivor.ui.discover_tools", return_value=results["tools"]))
            dns = stack.enter_context(patch("stellivor.ui.resolve_dns"))
            tcp = stack.enter_context(patch("stellivor.ui.check_tcp"))
            wireless = stack.enter_context(patch("stellivor.ui.wireless_snapshot"))
            ui.quick_local_audit()
        self.assertEqual(len(ui.results), 5)
        for operation in (system, interfaces, routes, listeners, tools):
            operation.assert_called_once()
        dns.assert_not_called()
        tcp.assert_not_called()
        wireless.assert_not_called()
        self.assertIn("No DNS/TCP probing", output.getvalue())

    def test_unknown_selection_keeps_application_alive(self):
        answers = iter(["invalid", "0"])
        output = io.StringIO()
        ui = StellivorUI(input_fn=lambda _prompt: next(answers), output=output, use_color=False)
        self.assertEqual(ui.run(), 0)
        self.assertIn("Unknown selection", output.getvalue())

    def test_branded_responsive_menu_has_no_startup_scan(self):
        output = io.StringIO()
        ui = StellivorUI(input_fn=lambda _prompt: "0", output=output, use_color=False)
        ui.banner()
        ui.menu()
        text = output.getvalue()
        self.assertIn("STELLIVOR", text)
        self.assertIn("STARTUP SCANS  /  NONE", text)
        self.assertIn("Wireless security lab", text)
        self.assertIn("SDR lab  [SIMULATION]", text)
        self.assertIn("Quick local audit  [READ-ONLY]", text)

    def test_ascii_fallback_and_no_tty_animation(self):
        class AsciiBuffer(io.StringIO):
            encoding = "ascii"
        output = AsciiBuffer()
        delays = []
        ui = StellivorUI(input_fn=lambda _prompt: "0", output=output, use_color=False, animate=True, sleep_fn=delays.append)
        self.assertFalse(ui.animate)
        self.assertFalse(ui.live_clock_enabled)
        ui.banner()
        self.assertIn("SYSTEMS", output.getvalue())
        self.assertIn("LOCAL", output.getvalue())
        self.assertEqual(delays, [])
        output.getvalue().encode("ascii")

    def test_termux_style_banner_draws_emblem_and_outline_with_clock_animation(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        output = TtyBuffer()
        ui = StellivorUI(output=output, use_color=True, sleep_fn=lambda _delay: None)
        ui.width = lambda: 44
        ui.banner()
        text = output.getvalue()
        self.assertIn("\033[38;2;", text)
        self.assertIn("╭─╮", text)
        self.assertTrue(any(0x2800 <= ord(char) <= 0x28FF for char in text))
        self.assertNotIn("█", text)
        self.assertNotIn("Opening interface", text)
        self.assertIn("PYTHON  /", text)
        self.assertIn("LOCAL", text)
        plain = re.sub(r"\x1b\[[0-9;]*m", "", text)
        self.assertLessEqual(max(map(len, plain.splitlines())), 44)

    def test_result_lines_are_paced_and_values_use_semantic_colors(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        output = TtyBuffer()
        delays = []
        ui = StellivorUI(output=output, use_color=True, theme="ice", sleep_fn=delays.append)
        ui.print_result(Result("system", "profile", Status.SUCCESS, "Local snapshot ready.", data={"count": 7, "ready": True, "label": "local"}))
        text = output.getvalue()
        self.assertGreater(len(delays), 5)
        self.assertEqual(len(delays), len(text.splitlines()))
        self.assertGreater(sum(delays), 0.8)
        self.assertLessEqual(sum(delays), 4.0)
        self.assertIn("\033[38;2;91;205;255m", text)  # keys
        self.assertIn("\033[38;2;255;222;140m", text)  # numeric values
        self.assertIn("\033[38;2;214;151;255m", text)  # booleans
        self.assertIn("\033[38;2;99;225;185m", text)  # success state

    def test_fast_output_bypasses_tty_pacing(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        delays = []
        ui = StellivorUI(output=TtyBuffer(), use_color=True, pace_results=False, sleep_fn=delays.append)
        ui.print_result(Result("test", "fast", Status.SUCCESS, "Immediate."))
        self.assertEqual(delays, [])

    def test_emblem_colors_are_brighter_and_more_saturated(self):
        source = (80, 30, 30)
        enhanced = StellivorUI._brighten_emblem_color(source)
        self.assertGreater(sum(enhanced), sum(source))
        self.assertGreater(max(enhanced) - min(enhanced), max(source) - min(source))
        self.assertTrue(all(0 <= channel <= 255 for channel in enhanced))

    def test_menu_clock_stays_visible_on_a_narrow_terminal(self):
        zone = timezone(timedelta(hours=1), "WAT")
        ui = StellivorUI(output=io.StringIO(), use_color=False, clock_fn=lambda: datetime(2026, 10, 24, 12, 34, 56, tzinfo=zone))
        ui.width = lambda: 24
        clock_line = ui._menu_clock_line()
        self.assertLessEqual(len(clock_line), 24)
        self.assertIn("12:34:56 WAT UTC+01:00", clock_line)

    def test_menu_clock_is_static_and_preserves_terminal_scrollback(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        output = TtyBuffer()
        ui = StellivorUI(output=output, use_color=False, sleep_fn=lambda _delay: None)
        self.assertTrue(ui.animate)
        self.assertFalse(ui.live_clock_enabled)
        ui.menu()
        text = output.getvalue()
        self.assertIn("Scrollback-safe mode", text)
        self.assertNotIn("\\033[1A", text)
        self.assertNotIn("\\033[s", text)

    def test_menu_input_does_not_start_a_cursor_redraw_thread(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        output = TtyBuffer()
        ui = StellivorUI(input_fn=lambda _prompt: "0", output=output, use_color=False)
        self.assertEqual(ui._menu_input(), "0")
        self.assertNotIn("\\033[1A", output.getvalue())

    def test_theme_presets_are_selectable(self):
        default = StellivorUI(output=io.StringIO(), use_color=True, theme="stellivor")
        ember = StellivorUI(output=io.StringIO(), use_color=True, theme="ember")
        ice = StellivorUI(output=io.StringIO(), use_color=True, theme="ice")
        self.assertEqual(len({default.CYAN, ember.CYAN, ice.CYAN}), 3)
        with self.assertRaises(ValueError):
            StellivorUI(output=io.StringIO(), theme="unknown")

    def test_panel_respects_narrow_terminal_width(self):
        output = io.StringIO()
        ui = StellivorUI(output=output, use_color=False)
        ui.width = lambda: 30
        ui.panel("NARROW SCREEN", ["A long menu description that must wrap instead of overflowing."])
        lines = output.getvalue().splitlines()
        self.assertTrue(lines)
        self.assertTrue(all(len(line) <= 30 for line in lines))

    def test_startup_clock_ticks_with_timezone_and_offset_on_tty(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        zone = timezone(timedelta(hours=1), "WAT")
        values = [datetime(2026, 10, 24, 12, 34, 56, tzinfo=zone)] * 5
        values.append(datetime(2026, 10, 24, 12, 34, 57, tzinfo=zone))
        output = TtyBuffer()
        delays = []
        ui = StellivorUI(
            output=output, use_color=False, animate=True, clock_fn=lambda: values.pop(0),
            sleep_fn=delays.append,
        )
        ui.banner()
        text = output.getvalue()
        self.assertEqual(len(delays), 6)
        self.assertIn("12:34:56.0  WAT  /  UTC+01:00", text)
        self.assertIn("12:34:57.0  WAT  /  UTC+01:00", text)
        self.assertIn("choose an operation", text)

    def test_valid_operation_shows_brief_dragon_transition(self):
        class TtyBuffer(io.StringIO):
            def isatty(self):
                return True
        output = TtyBuffer()
        delays = []
        ui = StellivorUI(output=output, use_color=False, pace_results=False, sleep_fn=delays.append)
        snapshot = Result("system", "profile", Status.SUCCESS, "Mock profile.")
        with patch("stellivor.ui.collect_system_info", return_value=snapshot):
            ui.dispatch("1")
        text = output.getvalue()
        self.assertEqual(len(delays), 4)
        self.assertIn("SYSTEM PROFILE", text)
        self.assertIn("🐉", text)
        self.assertLess(text.index("SYS"), text.index("SYSTEM PROFILE"))
        self.assertLess(text.index("SYSTEM PROFILE"), text.index("Mock profile."))
        self.assertLessEqual(sum(delays), 0.2)


if __name__ == "__main__":
    unittest.main()
