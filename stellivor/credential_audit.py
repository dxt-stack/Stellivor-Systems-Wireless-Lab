"""Local, opt-in John the Ripper workbench for user-owned hash files.

No hashes are collected, extracted, uploaded, or generated from network traffic.
All subprocess calls use argument arrays (never a shell) and require an explicit
authorization confirmation in the interactive UI.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .core import Result, Status


SESSION_RE = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")


def find_john() -> str | None:
    return shutil.which("john") or shutil.which("john.exe")


def find_hashcat() -> str | None:
    return shutil.which("hashcat") or shutil.which("hashcat.exe")


def audit_tool_status() -> Result:
    john, hashcat = find_john(), find_hashcat()
    return Result("credential_audit", "tool_status", Status.SUCCESS,
                  "Checked for optional local audit executables; presence is not a functionality test.",
                  {"john_found": bool(john), "john_path": john,
                   "hashcat_found": bool(hashcat), "hashcat_path": hashcat,
                   "network_used": False, "installation_attempted": False})


def _valid_file(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError(f"{label} does not exist or is not a regular file.")
    resolved = path.resolve(strict=True)
    if resolved.stat().st_size <= 0:
        raise ValueError(f"{label} is empty.")
    return resolved


def run_local_audit(mode: str, hash_file: str | Path, *,
                    wordlist: str | Path | None = None,
                    session: str | None = None,
                    authorized: bool = False) -> Result:
    """Run John locally against an explicitly supplied authorized hash file."""
    if not authorized:
        return Result("credential_audit", "john_run", Status.PERMISSION_RESTRICTED,
                      "Audit cancelled because authorization was not confirmed.",
                      errors=["Only hash files you own or are explicitly authorized to assess may be used."])
    john = find_john()
    if not john:
        return Result("credential_audit", "john_run", Status.DEPENDENCY_MISSING,
                      "John the Ripper was not found on PATH.",
                      data={"network_used": False}, errors=["Install John separately from its official source."])
    try:
        hashes = _valid_file(hash_file, "Hash file")
        if mode not in {"single", "wordlist", "rules"}:
            raise ValueError("Mode must be single, wordlist, or rules.")
        args = [john]
        if mode == "single":
            args.append("--single")
        else:
            if wordlist is None:
                raise ValueError("A wordlist file is required for this mode.")
            words = _valid_file(wordlist, "Wordlist")
            args.append(f"--wordlist={words}")
            if mode == "rules":
                args.append("--rules")
        if session is not None:
            if not SESSION_RE.fullmatch(session):
                raise ValueError("Session names may contain 1-40 letters, digits, underscores, or hyphens.")
            args.append(f"--session={session}")
        args.append(str(hashes))
    except (OSError, ValueError) as exc:
        return Result("credential_audit", "john_run", Status.FAILURE,
                      "Local audit request was not valid.", errors=[str(exc)],
                      data={"network_used": False})
    try:
        completed = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, errors="replace", timeout=3600, shell=False)
    except subprocess.TimeoutExpired:
        return Result("credential_audit", "john_run", Status.WARNING,
                      "Audit exceeded the one-hour execution limit and was stopped.",
                      data={"network_used": False, "hash_file": str(hashes), "mode": mode},
                      warnings=["Check the named John session before deciding whether to resume."])
    except OSError as exc:
        return Result("credential_audit", "john_run", Status.FAILURE,
                      "John could not be started.", errors=[str(exc)],
                      data={"network_used": False})
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return Result("credential_audit", "john_run",
                  Status.SUCCESS if completed.returncode == 0 else Status.WARNING,
                  "John completed the selected local audit operation." if completed.returncode == 0 else
                  f"John exited with status {completed.returncode}.",
                  {"mode": mode, "hash_file": str(hashes), "session": session,
                   "returncode": completed.returncode, "output": output[:12000],
                   "network_used": False, "shell_used": False},
                  warnings=["Hash files, session files, pot files, and recovered results are sensitive. Keep them private."])


def john_information(action: str, *, hash_file: str | Path | None = None,
                     session: str | None = None) -> Result:
    john = find_john()
    if not john:
        return Result("credential_audit", action, Status.DEPENDENCY_MISSING,
                      "John the Ripper was not found on PATH.")
    if action == "help":
        args = [john, "--help"]
    elif action == "build":
        args = [john, "--list=build-info"]
    elif action == "formats":
        args = [john, "--list=formats"]
    elif action == "show":
        if hash_file is None:
            return Result("credential_audit", action, Status.FAILURE, "A hash file is required.")
        try:
            args = [john, "--show", str(_valid_file(hash_file, "Hash file"))]
        except (OSError, ValueError) as exc:
            return Result("credential_audit", action, Status.FAILURE, "Invalid hash file.", errors=[str(exc)])
    elif action == "status":
        if not session or not SESSION_RE.fullmatch(session):
            return Result("credential_audit", action, Status.FAILURE, "A valid named session is required.")
        args = [john, f"--status={session}"]
    elif action == "resume":
        if not session or not SESSION_RE.fullmatch(session):
            return Result("credential_audit", action, Status.FAILURE, "A valid named session is required.")
        args = [john, f"--restore={session}"]
    else:
        return Result("credential_audit", action, Status.FAILURE, "Unsupported John information action.")
    try:
        if action == "resume":
            completed = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                        text=True, errors="replace", timeout=3600, shell=False)
        else:
            completed = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                       text=True, errors="replace", timeout=30, shell=False)
    except subprocess.TimeoutExpired:
        return Result("credential_audit", action, Status.WARNING, "John operation timed out.")
    except OSError as exc:
        return Result("credential_audit", action, Status.FAILURE, "John operation could not start.", errors=[str(exc)])
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return Result("credential_audit", action,
                  Status.SUCCESS if completed.returncode == 0 else Status.WARNING,
                  "John returned output for the selected local operation.",
                  {"returncode": completed.returncode, "output": output[:12000],
                   "network_used": False, "session": session},
                  warnings=["Output may contain recovered credentials. Do not export or share it casually."])
