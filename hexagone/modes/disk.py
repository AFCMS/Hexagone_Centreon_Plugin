"""Disk usage check mode (requires psutil)."""

import argparse

import psutil

from hexagone.plugin import BasePlugin, CheckResult, Perfdata, STATE_UNKNOWN, Threshold


def _bytes_to_gb(b: int) -> float:
    return round(b / (1024 ** 3), 2)


class DiskMode(BasePlugin):
    """Check disk space usage for a given mount point."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.path: str = args.path
        self.threshold = Threshold.from_args(args.warning, args.critical)

    def check(self) -> CheckResult:
        try:
            usage = psutil.disk_usage(self.path)
        except FileNotFoundError:
            return CheckResult(
                state=STATE_UNKNOWN,
                message=f"Path not found: {self.path}",
            )
        except PermissionError:
            return CheckResult(
                state=STATE_UNKNOWN,
                message=f"Permission denied accessing: {self.path}",
            )

        used_pct = usage.percent
        used_gb = _bytes_to_gb(usage.used)
        total_gb = _bytes_to_gb(usage.total)
        free_gb = _bytes_to_gb(usage.free)

        state = self.threshold.get_state(used_pct)

        return CheckResult(
            state=state,
            message=(
                f"Disk usage on {self.path}: {used_pct:.1f}% "
                f"({used_gb:.1f} GB used / {total_gb:.1f} GB total, "
                f"{free_gb:.1f} GB free)"
            ),
            perfdata=[
                Perfdata(
                    label="disk_used",
                    value=used_gb,
                    unit="GB",
                    minimum=0,
                    maximum=total_gb,
                ),
                Perfdata(
                    label="disk_used_pct",
                    value=round(used_pct, 1),
                    unit="%",
                    warning=self.threshold.warning,
                    critical=self.threshold.critical,
                    minimum=0,
                    maximum=100,
                ),
            ],
        )

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-p",
            "--path",
            default="/",
            metavar="PATH",
            help="Mount point / path to check (default: /)",
        )
        parser.add_argument(
            "-w",
            "--warning",
            default="80",
            metavar="PERCENT",
            help="Warning threshold for disk usage in %% (default: 80)",
        )
        parser.add_argument(
            "-c",
            "--critical",
            default="90",
            metavar="PERCENT",
            help="Critical threshold for disk usage in %% (default: 90)",
        )
