"""Read-only, capability-aware wireless adapters. Never requests Wi-Fi keys."""

from __future__ import annotations

import json
import shutil
from typing import Any

from .core import PlatformInfo, Result, Status, aggregate_status, detect_platform, run_command, utc_now


def _split_nmcli(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    fields.append("".join(current))
    return fields


def _parse_nmcli_networks(output: str) -> list[dict[str, Any]]:
    networks: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = _split_nmcli(line)
        fields += [""] * (7 - len(fields))
        networks.append({
            "in_use": fields[0] == "*",
            "ssid": fields[1],
            "hidden_ssid": fields[1] == "",
            "bssid": fields[2] or None,
            "channel": fields[3] or None,
            "frequency": fields[4] or None,
            "signal": fields[5] or None,
            "security": fields[6] or None,
        })
    return networks


def _parse_windows_profiles(output: str) -> list[str]:
    profiles: list[str] = []
    for line in output.splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        if "all user profile" in label.lower() and value.strip():
            profiles.append(value.strip())
    return profiles


def _parse_json_section(result: Result, expected_type: type) -> None:
    if not result.succeeded:
        return
    try:
        payload = json.loads(result.data.get("stdout", ""))
        if not isinstance(payload, expected_type):
            raise ValueError(f"Expected {expected_type.__name__} JSON output.")
        result.data["parsed"] = payload
    except (json.JSONDecodeError, ValueError) as exc:
        result.status = Status.FAILURE
        result.summary = "Wireless utility returned output that could not be parsed."
        result.errors.append(str(exc))


def _unsupported(info: PlatformInfo, detail: str) -> Result:
    return Result("wireless", "wireless_snapshot", Status.UNSUPPORTED, detail, data={"platform": info.label, "read_only": True, "passwords_extracted": False})


def wireless_snapshot(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    sections: dict[str, Result] = {}
    if info.name == "windows":
        sections["current_connection"] = run_command(["netsh", "wlan", "show", "interfaces"], module="wireless", operation="current_connection", timeout=12)
        sections["nearby_networks"] = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"], module="wireless", operation="nearby_networks", timeout=15)
        profiles = run_command(["netsh", "wlan", "show", "profiles"], module="wireless", operation="saved_profile_names", timeout=10)
        if profiles.succeeded:
            profiles.data["profile_names"] = _parse_windows_profiles(profiles.data.get("stdout", ""))
            profiles.warnings.append("Only profile names are requested. Localized netsh labels may require raw output for parsing; no keys are requested.")
        sections["saved_profile_names"] = profiles
    elif info.name == "linux":
        nearby = run_command(["nmcli", "-t", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes"], module="wireless", operation="nearby_networks", timeout=18)
        if nearby.succeeded:
            nearby.data["networks"] = _parse_nmcli_networks(nearby.data.get("stdout", ""))
            nearby.summary = f"NetworkManager returned {len(nearby.data['networks'])} nearby network record(s)."
        sections["nearby_networks"] = nearby
        sections["active_connections"] = run_command(["nmcli", "-t", "-f", "NAME,UUID,TYPE,DEVICE", "connection", "show", "--active"], module="wireless", operation="active_connections")
        saved = run_command(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], module="wireless", operation="saved_profile_names")
        if saved.succeeded:
            saved.data["wifi_profile_names"] = [_split_nmcli(line)[0] for line in saved.data.get("stdout", "").splitlines() if len(_split_nmcli(line)) >= 2 and _split_nmcli(line)[1] == "802-11-wireless"]
            saved.warnings.append("Only NetworkManager profile names are returned; no password or key material is requested.")
        sections["saved_profile_names"] = saved
        if shutil.which("iw"):
            sections["wireless_interfaces"] = run_command(["iw", "dev"], module="wireless", operation="wireless_interfaces")
    elif info.name == "termux":
        scan = run_command(["termux-wifi-scaninfo"], module="wireless", operation="nearby_networks", timeout=18)
        _parse_json_section(scan, list)
        scan.warnings.append("Requires the Termux:API app and package, plus Android permissions. A successful empty list is different from a failed scan.")
        sections["nearby_networks"] = scan
        current = run_command(["termux-wifi-connectioninfo"], module="wireless", operation="current_connection", timeout=10)
        _parse_json_section(current, dict)
        sections["current_connection"] = current
        sections["saved_profile_names"] = Result("wireless", "saved_profile_names", Status.UNSUPPORTED, "Android does not expose other applications' saved Wi-Fi profiles to this adapter.", data={"passwords_extracted": False})
    elif info.name == "android":
        return _unsupported(info, "Android wireless access requires a supported integration such as Termux:API; no scan was performed.")
    elif info.name == "macos":
        sections["wireless_information"] = run_command(["system_profiler", "SPAirPortDataType"], module="wireless", operation="wireless_information", timeout=20)
        sections["hardware_ports"] = run_command(["networksetup", "-listallhardwareports"], module="wireless", operation="hardware_ports")
    else:
        return _unsupported(info, "No wireless adapter is available for this platform.")

    status = aggregate_status(sections.values())
    errors = [f"{name}: {error}" for name, result in sections.items() for error in result.errors]
    warnings = ["Wireless visibility depends on the OS, permissions, hardware, and installed utilities.", "No Wi-Fi passwords or key material were requested or extracted."]
    return Result(
        "wireless",
        "wireless_snapshot",
        status,
        "Wireless snapshot finished; inspect each section for its actual capability status.",
        data={"platform": info.label, "snapshot_utc": utc_now(), "read_only": True, "passwords_extracted": False, "sections": {name: result.to_dict() for name, result in sections.items()}},
        errors=errors,
        warnings=warnings,
    )
