# STELLIVOR — AI Agent Project Statement

**Purpose:** Give a future AI coding agent the product brief, current implementation state, non-negotiable scope, QA evidence, and release process needed to continue STELLIVOR safely and coherently.

**Current release:** 0.6.0  
**Project name:** STELLIVOR // Systems & Wireless Lab  
**Current runtime baseline:** Python 3.10+; standard-library-only core  
**Current release date:** 2026-11-05  
**Current verified source baseline:** `f1a15a5` (documentation may be updated after this code baseline)

## Product purpose

STELLIVOR is an offline-first, mobile-friendly terminal workbench for local system diagnostics, wireless learning, and defensive checks. It reports what the current operating system and permissions actually expose. It is not a complete penetration-testing distribution, does not require root, and must not imply that an unavailable capability was tested successfully.

The original visual identity is a binary/circuit dragon guarding a stellar sphere. The terminal places a compact rendering of that emblem prominently above an outlined STELLIVOR wordmark. Keep the dragon and real planetary/star sphere together; do not replace it with a generic five-point star or solid block-letter logo.

## Accepted functionality and scope

The current implementation includes:

- Real local system profile: OS/runtime, CPU, uptime, memory, home-storage data, and optional filtered Termux:API battery status when selected.
- A read-only quick local audit: system profile, interfaces, routes, listening sockets, and optional-tool presence. It does not silently perform DNS/TCP checks or a wireless scan.
- User-selected, bounded DNS lookup and one-attempt TCP endpoint check; interface and route snapshots where supported.
- Read-only wireless snapshots using capability-aware adapters. Android/Termux results depend on installed optional Termux:API components and Android permissions.
- Saved Wi-Fi profile listing and metadata on supported systems; an explicit interactive action can display locally stored keys on Windows/Linux when permissions allow. Keys are transient and excluded from serializable results, session history, logs, and report exports. Android/Termux saved-profile key access is unsupported; macOS retrieval is not implemented.
- A local John the Ripper workbench for operator-supplied hash files. The interactive run path requires explicit confirmation of ownership or authorization. Supported modes are local single, wordlist, and wordlist-plus-rules; named session status/resume and local recovered-result display are available. Hashcat is detected only; the current code does not invoke it. No hashes are collected from network traffic or devices.
- Read-only file metadata, bounded signature hints and printable-string extraction, SHA-256 hashing, and digest verification. Never execute inspected files.
- Synthetic-only IQ generation and educational signal analysis. There is no live RF capture path.
- A defensive Wireless Security Lab: local rough test-phrase estimate, router-hardening checklist, wireless review hints, and safe owner recovery guidance.
- Tool-presence discovery that does not claim hardware or feature verification.
- Manual local JSON/Markdown report export with privacy guidance. Credential-audit stdout/stderr is excluded by default; the interactive export flow requires an explicit opt-in before adding it to a private report.
- Direct JSON-capable CLI commands and read-only authorized ADB/device readiness reporting.
- Responsive terminal UI, themes (`stellivor`, `ember`, `ice`), semantic result colors, immediate batched output by default, optional `--paced-output`, `--fast-output`, ASCII/no-color fallbacks, a brief startup clock, and a dragon selection cue.
- Interactive help, command palette, rerun, export, and quit shortcuts while preserving numbered navigation.

## UI behavior and acceptance requirements

- Interactive startup briefly displays the real local clock, timezone abbreviation, and UTC offset.
- The landing-menu timestamp is static to preserve terminal scrollback. Do not reintroduce a continuously redrawing clock unless the user explicitly requests it and scrollback behavior is reconsidered.
- `P` at the landing menu is informational; it does not pause a live ticker.
- A valid menu selection progressively reveals its short label beside a tiny dragon cue before the option content appears. Keep this TTY-only, bounded to about 0.18 seconds, and readable on narrow terminals.
- Result output is immediate and batched by default. `--paced-output` enables gradual interactive reveal; non-TTY output remains immediate. Do not add fake scanning/progress animations or claim that diagnostics ran before selection.
- The terminal emblem colors are deliberately brightened and more saturated for visibility, with an improved grayscale fallback. Preserve a no-color path.
- `--no-animation` disables startup and selection motion.

## Safety, privacy, and engineering constraints

- Offline-first; no telemetry, background uploads, cloud analysis, or automatic sharing.
- No root requirement, handshake capture, network hash harvesting, remote credential attempts, backdoors, exploit menus, or unauthorized attack features.
- The John workbench is limited to operator-supplied local hash files and optional local wordlists, with an explicit authorization confirmation in the interactive run flow. Never add network-derived hash collection or remote credential attempts. Keep hash files, wordlists, pot/session files, and recovered results private.
- Explicit local display of already-saved Windows/Linux Wi-Fi keys is permitted only under the transient-display rules above. Never serialize or log those values.
- No automatic package installation or configuration changes. Optional native utilities are detected, not installed.
- No archive code execution. File inspection is read-only.
- Use subprocess argument arrays (`shell=False`), bounded output, and timeouts. Keep network operations user-selected and bounded.
- Reports stay local until a user deliberately shares them; advise users to inspect reports for private paths/hostnames/addresses and sensitive credential-audit output.
- Preserve honest status distinctions: success, warning, failure, unsupported, permission restricted, missing dependency, and simulation.
- Keep the core dependency-free and suitable for Android/Termux; avoid heavyweight frameworks or needless architectural rewrites.

## Current project layout

- `stellivor/` — core results, adapters, diagnostics, UI, and terminal rendering.
- `stellivor/ui.py` — menu, startup/selection cues, output pacing, themes, and dragon/emblem rendering.
- `stellivor/cli.py` — direct machine-readable command interface.
- `stellivor/device.py` — read-only ADB/device readiness; no unlock, brute force, remote shell, payload, or data extraction.
- `stellivor/wireless_inspector.py` — local profile and wireless inspection adapters.
- `stellivor/credential_audit.py` — local authorized John workbench and optional-tool detection.
- `stellivor/brandmark.py` — pre-sampled emblem data; no runtime imaging library.
- `assets/` — original dragon-and-star artwork.
- `tests/` — deterministic unit and regression tests.
- `docs/` — architecture, testing, security, platform support, and roadmap.
- `README.md` — user setup, implemented capability list, and safety boundaries.
- `HANDOVER.md` — concise status and operational handover.

## Reproducible checks

From the project root:

```sh
python -m compileall -q stellivor tests main.py
python -m unittest discover -s tests -v
python main.py --version
python main.py --system-json
printf '0\n' | python main.py --no-color --no-animation
```

The maintainer reported **101 passing deterministic tests** in Termux, with compilation and `git diff --check` also passing. GitHub Actions run `44540449096` passed compilation and the deterministic suite on Python 3.10, 3.11, 3.12, and 3.13. CI uses Ubuntu runners; it is not native Windows/macOS or hardware validation.

Android/Termux still needs deliberate visual and native-integration checks on the current device. Never describe a platform capability as device-tested until the current version has been exercised on that platform.

## Release artifacts and handoff

- The current source baseline is version 0.6.0; do not claim that an old 0.5.3 ZIP is the current release artifact.
- Publish release artifacts only through an explicitly approved project release channel; do not include private diagnostic data or credentials.
- Exclude `__pycache__`, `.pyc`, virtual environments, credentials, and build artifacts from release ZIPs. Include the source, tests, README, docs, and project statement.
- Before publishing any next release: update version/changelog/README/testing/platform docs, run the full suite and CLI smoke checks, create the ZIP, extract it into a clean directory, rerun tests and smoke checks from the extraction, verify the checksum, then upload only to the release destination explicitly approved by the project maintainer and compare remote content hashes to local files.
- Preserve version history; use a new patch version for behavior changes and do not replace a published artifact with different contents under the same version.

## Suggested next work

1. Complete the current-version Termux visual/native-integration checklist.
2. Fix only reproducible issues; keep the landing-menu clock static and avoid unnecessary terminal redraws.
3. Continue strengthening deterministic tests and capability-aware output without expanding the defensive scope.
4. Keep the README, tests, platform-support status, and release artifacts synchronized with every change.
