"""Local JSON and Markdown report generation. Never uploads report data."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from . import __version__
from .core import Result, Status, detect_platform, to_primitive, utc_now

PRIVACY_NOTICE = (
    "This report may contain private hostnames, IP/MAC addresses, file paths, usernames, "
    "machine details, or local credential-audit output. Review it before sharing. "
    "STELLIVOR never uploads it automatically. Credential-audit output is excluded by "
    "default; explicitly opt in only when the report will remain private."
)


def build_report(
    results: Iterable[Result],
    *,
    title: str = "STELLIVOR Diagnostic Report",
    include_sensitive: bool = False,
) -> dict:
    materialized = list(results)
    if not materialized:
        raise ValueError("At least one diagnostic result is required.")
    if any(not isinstance(result, Result) for result in materialized):
        raise TypeError("Reports accept Result objects only.")
    clean_title = title.strip() if isinstance(title, str) else ""
    if not clean_title or len(clean_title) > 120:
        raise ValueError("Report title must contain 1-120 characters.")

    serialized_results = []
    for result in materialized:
        serialized = result.to_dict()
        if result.module == "credential_audit" and not include_sensitive:
            data = serialized.get("data")
            if isinstance(data, dict):
                data.pop("output", None)
                data.pop("stdout", None)
                data.pop("stderr", None)
                serialized["data"] = data
                serialized["sensitive_output_excluded"] = True
        serialized_results.append(serialized)

    return {
        "schema": "stellivor.report.v1",
        "title": clean_title,
        "created_utc": utc_now(),
        "generator": {"name": "STELLIVOR // Systems & Wireless Lab", "version": __version__},
        "environment": {"platform_adapter": detect_platform().name, "python_version": __import__("platform").python_version()},
        "privacy_notice": PRIVACY_NOTICE,
        "uploaded": False,
        "sensitive_output_included": bool(include_sensitive),
        "result_count": len(materialized),
        "results": serialized_results,
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"- Created (UTC): `{report['created_utc']}`",
        f"- Generator: `{report['generator']['name']} {report['generator']['version']}`",
        f"- Results: `{report['result_count']}`",
        "",
        "## Privacy notice",
        "",
        report["privacy_notice"],
        "",
        "## Results",
        "",
    ]
    for index, result in enumerate(report["results"], start=1):
        lines.extend([
            f"### {index}. {result['module']} / {result['operation']}",
            "",
            f"- Status: **{result['status']}**",
            f"- Timestamp (UTC): `{result['timestamp']}`",
            f"- Summary: {result['summary']}",
            "",
        ])
        if result.get("sensitive_output_excluded"):
            lines.extend(["- Sensitive local credential-audit output: **excluded**", ""])
        if result.get("errors"):
            lines.append("**Errors**")
            lines.append("")
            lines.extend(f"- {error}" for error in result["errors"])
            lines.append("")
        if result.get("warnings"):
            lines.append("**Warnings and limitations**")
            lines.append("")
            lines.extend(f"- {warning}" for warning in result["warnings"])
            lines.append("")
        lines.extend(["**Structured data**", "", "```json", json.dumps(result.get("data", {}), indent=2, ensure_ascii=False, sort_keys=True), "```", ""])
    return "\n".join(lines)


def _safe_stem(stem: str | None) -> str:
    if stem is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return f"stellivor-report-{stamp}"
    if not isinstance(stem, str):
        raise ValueError("Report name must be text.")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", stem.strip()).strip(".-")
    if not cleaned:
        raise ValueError("Report name contains no usable characters.")
    return cleaned[:80]


def _atomic_write(path: Path, content: str) -> None:
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
            handle.write(content)
            temporary_name = handle.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def save_report(
    results: Sequence[Result],
    output_directory: str | Path,
    *,
    formats: Sequence[str] = ("json", "markdown"),
    stem: str | None = None,
    include_sensitive: bool = False,
) -> Result:
    try:
        report = build_report(results, include_sensitive=include_sensitive)
        safe_stem = _safe_stem(stem)
        if not formats:
            raise ValueError("Select at least one report format.")
        if any(not isinstance(item, str) for item in formats):
            raise ValueError("Report formats must be text values.")
        normalized = ["markdown" if item.lower() == "md" else item.lower() for item in formats]
        if any(item not in ("json", "markdown") for item in normalized):
            raise ValueError("Supported report formats are JSON and Markdown.")
        normalized = list(dict.fromkeys(normalized))
        directory = Path(output_directory).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        if not directory.is_dir():
            raise ValueError("Report destination is not a directory.")
        written: list[str] = []
        if "json" in normalized:
            path = directory / f"{safe_stem}.json"
            _atomic_write(path, json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True, default=to_primitive) + "\n")
            written.append(str(path))
        if "markdown" in normalized:
            path = directory / f"{safe_stem}.md"
            _atomic_write(path, render_markdown(report))
            written.append(str(path))
    except (OSError, ValueError, TypeError) as exc:
        return Result("reports", "save_report", Status.FAILURE, "Could not save the local report.", errors=[f"{type(exc).__name__}: {exc}"], data={"uploaded": False})
    return Result(
        "reports",
        "save_report",
        Status.SUCCESS,
        f"Saved {len(written)} local report file(s).",
        data={
            "files": written,
            "formats": normalized,
            "uploaded": False,
            "result_count": report["result_count"],
            "sensitive_output_included": bool(include_sensitive),
        },
        warnings=[PRIVACY_NOTICE],
    )
