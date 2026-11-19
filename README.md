# STELLIVOR // Systems & Wireless Lab

![Stellivor: binary-circuit dragon guarding a stellar sphere](assets/stellivor-emblem.png)

**Stellivor** is a cross-platform, offline-first systems and wireless learning workbench. The name is a coined, Latin-inspired “star-devourer”; the literal phrase “the one who devoured a star” is *qui stellam devoravit*.

Version: **0.6.0**.

**Scope, plainly:** STELLIVOR is a Python diagnostics app, not Kali Linux or NetHunter. It does not install Kali, provide root/kernel drivers, or contain hundreds of third-party tools. Its purpose is a fast, local, defensive workbench; it won't claim NetHunter-level capability.

## A terminal that feels like a workbench

The terminal renders the selected dragon-and-star emblem as compact true-colour Braille art, with brighter, more saturated colors and an outlined STELLIVOR wordmark. On interactive terminals, startup briefly animates the **actual local clock**, timezone abbreviation, and UTC offset. The landing menu keeps a static timestamp instead of repeatedly moving the terminal cursor, preserving normal scrollback on mobile terminals such as Termux. Choosing an operation reveals its short label in a smooth, brief text transition beside the tiny dragon mark, before that option's content appears. These are interface cues only—no scans or diagnostics run until selected. Interactive result lines reveal at a readable, bounded pace with semantic colors; choose `stellivor`, `ember`, or `ice`, and use `--fast-output` to remove result pacing. `--no-animation` disables startup and dragon transitions; non-interactive output stays immediate.

```sh
python main.py --theme ember
python main.py --theme ice --fast-output
python main.py --no-color
```

The shell also supports `?` for help, `/` for a command palette, `r` to rerun the last operation, `e` to export the current session, and `q` to quit. Existing numbered navigation remains available for narrow or basic Termux terminals.

## What is implemented

| Module | Behavior |
|---|---|
| System profile | Real OS/runtime/CPU/uptime, memory, Termux home-storage usage, and optional Termux:API battery status (only when selected) |
| Quick local audit | One selected, read-only bundle of system, interfaces, routes, listening sockets, and tool-presence checks; no DNS/TCP probing or Wi-Fi scan |
| Network diagnostics | User-requested DNS lookup, one bounded TCP endpoint attempt, interfaces, and route snapshots where available |
| Wireless snapshot | Read-only platform adapters; Termux may use optional Termux:API, subject to Android permissions |
| Connection inspector | Local listening TCP snapshot through available native utilities |
| File intelligence | Read-only metadata, SHA-256, bounded signature hints, and printable strings; never executes the file |
| Integrity Lab | Whole-file SHA-256 calculation and comparison with a supplied digest |
| SDR Lab | Deterministic synthetic IQ generation and FFT analysis, clearly marked as a simulation |
| Wireless Security Lab | Local rough passphrase estimate, router-hardening checklist, wireless snapshot, and safe owner recovery guidance |
| Tool catalog | Optional executable presence checks; presence is not proof a tool or hardware works |
| Reports | Manual, local JSON and Markdown export with privacy warnings |
| Authorized device readiness | Real read-only ADB inventory and readiness status for devices already visible to the local ADB client; no unlock, brute force, remote shell, payload, or data extraction |

No third-party Python package, root access, account, API key, telemetry, or cloud analysis is required for the core. Optional native utilities and Android permissions may affect particular features.

## Direct command mode

The same real operations can be used from scripts and shell pipelines without opening the animated UI:

```sh
python main.py system --json
python main.py network interfaces --json
python main.py network dns example.com --json
python main.py device readiness --json
python main.py file inspect ./examples/sample_report.json --json
python main.py integrity verify ./examples/sample_report.json SHA256_DIGEST --json
python main.py sdr simulate --frequency 1000 --count 1024 --json
python main.py wifi profiles --json
python main.py wifi nearby --json
python main.py wifi connection --json
python main.py wifi adapters --json
python main.py wifi refresh --json
```

`device readiness` checks the local `adb` installation, lists visible device states, distinguishes authorized from pending devices, and reports optional `scrcpy` availability. It never bypasses authentication, guesses a PIN, executes an arbitrary device shell, installs an APK, captures private data, or changes device state. See [`docs/CILOCKS_REVIEW.md`](docs/CILOCKS_REVIEW.md) for the CiLocks compatibility and licensing boundary.

## Wi-Fi Inspector integration

The supplied Wi-Fi Inspector archive is integrated through STELLIVOR's existing Result/status model, platform detection, terminal UI, direct CLI, and tests. It does not replace the project structure.

- Saved Wi-Fi profile names and non-secret profile metadata where the OS exposes them.
- Nearby Wi-Fi scan, current connection details, and a refresh operation.
- Network interfaces, IP configuration, and route snapshots.
- Read-only Wi-Fi security hints, owner recovery guidance, local passphrase estimate, and interactive router-hardening checklist.
- Optional John the Ripper / Hashcat detection. The John workbench supports local single, wordlist, and wordlist+rules modes, recovered-result display, named session status, and resume for hash files supplied by the operator. Every run requires an explicit authorization confirmation and uses local files only.

Platform limitations are explicit: Windows uses native WLAN commands; Linux uses NetworkManager where installed; Termux uses Termux:API where installed and permitted. Android does not expose other applications' saved Wi-Fi profiles. Unsupported or permission-limited operations are reported as such, never disguised as empty successful scans.

**Safety boundary:** STELLIVOR never extracts Wi-Fi keys (key=clear), captures handshakes, harvests hashes from networks/devices, or sends credential material to a service. John operates only on a local hash file and optional local wordlist that you supply and are authorized to audit. Hash files, John session files, john.pot, and recovered results are sensitive; keep them private. Tool detection does not install or validate tools.

## Run on Android / Termux

Python **3.10+** is required; the core is standard-library only. For a ZIP in Android Downloads, make sure Termux storage access has already been set up, then:

```sh
mkdir -p ~/stellivor-0.5.3
cd ~/stellivor-0.5.3
python -m zipfile -e ~/storage/downloads/STELLIVOR-Systems-Wireless-Lab-0.5.3.zip .
cd Stellivor-Systems-Wireless-Lab
python -m unittest discover -s tests -v
python main.py
```

No Kali/NetHunter image or SDR toolchain is needed to run Stellivor. The system-profile action reads local memory/storage and can query battery status through `termux-battery-status` if it is already installed; it does not install anything. For optional Termux Wi-Fi visibility, the compatible Termux:API app and package plus Android permissions may be required; the operating system may still restrict results. An unavailable scan is reported as unavailable, not as an empty successful scan.

## Run on Windows, Linux, or macOS

From the extracted project folder:

```sh
python -m unittest discover -s tests -v
python main.py
```

Windows users may use `py -3` instead of `python`; `run_windows.bat` is included. Native adapters are capability-dependent. See `docs/PLATFORM_SUPPORT.md` for the tested environment and the platforms that still need real-device validation.

## Safe operation and privacy

- DNS and TCP checks happen only when selected; the TCP test makes one connection attempt and sends no application payload.
- Wireless information depends on OS support, optional utilities, hardware, and permissions.
- File inspection is read-only and never executes a target file.
- Hash equality does not prove safety or trustworthiness.
- Passphrase input is hidden and evaluated locally. The module returns only derived metadata; it does not return, log, or save the entered phrase. Its estimate is intentionally rough—not a breach lookup or cracking simulation.
- Reports are not uploaded. Review them before sharing; they may contain private hostnames, addresses, paths, or machine details.
- Use diagnostics only on systems and networks you own or are authorized to inspect.

## Project files

- `stellivor/` — shared Python core, platform adapters, terminal art, UI, and educational security lab
- `tests/` — deterministic automated tests
- `assets/stellivor-emblem.png` — original logo artwork
- `HANDOVER.md` — concise project handover and operating boundaries
- `AI_AGENT_PROJECT_STATEMENT.md` — detailed project brief and continuation instructions for coding agents
- `docs/` — architecture, testing, safety, support, and roadmap

## License

MIT. See `LICENSE`.
