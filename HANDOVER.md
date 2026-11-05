# STELLIVOR // SYSTEMS & WIRELESS LAB — PROJECT HANDOVER

**Current release:** 0.5.3  
**Project status:** Implemented, packaged, and locally tested. The 0.5.3 live-clock ticking and brighter emblem have not yet been visually confirmed on the user's Termux device.

## Purpose

STELLIVOR is a dependency-light, offline-first workbench for local system diagnostics, wireless learning, and safe defensive checks. It reports actual local capabilities and does not claim to be a full mobile penetration-testing distribution.

## Implemented capabilities

- Local system profile, interface/route/listening-socket snapshots, selected DNS and one-attempt TCP diagnostics.
- Read-only file metadata, bounded printable-string hints, SHA-256 hashing and verification.
- Synthetic-only IQ generation and signal analysis; no live RF capture path.
- Defensive wireless snapshot, rough local test-phrase estimate, router-hardening checklist, and owner recovery guidance.
- Local report export, selected tool-presence checks, and a read-only quick audit.
- Responsive terminal UI with the original dragon-and-star emblem rendered in brighter, more saturated colors, outlined STELLIVOR wordmark, themes, actual local clock/timezone/UTC offset that ticks each second while the landing menu waits, `P` + Enter pause/resume control for scrollback, paced result lines, and a brief progressive option-label/dragon cue.

## Wireless Inspector reuse and limits

Reviewed safe concepts from the supplied WiFi Inspector project were incorporated: wireless status, defensive security guidance, a hardening checklist, local test-phrase estimation, and safe owner recovery guidance. Saved Wi-Fi key extraction, password cracking, handshake capture, backdoors, and unauthorized attack features are not included. A wireless snapshot does not reveal network passwords.

## Operational and privacy boundaries

- No startup scans, fake progress, telemetry, or cloud reporting.
- No automatic installation, root requirement, credential capture, or archive execution.
- Native commands use argument arrays, bounded output, and timeouts; inspected files are read-only.
- Reports remain local until a user chooses to share them.
- Network actions run only when selected; use them only on systems and networks the user owns or is authorized to inspect.

## Run and test

From the project root:

```sh
python -m unittest discover -s tests -v
python main.py
python main.py --theme ember
python main.py --fast-output --no-animation
```

The 0.5.3 release contains 72 deterministic tests. Workspace QA covers the current CLI, non-interactive behavior, and terminal animation with controlled clocks/fake TTYs; a pseudo-terminal check observed real per-second ticks and confirmed that the pause control stops further writes. The new release still needs on-device visual confirmation in Termux. The user's supplied screenshot documents version 0.4.0 on Android/Termux with Python 3.14.8, not the new 0.5.3 UI.

## Project layout

- `stellivor/` — shared operations, adapters, UI, and terminal emblem.
- `assets/` — original project dragon-and-star artwork.
- `tests/` — deterministic unit and regression tests.
- `docs/` — architecture, testing, security, platform support, and roadmap.
- `README.md` — current user documentation and setup instructions.

The release archive and SHA-256 file are `STELLIVOR-Systems-Wireless-Lab-0.5.3.zip` and `STELLIVOR-Systems-Wireless-Lab-0.5.3.zip.sha256`. The established private Dropbox destination is `/r/`; no public share link is authorized.
