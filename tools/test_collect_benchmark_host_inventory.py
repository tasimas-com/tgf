#!/usr/bin/env python3
"""Regression tests for the read-only benchmark-host inventory collector."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from collect_benchmark_host_inventory import collect_inventory


class BenchmarkHostInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cpu_root = self.root / "sys" / "devices" / "system" / "cpu"
        self.policy = self.cpu_root / "cpufreq" / "policy0"
        self.policy.mkdir(parents=True)
        self.thermal_root = self.root / "sys" / "class" / "thermal"
        self.zone = self.thermal_root / "thermal_zone0"
        self.zone.mkdir(parents=True)
        self.hwmon_root = self.root / "sys" / "class" / "hwmon"
        self.hwmon = self.hwmon_root / "hwmon0"
        self.hwmon.mkdir(parents=True)
        self.dmi_root = self.root / "sys" / "class" / "dmi" / "id"
        self.dmi_root.mkdir(parents=True)
        self.proc_root = self.root / "proc"
        self.proc_root.mkdir()

        for name, value in {
            "scaling_driver": "amd-pstate-epp\n",
            "scaling_governor": "performance\n",
            "scaling_min_freq": "3200000\n",
            "scaling_max_freq": "3200000\n",
            "cpuinfo_min_freq": "800000\n",
            "cpuinfo_max_freq": "5000000\n",
            "scaling_available_governors": "performance powersave\n",
            "scaling_available_frequencies": "3200000 4000000 5000000\n",
            "related_cpus": "0 1\n",
            "affected_cpus": "0 1\n",
            "energy_performance_preference": "performance\n",
        }.items():
            (self.policy / name).write_text(value, encoding="utf-8")

        (self.zone / "type").write_text("x86_pkg_temp\n", encoding="utf-8")
        (self.zone / "temp").write_text("47000\n", encoding="utf-8")
        (self.hwmon / "name").write_text("k10temp\n", encoding="utf-8")
        (self.hwmon / "temp1_input").write_text("51000\n", encoding="utf-8")
        (self.hwmon / "temp1_label").write_text("Tctl\n", encoding="utf-8")
        (self.hwmon / "temp1_crit").write_text("95000\n", encoding="utf-8")

        for name, value in {
            "sys_vendor": "Example Server Vendor\n",
            "product_name": "Example Bare Metal Model\n",
            "bios_vendor": "Example Firmware Vendor\n",
            "bios_version": "1.2.3\n",
            "bios_date": "10/01/2026\n",
            "product_serial": "MUST_NOT_BE_COLLECTED\n",
        }.items():
            (self.dmi_root / name).write_text(value, encoding="utf-8")

        self.cpuinfo = self.proc_root / "cpuinfo"
        self.cpuinfo.write_text(
            "processor : 0\n"
            "vendor_id : AuthenticAMD\n"
            "cpu family : 25\n"
            "model : 17\n"
            "stepping : 1\n"
            "model name : Example CPU\n"
            "physical id : 0\n"
            "core id : 0\n"
            "cpu cores : 2\n"
            "siblings : 2\n"
            "microcode : 0x123\n"
            "flags : fpu sse sse2 avx2\n\n"
            "processor : 1\n"
            "vendor_id : AuthenticAMD\n"
            "model name : Example CPU\n"
            "physical id : 0\n"
            "core id : 1\n",
            encoding="utf-8",
        )
        self.meminfo = self.proc_root / "meminfo"
        self.meminfo.write_text("MemTotal:       8388608 kB\nMemFree: 100000 kB\n", encoding="utf-8")
        self.os_release = self.root / "os-release"
        self.os_release.write_text(
            'NAME="Example Linux"\nVERSION_ID="1.0"\nID=example\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _command_runner(command: list[str]) -> dict:
        if command[:2] == ["systemd-detect-virt", "--vm"]:
            return {"available": True, "returncode": 1, "output": []}
        return {
            "available": True,
            "returncode": 0,
            "output": [f"{command[0]} test-version"],
        }

    def _collect(self, *, cpuinfo: Path | None = None) -> dict:
        return collect_inventory(
            cpu_sysfs_root=self.cpu_root,
            thermal_sysfs_root=self.thermal_root,
            hwmon_sysfs_root=self.hwmon_root,
            dmi_sysfs_root=self.dmi_root,
            cpuinfo_path=cpuinfo or self.cpuinfo,
            meminfo_path=self.meminfo,
            os_release_path=self.os_release,
            command_runner=self._command_runner,
            environment={
                "GITHUB_ACTIONS": "true",
                "RUNNER_ARCH": "X64",
                "GITHUB_RUN_ID": "12345",
                "GITHUB_TOKEN": "must-not-be-captured",
            },
        )

    def test_collects_cpu_memory_os_and_frequency_policy(self) -> None:
        report = self._collect()
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["host"]["os_release"]["NAME"], "Example Linux")
        self.assertEqual(report["hardware"]["cpu"]["model_name"], "Example CPU")
        self.assertEqual(report["hardware"]["cpu"]["logical_processors"], 2)
        self.assertEqual(report["hardware"]["cpu"]["physical_cores_visible"], 2)
        self.assertEqual(report["hardware"]["memory"]["total_bytes"], 8388608 * 1024)
        self.assertEqual(len(report["frequency_policies"]), 1)
        self.assertTrue(report["frequency_policies"][0]["pinned"])

    def test_collects_thermal_and_firmware_information(self) -> None:
        report = self._collect()
        self.assertEqual(report["thermal"]["thermal_zones"][0]["temperature_c"], 47.0)
        self.assertEqual(report["thermal"]["hwmon_sensors"][0]["temperature_c"], 51.0)
        self.assertEqual(report["hardware"]["dmi"]["bios_version"], "1.2.3")
        self.assertNotIn("product_serial", report["hardware"]["dmi"])

    def test_runner_metadata_is_allowlisted(self) -> None:
        report = self._collect()
        self.assertEqual(report["host"]["runner"]["GITHUB_RUN_ID"], "12345")
        self.assertNotIn("GITHUB_TOKEN", report["host"]["runner"])

    def test_records_virtualization_cpu_flag(self) -> None:
        self.cpuinfo.write_text(
            self.cpuinfo.read_text(encoding="utf-8").replace("avx2", "avx2 hypervisor"),
            encoding="utf-8",
        )
        report = self._collect()
        self.assertTrue(report["host"]["virtualization"]["detected"])

    def test_missing_sysfs_data_is_reported_without_crashing(self) -> None:
        empty_cpu_root = self.root / "empty-cpu"
        empty_cpu_root.mkdir()
        empty_thermal_root = self.root / "empty-thermal"
        empty_thermal_root.mkdir()
        report = collect_inventory(
            cpu_sysfs_root=empty_cpu_root,
            thermal_sysfs_root=empty_thermal_root,
            hwmon_sysfs_root=empty_thermal_root,
            dmi_sysfs_root=empty_thermal_root,
            cpuinfo_path=self.root / "missing-cpuinfo",
            meminfo_path=self.root / "missing-meminfo",
            os_release_path=self.root / "missing-os-release",
            command_runner=self._command_runner,
            environment={},
        )
        self.assertEqual(report["frequency_policies"], [])
        self.assertIsNone(report["hardware"]["cpu"]["logical_processors"])
        self.assertGreaterEqual(len(report["warnings"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
