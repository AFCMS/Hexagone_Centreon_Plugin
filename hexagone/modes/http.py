"""HTTP/HTTPS endpoint check mode."""

import argparse
import time
import urllib.error
import urllib.request
from typing import Optional

from hexagone.plugin import (
    BasePlugin,
    CheckResult,
    Perfdata,
    STATE_CRITICAL,
    STATE_OK,
    STATE_UNKNOWN,
    STATE_WARNING,
    Threshold,
)


class HttpMode(BasePlugin):
    """Check that an HTTP/HTTPS endpoint is reachable and returns an expected status code."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.url: str = args.url
        self.expected_code: int = args.expected_code
        self.timeout: int = args.timeout
        self.time_threshold = Threshold.from_args(args.warning, args.critical)
        self.string: Optional[str] = args.string

    def check(self) -> CheckResult:
        start = time.monotonic()
        try:
            req = urllib.request.Request(self.url)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = time.monotonic() - start
                code = resp.status
                body = resp.read().decode(errors="replace")
        except urllib.error.HTTPError as exc:
            elapsed = time.monotonic() - start
            code = exc.code
            body = ""
        except urllib.error.URLError as exc:
            return CheckResult(
                state=STATE_CRITICAL,
                message=f"Connection failed: {exc.reason}",
            )
        except TimeoutError:
            return CheckResult(
                state=STATE_CRITICAL,
                message=f"Connection timed out after {self.timeout}s",
            )

        elapsed_ms = elapsed * 1000

        # Check string presence in body
        if self.string and self.string not in body:
            return CheckResult(
                state=STATE_CRITICAL,
                message=f"String '{self.string}' not found in response",
                perfdata=[
                    Perfdata(
                        label="response_time",
                        value=round(elapsed_ms, 2),
                        unit="ms",
                        warning=self.time_threshold.warning,
                        critical=self.time_threshold.critical,
                        minimum=0,
                    )
                ],
            )

        # Check HTTP status code
        if code != self.expected_code:
            state = STATE_WARNING if code < 500 else STATE_CRITICAL
            return CheckResult(
                state=state,
                message=f"HTTP {code} (expected {self.expected_code})",
                perfdata=[
                    Perfdata(
                        label="response_time",
                        value=round(elapsed_ms, 2),
                        unit="ms",
                        warning=self.time_threshold.warning,
                        critical=self.time_threshold.critical,
                        minimum=0,
                    )
                ],
            )

        # Check response time thresholds
        time_state = self.time_threshold.get_state(elapsed_ms)
        state_label = {STATE_OK: "OK", STATE_WARNING: "WARNING", STATE_CRITICAL: "CRITICAL"}.get(
            time_state, "UNKNOWN"
        )

        return CheckResult(
            state=time_state,
            message=f"HTTP {code} - {elapsed_ms:.0f}ms response time ({state_label})",
            perfdata=[
                Perfdata(
                    label="response_time",
                    value=round(elapsed_ms, 2),
                    unit="ms",
                    warning=self.time_threshold.warning,
                    critical=self.time_threshold.critical,
                    minimum=0,
                )
            ],
        )

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-U",
            "--url",
            required=True,
            help="URL to check (e.g. https://example.com)",
        )
        parser.add_argument(
            "-e",
            "--expected-code",
            type=int,
            default=200,
            metavar="CODE",
            help="Expected HTTP status code (default: 200)",
        )
        parser.add_argument(
            "-s",
            "--string",
            default=None,
            metavar="STRING",
            help="String that must be present in the HTTP response body",
        )
        parser.add_argument(
            "-w",
            "--warning",
            default=None,
            metavar="MS",
            help="Warning threshold for response time in milliseconds",
        )
        parser.add_argument(
            "-c",
            "--critical",
            default=None,
            metavar="MS",
            help="Critical threshold for response time in milliseconds",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            type=int,
            default=10,
            metavar="SECONDS",
            help="Connection timeout in seconds (default: 10)",
        )
