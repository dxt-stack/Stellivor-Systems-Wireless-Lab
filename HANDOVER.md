# STELLIVOR // SYSTEMS & WIRELESS LAB — PROJECT HANDOVER

**Current release:** 0.6.0  
**Code baseline:** `f1a15a5`  
**Project status:** The deterministic suite passes locally and in the Python 3.10–3.13 GitHub Actions matrix. Real-device validation remains platform-specific; mocked tests do not establish native Windows/macOS behavior or live wireless hardware support.

## Purpose

STELLIVOR is a dependency-light, offline-first workbench for local system diagnostics, wireless learning, and safe defensive checks. It reports actual local capabilities and does not claim to be a full mobile penetration-testing distribution.

## Implemented capabilities

- Local system profile, interface/route/listening-socket snapshots, selected DNS and one-attempt TCP diagnostics.
- Read-only file metadata, bounded printable-string hints, SHA-256 hashing and verification.
- Synthetic-only IQ generation and signal analysis; no live RF capture path.
- Wireless snapshots, saved-profile metadata, explicit local saved-key display on supported Windows/Linux systems, current connection details, and network-configuration inspection.
- Defensive wireless review hints, rough local test-phrase estimate, router-hardening checklist, and owner recovery guidance.
- Optional local John the Ripper audit against operator-supplied hash files, with explicit authorization confirmation in the interactive run flow. Hashcat is detected but not invoked. John output is visible locally and excluded from reports by default; private-report inclusion requires explicit opt-in.
- Local report export, selected tool-presence checks, and a read-only quick audit.
- Direct JSON-capable CLI commands and a read-only authorized ADB/device readiness check.
- Responsive terminal UI with the original dragon-and-star emblem, outlined STELLIVOR wordmark, themes, brief startup clock, static landing-menu timestamp, selection cue, immediate output by default, and optional paced output.
- Interactive shortcuts for help (`?`), command palette (`/`), rerun (`r`), export (`e`), and quit (`q`).

## Wireless and credential-audit privacy

Saved Wi-Fi keys can be requested only through an explicit local interactive action on supported Windows/Linux platforms. Key values are transient and excluded from serializable results, session history, logs, and report exports. Android/Termux saved-profile key access is unsupported; macOS retrieval is not implemented.

The John workbench accepts local operator-supplied hash files and, for selected modes, local wordlists. It does not collect hashes from networks or devices or make remote credential attempts. Treat hash files, wordlists, pot/session files, and recovered output as sensitive. Review reports before sharing.

## Operational boundaries

- No startup scans, fake progress, telemetry, or cloud reporting.
- No automatic installation, root requirement, credential capture, handshake capture, or archive execution.
- Native commands use argument arrays, bounded output, and timeouts; inspected files are read-only.
- Reports remain local until a user chooses to share them.
- Network actions run only when selected; use them only on systems and networks the user owns or are authorized to inspect.

## Run and test

From the project root:

```sh
python -m compileall -q stellivor tests main.py
python -m unittest discover -s tests -v
python main.py
python main.py --theme ember
python main.py --fast-output --no-animation
```

The maintainer reported 101 passing tests in Termux. GitHub Actions run `44540449096` passed compilation and tests on Python 3.10, 3.11, 3.12, and 3.13. The current release still needs deliberate on-device visual and native-integration confirmation in Termux; Windows and macOS native adapters also need testing on those operating systems.

## Project layout

- `stellivor/` — shared operations, adapters, UI, and terminal emblem.
- `assets/` — original project dragon-and-star artwork.
- `tests/` — deterministic unit and regression tests.
- `docs/` — architecture, testing, security, platform support, and roadmap.
- `README.md` — current user documentation and setup instructions.

Release archives and checksum files should be generated from a clean checkout, verified after extraction, and distributed only through an explicitly approved release channel. Never publish local diagnostic reports, hash files, wordlists, credential-audit outputs, or device inventories.
