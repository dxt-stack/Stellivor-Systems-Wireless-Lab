"""Optional executable discovery. Presence is not a hardware/functionality test."""

from __future__ import annotations

import shutil
from typing import Any

from .core import PlatformInfo, Result, Status, detect_platform


TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"name": "ip", "executables": ("ip",), "purpose": "Linux interfaces and routes", "platforms": ("linux", "termux"), "requirements": "iproute2; Android may restrict results", "hardware": False},
    {"name": "ss", "executables": ("ss",), "purpose": "Linux socket snapshots", "platforms": ("linux", "termux"), "requirements": "iproute2; process details may need privileges", "hardware": False},
    {"name": "netstat", "executables": ("netstat",), "purpose": "Socket and route fallback", "platforms": ("linux", "termux", "macos", "windows"), "requirements": "Platform net-tools or native utility", "hardware": False},
    {"name": "nmcli", "executables": ("nmcli",), "purpose": "NetworkManager wireless visibility", "platforms": ("linux",), "requirements": "NetworkManager and permission to query it", "hardware": False},
    {"name": "iw", "executables": ("iw",), "purpose": "Linux wireless interface information", "platforms": ("linux",), "requirements": "Wireless drivers; some operations require privileges", "hardware": False},
    {"name": "netsh", "executables": ("netsh",), "purpose": "Windows native WLAN and network information", "platforms": ("windows",), "requirements": "Windows WLAN service and applicable permissions", "hardware": False},
    {"name": "lsof", "executables": ("lsof",), "purpose": "macOS listening-socket inspection", "platforms": ("macos", "linux"), "requirements": "OS visibility and permissions", "hardware": False},
    {"name": "Termux:API Wi-Fi scan", "executables": ("termux-wifi-scaninfo",), "purpose": "Android Wi-Fi scan where permitted", "platforms": ("termux",), "requirements": "Termux:API app and package, Android permissions, compatible device", "hardware": False},
    {"name": "Termux:API connection info", "executables": ("termux-wifi-connectioninfo",), "purpose": "Current Android Wi-Fi connection where permitted", "platforms": ("termux",), "requirements": "Termux:API app and package plus Android permissions", "hardware": False},
    {"name": "rtl_test", "executables": ("rtl_test",), "purpose": "Future RTL-SDR device testing", "platforms": ("linux", "termux", "macos", "windows"), "requirements": "RTL-SDR drivers/libraries and compatible USB hardware; not integrated in v0.5.3", "hardware": True},
    {"name": "rtl_fm", "executables": ("rtl_fm",), "purpose": "Future RTL-SDR reception integration", "platforms": ("linux", "termux", "macos", "windows"), "requirements": "RTL-SDR drivers/libraries and compatible USB hardware; not integrated in v0.5.3", "hardware": True},
    {"name": "GNU Radio Companion", "executables": ("gnuradio-companion",), "purpose": "External signal-processing flowgraphs", "platforms": ("linux", "macos", "windows"), "requirements": "Large optional installation; not required by STELLIVOR", "hardware": False},
    {"name": "dump1090", "executables": ("dump1090", "dump1090-mutability"), "purpose": "Future ADS-B sample/live decoding", "platforms": ("linux", "macos", "windows"), "requirements": "Valid samples or supported receiver; not integrated in v0.5.3", "hardware": True},
    {"name": "readsb", "executables": ("readsb",), "purpose": "Future ADS-B decoding integration", "platforms": ("linux",), "requirements": "Valid input or supported receiver; not integrated in v0.5.3", "hardware": True},
)


def discover_tools(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    entries: list[dict[str, Any]] = []
    found_count = 0
    for definition in TOOL_DEFINITIONS:
        detected_path = None
        detected_executable = None
        for executable in definition["executables"]:
            path = shutil.which(executable)
            if path:
                detected_path = path
                detected_executable = executable
                break
        if detected_path:
            found_count += 1
        entries.append({
            "name": definition["name"],
            "purpose": definition["purpose"],
            "executable_present": detected_path is not None,
            "detected_executable": detected_executable,
            "executable_path": detected_path,
            "supported_platforms": list(definition["platforms"]),
            "relevant_to_current_platform": info.name in definition["platforms"],
            "requirements": definition["requirements"],
            "requires_special_hardware": definition["hardware"],
            "functionality_verified": False,
            "hardware_verified": False,
        })
    return Result(
        "tools",
        "optional_tool_catalog",
        Status.SUCCESS,
        f"Checked {len(entries)} catalog entries; found {found_count} executable(s).",
        data={"platform": info.label, "tools": entries, "installation_attempted": False, "note": "Executable presence alone does not prove that the tool works or that compatible hardware is connected."},
    )
