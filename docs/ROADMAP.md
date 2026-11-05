# Roadmap

Features move to complete only after implementation and appropriate platform testing.

## Next: real-device visual validation of 0.5.3

- Verify the per-second live local clock, timezone/UTC offset, brighter dragon-and-star terminal emblem, `P` pause/resume behavior for scrollback, and selection transition on the user's Android/Termux terminal.
- Record the exact Termux/Python versions and terminal width/encoding if UI issues appear.
- Confirm the new cues remain brief and do not suggest scans or diagnostics ran automatically.
- Recheck file inspection, SHA-256, local reports, and simulated SDR only if needed; these features are unchanged from the user-confirmed 0.4.0 build.
- Test DNS/TCP or wireless visibility only if the user chooses and the relevant components/permissions are already available.
- Validate Windows adapters separately; no cross-platform claim should be inferred from mocks.

## Core improvements

- Add more native-output parsers with recorded fixtures and locale tests.
- Add optional report redaction and checksum manifests.
- Add evidence-based PE/ELF/Mach-O parsing in bounded, read-only modules.
- Add IQ-file import with explicit format, byte order, size and sample count.
- Improve spectrum visualization without making large dependencies mandatory.

## Hardware and desktop stages

- Verify third-party component availability, license, compatibility and installation size before any integration.
- Add RTL-SDR detection/permission diagnostics as a separate optional adapter.
- Keep hardware tests outside the deterministic suite.
- Stabilize the shared API before considering a desktop GUI or native Android app.
- Design a plugin trust boundary before permitting third-party plugin execution.

The predecessor WiFi Inspector is not wholesale-migrated. Only reviewed safe concepts were reused; saved-key extraction and password-cracking features remain excluded.
