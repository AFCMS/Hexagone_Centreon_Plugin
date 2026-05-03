"""Tests for hexagone.plugin (base framework)."""

import pytest

from hexagone.plugin import (
    STATE_CRITICAL,
    STATE_OK,
    STATE_UNKNOWN,
    STATE_WARNING,
    CheckResult,
    Perfdata,
    Threshold,
)


class TestPerfdata:
    def test_basic(self):
        p = Perfdata(label="cpu", value=45.0, unit="%")
        assert str(p) == "'cpu'=45%"

    def test_with_thresholds(self):
        p = Perfdata(label="cpu", value=45.0, unit="%", warning=80.0, critical=95.0)
        assert str(p) == "'cpu'=45%;80;95"

    def test_with_all_fields(self):
        p = Perfdata(
            label="cpu",
            value=45.0,
            unit="%",
            warning=80.0,
            critical=95.0,
            minimum=0.0,
            maximum=100.0,
        )
        assert str(p) == "'cpu'=45%;80;95;0;100"

    def test_label_spaces_replaced(self):
        p = Perfdata(label="my metric", value=1.0)
        assert str(p).startswith("'my_metric'=")

    def test_float_value(self):
        p = Perfdata(label="latency", value=123.45, unit="ms")
        assert str(p) == "'latency'=123.45ms"

    def test_integer_value_no_decimal(self):
        p = Perfdata(label="count", value=10.0)
        assert str(p) == "'count'=10"

    def test_trailing_empty_fields_stripped(self):
        p = Perfdata(label="x", value=5.0, unit="", warning=10.0)
        result = str(p)
        assert result == "'x'=5;10"


class TestThreshold:
    def test_ok(self):
        t = Threshold(warning=80.0, critical=95.0)
        assert t.get_state(50.0) == STATE_OK

    def test_warning(self):
        t = Threshold(warning=80.0, critical=95.0)
        assert t.get_state(80.0) == STATE_WARNING
        assert t.get_state(90.0) == STATE_WARNING

    def test_critical(self):
        t = Threshold(warning=80.0, critical=95.0)
        assert t.get_state(95.0) == STATE_CRITICAL
        assert t.get_state(99.9) == STATE_CRITICAL

    def test_no_thresholds(self):
        t = Threshold()
        assert t.get_state(999.0) == STATE_OK

    def test_from_args(self):
        t = Threshold.from_args("80", "95")
        assert t.warning == 80.0
        assert t.critical == 95.0

    def test_from_args_none(self):
        t = Threshold.from_args(None, None)
        assert t.warning is None
        assert t.critical is None


class TestCheckResult:
    def test_format_ok_no_perfdata(self):
        r = CheckResult(state=STATE_OK, message="All good")
        assert r.format_output() == "OK - All good"

    def test_format_warning(self):
        r = CheckResult(state=STATE_WARNING, message="High load")
        assert r.format_output() == "WARNING - High load"

    def test_format_critical(self):
        r = CheckResult(state=STATE_CRITICAL, message="Down!")
        assert r.format_output() == "CRITICAL - Down!"

    def test_format_unknown(self):
        r = CheckResult(state=STATE_UNKNOWN, message="Cannot reach host")
        assert r.format_output() == "UNKNOWN - Cannot reach host"

    def test_format_with_perfdata(self):
        r = CheckResult(state=STATE_OK, message="CPU OK")
        r.add_perfdata(Perfdata(label="cpu", value=45.0, unit="%", warning=80.0, critical=95.0))
        output = r.format_output()
        assert "OK - CPU OK" in output
        assert "| 'cpu'=45%;80;95" in output

    def test_format_multiple_perfdata(self):
        r = CheckResult(state=STATE_OK, message="OK")
        r.add_perfdata(Perfdata(label="a", value=1.0))
        r.add_perfdata(Perfdata(label="b", value=2.0))
        output = r.format_output()
        assert "'a'=1" in output
        assert "'b'=2" in output
