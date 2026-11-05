# Changelog

## 0.5.3 — 2026-11-05

Scrollback usability refinement for the live menu clock.

- Added `P` + Enter at the landing menu to pause/resume the per-second clock ticker. Pausing stops periodic terminal writes so scrollback can be read without a continuing clock redraw.
- Kept live ticking as the interactive default; `--no-animation` keeps the clock static from launch.
- Added regression coverage for pause/resume and checked ticker behavior in a pseudo-terminal.

## 0.5.2 — 2026-11-05

Live menu clock and brighter terminal emblem, following user feedback.

- The local time, timezone abbreviation, and UTC offset now update once per second while the interactive landing-menu prompt waits, so seconds visibly roll into minutes and hours.
- Increased the emblem's color saturation/brightness and lifted the grayscale fallback for better visibility on mobile terminals.
- Added deterministic tests for live clock refresh, narrow terminal clock layout, and emblem contrast.

## 0.5.1 — 2026-11-05

Selection feedback refinement to complete the requested progressive reveal.

- Landing and nested-menu selections now progressively reveal the option label across four short frames beside the dragon mark, before the option's content is released.
- The cue remains TTY-only and bounded to about 0.18 seconds; result lines keep their existing smooth, capped reveal, while non-TTY output remains immediate.
- Added regression checks for text-before-content ordering and the transition timing limit.

## 0.5.0 — 2026-10-24

A lightweight terminal polish update following user feedback from Android/Termux.

- Added a brief interactive startup clock that refreshes from the actual local system time and shows the timezone abbreviation and UTC offset; the menu keeps the current local time visible.
- Added a tiny four-frame dragon-mark transition when a valid operation is selected, including nested network/security choices.
- Kept animation short, TTY-only, dependency-free, and separate from actual work; no startup scans, fake progress, or delays in non-TTY output. `--no-animation` disables clock/dragon motion.
- Retained paced results, themes, ASCII/no-color fallbacks, and the `--fast-output` control.

## 0.4.0 — 2026-10-24

Terminal result presentation refinement following user feedback.

- Results now reveal line by line on interactive terminals with semantic status/JSON colors and a bounded pacing budget (at most 0.8 seconds per result); non-TTY output remains immediate.
- Added three restrained palettes: `stellivor` (default), `ember`, and `ice`, selectable with `--theme`.
- Added `--fast-output` to disable result pacing; the menu remained static in this release and the optional flourish was separate.
- Kept text practical and readable: neutral body text, colored keys/values/statuses, and preserved ASCII/no-color paths.

## 0.3.0 — 2026-10-24

Termux usability and operational-status refinement, following hands-on user testing of 0.2.0.

- Added a compact true-colour terminal rendering of the selected binary-circuit dragon and stellar sphere, sampled from the bundled emblem without an on-device image dependency.
- Replaced the filled block wordmark with thin outlined line-art letters and an ASCII fallback.
- Removed the automatic pre-menu flourish; startup now shows the actual platform and Python runtime. The brief animation remains opt-in with `--animation`.
- Expanded the user-selected system profile with local memory and Termux-home storage snapshots, plus optional Termux:API battery data when the profile action is selected.
- Added a one-choice, read-only quick local audit bundle for the system profile, interfaces, routes, listening sockets, and optional-tool presence; it deliberately performs no DNS/TCP probing or Wi-Fi scan.
- Battery output is filtered to a small allowlist; no extra identifiers are included. No package is installed automatically.
- Preserved offline-first operation, no startup scans, explicit capability limitations, and the defensive-only wireless-security boundary.
- Added tests for brand rendering and filtered Termux battery responses.

STELLIVOR 0.3.0 remains a Python diagnostics app, not Kali Linux or NetHunter. It does not supply root/kernel drivers or a catalogue of offensive tools. Android/Termux behavior for this release still requires real-device validation.

## 0.2.0 — 2026-10-24

Rebrand and mobile-first terminal refinement.

- Established the STELLIVOR product name and `stellivor` Python package.
- Added a large responsive ASCII wordmark, a short startup flourish for interactive terminals, ANSI status colors, responsive panels, and `--no-animation` / `--no-color` controls.
- Added an original binary-circuit dragon guarding a luminous stellar sphere as the project emblem.
- Added a defensive Wireless Security Lab: hidden-input, local-only passphrase heuristic; router-hardening checklist; permitted wireless snapshot; and safe owner recovery guidance.
- Reviewed the recovered WiFi Inspector ZIP. Reused safe ideas, but did not port its saved-key reveal (`key=clear`) or John/Hashcat password-cracking workflow.
- Retained explicit capability/error reporting and no-startup-scan behavior.

## 0.1.1 — 2026-10-24

Reliability corrections to the initial source.

- Bounded subprocess output capture, added input/SDR validation, corrected platform-support documentation, and created a tested source archive.
