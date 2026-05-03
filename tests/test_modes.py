"""Tests for CPU, memory, and disk check modes."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from hexagone.modes.cpu import CpuMode
from hexagone.modes.disk import DiskMode
from hexagone.modes.memory import MemoryMode
from hexagone.plugin import STATE_CRITICAL, STATE_OK, STATE_UNKNOWN, STATE_WARNING


def _cpu_args(**kwargs) -> argparse.Namespace:
    defaults = {"warning": "80", "critical": "95", "per_cpu": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _mem_args(**kwargs) -> argparse.Namespace:
    defaults = {"warning": "80", "critical": "95"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _disk_args(**kwargs) -> argparse.Namespace:
    defaults = {"path": "/", "warning": "80", "critical": "90"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCpuMode:
    def test_ok(self):
        with patch("psutil.cpu_percent", return_value=50.0):
            result = CpuMode(_cpu_args()).check()
        assert result.state == STATE_OK
        assert "50.0%" in result.message

    def test_warning(self):
        with patch("psutil.cpu_percent", return_value=85.0):
            result = CpuMode(_cpu_args()).check()
        assert result.state == STATE_WARNING

    def test_critical(self):
        with patch("psutil.cpu_percent", return_value=98.0):
            result = CpuMode(_cpu_args()).check()
        assert result.state == STATE_CRITICAL

    def test_per_cpu(self):
        with patch("psutil.cpu_percent", return_value=[30.0, 40.0, 50.0, 60.0]):
            result = CpuMode(_cpu_args(per_cpu=True)).check()
        assert result.state == STATE_OK
        assert any(p.label == "cpu_avg" for p in result.perfdata)
        assert any(p.label == "cpu0" for p in result.perfdata)

    def test_perfdata_present(self):
        with patch("psutil.cpu_percent", return_value=45.0):
            result = CpuMode(_cpu_args()).check()
        assert any(p.label == "cpu" for p in result.perfdata)


class TestMemoryMode:
    def _mock_vmem(self, percent: float, used: int, total: int, available: int):
        mem = MagicMock()
        mem.percent = percent
        mem.used = used
        mem.total = total
        mem.available = available
        return mem

    def test_ok(self):
        mem = self._mock_vmem(50.0, 4 * 1024**3, 8 * 1024**3, 4 * 1024**3)
        with patch("psutil.virtual_memory", return_value=mem):
            result = MemoryMode(_mem_args()).check()
        assert result.state == STATE_OK

    def test_warning(self):
        mem = self._mock_vmem(85.0, 7 * 1024**3, 8 * 1024**3, 1 * 1024**3)
        with patch("psutil.virtual_memory", return_value=mem):
            result = MemoryMode(_mem_args()).check()
        assert result.state == STATE_WARNING

    def test_critical(self):
        mem = self._mock_vmem(96.0, 7 * 1024**3, 8 * 1024**3, 1 * 1024**3)
        with patch("psutil.virtual_memory", return_value=mem):
            result = MemoryMode(_mem_args()).check()
        assert result.state == STATE_CRITICAL

    def test_perfdata_present(self):
        mem = self._mock_vmem(50.0, 4 * 1024**3, 8 * 1024**3, 4 * 1024**3)
        with patch("psutil.virtual_memory", return_value=mem):
            result = MemoryMode(_mem_args()).check()
        labels = [p.label for p in result.perfdata]
        assert "memory_used" in labels
        assert "memory_used_pct" in labels


class TestDiskMode:
    def _mock_usage(self, percent: float, used: int, total: int, free: int):
        usage = MagicMock()
        usage.percent = percent
        usage.used = used
        usage.total = total
        usage.free = free
        return usage

    def test_ok(self):
        usage = self._mock_usage(50.0, 50 * 1024**3, 100 * 1024**3, 50 * 1024**3)
        with patch("psutil.disk_usage", return_value=usage):
            result = DiskMode(_disk_args()).check()
        assert result.state == STATE_OK

    def test_warning(self):
        usage = self._mock_usage(85.0, 85 * 1024**3, 100 * 1024**3, 15 * 1024**3)
        with patch("psutil.disk_usage", return_value=usage):
            result = DiskMode(_disk_args()).check()
        assert result.state == STATE_WARNING

    def test_critical(self):
        usage = self._mock_usage(92.0, 92 * 1024**3, 100 * 1024**3, 8 * 1024**3)
        with patch("psutil.disk_usage", return_value=usage):
            result = DiskMode(_disk_args()).check()
        assert result.state == STATE_CRITICAL

    def test_path_not_found(self):
        with patch("psutil.disk_usage", side_effect=FileNotFoundError):
            result = DiskMode(_disk_args(path="/nonexistent")).check()
        assert result.state == STATE_UNKNOWN

    def test_permission_denied(self):
        with patch("psutil.disk_usage", side_effect=PermissionError):
            result = DiskMode(_disk_args()).check()
        assert result.state == STATE_UNKNOWN

    def test_perfdata_present(self):
        usage = self._mock_usage(50.0, 50 * 1024**3, 100 * 1024**3, 50 * 1024**3)
        with patch("psutil.disk_usage", return_value=usage):
            result = DiskMode(_disk_args()).check()
        labels = [p.label for p in result.perfdata]
        assert "disk_used" in labels
        assert "disk_used_pct" in labels
