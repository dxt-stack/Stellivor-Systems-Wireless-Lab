# Architecture

## Design goal

STELLIVOR separates a shared Python core from a replaceable terminal interface. Diagnostics return structured results; the UI formats them. A future GUI can reuse these operations rather than reimplementing platform logic.

## Module boundaries

- `stellivor/core.py`: result/status types, platform detection, JSON conversion, status aggregation, and safe bounded native-command execution.
- `stellivor/system_info.py`: local OS/runtime and memory/storage snapshots; optional filtered Termux battery status when the user selects the profile.
- `stellivor/network.py`: host validation, DNS, a single TCP connection attempt, and native interface/route adapters.
- `stellivor/wireless.py`: read-only OS-specific wireless snapshots and Termux:API boundaries.
- `stellivor/wireless_inspector.py`: saved-profile listing/metadata, explicit local saved-key display on supported Windows/Linux systems, nearby/current Wi-Fi information, and network-configuration snapshots.
- `stellivor/credential_audit.py`: optional local John the Ripper operations against operator-supplied hash files, with an explicit authorization gate; Hashcat is detected but not invoked by the current workbench.
- `stellivor/connections.py`: local listening TCP snapshots.
- `stellivor/file_intel.py`: read-only metadata, hashing, integrity verification, signature hints, and bounded strings.
- `stellivor/sdr.py`: synthetic IQ and deterministic educational signal analysis only.
- `stellivor/security_lab.py`: defensive local passphrase heuristic and router-hardening guidance.
- `stellivor/tools.py`: optional executable discovery without claiming functionality/hardware verification.
- `stellivor/device.py`: read-only ADB version/device inventory and authorized-device readiness; no arbitrary remote commands or state changes.
- `stellivor/reports.py`: local JSON/Markdown reports and atomic file writes.
- `stellivor/cli.py`: direct JSON-capable command interface for scripts and Termux shell workflows.
- `stellivor/ui.py`: responsive menus, RGB emblem rendering, outlined wordmark, TTY-only startup/selection animations, prompts, and result presentation.
- `stellivor/brandmark.py`: pre-sampled pixels from the bundled emblem; avoids an on-device imaging dependency.

`main.py` is the executable entry point. `stellivor/__init__.py` owns the version.

## UI and startup

The terminal emblem is rendered from pre-sampled pixels of the bundled image; its colors are brightened and saturated for true-colour ANSI/Braille output, with a lifted grayscale/ASCII fallback. The wordmark uses outlined strokes and adapts to narrow terminals. On interactive terminals the startup clock briefly uses actual local time and includes timezone/UTC offset. The landing-menu timestamp is static so periodic redraws do not interfere with terminal scrollback. `P` is retained as an informational input; it does not pause a live ticker. Valid operation selections progressively reveal their short label across four frames beside the dragon mark before opening/running; the transition is bounded to about 0.18 seconds. `--no-animation` disables startup and selection motion. Result output is immediate and batched by default; `--paced-output` enables the optional gradual reveal, while `--fast-output` selects immediate output. ANSI palettes are selectable. No network/radio/hardware scan runs before the user selects an action. The one-choice quick-audit bundle is read-only and omits DNS/TCP probing and Wi-Fi scans.

The high-resolution dragon-and-star logo remains in `assets/`; `stellivor/brandmark.py` contains the compact terminal raster. Runtime needs no imaging library.

The interactive UI keeps numbered navigation and adds help, command-palette, rerun, export, and quit shortcuts. Direct CLI mode uses the same `Result` contract as the interactive UI, so missing dependencies and permission restrictions remain explicit rather than being presented as successful operations.

## Result contract

Every diagnostic returns a `Result` with module and operation names, a UTC timestamp, status, summary, structured data, errors, and warnings/limitations. Statuses distinguish success, failure, warning, unsupported capability, permission restriction, missing dependency, simulation, and in-progress work.

## Native commands

Commands are argument arrays executed with `shell=False`, timeouts, and bounded stdout/stderr capture. Excess output is drained and discarded; it is not written to an unbounded temporary file. Missing executables, nonzero exits, timeouts, and permission errors remain distinct.

Platform adapters receive explicit `PlatformInfo`. Termux is treated as Android, not as an unrestricted desktop Linux system.

## Wireless and credential-audit boundaries

Wireless discovery and profile metadata are capability-aware. Saved Wi-Fi profile names may be listed where supported. On Windows and Linux, an explicit interactive action can request and display a key already stored for a selected local profile. Android/Termux does not expose other applications' saved Wi-Fi credentials through this adapter; macOS key retrieval is not implemented. Displayed key values are transient: they are not put in serializable `Result` objects, session history, logs, or report exports.

The local credential-audit workbench invokes John the Ripper only against a hash file supplied by the operator, with a local wordlist when the selected mode requires one. The interactive run path requires explicit confirmation that the operator owns or is authorized to assess the file. Hashcat availability is detected, but the current workbench does not invoke Hashcat. No hashes are collected from networks or devices, and no remote credential attempts are made. John output may contain recovered credentials; it remains visible locally, is excluded from report exports by default, and requires an explicit opt-in before inclusion in a private report. Hash files, wordlists, pot/session files, and recovered output must be kept private.

The passphrase estimator is separate from the credential-audit workbench: it evaluates a user-entered test phrase in memory and returns derived metadata only. It does not return, save, log, transmit, or compare the phrase against external sources.

## File and SDR boundaries

Inspected files are opened read-only and never executed. Hashing streams in chunks; partial digests are marked. Signature hints are not complete parsers.

The SDR module generates mathematical complex samples and labels them as simulation. It has no live receiver path. Seeded noise and FFT behavior are deterministic for tests.

## Reports and testing

Reports are local and manually exported. They preserve errors and limitations, with a privacy notice. Credential-audit stdout/stderr is excluded by default; explicit inclusion is intended only for a private report destination. Tests cover deterministic behavior and mocked platform outputs; real device and hardware integrations require separately recorded testing on each platform.
