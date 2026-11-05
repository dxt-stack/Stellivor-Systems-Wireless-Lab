"""Responsive, dependency-free terminal interface for Stellivor."""
from __future__ import annotations

import getpass
import json
import os
import re
from datetime import datetime
import shutil
import sys
import textwrap
import time
from pathlib import Path
from threading import Event, Thread
from typing import Callable, TextIO

from . import __version__
from .brandmark import EMBLEM_HEIGHT, EMBLEM_ROWS, EMBLEM_WIDTH
from .connections import list_listening_tcp
from .core import Result, Status, detect_platform
from .device import device_readiness
from .file_intel import inspect_file, verify_sha256
from .network import check_tcp, interface_information, resolve_dns, route_information
from .reports import PRIVACY_NOTICE, save_report
from .sdr import simulate_tone
from .security_lab import HARDENING_CHECKLIST, estimate_passphrase_strength
from .system_info import collect_system_info
from .tools import discover_tools
from .wireless import wireless_snapshot


_OUTLINE_FONT: dict[str, tuple[str, ...]] = {
    "S": ("╭─╮", "│  ", "╰─╮", "  │", "╰─╯"),
    "T": ("╭─╮", " │ ", " │ ", " │ ", " │ "),
    "E": ("┌─┐", "│  ", "├─┤", "│  ", "└─┘"),
    "L": ("│  ", "│  ", "│  ", "│  ", "└─┘"),
    "I": ("─┬─", " │ ", " │ ", " │ ", "─┴─"),
    "V": ("│ │", "│ │", "│ │", "╲ ╱", " ╲╱"),
    "O": ("╭─╮", "│ │", "│ │", "│ │", "╰─╯"),
    "R": ("╭─╮", "│ │", "├─╯", "│╲ ", "│ ╲"),
}
_ASCII_OUTLINE_FONT: dict[str, tuple[str, ...]] = {
    "S": ("+-+", "|  ", "+-+", "  |", "+-+"),
    "T": ("+-+", " | ", " | ", " | ", " | "),
    "E": ("+-+", "|  ", "+-+", "|  ", "+-+"),
    "L": ("|  ", "|  ", "|  ", "|  ", "+-+"),
    "I": ("-+-", " | ", " | ", " | ", "-+-"),
    "V": ("| |", "| |", "| |", "\\ /", " V "),
    "O": ("+-+", "| |", "| |", "| |", "+-+"),
    "R": ("+-+", "| |", "+-+", "|\\ ", "| \\"),
}

_THEMES: dict[str, dict[str, str]] = {
    "stellivor": {
        "primary": "\033[38;2;69;222;235m", "secondary": "\033[38;2;151;128;255m",
        "accent": "\033[38;2;255;190;92m", "success": "\033[38;2;104;220;145m",
        "warning": "\033[38;2;255;202;96m", "danger": "\033[38;2;255;105;123m",
        "magenta": "\033[38;2;221;125;255m", "muted": "\033[38;2;135;145;165m",
    },
    "ember": {
        "primary": "\033[38;2;255;143;79m", "secondary": "\033[38;2;255;205;96m",
        "accent": "\033[38;2;98;220;180m", "success": "\033[38;2;127;220;142m",
        "warning": "\033[38;2;255;204;100m", "danger": "\033[38;2;255;100;100m",
        "magenta": "\033[38;2;236;124;180m", "muted": "\033[38;2;155;140;130m",
    },
    "ice": {
        "primary": "\033[38;2;91;205;255m", "secondary": "\033[38;2;175;143;255m",
        "accent": "\033[38;2;255;222;140m", "success": "\033[38;2;99;225;185m",
        "warning": "\033[38;2;255;210;117m", "danger": "\033[38;2;255;116;150m",
        "magenta": "\033[38;2;214;151;255m", "muted": "\033[38;2;134;155;180m",
    },
}


class StellivorUI:
    """A compact mobile-friendly shell around the shared diagnostic core."""

    COLORS = {
        Status.SUCCESS: "\033[32m",
        Status.FAILURE: "\033[31m",
        Status.WARNING: "\033[33m",
        Status.UNSUPPORTED: "\033[35m",
        Status.PERMISSION_RESTRICTED: "\033[33m",
        Status.DEPENDENCY_MISSING: "\033[33m",
        Status.SIMULATION: "\033[36m",
        Status.IN_PROGRESS: "\033[34m",
    }
    CYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[32m"
    MUTED = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(
        self,
        *,
        input_fn: Callable[[str], str] = input,
        output: TextIO | None = None,
        use_color: bool | None = None,
        animate: bool | None = None,
        pace_results: bool | None = None,
        theme: str = "stellivor",
        clock_fn: Callable[[], datetime] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.input_fn = input_fn
        self.output = output or sys.stdout
        is_tty = bool(getattr(self.output, "isatty", lambda: False)())
        if use_color is None:
            use_color = is_tty and os.environ.get("TERM", "") != "dumb" and "NO_COLOR" not in os.environ
        self.use_color = bool(use_color)
        if theme not in _THEMES:
            raise ValueError(f"Unknown theme {theme!r}; choose from {', '.join(sorted(_THEMES))}.")
        self.theme = theme
        palette = _THEMES[theme]
        self.CYAN = palette["primary"]
        self.BLUE = palette["secondary"]
        self.GOLD = palette["accent"]
        self.GREEN = palette["success"]
        self.YELLOW = palette["warning"]
        self.RED = palette["danger"]
        self.MAGENTA = palette["magenta"]
        self.MUTED = palette["muted"]
        self.COLORS = {
            Status.SUCCESS: self.GREEN,
            Status.FAILURE: self.RED,
            Status.WARNING: self.YELLOW,
            Status.UNSUPPORTED: self.MAGENTA,
            Status.PERMISSION_RESTRICTED: self.YELLOW,
            Status.DEPENDENCY_MISSING: self.YELLOW,
            Status.SIMULATION: self.CYAN,
            Status.IN_PROGRESS: self.BLUE,
        }
        if animate is None:
            animate = is_tty
        self.animate = bool(animate and is_tty)
        self.live_clock_enabled = self.animate
        self.pace_results = bool(is_tty if pace_results is None else (pace_results and is_tty))
        self.clock_fn = clock_fn or (lambda: datetime.now().astimezone())
        self.sleep_fn = sleep_fn
        encoding = getattr(self.output, "encoding", None) or "utf-8"
        self.unicode = "utf" in encoding.lower()
        self.results: list[Result] = []
        self.running = True
        self.last_choice: str | None = None

    def _paint(self, text: str, color: str, *, bold: bool = False) -> str:
        if not self.use_color:
            return text
        return f"{self.BOLD if bold else ''}{color}{text}{self.RESET}"

    def width(self) -> int:
        columns = shutil.get_terminal_size((44, 24)).columns
        return max(24, min(columns, 76))

    def write(self, text: str = "") -> None:
        self.output.write(text + "\n")
        self.output.flush()

    def _clock_details(self, now: datetime | None = None) -> tuple[datetime, str, str]:
        current = now if now is not None else self.clock_fn()
        if current.tzinfo is None:
            current = current.astimezone()
        zone = current.tzname() or "LOCAL"
        offset = current.strftime("%z")
        if len(offset) == 5:
            offset = f"UTC{offset[:3]}:{offset[3:]}"
        else:
            offset = "UTC"
        return current, zone, offset

    def _local_clock_label(self) -> str:
        now, zone, offset = self._clock_details()
        return f"{now.strftime('%H:%M:%S')}.{now.microsecond // 100000}  {zone}  /  {offset}"

    def _menu_clock_line(self) -> str:
        now, zone, offset = self._clock_details()
        full = f"  LOCAL  {now.strftime('%H:%M:%S')}.{now.microsecond // 100000}  {zone}  /  {offset}"
        if len(full) > self.width():
            zone_width = max(1, self.width() - 10 - len(offset))
            full = f"{now.strftime('%H:%M:%S')} {zone[:zone_width]} {offset}"
        return self._paint(full[:self.width()], self.MUTED)

    def _live_clock_loop(self, stop: Event) -> None:
        """Refresh the menu clock while the interactive main-menu prompt waits."""
        while not stop.is_set():
            now, _zone, _offset = self._clock_details()
            delay = max(0.05, 1.0 - now.microsecond / 1_000_000)
            if stop.wait(delay):
                return
            try:
                # Save/restore the cursor so typed input on the prompt line is untouched.
                self.output.write("\033[s\033[1A\r" + self._menu_clock_line() + "\033[K\033[u")
                self.output.flush()
            except (OSError, ValueError):
                stop.set()
                return

    def _menu_input(self) -> str:
        if not (self.animate and self.live_clock_enabled and self.input_fn is input and getattr(self.output, "isatty", lambda: False)()):
            return self.input_fn("Select: ").strip()
        stop = Event()
        ticker = Thread(target=self._live_clock_loop, args=(stop,), name="stellivor-clock", daemon=True)
        ticker.start()
        try:
            return self.input_fn("Select: ").strip()
        finally:
            stop.set()
            ticker.join(timeout=1.1)

    def _startup_clock(self) -> None:
        if not self.animate:
            self.write(self._paint("  LOCAL  " + self._local_clock_label(), self.MUTED))
            return
        frames = ("·", "◔", "◑", "◕", "●", "✦") if self.unicode else (".", "o", "O", "0", "O", "*")
        for frame in frames:
            line = (
                self._paint("  LOCAL  ", self.MUTED)
                + self._paint(self._local_clock_label(), self.GREEN, bold=True)
                + self._paint("  " + frame, self.GOLD, bold=True)
            )
            self.output.write("\r" + line + "\033[K")
            self.output.flush()
            self.sleep_fn(0.09)
        self.output.write("\n")
        self.output.flush()

    def _dragon_transition(self, label: str) -> None:
        if not self.animate:
            return
        dragon = "🐉" if self.unicode else "<DRGN>"
        frames = ("·", "✧", "✦", "✧") if self.unicode else (".", "o", "*", ".")
        dragon_width = 2 if self.unicode else len(dragon)
        label_width = max(1, self.width() - (2 + dragon_width + 2 + 3))
        short_label = label.upper()[:label_width]
        for index, frame in enumerate(frames, start=1):
            visible_length = max(1, (len(short_label) * index + len(frames) - 1) // len(frames))
            visible_label = short_label[:visible_length]
            line = (
                self._paint("  " + dragon, self.CYAN, bold=True)
                + self._paint("  " + visible_label, self.MUTED)
                + self._paint("  " + frame, self.GOLD, bold=True)
            )
            self.output.write("\r" + line + "\033[K")
            self.output.flush()
            self.sleep_fn(0.045)
        self.output.write("\n")
        self.output.flush()

    def _logo_rows(self) -> list[str]:
        font = _OUTLINE_FONT if self.unicode else _ASCII_OUTLINE_FONT
        letters = "STELLIVOR"
        return [" ".join(font[letter][row_index] for letter in letters).rstrip() for row_index in range(5)]

    def _emblem_matrix(self) -> list[list[tuple[int, int, int] | None]]:
        matrix: list[list[tuple[int, int, int] | None]] = []
        for row in EMBLEM_ROWS:
            pixels = []
            for token in row.split():
                pixels.append(None if token == "......" else tuple(int(token[i:i + 2], 16) for i in (0, 2, 4)))
            matrix.append(pixels)
        if len(matrix) != EMBLEM_HEIGHT or any(len(row) != EMBLEM_WIDTH for row in matrix):
            raise ValueError("Bundled terminal emblem dimensions are invalid.")
        return matrix

    @staticmethod
    def _brighten_emblem_color(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """Lift dark pixels and increase color separation for small terminal art."""
        luminance = (rgb[0] * 3 + rgb[1] * 6 + rgb[2]) // 10
        return tuple(
            min(255, max(0, round(luminance + (channel - luminance) * 1.35 + 28)))
            for channel in rgb
        )

    def _draw_emblem(self) -> None:
        source = self._emblem_matrix()
        columns = max(16, min(40, self.width() - 4))
        target_width = columns * 2
        target_height = max(4, (columns // 2) * 4)
        matrix: list[list[tuple[int, int, int] | None]] = []
        for y in range(target_height):
            source_y = min(EMBLEM_HEIGHT - 1, int((y + 0.5) * EMBLEM_HEIGHT / target_height))
            row = []
            for x in range(target_width):
                source_x = min(EMBLEM_WIDTH - 1, int((x + 0.5) * EMBLEM_WIDTH / target_width))
                row.append(source[source_y][source_x])
            matrix.append(row)

        dot_positions = ((0, 0, 0), (0, 1, 3), (1, 0, 1), (1, 1, 4),
                         (2, 0, 2), (2, 1, 5), (3, 0, 6), (3, 1, 7))
        density = " .:-=+*#%@"
        for cell_y in range(0, target_height, 4):
            line = ["  "]
            for cell_x in range(0, target_width, 2):
                pixels = []
                mask = 0
                for dy, dx, bit in dot_positions:
                    pixel = matrix[cell_y + dy][cell_x + dx]
                    if pixel is not None:
                        mask |= 1 << bit
                        pixels.append(pixel)
                if not pixels:
                    line.append(" ")
                    continue
                if self.use_color and self.unicode:
                    average = tuple(sum(pixel[index] for pixel in pixels) // len(pixels) for index in range(3))
                    rgb = self._brighten_emblem_color(average)
                    line.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{chr(0x2800 + mask)}")
                else:
                    luminance = sum((r * 3 + g * 6 + b) // 10 for r, g, b in pixels) // len(pixels)
                    luminance = min(255, (luminance * 4 + 255) // 5)
                    line.append(density[min(len(density) - 1, luminance * len(density) // 256)])
            if self.use_color and self.unicode:
                self.output.write("".join(line) + self.RESET + "\n")
            else:
                self.write("".join(line).rstrip())
        if self.use_color and self.unicode:
            self.output.flush()

    def banner(self) -> None:
        self.write()
        self._draw_emblem()
        if self.width() >= 37:
            for index, row in enumerate(self._logo_rows()):
                color = self.CYAN if index % 2 == 0 else self.BLUE
                self.write(self._paint("  " + row, color, bold=True))
        else:
            self.write(self._paint("  STELLIVOR", self.CYAN, bold=True))
        self.write(self._paint("  SYSTEMS  /  WIRELESS  /  SIGNALS", self.BLUE, bold=True))
        separator = "•" if self.unicode else "/"
        self.write(self._paint(f"  Local workbench  {separator}  v{__version__}", self.GREEN))
        self.write("  STARTUP SCANS  /  NONE")
        self.write(self._paint(f"  PLATFORM  /  {detect_platform().label}", self.GREEN))
        self.write(self._paint(f"  PYTHON  /  {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", self.GREEN))
        self._startup_clock()
        self.write(self._paint("  READY  /  choose an operation", self.GREEN))

    def panel(self, title: str, rows: list[str]) -> None:
        width = self.width()
        inner = max(12, width - 6)
        if self.unicode:
            top_left, top_right, side, bottom_left, bottom_right, rule = "╭", "╮", "│", "╰", "╯", "─"
        else:
            top_left, top_right, side, bottom_left, bottom_right, rule = "+", "+", "|", "+", "+", "-"
        self.write(self._paint("  " + top_left + rule * (inner + 2) + top_right, self.CYAN))
        title_text = title[:inner]
        self.write(self._paint("  " + side + " ", self.CYAN) + self._paint(title_text.ljust(inner), self.BOLD, bold=True) + self._paint(" " + side, self.CYAN))
        self.write(self._paint("  " + side + " " + rule * inner + " " + side, self.MUTED))
        section_colors = {"OBSERVE": self.CYAN, "INSPECT & LEARN": self.BLUE, "TOOLS & REPORTS": self.GOLD}
        for row in rows:
            section_color = section_colors.get(row)
            wrapped = [row] if section_color else textwrap.wrap(row, width=inner, subsequent_indent="  ", break_long_words=True, break_on_hyphens=False) or [""]
            for line in wrapped:
                body = self._paint(line.ljust(inner), section_color, bold=True) if section_color else line.ljust(inner)
                self.write(self._paint("  " + side, self.CYAN) + " " + body + " " + self._paint(side, self.CYAN))
        self.write(self._paint("  " + bottom_left + rule * (inner + 2) + bottom_right, self.CYAN))

    def menu(self) -> None:
        adapter = detect_platform().label
        rows = [
            "OBSERVE",
            "  1   System profile",
            "  2   Network diagnostics",
            "  3   Wireless snapshot",
            "  4   Listening connections",
            "INSPECT & LEARN",
            "  5   File intelligence",
            "  6   SHA-256 integrity check",
            "  7   SDR lab  [SIMULATION]",
            "  8   Wireless security lab",
            "TOOLS & REPORTS",
            "  9   Optional tool catalog",
            " 10   Export session report",
            " 11   Quick local audit  [READ-ONLY]",
            " 12   Authorized device readiness  [ADB / READ-ONLY]",
            "  0   Exit",
        ]
        self.write()
        self.panel(f"STELLIVOR  /  {adapter}", rows)
        self.write(self._paint(f"  Session results recorded: {len(self.results)}", self.MUTED))
        if self.animate:
            action = "pause" if self.live_clock_enabled else "resume"
            self.write(self._paint(f"  P+Enter {action} clock", self.MUTED))
        self.write(self._menu_clock_line())

    def help_screen(self) -> None:
        self.panel("NAVIGATION / REAL CAPABILITIES", [
            "Numbers  Open an operation",
            "?         Show this help",
            "/         Open the command palette",
            "r         Rerun the last operation",
            "e         Export the current session locally",
            "p         Pause or resume the live clock",
            "q         Quit without uploading anything",
            "All diagnostics run only after you choose them; no startup scan is performed.",
        ])

    def command_palette(self) -> None:
        self.panel("COMMAND PALETTE", [
            "system       System profile",
            "network      Network diagnostics",
            "wireless     Wireless snapshot",
            "device       Authorized ADB/device readiness",
            "file         Read-only file intelligence",
            "integrity    SHA-256 integrity check",
            "sdr          Synthetic SDR learning lab",
            "audit        Quick local audit",
            "export       Export this session locally",
            "help         Show navigation help",
            "Type a command name or Q to close the palette.",
        ])
        aliases = {"system": "1", "network": "2", "wireless": "3", "device": "12", "file": "5", "integrity": "6", "sdr": "7", "audit": "11", "export": "10", "help": "?"}
        choice = self.input_fn("Command: ").strip().lower()
        if choice == "q" or not choice:
            return
        if choice == "?":
            self.help_screen()
        elif choice in aliases:
            if aliases[choice] == "?":
                self.help_screen()
            elif aliases[choice] == "10":
                self.export_menu()
            else:
                self.dispatch(aliases[choice])
        else:
            self.write("Unknown command. Type / again to reopen the palette.")

    def _wrap(self, text: str, *, indent: str = "  ") -> list[str]:
        return textwrap.wrap(
            str(text),
            width=max(20, self.width() - len(indent)),
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=True,
            break_on_hyphens=False,
        ) or [indent]

    def _color_json_segment(self, segment: str) -> str:
        if ":" not in segment:
            return segment
        key, value = segment.split(":", 1)
        if not key.lstrip().startswith('"'):
            return segment
        whitespace = value[:len(value) - len(value.lstrip())]
        payload = value.lstrip()
        bare_value = payload.rstrip(",")
        if payload.startswith('"'):
            color = self.GREEN
        elif bare_value in {"true", "false"}:
            color = self.MAGENTA
        elif bare_value == "null":
            color = self.MUTED
        elif payload[:1] in set("-0123456789"):
            color = self.GOLD
        else:
            color = self.BLUE
        return self._paint(key + ":", self.CYAN) + whitespace + self._paint(payload, color)

    def _emit_result_lines(self, lines: list[str]) -> None:
        if not lines:
            return
        delay = min(0.018, 0.8 / len(lines)) if self.pace_results else 0.0
        for line in lines:
            self.output.write(line + "\n")
            self.output.flush()
            if delay:
                self.sleep_fn(delay)

    def print_result(self, result: Result, *, max_data_characters: int = 10000) -> None:
        lines = [""]
        status = result.status.value.upper().replace("_", " ")
        lines.append(self._paint(f"[{status}] {result.module} / {result.operation}", self.COLORS.get(result.status, self.CYAN), bold=True))
        lines.extend(self._wrap(result.summary))
        for warning in result.warnings:
            lines.extend(self._paint(line, self.YELLOW) for line in self._wrap("NOTE: " + warning))
        for error in result.errors:
            lines.extend(self._paint(line, self.RED) for line in self._wrap("ERROR: " + error))
        if result.data:
            rendered = json.dumps(result.to_dict()["data"], indent=2, ensure_ascii=False, sort_keys=True)
            if len(rendered) > max_data_characters:
                rendered = rendered[:max_data_characters] + "\n... DISPLAY TRUNCATED; session export retains the result ..."
            lines.append(self._paint("  DETAILS", self.GOLD, bold=True))
            for raw_line in rendered.splitlines():
                indent = len(raw_line) - len(raw_line.lstrip())
                prefix = " " * indent
                content = raw_line[indent:]
                available = max(20, self.width() - len(prefix) - 2)
                segments = textwrap.wrap(content, width=available, subsequent_indent="  ", break_long_words=True, break_on_hyphens=False) or [""]
                lines.extend("  " + prefix + self._color_json_segment(segment) for segment in segments)
        self._emit_result_lines(lines)

    def record(self, result: Result) -> None:
        self.results.append(result)
        self.print_result(result)

    def pause(self) -> None:
        try:
            self.input_fn("\nPress Enter to return to the menu...")
        except (EOFError, KeyboardInterrupt):
            self.running = False

    def prompt(self, label: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        value = self.input_fn(f"{label}{suffix}: ").strip()
        return value if value else (default or "")

    def network_menu(self) -> None:
        while self.running:
            self.panel("NETWORK DIAGNOSTICS", [
                "1  Resolve one DNS hostname",
                "2  Check one TCP endpoint (single attempt)",
                "3  Show interfaces",
                "4  Show routes",
                "0  Back",
            ])
            choice = self.input_fn("Select: ").strip()
            if choice == "0":
                return
            submenu_labels = {"1": "DNS LOOKUP", "2": "SINGLE TCP CHECK", "3": "INTERFACES", "4": "ROUTES"}
            if choice in submenu_labels:
                self._dragon_transition(submenu_labels[choice])
            if choice == "1":
                self.record(resolve_dns(self.prompt("Hostname", "localhost")))
            elif choice == "2":
                host = self.prompt("Hostname or IP", "127.0.0.1")
                try:
                    port = int(self.prompt("TCP port", "80"))
                except ValueError:
                    self.record(Result("network", "single_tcp_check", Status.FAILURE, "Invalid TCP port.", errors=["Enter a whole number from 1 to 65535."]))
                    continue
                self.record(check_tcp(host, port))
            elif choice == "3":
                self.record(interface_information())
            elif choice == "4":
                self.record(route_information())
            else:
                self.write("Choose one of the displayed numbers.")

    def file_menu(self) -> None:
        path = self.prompt("Path to a local file (read-only)")
        if path:
            self.record(inspect_file(path))
        else:
            self.write("No file selected.")

    def integrity_menu(self) -> None:
        path = self.prompt("Path to a local file")
        expected = self.prompt("Expected SHA-256 (64 hex characters)")
        if path:
            self.record(verify_sha256(path, expected))
        else:
            self.write("No file selected.")

    def sdr_menu(self) -> None:
        self.panel("SDR LEARNING LAB  /  SYNTHETIC ONLY", [
            "This creates mathematical IQ samples; it does not listen to radio hardware.",
            "1,024 samples at 48 kHz is a good mobile starting point.",
        ])
        try:
            frequency = float(self.prompt("Tone frequency in Hz", "1000"))
            sample_rate = float(self.prompt("Sample rate in Hz", "48000"))
            count = int(self.prompt("Sample count (2-65536)", "1024"))
            noise = float(self.prompt("Synthetic noise standard deviation", "0"))
            seed = int(self.prompt("Noise seed", "0"))
        except ValueError:
            self.record(Result("sdr", "synthetic_tone", Status.FAILURE, "Invalid numeric input.", errors=["Frequency, rate, and noise must be numeric; sample count and seed must be integers."], data={"simulated": True, "live_rf_capture": False}))
            return
        self.record(simulate_tone(frequency, sample_rate, count, noise_stddev=noise, seed=seed))

    def wireless_security_menu(self) -> None:
        while self.running:
            self.panel("WIRELESS SECURITY LAB  /  DEFENSIVE", [
                "1  Review a permitted wireless snapshot",
                "2  Estimate a test passphrase (hidden input; never saved)",
                "3  Router hardening checklist",
                "4  Safe recovery guidance for your own router",
                "0  Back",
            ])
            choice = self.input_fn("Select: ").strip()
            if choice == "0":
                return
            submenu_labels = {"1": "WIRELESS SNAPSHOT", "2": "PASSPHRASE ESTIMATE", "3": "HARDENING CHECKLIST", "4": "OWNER RECOVERY"}
            if choice in submenu_labels:
                self._dragon_transition(submenu_labels[choice])
            if choice == "1":
                self.record(wireless_snapshot())
            elif choice == "2":
                try:
                    password = getpass.getpass("Enter a test phrase (input hidden): ")
                except (EOFError, KeyboardInterrupt):
                    self.write("Cancelled; no estimate was recorded.")
                    continue
                result = estimate_passphrase_strength(password)
                del password
                self.record(result)
            elif choice == "3":
                self.hardening_checklist()
            elif choice == "4":
                self.recovery_guidance()
            else:
                self.write("Choose one of the displayed numbers.")

    def hardening_checklist(self) -> None:
        checked: set[int] = set()
        while True:
            rows = [f"{index}. [{'x' if index in checked else ' '}] {item}" for index, item in enumerate(HARDENING_CHECKLIST, 1)]
            rows.extend([f"Progress: {len(checked)}/{len(HARDENING_CHECKLIST)}", "Enter an item number to toggle, or Q to finish."])
            self.panel("OWN-ROUTER HARDENING CHECKLIST", rows)
            choice = self.input_fn("Item or Q: ").strip().lower()
            if choice == "q":
                result = Result(
                    "security_lab", "router_hardening_checklist", Status.SUCCESS,
                    "Saved the checklist completion state in this session only.",
                    data={"completed_count": len(checked), "total_count": len(HARDENING_CHECKLIST), "checked_items": [HARDENING_CHECKLIST[i - 1] for i in sorted(checked)], "persisted_to_disk": False},
                )
                self.record(result)
                return
            if choice.isdigit() and 1 <= int(choice) <= len(HARDENING_CHECKLIST):
                self._dragon_transition("CHECKLIST UPDATE")
                index = int(choice)
                if index in checked:
                    checked.remove(index)
                else:
                    checked.add(index)
            else:
                self.write("Enter a listed number or Q.")

    def recovery_guidance(self) -> None:
        self.record(Result(
            "security_lab", "owner_recovery_guidance", Status.SUCCESS,
            "Use official recovery paths for a network you own or administer.",
            data={"steps": [
                "Check the router label or official router-management app/web page.",
                "Use an already-authorized device or account to review settings through its normal UI.",
                "Contact the ISP or router manufacturer using official support.",
                "If necessary, reset your own router and set a new unique passphrase.",
            ], "nearby_network_passwords_retrieved": False, "saved_keys_extracted": False},
            warnings=["A nearby-network scan cannot reveal a network's password. Stellivor never extracts saved Wi-Fi keys."],
        ))

    def quick_local_audit(self) -> None:
        self.panel("QUICK LOCAL AUDIT  /  READ-ONLY", [
            "Collects system health, interfaces, routes, visible listening sockets, and optional-tool presence.",
            "No DNS/TCP probing, nearby Wi-Fi scan, installation, or configuration change is included.",
        ])
        for operation in (collect_system_info, interface_information, route_information, list_listening_tcp, discover_tools):
            self.record(operation())

    def export_menu(self) -> None:
        if not self.results:
            self.write("No session results to export yet.")
            return
        self.write(PRIVACY_NOTICE)
        directory = self.prompt("Local report directory", str(Path.cwd() / "reports"))
        self.print_result(save_report(self.results, directory))

    def dispatch(self, choice: str) -> None:
        if choice == "0":
            self.running = False
            return
        actions: dict[str, Callable[[], None]] = {
            "1": lambda: self.record(collect_system_info()),
            "2": self.network_menu,
            "3": lambda: self.record(wireless_snapshot()),
            "4": lambda: self.record(list_listening_tcp()),
            "5": self.file_menu,
            "6": self.integrity_menu,
            "7": self.sdr_menu,
            "8": self.wireless_security_menu,
            "9": lambda: self.record(discover_tools()),
            "10": self.export_menu,
            "11": self.quick_local_audit,
            "12": lambda: self.record(device_readiness()),
        }
        action = actions.get(choice)
        if action is None:
            self.write("Unknown selection. Choose 0-12, or use ?, /, r, e, or q.")
            return
        labels = {
            "1": "SYSTEM PROFILE", "2": "NETWORK DIAGNOSTICS", "3": "WIRELESS SNAPSHOT",
            "4": "LISTENING CONNECTIONS", "5": "FILE INTELLIGENCE", "6": "SHA-256 INTEGRITY",
            "7": "SDR SIMULATION", "8": "WIRELESS SECURITY", "9": "TOOL CATALOG",
            "10": "REPORT EXPORT", "11": "QUICK LOCAL AUDIT",
            "12": "AUTHORIZED DEVICE READINESS",
        }
        self.last_choice = choice
        self._dragon_transition(labels[choice])
        try:
            action()
        except (EOFError, KeyboardInterrupt):
            self.running = False
        except Exception as exc:
            self.record(Result("ui", "operation_guard", Status.FAILURE, "An operation failed unexpectedly; the menu remains usable.", errors=[f"{type(exc).__name__}: {exc}"]))

    def run(self) -> int:
        self.banner()
        while self.running:
            try:
                self.menu()
                choice = self._menu_input()
                normalized = choice.strip().lower()
                if normalized in {"?", "help"}:
                    self.help_screen()
                    continue
                if normalized in {"/", "palette"}:
                    self.command_palette()
                    continue
                if normalized == "r":
                    if self.last_choice:
                        self.dispatch(self.last_choice)
                    else:
                        self.write("No operation has been run yet.")
                    continue
                if normalized == "e":
                    self.export_menu()
                    continue
                if normalized in {"q", "quit", "exit"}:
                    self.running = False
                    continue
                if normalized == "p":
                    if self.animate:
                        self.live_clock_enabled = not self.live_clock_enabled
                        state = "paused; periodic terminal writes stopped" if not self.live_clock_enabled else "resumed"
                        self.write(self._paint(f"Live clock {state}.", self.MUTED))
                    else:
                        self.write("Clock animation is disabled in this mode.")
                    continue
                self.dispatch(choice.strip())
            except (EOFError, KeyboardInterrupt):
                self.write("\nInput closed. Exiting cleanly.")
                break
        self.write("STELLIVOR closed. Session data was not uploaded.")
        return 0


def main(
    *,
    use_color: bool | None = None,
    animate: bool | None = None,
    pace_results: bool | None = None,
    theme: str = "stellivor",
) -> int:
    return StellivorUI(use_color=use_color, animate=animate, pace_results=pace_results, theme=theme).run()
