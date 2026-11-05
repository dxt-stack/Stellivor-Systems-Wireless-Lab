"""Read-only snapshots of listening TCP sockets."""

from __future__ import annotations

from typing import Any

from .core import PlatformInfo, Result, Status, detect_platform, run_command, utc_now


def _parse_netstat_listeners(output: str, windows: bool) -> list[dict[str, Any]]:
    listeners: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split()
        if windows:
            if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
                listeners.append({"local_endpoint": parts[1], "remote_endpoint": parts[2], "state": parts[3], "pid": parts[4], "raw": line.strip()})
        elif len(parts) >= 6 and parts[0].lower().startswith("tcp") and parts[5].upper() == "LISTEN":
            listeners.append({"local_endpoint": parts[3], "remote_endpoint": parts[4], "state": parts[5], "process": " ".join(parts[6:]) or None, "raw": line.strip()})
    return listeners


def _parse_ss_listeners(output: str) -> list[dict[str, Any]]:
    listeners: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() in ("LISTEN", "TCP"):
            state_index = 0 if parts[0].upper() == "LISTEN" else 1
            if parts[state_index].upper() != "LISTEN" or len(parts) < state_index + 5:
                continue
            local = parts[state_index + 3]
            remote = parts[state_index + 4]
            process = " ".join(parts[state_index + 5:]) or None
            listeners.append({"local_endpoint": local, "remote_endpoint": remote, "state": "LISTEN", "process": process, "raw": line.strip()})
    return listeners


def list_listening_tcp(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    if info.name == "windows":
        result = run_command(["netstat", "-ano", "-p", "tcp"], module="connections", operation="listening_tcp")
        if result.succeeded:
            result.data["listeners"] = _parse_netstat_listeners(result.data.get("stdout", ""), windows=True)
            result.summary = f"Observed {len(result.data['listeners'])} listening TCP socket(s) visible to netstat."
    elif info.name in ("linux", "termux", "android"):
        result = run_command(["ss", "-ltnp"], module="connections", operation="listening_tcp")
        if result.status == Status.DEPENDENCY_MISSING:
            fallback = run_command(["netstat", "-ltnp"], module="connections", operation="listening_tcp")
            fallback.warnings.append("'ss' was unavailable; this result uses the netstat fallback.")
            result = fallback
        if result.succeeded:
            parser = _parse_ss_listeners if result.data["command"][0] == "ss" else _parse_netstat_listeners
            listeners = parser(result.data.get("stdout", "")) if parser == _parse_ss_listeners else parser(result.data.get("stdout", ""), windows=False)
            result.data["listeners"] = listeners
            result.summary = f"Observed {len(listeners)} listening TCP socket(s) visible to the native utility."
    elif info.name == "macos":
        result = run_command(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], module="connections", operation="listening_tcp")
    else:
        return Result("connections", "listening_tcp", Status.UNSUPPORTED, "No listening-socket adapter is available for this platform.", data={"platform": info.label})

    result.data["snapshot_utc"] = utc_now()
    result.data["snapshot"] = True
    result.data["scope"] = "Listening TCP sockets visible to the current user and native utility; not a packet capture or complete activity monitor"
    result.warnings.append("Process details may be incomplete without additional operating-system permissions.")
    return result
