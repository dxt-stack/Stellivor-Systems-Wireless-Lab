"""Authorized device readiness and inventory checks.

This module only observes devices already visible to the local ADB client. It
never unlocks a device, guesses credentials, runs an arbitrary remote shell,
installs an APK, captures data, or changes device state.
"""
from __future__ import annotations

import re
from typing import Any

from .core import Result, Status, run_command

_DEVICE_LINE = re.compile(r"^(?P<serial>\S+)\s+(?P<state>\S+)(?:\s+(?P<details>.*))?$")


def _parse_devices(stdout: str) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("List of devices attached") or line.startswith("*"):
            continue
        match = _DEVICE_LINE.match(line)
        if not match:
            continue
        details: dict[str, str] = {}
        for token in (match.group("details") or "").split():
            if ":" in token:
                key, value = token.split(":", 1)
                details[key] = value
        devices.append({"serial": match.group("serial"), "state": match.group("state"), "details": details})
    return devices


def _with_device_summary(result: Result, *, adb_found: bool, scrcpy_found: bool) -> Result:
    data = dict(result.data)
    data["adb_found"] = adb_found
    data["scrcpy_found"] = scrcpy_found
    data["authorized_operations_only"] = True
    data["unsupported_operations"] = [
        "lockscreen_bypass",
        "pin_bruteforce",
        "credential_extraction",
        "payload_or_backdoor_installation",
        "covert_camera_or_ip_logging",
    ]
    result.data = data
    return result


def device_readiness() -> Result:
    """Return real local ADB readiness and visible device states."""
    adb_probe = run_command(["adb", "version"], module="device", operation="adb_version", timeout=4.0, max_output_bytes=16 * 1024)
    scrcpy_probe = run_command(["scrcpy", "--version"], module="device", operation="scrcpy_version", timeout=4.0, max_output_bytes=16 * 1024)
    adb_found = adb_probe.status != Status.DEPENDENCY_MISSING
    scrcpy_found = scrcpy_probe.status != Status.DEPENDENCY_MISSING
    if not adb_found:
        return _with_device_summary(Result(
            "device", "authorized_device_readiness", Status.DEPENDENCY_MISSING,
            "ADB is not installed or not available on PATH; no device inventory was attempted.",
            data={"devices": [], "adb": adb_probe.to_dict(), "scrcpy": scrcpy_probe.to_dict()},
            warnings=["Install Android platform-tools separately if you need authorized ADB diagnostics. STELLIVOR does not install packages automatically."],
        ), adb_found=False, scrcpy_found=scrcpy_found)

    listing = run_command(["adb", "devices", "-l"], module="device", operation="adb_devices", timeout=6.0, max_output_bytes=64 * 1024)
    if listing.status != Status.SUCCESS:
        return _with_device_summary(Result(
            "device", "authorized_device_readiness", listing.status,
            "ADB is present, but the connected-device inventory could not be read.",
            data={"devices": [], "adb": adb_probe.to_dict(), "scrcpy": scrcpy_probe.to_dict(), "inventory": listing.to_dict()},
            errors=list(listing.errors), warnings=list(listing.warnings),
        ), adb_found=adb_found, scrcpy_found=scrcpy_found)

    devices = _parse_devices(listing.data.get("stdout", ""))
    authorized = [device for device in devices if device["state"] == "device"]
    pending = [device for device in devices if device["state"] in {"unauthorized", "authorizing"}]
    if authorized:
        status = Status.SUCCESS
        summary = f"ADB is ready with {len(authorized)} authorized device(s) visible to this host."
    elif pending:
        status = Status.PERMISSION_RESTRICTED
        summary = "ADB is installed, but a device is waiting for authorization on its screen."
    else:
        status = Status.WARNING
        summary = "ADB is installed, but no authorized device is currently connected."
    warnings = [
        "Inventory is read-only and limited to devices already exposed by the local ADB client.",
        "An ADB connection does not authorize bypassing authentication or accessing data without the owner's permission.",
    ]
    if not scrcpy_found:
        warnings.append("scrcpy is not available; STELLIVOR does not install or launch it automatically.")
    return _with_device_summary(Result(
        "device", "authorized_device_readiness", status, summary,
        data={
            "devices": devices,
            "authorized_device_count": len(authorized),
            "pending_authorization_count": len(pending),
            "adb_version": adb_probe.data.get("stdout", "").strip(),
            "scrcpy_version": scrcpy_probe.data.get("stdout", "").strip() if scrcpy_found else None,
            "adb": adb_probe.to_dict(),
            "scrcpy": scrcpy_probe.to_dict(),
        }, warnings=warnings,
    ), adb_found=adb_found, scrcpy_found=scrcpy_found)
