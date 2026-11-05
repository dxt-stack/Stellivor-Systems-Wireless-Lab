"""User-initiated DNS, single-endpoint TCP, interface, and route diagnostics."""

from __future__ import annotations

import ipaddress
import json
import math
import queue
import re
import socket
import threading
import time
from typing import Any

from .core import PlatformInfo, Result, Status, aggregate_status, detect_platform, run_command, utc_now

_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def validate_hostname(hostname: str) -> str:
    if not isinstance(hostname, str):
        raise ValueError("Hostname must be text.")
    host = hostname.strip()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if not host or len(host) > 253 or any(char.isspace() for char in host):
        raise ValueError("Enter a hostname or IP address without spaces, a URL scheme, path, or port.")
    if any(char in host for char in "/\\@"):
        raise ValueError("Enter only a hostname or IP address, not a URL or path.")
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if ":" in host:
        raise ValueError("Invalid IP address or hostname.")
    absolute = host.endswith(".")
    candidate = host[:-1] if absolute else host
    try:
        ascii_host = candidate.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(f"Hostname cannot be converted to IDNA: {exc}") from exc
    labels = ascii_host.split(".")
    if not ascii_host or len(ascii_host) > 253 or any(not _LABEL.fullmatch(label) for label in labels):
        raise ValueError("Hostname labels must contain 1-63 letters, digits, or interior hyphens.")
    return ascii_host + ("." if absolute else "")


def _getaddrinfo(host: str, port: int | None, timeout: float) -> list[tuple[Any, ...]]:
    """Bound the caller's wait even on platforms without DNS timeout controls."""
    responses: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            responses.put((True, socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
        except BaseException as exc:  # returned to the caller; daemon must not print
            responses.put((False, exc))

    worker = threading.Thread(target=resolve, name="stellivor-dns", daemon=True)
    worker.start()
    try:
        success, value = responses.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError(f"Name resolution did not finish within {timeout:g} seconds.") from exc
    if success:
        return value
    raise value


def resolve_dns(hostname: str, *, timeout: float = 5.0) -> Result:
    try:
        host = validate_hostname(hostname)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(float(timeout)) or not 0.1 <= float(timeout) <= 15.0:
            raise ValueError("DNS timeout must be between 0.1 and 15 seconds.")
        records = _getaddrinfo(host, None, float(timeout))
    except (ValueError, TimeoutError, OSError) as exc:
        return Result("network", "dns_resolution", Status.FAILURE, f"Could not resolve '{hostname}'.", errors=[f"{type(exc).__name__}: {exc}"], data={"hostname": hostname, "resolved": False})

    addresses: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for family, _type, _proto, _canonical, sockaddr in records:
        family_name = "IPv6" if family == socket.AF_INET6 else "IPv4" if family == socket.AF_INET else str(family)
        address = sockaddr[0]
        key = (family_name, address)
        if key not in seen:
            seen.add(key)
            addresses.append({"family": family_name, "address": address})
    if not addresses:
        return Result("network", "dns_resolution", Status.FAILURE, f"Resolver returned no addresses for '{host}'.", data={"hostname": host, "resolved": False, "addresses": []})
    return Result(
        "network",
        "dns_resolution",
        Status.SUCCESS,
        f"Resolved '{host}' to {len(addresses)} unique address(es).",
        data={"hostname": host, "resolved": True, "addresses": addresses, "note": "DNS success does not guarantee application or TCP connectivity."},
    )


def check_tcp(hostname: str, port: int, *, timeout: float = 3.0) -> Result:
    try:
        host = validate_hostname(hostname)
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("TCP port must be an integer between 1 and 65535.")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(float(timeout)) or not 0.1 <= float(timeout) <= 15.0:
            raise ValueError("TCP timeout must be between 0.1 and 15 seconds.")
        records = _getaddrinfo(host, port, float(timeout))
        if not records:
            raise OSError("Resolver returned no usable TCP addresses.")
        family, socktype, proto, _canonical, sockaddr = records[0]
        selected_address = sockaddr[0]
    except (ValueError, TimeoutError, OSError) as exc:
        return Result("network", "single_tcp_check", Status.FAILURE, "TCP check could not be started.", errors=[f"{type(exc).__name__}: {exc}"], data={"hostname": hostname, "port": port, "connected": False, "connection_attempts": 0})

    started = time.monotonic()
    connection = None
    attempts = 0
    try:
        connection = socket.socket(family, socktype, proto)
        connection.settimeout(float(timeout))
        attempts = 1
        connection.connect(sockaddr)
        elapsed = round(time.monotonic() - started, 3)
        local = connection.getsockname()
        return Result(
            "network",
            "single_tcp_check",
            Status.SUCCESS,
            f"TCP connection to {host}:{port} succeeded.",
            data={
                "hostname": host,
                "port": port,
                "selected_address": selected_address,
                "local_endpoint": list(local) if isinstance(local, tuple) else str(local),
                "connected": True,
                "connection_attempts": 1,
                "duration_seconds": elapsed,
                "application_data_sent": False,
                "note": "One endpoint was tested; this was not a port scan or application-protocol test.",
            },
        )
    except (TimeoutError, OSError) as exc:
        return Result(
            "network",
            "single_tcp_check",
            Status.FAILURE,
            f"TCP connection to {host}:{port} failed.",
            errors=[f"{type(exc).__name__}: {exc}"],
            data={"hostname": host, "port": port, "selected_address": selected_address, "connected": False, "connection_attempts": attempts, "duration_seconds": round(time.monotonic() - started, 3), "application_data_sent": False},
        )
    finally:
        if connection is not None:
            connection.close()


def _mark_snapshot(result: Result, scope: str) -> Result:
    result.data["snapshot_utc"] = utc_now()
    result.data["scope"] = scope
    return result


def interface_information(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    if info.name == "windows":
        return _mark_snapshot(run_command(["ipconfig", "/all"], module="network", operation="interface_information"), "Native Windows ipconfig output")
    if info.name in ("linux", "termux", "android"):
        result = run_command(["ip", "-json", "address", "show"], module="network", operation="interface_information")
        if result.succeeded:
            try:
                payload = json.loads(result.data.get("stdout", ""))
                interfaces = []
                for item in payload:
                    interfaces.append({
                        "name": item.get("ifname"),
                        "state": item.get("operstate"),
                        "flags": item.get("flags", []),
                        "mac_address": item.get("address"),
                        "addresses": [{"family": addr.get("family"), "address": addr.get("local"), "prefix_length": addr.get("prefixlen"), "scope": addr.get("scope")} for addr in item.get("addr_info", [])],
                    })
                result.data["interfaces"] = interfaces
                result.summary = f"Observed {len(interfaces)} network interface(s) through 'ip'."
                return _mark_snapshot(result, "Interfaces and addresses visible to the current user")
            except (json.JSONDecodeError, TypeError, AttributeError) as exc:
                result.warnings.append(f"Could not parse JSON interface output: {exc}")
                return _mark_snapshot(result, "Unparsed native 'ip' output")
        if result.status == Status.DEPENDENCY_MISSING:
            return _mark_snapshot(result, "Interface inspection unavailable because the native utility is missing")
        fallback = run_command(["ip", "address", "show"], module="network", operation="interface_information")
        fallback.warnings.append("JSON interface output was unavailable; showing the fallback command result.")
        fallback.data["initial_attempt_error"] = result.errors
        return _mark_snapshot(fallback, "Native ip command output")
    if info.name == "macos":
        return _mark_snapshot(run_command(["ifconfig", "-a"], module="network", operation="interface_information"), "Native macOS ifconfig output")
    return Result("network", "interface_information", Status.UNSUPPORTED, "No interface adapter is available for this platform.", data={"platform": info.label})


def route_information(info: PlatformInfo | None = None) -> Result:
    info = info or detect_platform()
    if info.name == "windows":
        return _mark_snapshot(run_command(["route", "print"], module="network", operation="route_information"), "Native Windows route table")
    if info.name == "macos":
        return _mark_snapshot(run_command(["netstat", "-rn"], module="network", operation="route_information"), "Native macOS route table")
    if info.name in ("linux", "termux", "android"):
        ipv4 = run_command(["ip", "route", "show"], module="network", operation="route_information_ipv4")
        ipv6 = run_command(["ip", "-6", "route", "show"], module="network", operation="route_information_ipv6")
        status = aggregate_status([ipv4, ipv6])
        return Result(
            "network",
            "route_information",
            status,
            "Collected available IPv4 and IPv6 route information.",
            data={"platform": info.label, "snapshot_utc": utc_now(), "sections": {"ipv4": ipv4.to_dict(), "ipv6": ipv6.to_dict()}, "scope": "Routes visible to the current user; not necessarily every network namespace"},
            errors=[f"{section.operation}: {error}" for section in (ipv4, ipv6) for error in section.errors],
        )
    return Result("network", "route_information", Status.UNSUPPORTED, "No route adapter is available for this platform.", data={"platform": info.label})
