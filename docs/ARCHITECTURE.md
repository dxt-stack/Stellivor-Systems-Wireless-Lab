# Architecture

## Design goal

STELLIVOR separates a shared Python core from a replaceable terminal interface. Diagnostics return structured results; the UI formats them. A future GUI can reuse these operations rather than reimplementing platform logic.

## Module boundaries

- `stellivor/core.py`: result/status types, platform detection, JSON conversion, status aggregation, and safe bounded native-command execution.
- `stellivor/system_info.py`: local OS/runtime and memory/storage snapshots; optional filtered Termux battery status when the user selects the profile.
- `stellivor/network.py`: host validation, DNS, a single TCP connection attempt, and native interface/route adapters.
- `stellivor/wireless.py`: read-only OS-specific wireless snapshots and Termux:API boundaries.
- `stellivor/connections.py`: local listening TCP snapshots.
- `stellivor/file_intel.py`: read-only metadata, hashing, integrity verification, signature hints, and bounded strings.
- `stellivor/sdr.py`: synthetic IQ and deterministic educational signal analysis only.
- `stellivor/security_lab.py`: defensive local passphrase heuristic and router-hardening guidance; no key extraction or cracking.
- `stellivor/tools.py`: optional executable discovery without claiming functionality/hardware verification.
- `stellivor/device.py`: read-only ADB version/device inventory and authorized-device readiness; no arbitrary remote commands or state changes.
- `stellivor/reports.py`: local JSON/Markdown reports and atomic file writes.
- `stellivor/cli.py`: direct JSON-capable command interface for scripts and Termux shell workflows.
- `stellivor/ui.py`: responsive menus, RGB emblem rendering, outlined wordmark, TTY-only startup/selection animations, prompts, and result presentation.
- `stellivor/brandmark.py`: pre-sampled pixels from the bundled emblem; avoids an on-device imaging dependency.

`main.py` is the executable entry point. `stellivor/__init__.py` owns the version.

## UI and startup

The terminal emblem is rendered from pre-sampled pixels of the bundled image; its colors are brightened and saturated for true-colour ANSI/Braille output, with a lifted grayscale/ASCII fallback. The wordmark uses outlined strokes and adapts to narrow terminals. On interactive terminals the startup clock uses actual local time and includes timezone/UTC offset; while the landing menu waits for input, it refreshes each second and visibly rolls through minutes and hours. At the menu, `P` + Enter pauses/resumes the ticker; a pause stops periodic terminal writes to allow scrollback. Valid operation selections progressively reveal their short label across four frames beside the dragon mark before opening/running; the transition is bounded to about 0.18 seconds. `--no-animation` disables motion and live ticking. Interactive results are revealed line by line with a per-result delay cap; `--fast-output` disables pacing. ANSI palettes are selectable. No network/radio/hardware scan runs before the user selects an action. The one-choice quick-audit bundle is read-only and omits DNS/TCP probing and Wi-Fi scans.

The high-resolution dragon-and-star logo remains in `assets/`; `stellivor/brandmark.py` contains the compact terminal raster. Runtime needs no imaging library.

The interactive UI keeps numbered navigation and adds help, command-palette, rerun, export, and quit shortcuts. Direct CLI mode uses the same `Result` contract as the interactive UI, so missing dependencies and permission restrictions remain explicit rather than being presented as successful operations.

## Result contract

Every diagnostic returns a `Result` with module and operation names, a UTC timestamp, status, summary, structured data, errors, and warnings/limitations. Statuses distinguish success, failure, warning, unsupported capability, permission restriction, missing dependency, simulation, and in-progress work.

## Native commands

Commands are argument arrays executed with `shell=False`, timeouts, and bounded stdout/stderr capture. Excess output is drained and discarded; it is not written to an unbounded temporary file. Missing executables, nonzero exits, timeouts, and permission errors remain distinct.

Platform adapters receive explicit `PlatformInfo`. Termux is treated as Android, not as an unrestricted desktop Linux system.

## Wireless-security boundary

Wireless inspection is read-only and capability-aware. Saved profile names may be listed where supported; keys are never requested. The passphrase estimator evaluates a string in memory and returns derived metadata only; it does not return, save, log, transmit, crack, or compare the passphrase against external sources. The recovered predecessor's `key=clear` and John/Hashcat workflows are intentionally not part of STELLIVOR.

## File and SDR boundaries

Inspected files are opened read-only and never executed. Hashing streams in chunks; partial digests are marked. Signature hints are not complete parsers.

The SDR module generates mathematical complex samples and labels them as simulation. It has no live receiver path. Seeded noise and FFT behavior are deterministic for tests.

## Reports and testing

Reports are local and manually exported. They preserve errors and limitations, with a privacy notice. Tests cover deterministic behavior and mocked platform outputs; real device and hardware integrations require separately recorded testing on each platform.
