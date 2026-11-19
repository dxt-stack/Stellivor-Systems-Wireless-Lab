"""Non-interactive command interface for scripting and Termux workflows."""
from __future__ import annotations

import argparse
import json

from .connections import list_listening_tcp
from .core import Result, Status
from .device import device_readiness
from .file_intel import inspect_file, verify_sha256
from .network import interface_information, resolve_dns, route_information
from .reports import save_report
from .sdr import simulate_tone
from .system_info import collect_system_info
from .tools import discover_tools
from .wireless import wireless_snapshot
from .wireless_inspector import (
    current_connection, inspect_saved_profile, network_configuration,
    nearby_networks, refresh_wireless_information, saved_profile_names,
)


def _print_result(result: Result, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"[{result.status.value.upper()}] {result.module} / {result.operation}")
        print(result.summary)
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
        if result.data:
            print(json.dumps(result.to_dict()["data"], indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result.status in (Status.SUCCESS, Status.SIMULATION, Status.WARNING) else 2


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit one machine-readable JSON result.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stellivor", description="STELLIVOR real local diagnostics and defensive learning workbench")
    parser.add_argument("--json", action="store_true", help="Emit JSON for the selected command.")
    sub = parser.add_subparsers(dest="domain")

    system = sub.add_parser("system", help="Inspect the local system")
    _add_json(system)
    system.add_argument("action", choices=("profile",), nargs="?", default="profile")

    network = sub.add_parser("network", help="Run one selected network diagnostic")
    _add_json(network)
    network.add_argument("action", choices=("interfaces", "routes", "dns"))
    network.add_argument("hostname", nargs="?", help="Hostname for the dns action")

    device = sub.add_parser("device", help="Inspect authorized Android/ADB readiness")
    _add_json(device)
    device.add_argument("action", choices=("inventory", "readiness"), nargs="?", default="readiness")

    file_parser = sub.add_parser("file", help="Read-only local file intelligence")
    _add_json(file_parser)
    file_parser.add_argument("action", choices=("inspect",))
    file_parser.add_argument("path")

    integrity = sub.add_parser("integrity", help="Hash and verify local files")
    _add_json(integrity)
    integrity.add_argument("action", choices=("verify",))
    integrity.add_argument("path")
    integrity.add_argument("digest")

    sdr = sub.add_parser("sdr", help="Run explicitly synthetic signal analysis")
    _add_json(sdr)
    sdr.add_argument("action", choices=("simulate",))
    sdr.add_argument("--frequency", type=float, default=1000.0)
    sdr.add_argument("--sample-rate", type=float, default=48000.0)
    sdr.add_argument("--count", type=int, default=1024)
    sdr.add_argument("--noise", type=float, default=0.0)
    sdr.add_argument("--seed", type=int, default=0)

    for name, help_text in (("wireless", "Read-only wireless capability snapshot"), ("connections", "List local listening TCP sockets"), ("tools", "Check optional executable presence")):
        command = sub.add_parser(name, help=help_text)
        _add_json(command)
        command.add_argument("action", choices=("snapshot",), nargs="?", default="snapshot")

    wifi = sub.add_parser("wifi", help="Wi-Fi Inspector: read-only wireless and adapter workflows")
    _add_json(wifi)
    wifi.add_argument("action", choices=("profiles", "profile", "nearby", "connection", "adapters", "refresh"))
    wifi.add_argument("profile_name", nargs="?", help="Saved profile name for the profile action")
    return parser


def execute(arguments: argparse.Namespace) -> Result | None:
    domain = arguments.domain
    if domain == "system":
        return collect_system_info()
    if domain == "network":
        if arguments.action == "interfaces":
            return interface_information()
        if arguments.action == "routes":
            return route_information()
        if not arguments.hostname:
            return Result("cli", "dns", Status.FAILURE, "A hostname is required for a DNS lookup.", errors=["Use: stellivor network dns example.com"])
        return resolve_dns(arguments.hostname)
    if domain == "device":
        return device_readiness()
    if domain == "file":
        return inspect_file(arguments.path)
    if domain == "integrity":
        return verify_sha256(arguments.path, arguments.digest)
    if domain == "sdr":
        return simulate_tone(arguments.frequency, arguments.sample_rate, arguments.count, noise_stddev=arguments.noise, seed=arguments.seed)
    if domain == "wireless":
        return wireless_snapshot()
    if domain == "wifi":
        if arguments.action == "profiles":
            return saved_profile_names()
        if arguments.action == "profile":
            if not arguments.profile_name:
                return Result("cli", "wifi_profile", Status.FAILURE,
                              "A saved profile name is required.",
                              errors=["A saved profile name must be supplied."])
            return inspect_saved_profile(arguments.profile_name)
        if arguments.action == "nearby":
            return nearby_networks()
        if arguments.action == "connection":
            return current_connection()
        if arguments.action == "adapters":
            return network_configuration()
        return refresh_wireless_information()
    if domain == "connections":
        return list_listening_tcp()
    if domain == "tools":
        return discover_tools()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.domain is None:
        parser.print_help()
        return 0
    as_json = bool(arguments.json)
    return _print_result(execute(arguments), as_json)  # type: ignore[arg-type]


if __name__ == "__main__":
    raise SystemExit(main())
