# Platform support and validation status

STELLIVOR reports local capabilities honestly. Mocked adapter tests do not establish real-device support.

## Current automated validation

| Check | Result |
|---|---|
| Maintainer-reported Termux run | **101 tests passed**; source/test compilation and `git diff --check` also passed. This is a test run, not complete native-feature validation. |
| GitHub Actions | **Passed** on the public repository for Python 3.10, 3.11, 3.12, and 3.13. |
| CI workflow | Compiles `stellivor`, `tests`, and `main.py`, then runs `python -m unittest discover -s tests -v`. |
| Latest recorded successful run | Run `44540449096`, commit `f1a15a5` (`Fix wireless adapter test fixtures`). |
| Scope of CI | Deterministic unit tests and compilation on Ubuntu runners; not native Windows/macOS testing, Android hardware validation, or live Wi-Fi testing. |

The public repository uses standard GitHub-hosted runners. GitHub documents standard runner use for public repositories as free; larger runners and other separately billed services are outside this statement. See GitHub's [Actions billing and usage](https://docs.github.com/en/actions/concepts/billing-and-usage) documentation.

## Android / Termux

The maintainer has run the current deterministic suite in Termux with 101 passing tests. The current version still needs a separate real-device checklist for interactive visual behavior and the native Android integrations; a passing Python test suite does not prove that Termux:API, Wi-Fi scanning, ADB, or device permissions work on a particular phone.

Android is detected separately from desktop Linux. Wireless visibility may require an already configured Termux:API package/app and Android permissions; Android can still restrict results. Battery status may likewise be unavailable without the compatible Termux:API components. STELLIVOR does not install packages automatically. Saved-profile listing and saved-key retrieval are unsupported through the current Android/Termux adapter.

## Other platforms

- Linux: deterministic tests and selected adapter behavior are covered in CI and workspace tests; real results depend on distribution, installed utilities, locale, and permissions.
- Windows: platform parsing is covered with mocks; real Windows native commands and UI remain unverified for the current release.
- macOS: platform detection is covered with mocks; real native commands and UI remain unverified for the current release.
- SDR hardware: no live hardware adapter is implemented or claimed.

Only mark an adapter as validated after it is exercised on its actual OS and capability, with its limitations documented.
