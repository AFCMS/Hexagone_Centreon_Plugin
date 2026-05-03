"""Base plugin framework: exit codes, threshold management, and output formatting."""

import sys
from dataclasses import dataclass, field
from typing import Optional


# Nagios/Centreon standard exit codes
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

STATE_LABELS = {
    STATE_OK: "OK",
    STATE_WARNING: "WARNING",
    STATE_CRITICAL: "CRITICAL",
    STATE_UNKNOWN: "UNKNOWN",
}


@dataclass
class Perfdata:
    """A single performance data metric in Centreon/Nagios format.

    Format: label=value[unit];[warn];[crit];[min];[max]
    """

    label: str
    value: float
    unit: str = ""
    warning: Optional[float] = None
    critical: Optional[float] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def _fmt(self, v: Optional[float]) -> str:
        if v is None:
            return ""
        return str(int(v) if v == int(v) else v)

    def __str__(self) -> str:
        label = self.label.replace(" ", "_").replace("'", "")
        value = self._fmt(self.value)
        parts = [
            f"'{label}'={value}{self.unit}",
            self._fmt(self.warning),
            self._fmt(self.critical),
            self._fmt(self.minimum),
            self._fmt(self.maximum),
        ]
        # Strip trailing empty fields
        while parts and parts[-1] == "":
            parts.pop()
        return ";".join(parts)


@dataclass
class CheckResult:
    """Holds the result of a single check."""

    state: int
    message: str
    perfdata: list[Perfdata] = field(default_factory=list)

    def add_perfdata(self, metric: Perfdata) -> None:
        self.perfdata.append(metric)

    def format_output(self) -> str:
        """Return the formatted plugin output line."""
        label = STATE_LABELS.get(self.state, "UNKNOWN")
        line = f"{label} - {self.message}"
        if self.perfdata:
            perf_str = " ".join(str(p) for p in self.perfdata)
            line = f"{line} | {perf_str}"
        return line


class Threshold:
    """Represents a simple numeric threshold (warn/critical)."""

    def __init__(
        self,
        warning: Optional[float] = None,
        critical: Optional[float] = None,
    ) -> None:
        self.warning = warning
        self.critical = critical

    @classmethod
    def from_args(
        cls,
        warning: Optional[str],
        critical: Optional[str],
    ) -> "Threshold":
        """Parse string thresholds from command-line arguments."""
        w = float(warning) if warning is not None else None
        c = float(critical) if critical is not None else None
        return cls(warning=w, critical=c)

    def get_state(self, value: float) -> int:
        """Return the Centreon state for *value* against this threshold."""
        if self.critical is not None and value >= self.critical:
            return STATE_CRITICAL
        if self.warning is not None and value >= self.warning:
            return STATE_WARNING
        return STATE_OK


class BasePlugin:
    """Base class for all check modes.

    Subclasses must implement :meth:`check` which returns a
    :class:`CheckResult`.  Call :meth:`run` to execute and exit.
    """

    VERSION = "1.0.0"

    def check(self) -> CheckResult:
        raise NotImplementedError

    def run(self) -> None:
        """Execute the check, print output, and exit with the proper code."""
        try:
            result = self.check()
        except Exception as exc:  # noqa: BLE001
            result = CheckResult(
                state=STATE_UNKNOWN,
                message=f"Plugin error: {exc}",
            )
        print(result.format_output())
        sys.exit(result.state)
