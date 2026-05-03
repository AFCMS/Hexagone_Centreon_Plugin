#!/usr/bin/env python3
"""Hexagone Centreon Plugin — main entry point.

Usage:
    check_hexagone.py <mode> [options]

Modes:
    http      Check an HTTP/HTTPS endpoint
    cpu       Check CPU usage
    memory    Check memory (RAM) usage
    disk      Check disk space usage
"""

import argparse
import sys

from hexagone.plugin import STATE_UNKNOWN, BasePlugin

VERSION = "1.0.0"

MODES: dict[str, type[BasePlugin]] = {}

try:
    from hexagone.modes.http import HttpMode

    MODES["http"] = HttpMode
except ImportError:
    pass

try:
    from hexagone.modes.cpu import CpuMode
    from hexagone.modes.memory import MemoryMode

    MODES["cpu"] = CpuMode
    MODES["memory"] = MemoryMode
except ImportError:
    pass

try:
    from hexagone.modes.disk import DiskMode

    MODES["disk"] = DiskMode
except ImportError:
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_hexagone",
        description="Hexagone Centreon Plugin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="mode", metavar="MODE")
    subparsers.required = True

    for name, mode_cls in MODES.items():
        sub = subparsers.add_parser(name, help=mode_cls.__doc__)
        mode_cls.add_arguments(sub)

    return parser


def main() -> None:
    if not MODES:
        print("UNKNOWN - No check modes available. Install required dependencies.")
        sys.exit(STATE_UNKNOWN)

    parser = build_parser()
    args = parser.parse_args()

    mode_cls = MODES[args.mode]
    plugin = mode_cls(args)
    plugin.run()


if __name__ == "__main__":
    main()
