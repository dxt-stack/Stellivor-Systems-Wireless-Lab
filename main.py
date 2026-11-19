#!/usr/bin/env python3
"""STELLIVOR terminal entry point and direct command interface."""
from __future__ import annotations

import argparse
import json

from stellivor import __version__
from stellivor.cli import main as run_cli
from stellivor.system_info import collect_system_info
from stellivor.ui import main as run_ui


def main() -> int:
    parser = argparse.ArgumentParser(description="STELLIVOR // Systems & Wireless Lab")
    parser.add_argument("--version", action="version", version=f"STELLIVOR {__version__}")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI terminal colors")
    parser.add_argument("--theme", choices=("stellivor", "ember", "ice"), default="stellivor", help="Choose a restrained terminal color theme")
    parser.add_argument("--fast-output", action="store_true", help="Legacy alias; print result lines immediately")
    parser.add_argument("--paced-output", action="store_true", help="Reveal result lines gradually (optional presentation mode)")
    animation = parser.add_mutually_exclusive_group()
    animation.add_argument("--animation", action="store_true", help="Enable live clock ticking and dragon cues on an interactive terminal")
    animation.add_argument("--no-animation", action="store_true", help="Keep the clock static and disable dragon transitions")
    parser.add_argument("--system-json", action="store_true", help="Print one real system profile as JSON and exit")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Optional direct command; use `main.py device --help` for command help.")
    arguments = parser.parse_args()
    if arguments.system_json:
        print(json.dumps(collect_system_info().to_dict(), indent=2, sort_keys=True))
        return 0
    if arguments.command:
        return run_cli(arguments.command)
    animate = True if arguments.animation else False if arguments.no_animation else None
    return run_ui(
        use_color=False if arguments.no_color else None,
        animate=animate,
        pace_results=True if arguments.paced_output else False,
        theme=arguments.theme,
    )


if __name__ == "__main__":
    raise SystemExit(main())
