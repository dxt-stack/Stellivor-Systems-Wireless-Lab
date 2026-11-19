"""Expanded, read-only Wi-Fi and network inspection adapters.

This module reuses the source Wi-Fi Inspector's useful inspection workflows
inside STELLIVOR's Result/status architecture. It never requests Wi-Fi keys.
"""
from __future__ import annotations

import re
from typing import Any

from .core import PlatformInfo, Result, Status, detect_platform, run_command
from .wireless import wireless_snapshot


def _result(module: str, operation: str, status: Status, summary: str,
            data: dict[str, Any] | None = None, errors: list[str] | None = None,
            warnings: list[str] | None = None) -> Result:
    return Result(module, operation, status, summary, data or {}, errors or [], warnings or [])


def saved_profile_names(info: PlatformInfo | None = None) -> Result:
    """List saved Wi-Fi profile names only; never request key material."""
    info = info or detect_platform()
    if info.name == "windows":
        result = run_command(["netsh", "wlan", "show", "profiles"],
                             module="wireless_inspector", operation="saved_profiles", timeout=12)
        if result.succeeded:
            names = []
            for line in result.data.get("stdout", "").splitlines():
                match = re.match(r"\\s*(?:All User Profile|User Profile)\\s*:\\s*(.*?)\\s*$",
                                 line, re.IGNORECASE)
                if match and match.group(1).strip():
                    names.append(match.group(1).strip())
            result.data["profiles"] = list(dict.fromkeys(names))
            result.data["count"] = len(result.data["profiles"])
            result.data["key_material_requested"] = False
            result.warnings.append("Only saved profile names are listed. Wi-Fi keys are never requested.")
            return result
        return result
    if info.name == "linux":
        result = run_command(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                             module="wireless_inspector", operation="saved_profiles", timeout=12)
        if result.succeeded:
            profiles = []
            for line in result.data.get("stdout", "").splitlines():
                fields = line.split(":")
                if len(fields) >= 2 and fields[-1] == "802-11-wireless":
                    profiles.append(":".join(fields[:-1]))
            result.data.update(profiles=profiles, count=len(profiles), key_material_requested=False)
            result.warnings.append("Only NetworkManager profile names are listed; no secrets are requested.")
        return result
    if info.name in {"termux", "android"}:
        return _result("wireless_inspector", "saved_profiles", Status.UNSUPPORTED,
                       "Android does not expose other applications' saved Wi-Fi profiles to this adapter.",
                       {"platform": info.label, "key_material_requested": False})
    return _result("wireless_inspector", "saved_profiles", Status.UNSUPPORTED,
                   "Saved Wi-Fi profile listing is unsupported on this platform.",
                   {"platform": info.label, "key_material_requested": False})


def inspect_saved_profile(profile: str, info: PlatformInfo | None = None) -> Result:
    """Inspect non-secret metadata for one named profile."""
    info = info or detect_platform()
    name = profile.strip()
    if not name or len(name) > 128 or any(ord(c) < 32 for c in name):
        return _result("wireless_inspector", "profile_inspection", Status.FAILURE,
                       "A valid profile name is required.", errors=["Profile name is empty or invalid."])
    if info.name == "windows":
        # Deliberately omit key=clear: the command returns profile metadata only.
        return run_command(["netsh", "wlan", "show", "profile", f"name={name}"],
                           module="wireless_inspector", operation="profile_inspection", timeout=12)
    if info.name == "linux":
        return run_command(["nmcli", "-f", "NAME,UUID,TYPE,AUTOCONNECT", "connection", "show", name],
                           module="wireless_inspector", operation="profile_inspection", timeout=12)
    return _result("wireless_inspector", "profile_inspection", Status.UNSUPPORTED,
                   "This platform does not expose saved-profile metadata through the current adapter.",
                   {"platform": info.label, "profile": name, "key_material_requested": False})


def nearby_networks(info: PlatformInfo | None = None) -> Result:
    """Return the shared platform-aware scan; actual status is retained per section."""
    return wireless_snapshot(info)


def _termux_connection_is_active(payload: dict[str, Any]) -> bool:
    """Recognize an active Wi-Fi association without trusting command exit status alone."""
    state = str(payload.get("supplicant_state", "")).strip().upper()
    if state == "COMPLETED":
        return True

    ssid = str(payload.get("ssid", "")).strip()
    unknown_ssids = {"", "<unknown ssid>", "<unknown>", "unknown", "0x"}
    try:
        frequency = int(payload.get("frequency_mhz", -1))
    except (TypeError, ValueError):
        frequency = -1
    return ssid.lower() not in unknown_ssids and frequency > 0


def current_connection(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    if info.name == "windows":
        return run_command(["netsh", "wlan", "show", "interfaces"],
                           module="wireless_inspector", operation="current_connection", timeout=12)
    if info.name == "linux":
        return run_command(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
                           module="wireless_inspector", operation="current_connection", timeout=12)
    if info.name == "termux":
        result = run_command(["termux-wifi-connectioninfo"], module="wireless_inspector",
                             operation="current_connection", timeout=12)
        if result.succeeded:
            import json
            try:
                payload = json.loads(result.data.get("stdout", ""))
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object.")
                allowed = {"ssid", "bssid", "ip", "frequency_mhz", "link_speed_mbps",
                           "rssi", "network_id", "supplicant_state"}
                result.data["connection"] = {k: v for k, v in payload.items() if k in allowed}
                if _termux_connection_is_active(payload):
                    result.summary = "Active Wi-Fi connection detected."
                else:
                    result.status = Status.WARNING
                    result.summary = "The command succeeded, but Android reports no active Wi-Fi connection."
                    result.warnings.append(
                        "No active Wi-Fi association was detected; connection fields contain unavailable-value markers."
                    )
            except (ValueError, json.JSONDecodeError) as exc:
                result.status = Status.FAILURE
                result.summary = "Could not interpret the Termux:API connection response."
                result.errors.append(f"Could not parse Termux:API response: {exc}")
            finally:
                # The raw response can include device MAC addresses. Keep only
                # the explicit allow-listed connection fields in serialized output.
                result.data.pop("stdout", None)
        result.warnings.append("Requires Termux:API and Android permissions; sensitive fields are filtered.")
        return result
    return _result("wireless_inspector", "current_connection", Status.UNSUPPORTED,
                   "Current Wi-Fi connection details are unsupported on this platform.",
                   {"platform": info.label})


def network_configuration(info: PlatformInfo | None = None) -> Result:
    """Collect interface and route snapshots without changing network state."""
    from .network import interface_information, route_information
    info = info or detect_platform()
    interfaces = interface_information(info)
    routes = route_information(info)
    status = (Status.SUCCESS if interfaces.succeeded and routes.succeeded else
              Status.WARNING if interfaces.succeeded or routes.succeeded else
              Status.UNSUPPORTED if interfaces.status == routes.status == Status.UNSUPPORTED else Status.FAILURE)
    return _result("wireless_inspector", "network_configuration", status,
                   "Network adapter and route inspection completed; review each section's status.",
                   {"platform": info.label, "read_only": True,
                    "interfaces": interfaces.to_dict(), "routes": routes.to_dict()},
                   interfaces.errors + routes.errors,
                   ["Inspection only: no adapter, address, or route configuration was changed."])


def refresh_wireless_information(info: PlatformInfo | None = None) -> Result:
    """Refresh saved-profile, nearby-network, and active-connection observations."""
    info = info or detect_platform()
    profiles = saved_profile_names(info)
    nearby = nearby_networks(info)
    active = current_connection(info)
    usable = {Status.SUCCESS, Status.SIMULATION, Status.WARNING}
    successes = sum(item.status in usable for item in (profiles, nearby, active))
    status = Status.SUCCESS if successes == 3 else Status.WARNING if successes else Status.FAILURE
    return _result("wireless_inspector", "refresh", status,
                   f"Refresh completed: {successes}/3 sections returned usable data.",
                   {"platform": info.label, "saved_profiles": profiles.to_dict(),
                    "nearby_networks": nearby.to_dict(), "current_connection": active.to_dict()},
                   profiles.errors + nearby.errors + active.errors,
                   ["Wireless results depend on OS, hardware, permissions, and installed utilities."])
