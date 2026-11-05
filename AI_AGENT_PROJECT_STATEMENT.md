# STELLIVOR — AI Agent Project Statement

**Purpose:** Give a future AI coding agent the product brief, current implementation state, non-negotiable scope, QA evidence, and release process needed to continue STELLIVOR safely and coherently.

**Current release:** 0.6.0  
**Project name:** STELLIVOR // Systems & Wireless Lab  
**Current runtime baseline:** Python 3.10+; standard-library-only core  
**Current release date:** 2026-11-05

## Product purpose

STELLIVOR is an offline-first, mobile-friendly terminal workbench for local system diagnostics, wireless learning, and defensive checks. It reports what the current operating system and permissions actually expose. It is not a complete penetration-testing distribution, does not require root, and must not imply that an unavailable capability was tested successfully.

The original visual identity is a binary/circuit dragon guarding a stellar sphere. The terminal places a compact rendering of that emblem prominently above an outlined STELLIVOR wordmark. Keep the dragon and real planetary/star sphere together; do not replace it with a generic five-point star or solid block-letter logo.

## Accepted functionality and scope

The current implementation includes:

- Real local system profile: OS/runtime, CPU, uptime, memory, home-storage data, and optional filtered Termux:API battery status when selected.
- A read-only quick local audit: system profile, interfaces, routes, listening sockets, and optional-tool presence. It does not silently perform DNS/TCP checks or a wireless scan.
- User-selected, bounded DNS lookup and one-attempt TCP endpoint check; interface and route snapshots where supported.
- Read-only wireless snapshots using capability-aware adapters. Android/Termux results depend on installed optional Termux:API components and Android permissions.
- Read-only file metadata, bounded signature hints and printable-string extraction, SHA-256 hashing, and digest verification. Never execute inspected files.
- Synthetic-only IQ generation and educational signal analysis. There is no live RF capture path.
- A defensive Wireless Security Lab: local rough test-phrase estimate, router-hardening checklist, permitted wireless snapshot, and safe owner recovery guidance.
- Tool-presence discovery that does not claim hardware or feature verification.
- Manual local JSON/Markdown report export with privacy guidance.
- Direct JSON-capable CLI commands and read-only authorized ADB/device readiness reporting.
- Responsive terminal UI, themes (`stellivor`, `ember`, `ice`), semantic result colors, bounded line-by-line result reveal, `--fast-output`, ASCII/no-color fallbacks, a live local clock, dragon selection cue, and a pause control for scrollback.
- Interactive help, command palette, rerun, export, and quit shortcuts while preserving numbered navigation.

### Reviewed WiFi Inspector reuse

Safe concepts from the user-supplied WiFi Inspector archive were incorporated: wireless status, defensive security guidance, a hardening checklist, local test-phrase estimation, and owner recovery guidance. Do not add saved Wi-Fi key extraction, password cracking, handshake capture, credential capture, backdoors, exploit menus, or unauthorized attack features. A wireless scan cannot reveal a network password.

## UI behavior and acceptance requirements

- Interactive startup displays the real local clock, timezone abbreviation, and UTC offset. The clock updates once per second while the landing menu is waiting, including normal second/minute/hour rollover.
- At the landing menu, `P` then Enter pauses/resumes the live clock. While paused, no periodic terminal writes occur; the user can scroll back without the clock repeatedly updating the terminal. `--no-animation` starts with a static clock and no dragon transition.
- Python cannot reliably detect a touch-scroll gesture in the terminal. Therefore do not claim automatic scroll detection: users should pause the ticker before scrolling, or launch with `--no-animation` for a static session.
- A valid menu selection progressively reveals its short label beside a tiny dragon cue before the option content appears. Keep this TTY-only, bounded to about 0.18 seconds, and readable on narrow terminals.
- Result content is progressively revealed on interactive terminals with a bounded pacing budget; non-TTY output remains immediate. Do not add fake scanning/progress animations or claim that diagnostics ran before selection.
- The terminal emblem colors are deliberately brightened and more saturated for visibility, with an improved grayscale fallback. Preserve a no-color path.

## Safety, privacy, and engineering constraints

- Offline-first; no telemetry, background uploads, cloud analysis, or automatic sharing.
- No root requirement, credential capture, saved-key extraction, password cracking, backdoors, or exploit/attack workflows.
- No automatic package installation or configuration changes. Optional native utilities are detected, not installed.
- No archive code execution. File inspection is read-only.
- Use subprocess argument arrays (`shell=False`), bounded output, and timeouts. Keep network operations user-selected and bounded.
- Reports stay local until a user deliberately shares them; advise users to inspect reports for private paths/hostnames/addresses.
- Preserve honest status distinctions: success, warning, failure, unsupported, permission restricted, missing dependency, and simulation.
- Keep the core dependency-free and suitable for Android/Termux; avoid heavyweight frameworks or needless architectural rewrites.

## Current project layout

- `stellivor/` — core results, adapters, diagnostics, UI, and terminal rendering.
- `stellivor/ui.py` — menu, live clock/pause control, paced output, themes, and dragon/emblem rendering.
- `stellivor/cli.py` — direct machine-readable command interface.
- `stellivor/device.py` — read-only ADB/device readiness; no unlock, brute force, remote shell, payload, or data extraction.
- `stellivor/brandmark.py` — pre-sampled emblem data; no runtime imaging library.
- `assets/` — original dragon-and-star artwork.
- `tests/` — deterministic unit and regression tests.
- `docs/` — architecture, testing, security, platform support, and roadmap.
- `README.md` — user setup, implemented capability list, and safety boundaries.
- `HANDOVER.md` — concise status and operational handover.

## Reproducible checks

From the project root:

```sh
python -W error::SyntaxWarning -m py_compile main.py stellivor/*.py tests/*.py
python -W error::ResourceWarning -m unittest discover -s tests -v
python main.py --version
python main.py --system-json
printf '0\n' | python main.py --no-color --no-animation
```

Current release QA recorded **75 passing deterministic tests**. It also passed direct JSON CLI/system/menu smoke checks and a pseudo-terminal test confirming: (1) the clock ticks in real time, (2) pausing causes no terminal writes during the measured wait, and (3) resuming restores the ticker. The test workspace was Linux; pseudo-terminal tests are not a substitute for actual Termux visual testing.

A user screenshot confirms **0.4.0** ran in Android/Termux with Python 3.14.8. The 0.6.0 shell shortcuts and ADB readiness check have not yet been visually confirmed on that phone. Never describe this release as device-tested until the user confirms it.

## Release artifacts and handoff

- ZIP: `STELLIVOR-Systems-Wireless-Lab-0.5.3.zip`
- Checksum: `STELLIVOR-Systems-Wireless-Lab-0.5.3.zip.sha256`
- The established Dropbox destination is private folder `/r/`. Private uploads are authorized by the user; **do not create a public/shared link**.
- Exclude `__pycache__`, `.pyc`, virtual environments, credentials, and build artifacts from release ZIPs. Include the source, tests, README, docs, and project statement.
- Before publishing any next release: update version/changelog/README/testing/platform docs, run the full suite and CLI smoke checks, create the ZIP, extract it into a clean directory, rerun tests and smoke checks from the extraction, verify the checksum, then upload only to private `/r/` and compare remote content hashes to local files.
- Preserve version history; use a new patch version for behavior changes and revision-checked replacement only for a correction to an already-private artifact with the same release version.

## Suggested next work

1. Ask the user to test 0.6.0 in Termux, especially the live clock, `P` pause/resume, command palette, direct commands, and ADB readiness under their actual environment.
2. Fix only reproducible issues; keep the pause control simple and avoid periodic writes while paused.
3. Continue strengthening deterministic tests and capability-aware output without expanding the defensive scope.
4. Keep the README, tests, platform-support status, and release artifacts synchronized with every change.
