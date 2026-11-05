"""Local, defensive wireless-security learning helpers.

This module never reads saved Wi-Fi keys, cracks hashes, or transmits the
passphrase supplied to the estimator. Only derived, non-secret metadata is
returned.
"""
from __future__ import annotations

import math

from .core import Result, Status


HARDENING_CHECKLIST: tuple[str, ...] = (
    "Use WPA3-Personal where all your devices support it; otherwise use WPA2-AES.",
    "Choose a unique Wi-Fi passphrase that is long and not reused elsewhere.",
    "Change the router administrator password from its factory default.",
    "Install router firmware updates from the manufacturer's official source.",
    "Disable WPS if you do not need it and your router allows that safely.",
    "Use a guest network for visitors and untrusted smart devices.",
    "Review the router's connected-device list and investigate unfamiliar devices.",
    "Keep a recovery method for your own router in a secure place.",
)


def estimate_passphrase_strength(password: str) -> Result:
    """Return a deliberately rough local estimate without returning the secret."""
    if not isinstance(password, str):
        return Result(
            "security_lab", "passphrase_estimate", Status.FAILURE,
            "Passphrase input must be text.", errors=["No estimate was performed."],
            data={"secret_stored": False, "secret_logged": False},
        )
    if not password:
        return Result(
            "security_lab", "passphrase_estimate", Status.FAILURE,
            "No passphrase was entered.", errors=["Enter a test phrase to evaluate."],
            data={"secret_stored": False, "secret_logged": False},
        )
    if len(password) > 256:
        return Result(
            "security_lab", "passphrase_estimate", Status.FAILURE,
            "Passphrase exceeds the 256-character input limit.",
            errors=["No estimate was performed."],
            data={"secret_stored": False, "secret_logged": False},
        )

    categories: list[str] = []
    pool_size = 0
    for present, label, size in (
        (any(char.islower() for char in password), "lowercase", 26),
        (any(char.isupper() for char in password), "uppercase", 26),
        (any(char.isdigit() for char in password), "digits", 10),
        (any(not char.isalnum() for char in password), "symbols_or_spaces", 33),
    ):
        if present:
            categories.append(label)
            pool_size += size

    rough_bits = round(len(password) * math.log2(pool_size), 1) if pool_size > 1 else 0.0
    if len(password) >= 16 and len(categories) >= 2:
        rating = "strong-by-length-and-variety-heuristic"
        guidance = "Good length and variety by this simple estimate; uniqueness and unpredictability still matter."
    elif len(password) >= 12:
        rating = "moderate-by-length-heuristic"
        guidance = "Consider a longer, unique passphrase; avoid predictable patterns and reuse."
    else:
        rating = "weak-by-length-heuristic"
        guidance = "Prefer a longer, unique passphrase rather than relying on substitutions or symbol variety."

    return Result(
        "security_lab",
        "passphrase_estimate",
        Status.WARNING,
        "Produced a local, coarse passphrase estimate; this is not a password audit or safety verdict.",
        data={
            "character_count": len(password),
            "character_categories": categories,
            "rough_character_pool_bits": rough_bits,
            "heuristic_rating": rating,
            "secret_stored": False,
            "secret_logged": False,
            "secret_in_result": False,
            "network_used": False,
            "guidance": guidance,
        },
        warnings=[
            "This estimate does not check common-password lists, reuse, breaches, keyboard patterns, or real attacker models.",
            "The passphrase is evaluated only in memory and is not included in the returned result or saved by this module.",
        ],
    )
