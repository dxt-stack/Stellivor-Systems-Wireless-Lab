# Security, privacy, and authorized use

## Scope

STELLIVOR is a systems-diagnostics and defensive learning workbench. Use it only on devices, files, networks, and radio inputs you own or have permission to inspect. Its terminal styling is visual only; it does not provide stealth, exploitation, backdoors, remote credential attacks, or destructive operations.

## Privacy

- No account, API key, telemetry, or cloud client is required for the core.
- No binary, diagnostic result, or report is uploaded automatically.
- Reports are written locally only after the user chooses export.
- Wi-Fi profile names and metadata can be listed where the operating system exposes them. A separate explicit interactive action can display locally stored Wi-Fi keys on supported Windows and Linux systems; Android/Termux does not expose other apps' saved credentials through this adapter, and macOS key retrieval is not implemented.
- Displayed Wi-Fi keys are transient and are not added to serializable results, session history, logs, or report exports. Terminal scrollback and screenshots can still expose them.
- The system-profile action reads local memory/storage data and, on Termux, may request battery status through the optional Termux:API command. It filters the response to a small allowlist; the query does not run at startup.
- Passphrase input is hidden. The estimator returns length/category metadata and a rough rating only; it does not return, log, save, transmit, or externally check the phrase.
- Reports can contain hostnames, IP/MAC addresses, paths, usernames, and machine details. Review them before sharing; reports are not encrypted by STELLIVOR.

## Local credential-audit workbench

The optional John the Ripper workbench operates only on a local hash file supplied by the operator and, for wordlist modes, a local wordlist. The interactive run path requires explicit confirmation that the operator owns or is authorized to assess the hash file. Commands use argument arrays with `shell=False`, and the workbench does not collect hashes from networks or devices or make remote credential attempts. Hashcat is detected as an optional executable, but the current workbench does not invoke it.

John output may contain recovered credentials. It is shown locally to the operator and is excluded from JSON/Markdown reports by default. The interactive export flow asks for explicit opt-in before including that output in a private report. Hash files, wordlists, John pot/session files, and recovered results are sensitive and must not be committed, uploaded, or shared casually.

## Subprocesses

- Fixed argument arrays; `shell=False`.
- No automatic elevation, installation, or destructive commands.
- Timeouts and bounded stdout/stderr capture.
- Missing executable, permission failure, timeout, and nonzero exit remain explicit outcomes.

## Files

- File inspection is read-only; targets are never executed.
- Hashing streams and reports whole-file versus partial coverage.
- Verification never compares a partial hash.
- File signatures and printable strings are evidence hints, not verdicts.

## Networks and wireless

- DNS and a single TCP connection attempt occur only when selected.
- No port ranges, host ranges, handshake capture, or background scanning.
- Nearby Wi-Fi data depends on the OS, optional tools, hardware, and permissions; a failed scan is never presented as an empty successful scan.
- Saved-key display is limited to locally stored profiles on supported Windows/Linux systems and requires an explicit user action. It is not nearby-network password discovery.

## Reused WiFi Inspector concepts

STELLIVOR incorporates reviewed wireless status and profile inspection, defensive security guidance, a hardening checklist, a local passphrase heuristic, explicit local saved-key display on supported platforms, and an authorized local John workbench. It does not include handshake capture, network hash harvesting, remote credential attempts, backdoors, or unauthorized attack features.

## Hardware and optional tools

Executable discovery is a PATH check, not a functional test. Live RTL-SDR and ADS-B integrations are absent. STELLIVOR does not install drivers, flash devices, load kernel modules, or download toolchains.
