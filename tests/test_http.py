"""Tests for the HTTP check mode."""

import argparse
import io
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from hexagone.modes.http import HttpMode
from hexagone.plugin import STATE_CRITICAL, STATE_OK, STATE_WARNING


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "url": "http://example.com",
        "expected_code": 200,
        "timeout": 10,
        "warning": None,
        "critical": None,
        "string": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestHttpMode:
    def _mock_response(self, status: int = 200, body: bytes = b"OK"):
        resp = MagicMock()
        resp.status = status
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    def test_ok_200(self):
        args = _make_args()
        mode = HttpMode(args)
        with patch("urllib.request.urlopen", return_value=self._mock_response(200)):
            result = mode.check()
        assert result.state == STATE_OK

    def test_unexpected_status_code(self):
        args = _make_args(expected_code=200)
        mode = HttpMode(args)
        with patch("urllib.request.urlopen", return_value=self._mock_response(404)):
            result = mode.check()
        assert result.state == STATE_WARNING
        assert "404" in result.message

    def test_server_error_status_code(self):
        args = _make_args(expected_code=200)
        mode = HttpMode(args)
        with patch("urllib.request.urlopen", return_value=self._mock_response(500)):
            result = mode.check()
        assert result.state == STATE_CRITICAL

    def test_connection_failure(self):
        args = _make_args()
        mode = HttpMode(args)
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            result = mode.check()
        assert result.state == STATE_CRITICAL
        assert "Connection failed" in result.message

    def test_string_found(self):
        args = _make_args(string="Welcome")
        mode = HttpMode(args)
        with patch(
            "urllib.request.urlopen",
            return_value=self._mock_response(200, b"Welcome to the site"),
        ):
            result = mode.check()
        assert result.state == STATE_OK

    def test_string_not_found(self):
        args = _make_args(string="Missing text")
        mode = HttpMode(args)
        with patch(
            "urllib.request.urlopen",
            return_value=self._mock_response(200, b"Hello world"),
        ):
            result = mode.check()
        assert result.state == STATE_CRITICAL
        assert "Missing text" in result.message

    def test_response_time_warning(self):
        args = _make_args(warning="100", critical="500")
        mode = HttpMode(args)

        resp = self._mock_response(200)

        import time

        def slow_open(*a, **kw):
            return resp

        with patch("urllib.request.urlopen", side_effect=slow_open):
            with patch("time.monotonic", side_effect=[0.0, 0.2]):
                result = mode.check()

        assert result.state == STATE_WARNING

    def test_perfdata_present(self):
        args = _make_args()
        mode = HttpMode(args)
        with patch("urllib.request.urlopen", return_value=self._mock_response(200)):
            result = mode.check()
        assert any(p.label == "response_time" for p in result.perfdata)

    def test_http_error_handled(self):
        args = _make_args(expected_code=200)
        mode = HttpMode(args)
        exc = urllib.error.HTTPError(
            url="http://example.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            result = mode.check()
        assert result.state == STATE_WARNING
        assert "403" in result.message
