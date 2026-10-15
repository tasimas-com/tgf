#!/usr/bin/env python3
"""Unit tests for the pinned-frequency and bare-metal runner preflight."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from check_benchmark_host import verify_bare_metal, verify_pinned_frequency


class BenchmarkHostPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = self.root / "cpufreq" / "policy0"
        self.policy.mkdir(parents=True)
        self._write("scaling_governor", "performance\n")
        self._write("scaling_min_freq", "3200000\n")
        self._write("scaling_max_freq", "3200000\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, name: str, value: str) -> None:
        (self.policy / name).write_text(value, encoding="utf-8")

    def test_accepts_performance_governor_and_fixed_frequency(self) -> None:
        ok, messages = verify_pinned_frequency(self.root)
        self.assertTrue(ok, messages)
        self.assertIn("fixed frequency verified", messages[0])

    def test_rejects_non_performance_governor(self) -> None:
        self._write("scaling_governor", "powersave\n")
        ok, messages = verify_pinned_frequency(self.root)
        self.assertFalse(ok)
        self.assertTrue(any("governor" in message for message in messages))

    def test_rejects_frequency_scaling(self) -> None:
        self._write("scaling_max_freq", "4200000\n")
        ok, messages = verify_pinned_frequency(self.root)
        self.assertFalse(ok)
        self.assertTrue(any("not pinned" in message for message in messages))

    def test_rejects_missing_frequency_controls(self) -> None:
        (self.policy / "scaling_max_freq").unlink()
        ok, messages = verify_pinned_frequency(self.root)
        self.assertFalse(ok)
        self.assertTrue(any("unavailable" in message for message in messages))

    def test_rejects_host_without_frequency_policies(self) -> None:
        empty_root = self.root / "empty"
        empty_root.mkdir()
        ok, messages = verify_pinned_frequency(empty_root)
        self.assertFalse(ok)
        self.assertTrue(any("No CPU frequency policy" in message for message in messages))

    def test_accepts_x86_64_when_systemd_reports_no_vm(self) -> None:
        cpuinfo = self.root / "cpuinfo"
        cpuinfo.write_text("flags : fpu sse sse2 avx2\n", encoding="utf-8")
        ok, messages = verify_bare_metal(
            machine="x86_64",
            cpuinfo_path=cpuinfo,
            detector=lambda: (1, ""),
        )
        self.assertTrue(ok, messages)
        self.assertTrue(any("no VM" in message for message in messages))

    def test_rejects_virtual_machine_reported_by_systemd(self) -> None:
        cpuinfo = self.root / "cpuinfo"
        cpuinfo.write_text("flags : fpu sse sse2\n", encoding="utf-8")
        ok, messages = verify_bare_metal(
            machine="x86_64",
            cpuinfo_path=cpuinfo,
            detector=lambda: (0, "kvm"),
        )
        self.assertFalse(ok)
        self.assertTrue(any("virtual machine: kvm" in message for message in messages))

    def test_rejects_hypervisor_cpu_flag_even_if_detector_says_none(self) -> None:
        cpuinfo = self.root / "cpuinfo"
        cpuinfo.write_text("flags : fpu sse hypervisor\n", encoding="utf-8")
        ok, messages = verify_bare_metal(
            machine="x86_64",
            cpuinfo_path=cpuinfo,
            detector=lambda: (1, ""),
        )
        self.assertFalse(ok)
        self.assertTrue(any("hypervisor flag" in message for message in messages))

    def test_rejects_non_x86_64_architecture(self) -> None:
        cpuinfo = self.root / "cpuinfo"
        cpuinfo.write_text("flags : fpu sse sse2\n", encoding="utf-8")
        ok, messages = verify_bare_metal(
            machine="aarch64",
            cpuinfo_path=cpuinfo,
            detector=lambda: (1, ""),
        )
        self.assertFalse(ok)
        self.assertTrue(any("must be x86_64" in message for message in messages))

    def test_fails_closed_when_virtualization_detection_is_unavailable(self) -> None:
        cpuinfo = self.root / "cpuinfo"
        cpuinfo.write_text("flags : fpu sse sse2\n", encoding="utf-8")

        def unavailable() -> tuple[int, str]:
            raise FileNotFoundError("systemd-detect-virt missing")

        ok, messages = verify_bare_metal(
            machine="x86_64",
            cpuinfo_path=cpuinfo,
            detector=unavailable,
        )
        self.assertFalse(ok)
        self.assertTrue(any("cannot prove bare-metal" in message for message in messages))


if __name__ == "__main__":
    unittest.main(verbosity=2)
