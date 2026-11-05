# Security, privacy, and authorized use

## Scope

STELLIVOR is a systems-diagnostics and defensive learning workbench. Use it only on devices, files, networks, and radio inputs you own or have permission to inspect. Its terminal styling is visual only; it is not a front-end to stealth, exploitation, backdoors, credential theft, password cracking, or destructive operations.

## Privacy

- No account, API key, telemetry, or cloud client is required.
- No binary, diagnostic result, or report is uploaded automatically.
- Reports are written locally only after the user chooses export.
- Wi-Fi profile adapters request names only; they do not ask the OS for stored keys.
- The system-profile action reads local memory/storage data and, on Termux, may request battery status through the optional Termux:API command. It filters the response to a small allowlist; the query does not run at startup.
- Passphrase input is hidden. The estimator returns length/category metadata and a rough rating only; it does not return, log, save, transmit, or crack the phrase.
- Reports can contain hostnames, IP/MAC addresses, paths, usernames, and machine details. Review them before sharing; reports are not encrypted by STELLIVOR.

## Subprocesses

- Fixed argument arrays; `shell=False`.
- No automatic elevation, installation, or destructive commands.
- Timeouts and bounded stdout/stderr capture.
- Missing executable, permission failure, timeout, and nonzero exit remain explicit outcomes.

## Files

- Inspection is read-only; targets are never executed.
- Hashing streams and reports whole-file versus partial coverage.
- Verification never compares a partial hash.
- File signatures and printable strings are evidence hints, not verdicts.

## Networks and wireless

- DNS and a single TCP connection attempt occur only when selected.
- No port ranges, host ranges, password attempts, handshake capture, or background scanning.
- Nearby Wi-Fi data depends on the OS, optional tools, hardware, and permissions; a failed scan is never presented as an empty successful scan.
- No saved Wi-Fi keys or key material are extracted.

## Recovered WiFi Inspector predecessor

The supplied archive contained useful read-only Windows diagnostics and defensive learning features, but also a saved-profile command using `key=clear` and a John the Ripper/Hashcat cracking workbench. STELLIVOR reuses safe concepts such as profile-name visibility, security guidance, a hardening checklist, and a local passphrase heuristic. It intentionally excludes key extraction and password-cracking workflows.

## Hardware and optional tools

Executable discovery is a PATH check, not a functional test. Live RTL-SDR and ADS-B integrations are absent. STELLIVOR does not install drivers, flash devices, load kernel modules, or download toolchains.
