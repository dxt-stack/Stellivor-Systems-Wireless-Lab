"""Real operating-system and Python runtime observations."""

from __future__ import annotations

import os
import json
import platform
import shutil
import socket
import struct
import sys
from pathlib import Path
from typing import Any

from .core import PlatformInfo, Result, Status, detect_platform, run_command


def _uptime_seconds(info: PlatformInfo) -> float | None:
    if info.system.lower() == "Linux":
        try:
            text = Path("/proc/uptime").read_text(encoding="ascii", errors="replace")
            value = float(text.split()[0])
            return round(value, 1) if value >= 0 else None
        except (OSError, ValueError, IndexError):
            return None
    return None


def _memory_snapshot(info: PlatformInfo) -> dict[str, int] | None:
    if info.name not in {"linux", "termux", "android"}:
        return None
    try:
        values: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="ascii", errors="replace").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].rstrip(":") in {"MemTotal", "MemAvailable", "MemFree", "SwapTotal", "SwapFree"}:
                key = parts[0].rstrip(":")
                value = int(parts[1])
                values[key] = value * 1024 if len(parts) >= 3 and parts[2].lower() == "kb" else value
        if "MemTotal" not in values:
            return None
        return {
            "total_bytes": values["MemTotal"],
            "total_mib": round(values["MemTotal"] / (1024 ** 2), 1),
            "available_bytes": values.get("MemAvailable"),
            "available_mib": round(values["MemAvailable"] / (1024 ** 2), 1) if "MemAvailable" in values else None,
            "free_bytes": values.get("MemFree"),
            "swap_total_bytes": values.get("SwapTotal"),
            "swap_free_bytes": values.get("SwapFree"),
        }
    except (OSError, ValueError, IndexError):
        return None


def _storage_snapshot() -> dict[str, int] | None:
    try:
        usage = shutil.disk_usage(Path.home())
        return {
            "total_bytes": usage.total,
            "total_gib": round(usage.total / (1024 ** 3), 1),
            "used_bytes": usage.used,
            "used_gib": round(usage.used / (1024 ** 3), 1),
            "free_bytes": usage.free,
            "free_gib": round(usage.free / (1024 ** 3), 1),
        }
    except OSError:
        return None


def _battery_snapshot(info: PlatformInfo) -> dict[str, Any]:
    if not info.is_termux:
        return {"availability": "not_applicable"}
    result = run_command(
        ["termux-battery-status"],
        module="system",
        operation="termux_battery_status",
        timeout=4.0,
        max_output_bytes=16 * 1024,
    )
    if result.status != Status.SUCCESS:
        return {"availability": result.status.value, "summary": result.summary}
    try:
        raw = json.loads(result.data.get("stdout", ""))
    except (TypeError, json.JSONDecodeError):
        return {"availability": "invalid_response", "summary": "Termux:API returned invalid battery JSON."}
    if not isinstance(raw, dict):
        return {"availability": "invalid_response", "summary": "Termux:API returned an unexpected battery response."}
    permitted = {"percentage", "status", "health", "plugged", "temperature", "current"}
    safe_data = {key: raw[key] for key in permitted if key in raw and isinstance(raw[key], (str, int, float, bool, type(None)))}
    return {"availability": "available", "data": safe_data}


def collect_system_info(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    warnings: list[str] = []
    try:
        hostname = socket.gethostname()
    except OSError as exc:
        hostname = None
        warnings.append(f"Hostname unavailable: {exc}")

    android_release = None
    if info.is_android:
        try:
            android_release = platform.android_ver().release or None
        except (AttributeError, OSError):
            warnings.append("Android release could not be determined through the Python runtime.")

    uptime = _uptime_seconds(info)
    if uptime is None:
        warnings.append("Uptime is unavailable on this runtime or platform; unknown is not zero.")
    memory = _memory_snapshot(info)
    storage = _storage_snapshot()
    battery = _battery_snapshot(info)

    data: dict[str, Any] = {
        "observation_source": "local Python runtime and operating system",
        "platform": info.label,
        "platform_adapter": info.name,
        "operating_system": info.system,
        "os_release": platform.release() or None,
        "os_version": platform.version() or None,
        "machine_architecture": platform.machine() or None,
        "processor": platform.processor() or None,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable or None,
        "pointer_width_bits": struct.calcsize("P") * 8,
        "hostname": hostname,
        "logical_cpu_count": os.cpu_count(),
        "uptime_seconds": uptime,
        "resources": {
            "memory": memory or {"availability": "unavailable"},
            "termux_home_storage": storage or {"availability": "unavailable"},
            "battery": battery,
        },
        "android_release": android_release,
        "termux_version": os.environ.get("TERMUX_VERSION") if info.is_termux else None,
        "capabilities": {
            "system_profile": "available",
            "dns_resolution": "available; network and resolver permitting",
            "single_tcp_check": "available; network and remote service permitting",
            "file_intelligence": "available for readable local files",
            "sdr_simulation": "available without hardware",
            "native_interfaces_routes": "platform utility and permission dependent",
            "wireless": "platform utility, operating-system, and permission dependent",
            "listening_sockets": "platform utility and permission dependent",
            "live_rtl_sdr": "not implemented in this release",
            "adsb_decoding": "not implemented in this release",
        },
    }
    return Result(
        module="system",
        operation="system_profile",
        status=Status.SUCCESS if hostname is not None else Status.WARNING,
        summary="Observed the local operating system and Python runtime.",
        data=data,
        warnings=warnings + ["Reports containing this profile may include a private hostname or local paths."],
    )
