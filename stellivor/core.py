"""Shared result types, platform detection, and safe command execution."""

from __future__ import annotations

import math
import os
import platform
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class Status(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    UNSUPPORTED = "unsupported"
    PERMISSION_RESTRICTED = "permission_restricted"
    DEPENDENCY_MISSING = "dependency_missing"
    SIMULATION = "simulation"
    IN_PROGRESS = "in_progress"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def to_primitive(value: Any) -> Any:
    """Convert result data into deterministic JSON-compatible values."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return to_primitive(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_primitive(item) for item in value]
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, bytes):
        return value.hex()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


@dataclass
class Result:
    """A truthful, serializable outcome from one operation."""

    module: str
    operation: str
    status: Status
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now)

    @property
    def succeeded(self) -> bool:
        return self.status in (Status.SUCCESS, Status.SIMULATION)

    def to_dict(self) -> dict[str, Any]:
        return to_primitive(self)


@dataclass(frozen=True)
class PlatformInfo:
    name: str
    system: str
    is_android: bool = False
    is_termux: bool = False

    @property
    def label(self) -> str:
        if self.is_termux:
            return "Android / Termux"
        if self.is_android:
            return "Android"
        return self.system or "Unknown"


def detect_platform(
    environ: Mapping[str, str] | None = None,
    system_name: str | None = None,
) -> PlatformInfo:
    env = os.environ if environ is None else environ
    system = (platform.system() if system_name is None else system_name).strip()
    lowered = system.lower()
    prefix = env.get("PREFIX", "")
    is_termux = bool(env.get("TERMUX_VERSION")) or "com.termux" in prefix
    is_android = is_termux or (
        bool(env.get("ANDROID_ROOT")) and bool(env.get("ANDROID_DATA"))
    )
    if is_termux:
        name = "termux"
    elif is_android:
        name = "android"
    elif lowered == "windows":
        name = "windows"
    elif lowered == "linux":
        name = "linux"
    elif lowered == "darwin":
        name = "macos"
    else:
        name = "unknown"
    return PlatformInfo(name=name, system=system or "Unknown", is_android=is_android, is_termux=is_termux)


def _validate_command(arguments: Sequence[str], timeout: float, max_output_bytes: int) -> None:
    if isinstance(arguments, (str, bytes)) or not arguments or len(arguments) > 64:
        raise ValueError("A command must be an argument array containing between 1 and 64 strings.")
    if any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in arguments):
        raise ValueError("Command arguments must be non-empty strings without NUL bytes.")
    if any(len(arg) > 4096 for arg in arguments):
        raise ValueError("A command argument exceeds the 4096-character limit.")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("Timeout must be numeric.")
    if not math.isfinite(float(timeout)) or not 0.1 <= float(timeout) <= 60.0:
        raise ValueError("Timeout must be between 0.1 and 60 seconds.")
    if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int):
        raise ValueError("Output limit must be an integer.")
    if not 1024 <= max_output_bytes <= 4 * 1024 * 1024:
        raise ValueError("Output limit must be between 1 KiB and 4 MiB.")


def _drain_bounded(stream: Any, limit: int, destination: dict[str, tuple[bytes, bool]], key: str) -> None:
    """Drain a child pipe while retaining no more than ``limit`` bytes.

    The reader continues discarding excess output so a noisy child cannot block
    on a full pipe. Captured output is bounded in memory and never spooled to an
    unbounded temporary file.
    """
    captured = bytearray()
    truncated = False
    try:
        while True:
            chunk = stream.read(64 * 1024)
            if not chunk:
                break
            remaining = limit - len(captured)
            if remaining > 0:
                captured.extend(chunk[:remaining])
            if len(chunk) > remaining:
                truncated = True
    except (OSError, ValueError):
        # The parent may close a pipe if a child process outlives its timeout.
        pass
    finally:
        destination[key] = (bytes(captured), truncated)


def run_command(
    arguments: Sequence[str],
    *,
    module: str,
    operation: str,
    timeout: float = 8.0,
    max_output_bytes: int = 256 * 1024,
) -> Result:
    """Run a fixed argument vector without a shell and with bounded time/output.

    Output is written to temporary files while the process runs, so a noisy
    child cannot grow the application's memory without bound.
    """
    try:
        _validate_command(arguments, timeout, max_output_bytes)
    except ValueError as exc:
        return Result(module, operation, Status.FAILURE, "Invalid command request.", errors=[str(exc)])

    executable = shutil.which(arguments[0])
    if executable is None:
        return Result(
            module,
            operation,
            Status.DEPENDENCY_MISSING,
            f"Required executable '{arguments[0]}' was not found.",
            data={"command": list(arguments), "executable": arguments[0], "found": False},
            errors=[f"Install or expose '{arguments[0]}' on PATH, then try again."],
        )

    command = [executable, *arguments[1:]]
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            bufsize=0,
        )
        assert process.stdout is not None and process.stderr is not None
        captured: dict[str, tuple[bytes, bool]] = {}
        readers = [
            threading.Thread(target=_drain_bounded, args=(process.stdout, max_output_bytes, captured, "stdout"), daemon=True),
            threading.Thread(target=_drain_bounded, args=(process.stderr, max_output_bytes, captured, "stderr"), daemon=True),
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            returncode = process.wait(timeout=float(timeout))
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            returncode = process.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=1.0)
        for stream, reader in ((process.stdout, readers[0]), (process.stderr, readers[1])):
            if reader.is_alive():
                stream.close()
                reader.join(timeout=0.5)
            else:
                stream.close()
        stdout_raw, stdout_truncated = captured.get("stdout", (b"", False))
        stderr_raw, stderr_truncated = captured.get("stderr", (b"", False))
        stdout = stdout_raw.decode("utf-8", errors="replace")
        stderr = stderr_raw.decode("utf-8", errors="replace")
    except PermissionError as exc:
        return Result(
            module,
            operation,
            Status.PERMISSION_RESTRICTED,
            f"Permission prevented execution of '{arguments[0]}'.",
            data={"command": list(arguments), "executable": executable},
            errors=[str(exc)],
        )
    except OSError as exc:
        return Result(
            module,
            operation,
            Status.FAILURE,
            f"Could not execute '{arguments[0]}'.",
            data={"command": list(arguments), "executable": executable},
            errors=[f"{type(exc).__name__}: {exc}"],
        )

    elapsed = round(time.monotonic() - started, 3)
    data = {
        "command": list(arguments),
        "executable": executable,
        "returncode": returncode,
        "duration_seconds": elapsed,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "timed_out": timed_out,
    }
    warnings: list[str] = []
    if stdout_truncated or stderr_truncated:
        warnings.append(f"Command output was truncated to {max_output_bytes} bytes per stream.")
    if timed_out:
        return Result(
            module,
            operation,
            Status.FAILURE,
            f"Command timed out after {float(timeout):g} seconds.",
            data=data,
            errors=["The process was terminated; no successful result is claimed."],
            warnings=warnings,
        )
    if returncode != 0:
        lowered = f"{stdout}\n{stderr}".lower()
        permission_markers = ("permission denied", "operation not permitted", "access is denied", "not permitted")
        status = Status.PERMISSION_RESTRICTED if any(marker in lowered for marker in permission_markers) else Status.FAILURE
        detail = stderr.strip() or stdout.strip() or f"Process exited with status {returncode}."
        return Result(
            module,
            operation,
            status,
            f"Command failed with exit status {returncode}.",
            data=data,
            errors=[detail],
            warnings=warnings,
        )
    return Result(
        module,
        operation,
        Status.SUCCESS,
        "Command completed successfully.",
        data=data,
        warnings=warnings,
    )


def aggregate_status(results: Iterable[Result]) -> Status:
    """Aggregate sections without hiding partial or failed operations."""
    statuses = [result.status for result in results]
    if not statuses:
        return Status.UNSUPPORTED
    good = {Status.SUCCESS, Status.SIMULATION}
    if any(status in good for status in statuses):
        return Status.SUCCESS if all(status in good for status in statuses) else Status.WARNING
    if all(status == Status.UNSUPPORTED for status in statuses):
        return Status.UNSUPPORTED
    if all(status == Status.DEPENDENCY_MISSING for status in statuses):
        return Status.DEPENDENCY_MISSING
    if all(status == Status.PERMISSION_RESTRICTED for status in statuses):
        return Status.PERMISSION_RESTRICTED
    if any(status == Status.PERMISSION_RESTRICTED for status in statuses):
        return Status.PERMISSION_RESTRICTED
    return Status.FAILURE
