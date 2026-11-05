# Testing STELLIVOR

## Deterministic suite

Run from the project root:

```sh
python -m unittest discover -s tests -v
```

On Windows, `py -3` may replace `python`.

Version 0.5.3 contains 72 deterministic tests covering:

- result serialization, status aggregation, platform detection, subprocess timeouts, and bounded stdout/stderr;
- SHA-256 known vectors, partial/full hashing, digest comparison, signature hints, string limits, and read-only inspection;
- synthetic IQ generation, RMS, FFT bins, reproducible noise, finite-value validation, and invalid parameters;
- report generation, error/limitation preservation, privacy notices, and local JSON/Markdown writes;
- hostname validation and mocked DNS/TCP outcomes without external network access;
- representative Linux and Termux wireless adapter parsing with mocked commands, not real radio scans;
- local passphrase-estimator behavior, no-secret-return guarantee, and hardening checklist;
- tool-discovery semantics; brighter true-colour emblem, outlined/ASCII wordmark, startup and per-second live local clock with timezone/offset, pause/resume without background writes, progressive selection-label reveal before content with a bounded dragon cue, non-TTY immediacy, narrow-panel wrapping, and the read-only quick-audit bundle; filtered Termux battery data;
- paced interactive result reveal with a bounded delay, semantic JSON colors, and selectable theme palettes.

A passing test suite proves only those tested behaviors in the recorded environment. It does not prove Termux, Windows, macOS, wireless hardware, or live network behavior.

## Smoke tests

```sh
python main.py --version
printf '0\n' | python main.py --no-color --no-animation
python main.py --system-json
```

Expected: version is `STELLIVOR 0.5.3`; the noninteractive menu exits cleanly; system JSON is valid. Non-TTY output stays immediate, and no diagnostic runs automatically. On an interactive terminal, the actual local clock shows timezone/offset at startup and continues ticking once per second while the landing menu waits. Press `P` + Enter to stop ticker writes for scrollback; valid selections show the progressive dragon cue.

## Termux validation checklist

1. Record `python --version` and verify the package version.
2. Run the full test suite.
3. Launch interactively; check the wordmark and menu at phone width.
4. Try system profile, file inspection, a known SHA-256 vector, and synthetic SDR.
5. Check the passphrase estimator using a test phrase only; confirm no phrase appears in results or report output.
6. Export a local JSON/Markdown report and inspect it before sharing.
7. Check interface/route/listener visibility; record unavailable commands or permissions.
8. Perform DNS/TCP only if desired and only against an authorized endpoint.
9. Try a wireless snapshot only if Termux:API is already configured; distinguish unavailable from a genuine empty scan.

## Cross-platform status

Run native adapters on real Windows, Linux distributions, macOS versions, and Android devices before claiming support for them. Mocked platform tests are not device tests. No SDR receiver is needed by the deterministic suite.
