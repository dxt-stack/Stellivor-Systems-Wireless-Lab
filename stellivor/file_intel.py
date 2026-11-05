"""Read-only file inspection and SHA-256 integrity operations."""

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Result, Status

DEFAULT_HASH_LIMIT = 64 * 1024 * 1024
DEFAULT_VERIFY_LIMIT = 256 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")


def _positive_limit(value: int, name: str, maximum: int = 4 * 1024 * 1024 * 1024) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be an integer between 1 and {maximum} bytes.")
    return value


def _readable_file(path: str | Path) -> tuple[Path, Any]:
    candidate = Path(path).expanduser()
    if not candidate.exists():
        raise FileNotFoundError(f"File does not exist: {candidate}")
    if not candidate.is_file():
        raise ValueError(f"Not a regular file: {candidate}")
    return candidate, candidate.stat()


def _hash_file(path: Path, size: int, max_bytes: int) -> dict[str, Any]:
    digest = hashlib.sha256()
    hashed_bytes = 0
    before = path.stat()
    with path.open("rb") as handle:
        while hashed_bytes < min(size, max_bytes):
            amount = min(CHUNK_SIZE, max_bytes - hashed_bytes)
            chunk = handle.read(amount)
            if not chunk:
                break
            digest.update(chunk)
            hashed_bytes += len(chunk)
    after = path.stat()
    changed = (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
    complete = hashed_bytes == size and not changed
    return {
        "algorithm": "SHA-256",
        "digest": digest.hexdigest(),
        "file_size_bytes": size,
        "hashed_bytes": hashed_bytes,
        "covers_entire_file": complete,
        "partial": not complete,
        "file_changed_during_read": changed,
    }


def calculate_sha256(path: str | Path, max_bytes: int = DEFAULT_HASH_LIMIT) -> Result:
    try:
        max_bytes = _positive_limit(max_bytes, "Hash limit")
        candidate, stat = _readable_file(path)
        hashed = _hash_file(candidate, stat.st_size, max_bytes)
    except (OSError, ValueError) as exc:
        return Result("integrity", "calculate_sha256", Status.FAILURE, "Could not hash the file.", errors=[f"{type(exc).__name__}: {exc}"])

    warnings: list[str] = []
    if hashed["partial"]:
        warnings.append("The digest covers only the stated number of bytes; it is not a whole-file digest.")
    if hashed["file_changed_during_read"]:
        warnings.append("The file changed while being read. Hash it again when it is stable.")
    return Result(
        "integrity",
        "calculate_sha256",
        Status.SUCCESS if hashed["covers_entire_file"] else Status.WARNING,
        "Calculated a whole-file SHA-256 digest." if hashed["covers_entire_file"] else "Calculated a partial SHA-256 digest.",
        data={"path": str(candidate), **hashed},
        warnings=warnings,
    )


def signature_hint(header: bytes) -> dict[str, Any]:
    """Return a conservative magic-byte hint, never a full format validation."""
    signatures: list[tuple[bytes, str, str]] = [
        (b"\x7fELF", "ELF", "ELF executable/object container"),
        (b"\xcf\xfa\xed\xfe", "Mach-O", "Mach-O 64-bit little-endian binary"),
        (b"\xce\xfa\xed\xfe", "Mach-O", "Mach-O 32-bit little-endian binary"),
        (b"\xfe\xed\xfa\xce", "Mach-O", "Mach-O 32-bit big-endian binary"),
        (b"\xfe\xed\xfa\xcf", "Mach-O", "Mach-O 64-bit big-endian binary"),
        (b"\xca\xfe\xba\xbe", "Mach-O/Java", "Fat Mach-O or Java class; more parsing is required"),
        (b"%PDF-", "PDF", "PDF document"),
        (b"\x89PNG\r\n\x1a\n", "PNG", "PNG image"),
        (b"\xff\xd8\xff", "JPEG", "JPEG image"),
        (b"PK\x03\x04", "ZIP", "ZIP-based container; document type is not established"),
        (b"PK\x05\x06", "ZIP", "Empty ZIP archive"),
        (b"\x1f\x8b", "GZIP", "Gzip compressed data"),
        (b"7z\xbc\xaf\x27\x1c", "7Z", "7-Zip archive"),
        (b"Rar!\x1a\x07", "RAR", "RAR archive"),
        (b"SQLite format 3\x00", "SQLite", "SQLite 3 database"),
        (b"\x00asm", "WebAssembly", "WebAssembly binary module"),
        (b"dex\n", "DEX", "Android Dalvik executable"),
    ]
    for magic, name, description in signatures:
        if header.startswith(magic):
            return {"offset": 0, "name": name, "description": description, "heuristic": True}
    if header.startswith(b"MZ"):
        return {
            "offset": 0,
            "name": "Possible PE",
            "description": "DOS MZ header; a PE/COFF header must be parsed before calling this a PE file",
            "heuristic": True,
        }
    return {"offset": None, "name": "Unknown", "description": "No recognized signature hint in the bounded header", "heuristic": True}


def extract_printable_strings(
    data: bytes,
    *,
    min_length: int = 4,
    max_strings: int = 200,
    max_string_length: int = 240,
) -> tuple[list[dict[str, Any]], bool]:
    if isinstance(min_length, bool) or not isinstance(min_length, int) or not 4 <= min_length <= 128:
        raise ValueError("Minimum string length must be between 4 and 128.")
    if isinstance(max_strings, bool) or not isinstance(max_strings, int) or not 1 <= max_strings <= 5000:
        raise ValueError("Maximum strings must be between 1 and 5000.")
    if isinstance(max_string_length, bool) or not isinstance(max_string_length, int) or not 4 <= max_string_length <= 4096:
        raise ValueError("Maximum string length must be between 4 and 4096.")
    pattern = re.compile(rb"[\x20-\x7e]{%d,}" % min_length)
    strings: list[dict[str, Any]] = []
    truncated = False
    for match in pattern.finditer(data):
        if len(strings) >= max_strings:
            truncated = True
            break
        raw = match.group(0)
        if len(raw) > max_string_length:
            raw = raw[:max_string_length]
            truncated = True
        strings.append({"offset": match.start(), "encoding": "ASCII", "value": raw.decode("ascii")})
    return strings, truncated


def inspect_file(
    path: str | Path,
    *,
    max_hash_bytes: int = DEFAULT_HASH_LIMIT,
    max_strings_bytes: int = 1024 * 1024,
    max_strings: int = 200,
) -> Result:
    try:
        max_hash_bytes = _positive_limit(max_hash_bytes, "Hash limit")
        max_strings_bytes = _positive_limit(max_strings_bytes, "Strings scan limit", 64 * 1024 * 1024)
        candidate, stat = _readable_file(path)
        hashed = _hash_file(candidate, stat.st_size, max_hash_bytes)
        with candidate.open("rb") as handle:
            header = handle.read(4096)
            handle.seek(0)
            string_data = handle.read(max_strings_bytes + 1)
        strings_scan_truncated = len(string_data) > max_strings_bytes
        string_data = string_data[:max_strings_bytes]
        strings, strings_truncated = extract_printable_strings(string_data, max_strings=max_strings)
    except (OSError, ValueError) as exc:
        return Result("file_intel", "inspect_file", Status.FAILURE, "Could not inspect the file.", errors=[f"{type(exc).__name__}: {exc}"])

    modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    warnings = [
        "Signature hints are heuristics, not complete format validation.",
        "Printable strings do not prove program behavior.",
        "The file was opened read-only and was not executed.",
    ]
    if hashed["partial"]:
        warnings.append("SHA-256 is partial because the configured byte limit was reached or the file changed.")
    if strings_scan_truncated or strings_truncated:
        warnings.append("String extraction was bounded and may be incomplete.")
    data = {
        "path": str(candidate),
        "size_bytes": stat.st_size,
        "modified_utc": modified,
        "sha256": hashed,
        "signature_hint": signature_hint(header),
        "header_bytes_read": len(header),
        "strings": {
            "items": strings,
            "count_returned": len(strings),
            "bytes_scanned": len(string_data),
            "scan_limit_bytes": max_strings_bytes,
            "truncated": strings_scan_truncated or strings_truncated,
        },
        "executed": False,
    }
    return Result(
        "file_intel",
        "inspect_file",
        Status.SUCCESS if hashed["covers_entire_file"] else Status.WARNING,
        "Inspected the file without executing it.",
        data=data,
        warnings=warnings,
    )


def verify_sha256(path: str | Path, expected_digest: str, *, max_bytes: int = DEFAULT_VERIFY_LIMIT) -> Result:
    expected = expected_digest.strip() if isinstance(expected_digest, str) else ""
    if not _SHA256_RE.fullmatch(expected):
        return Result(
            "integrity",
            "verify_sha256",
            Status.FAILURE,
            "Invalid SHA-256 reference digest.",
            errors=["Enter exactly 64 hexadecimal characters. No comparison was performed."],
            data={"verification_completed": False},
        )
    try:
        max_bytes = _positive_limit(max_bytes, "Verification limit")
        candidate, stat = _readable_file(path)
        if stat.st_size > max_bytes:
            return Result(
                "integrity",
                "verify_sha256",
                Status.FAILURE,
                "File exceeds the whole-file verification limit.",
                errors=[f"Size is {stat.st_size} bytes; limit is {max_bytes} bytes. A partial digest was not compared."],
                data={"verification_completed": False, "file_size_bytes": stat.st_size, "limit_bytes": max_bytes},
            )
        hashed = _hash_file(candidate, stat.st_size, max_bytes)
        if not hashed["covers_entire_file"]:
            return Result("integrity", "verify_sha256", Status.FAILURE, "Whole-file verification was not completed.", data={"path": str(candidate), "sha256": hashed, "verification_completed": False}, errors=["The file changed or could not be read completely."])
    except (OSError, ValueError) as exc:
        return Result("integrity", "verify_sha256", Status.FAILURE, "Could not verify the file.", errors=[f"{type(exc).__name__}: {exc}"], data={"verification_completed": False})

    match = hmac.compare_digest(hashed["digest"], expected.lower())
    data = {
        "path": str(candidate),
        "calculated_sha256": hashed["digest"],
        "reference_sha256": expected.lower(),
        "match": match,
        "verification_completed": True,
        "covers_entire_file": True,
        "reference_is_trusted": False,
        "meaning": "A match proves byte equality with the supplied digest, not safety or trustworthiness.",
    }
    return Result(
        "integrity",
        "verify_sha256",
        Status.SUCCESS if match else Status.FAILURE,
        "SHA-256 matches the supplied reference." if match else "SHA-256 does not match the supplied reference.",
        data=data,
    )
