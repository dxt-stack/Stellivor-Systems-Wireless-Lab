# Platform support and validation status

STELLIVOR reports local capabilities honestly. Mocked adapter tests do not establish real-device support.

## Recorded workspace validation (0.5.3 baseline)

| Check | Result |
|---|---|
| Test environment | CPython 3.13.16, Linux x86_64, kernel 6.1.158+ |
| Automated tests | **72 passed**, with `ResourceWarning` treated as an error |
| Syntax | `py_compile` passed with `SyntaxWarning` treated as an error |
| Entry point | `STELLIVOR 0.5.3`; version, system JSON, and menu-exit smoke checks passed |
| Terminal | Brighter Braille/true-colour emblem, outlined wordmark, ASCII fallback, startup and per-second live local clock/timezone/offset, `P` pause/resume with no writes while paused, progressive option-label reveal before content with dragon cue, narrow-panel wrapping, paced output, and three color palettes tested |
| System profile | Local memory and home-filesystem storage fields returned on the QA host |
| Termux battery | API response filtering tested with a mock; no real battery API was available in this QA environment |
| Interfaces and routes | Linux `ip` adapters returned local results |
| Listening sockets | Linux native utility returned a local snapshot |
| Wireless | `nmcli` was absent; adapter reported `dependency_missing`. No wireless scan was run. |
| SDR | Synthetic IQ simulation succeeded; no RF hardware was used |
| Reports | Local JSON/Markdown export succeeded; no upload occurred |
| Network | No DNS query or TCP endpoint check was made during this QA pass |

Workspace checks are not device checks.

## Android / Termux

An earlier STELLIVOR release was demonstrated in Android/Termux. The current 0.6.0 release and its Wi-Fi Inspector integration still require current-version on-device validation; workspace and mocked tests cannot substitute for that check.

Android is detected separately from desktop Linux. Wireless visibility may require an already configured Termux:API package/app and Android permissions; Android can still restrict results. Battery status may likewise be unavailable without the compatible Termux:API components. STELLIVOR does not install packages automatically, and does not expose saved Wi-Fi keys through Android/Termux. Saved-profile key display is supported through native Windows WLAN commands and Linux NetworkManager when permissions and profile configuration allow it; macOS retrieval is not implemented. Key display is an explicit local action and keys are not stored in results or exports.

## Other platforms

- Linux: core suite and selected adapters tested in the listed workspace; other distributions/locales still need validation.
- Windows: platform parsing is covered with mocks; real Windows native commands and UI remain untested for the current release.
- macOS: platform detection is covered with mocks; real native commands and UI remain untested for the current release.
- SDR hardware: no live hardware adapter is implemented or claimed.

Only mark an adapter as validated after it is exercised on its actual OS and capability, with its limitations documented.
