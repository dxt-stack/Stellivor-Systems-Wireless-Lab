# Roadmap

Features move to complete only after implementation and appropriate platform testing. The current baseline is STELLIVOR 0.6.0; the repository's deterministic suite passes in CI on Python 3.10–3.13, and the maintainer has reported 101 passing tests in Termux.

## Next: finish current-version device validation

- Verify the 0.6.0 terminal layout, startup clock, selection cue, themes, command palette, and direct CLI commands on the maintainer's Android/Termux device.
- Record exact Termux/Python versions and terminal width/encoding if UI issues appear.
- Exercise Termux:API battery and Wi-Fi operations only when the optional app/package and Android permissions are already configured; record unsupported or permission-limited behavior honestly.
- Check ADB readiness with a device already authorized through Android's normal developer settings; do not attempt to bypass authorization.
- Validate Windows and macOS native adapters separately; mocked tests and Linux CI do not establish native support.

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

## Security and documentation maintenance

- Keep the actual behavior of saved Wi-Fi key display and the local John workbench accurately described across the README, architecture, security, and handover documents.
- Preserve the transient-display and report-exclusion protections for saved keys and credential-audit output.
- Do not imply Hashcat execution: current code only checks whether the Hashcat executable is present.
