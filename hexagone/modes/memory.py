"""Memory usage check mode (requires psutil)."""

import argparse

import psutil

from hexagone.plugin import BasePlugin, CheckResult, Perfdata, Threshold


def _bytes_to_mb(b: int) -> float:
    return round(b / (1024 ** 2), 2)


class MemoryMode(BasePlugin):
    """Check physical memory (RAM) usage."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.threshold = Threshold.from_args(args.warning, args.critical)

    def check(self) -> CheckResult:
        mem = psutil.virtual_memory()
        used_pct = mem.percent
        used_mb = _bytes_to_mb(mem.used)
        total_mb = _bytes_to_mb(mem.total)
        available_mb = _bytes_to_mb(mem.available)

        state = self.threshold.get_state(used_pct)

        return CheckResult(
            state=state,
            message=(
                f"Memory usage: {used_pct:.1f}% "
                f"({used_mb:.0f} MB used / {total_mb:.0f} MB total, "
                f"{available_mb:.0f} MB available)"
            ),
            perfdata=[
                Perfdata(
                    label="memory_used",
                    value=used_mb,
                    unit="MB",
                    minimum=0,
                    maximum=total_mb,
                ),
                Perfdata(
                    label="memory_used_pct",
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
            "-w",
            "--warning",
            default="80",
            metavar="PERCENT",
            help="Warning threshold for memory usage in %% (default: 80)",
        )
        parser.add_argument(
            "-c",
            "--critical",
            default="95",
            metavar="PERCENT",
            help="Critical threshold for memory usage in %% (default: 95)",
        )
