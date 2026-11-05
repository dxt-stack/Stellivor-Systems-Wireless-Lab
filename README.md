# STELLIVOR // Systems & Wireless Lab

![Stellivor: binary-circuit dragon guarding a stellar sphere](assets/stellivor-emblem.png)

**Stellivor** is a cross-platform, offline-first systems and wireless learning workbench. The name is a coined, Latin-inspired “star-devourer”; the literal phrase “the one who devoured a star” is *qui stellam devoravit*.

Version: **0.5.3**.

**Scope, plainly:** STELLIVOR is a Python diagnostics app, not Kali Linux or NetHunter. It does not install Kali, provide root/kernel drivers, or contain hundreds of third-party tools. Its purpose is a fast, local, defensive workbench; it won't claim NetHunter-level capability.

## A terminal that feels like a workbench

The terminal renders the selected dragon-and-star emblem as compact true-colour Braille art, with brighter, more saturated colors and an outlined STELLIVOR wordmark. On interactive terminals, startup briefly animates the **actual local clock**, timezone abbreviation, and UTC offset; while the landing menu waits for input, the seconds keep ticking and roll through minutes and hours. At the menu, type `P` then Enter to pause the live clock before scrolling back; press it again to resume. Pausing stops periodic terminal writes. Choosing an operation reveals its short label in a smooth, brief text transition beside the tiny dragon mark, before that option's content appears. These are interface cues only—no scans or diagnostics run until selected. Result lines reveal at a brief bounded pace with semantic colors; choose `stellivor`, `ember`, or `ice`, and use `--fast-output` to remove result pacing. `--no-animation` keeps the clock static and disables dragon transitions; non-interactive output stays immediate.

```sh
python main.py --theme ember
python main.py --theme ice --fast-output
python main.py --no-color
```

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

No third-party Python package, root access, account, API key, telemetry, or cloud analysis is required for the core. Optional native utilities and Android permissions may affect particular features.

## Safe WiFi Inspector reuse

The supplied WiFi Inspector archive was reviewed before integration. Stellivor reuses the safe product ideas—wireless status, security guidance, a checklist, and a local passphrase estimate—through its own modular, capability-aware code.

**Not included:** saved Wi-Fi key extraction (`key=clear`), John the Ripper/Hashcat password-cracking workflows, handshake capture, backdoor tools, exploit menus, or unauthorized attack features. On Windows, Stellivor can show saved profile names where native support permits; it does not request key material. Android/Termux cannot be assumed to expose saved profiles.

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
