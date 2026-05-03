"""CPU usage check mode (requires psutil)."""

import argparse

import psutil

from hexagone.plugin import BasePlugin, CheckResult, Perfdata, Threshold


class CpuMode(BasePlugin):
    """Check overall CPU usage (1-second sample)."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.threshold = Threshold.from_args(args.warning, args.critical)
        self.per_cpu: bool = args.per_cpu

    def check(self) -> CheckResult:
        # interval=1 blocks for 1 second for a meaningful sample
        if self.per_cpu:
            percentages = psutil.cpu_percent(interval=1, percpu=True)
            avg = sum(percentages) / len(percentages)
            state = self.threshold.get_state(avg)

            perfdata = [
                Perfdata(
                    label=f"cpu{i}",
                    value=round(pct, 1),
                    unit="%",
                    warning=self.threshold.warning,
                    critical=self.threshold.critical,
                    minimum=0,
                    maximum=100,
                )
                for i, pct in enumerate(percentages)
            ]
            perfdata.insert(
                0,
                Perfdata(
                    label="cpu_avg",
                    value=round(avg, 1),
                    unit="%",
                    warning=self.threshold.warning,
                    critical=self.threshold.critical,
                    minimum=0,
                    maximum=100,
                ),
            )

            return CheckResult(
                state=state,
                message=f"CPU average usage: {avg:.1f}%",
                perfdata=perfdata,
            )

        pct = psutil.cpu_percent(interval=1)
        state = self.threshold.get_state(pct)

        return CheckResult(
            state=state,
            message=f"CPU usage: {pct:.1f}%",
            perfdata=[
                Perfdata(
                    label="cpu",
                    value=round(pct, 1),
                    unit="%",
                    warning=self.threshold.warning,
                    critical=self.threshold.critical,
                    minimum=0,
                    maximum=100,
                )
            ],
        )

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-w",
            "--warning",
            default="80",
            metavar="PERCENT",
            help="Warning threshold for CPU usage in %% (default: 80)",
        )
        parser.add_argument(
            "-c",
            "--critical",
            default="95",
            metavar="PERCENT",
            help="Critical threshold for CPU usage in %% (default: 95)",
        )
        parser.add_argument(
            "--per-cpu",
            action="store_true",
            help="Report usage per CPU core in addition to average",
        )
