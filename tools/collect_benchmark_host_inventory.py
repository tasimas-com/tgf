#!/usr/bin/env python3
"""Collect a privacy-conscious, machine-readable inventory for TGF benchmark hosts.

This tool is read-only. It never changes CPU frequency, power, firmware, or
thermal settings. Run it after host configuration and attach the JSON report
to the first benchmark-runner acceptance review.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys
from typing import Any, Callable


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def parse_assignments(path: Path, separator: str = ":") -> dict[str, str]:
    result: dict[str, str] = {}
    raw = read_text(path)
    if raw is None:
        return result
    for line in raw.splitlines():
        if separator not in line:
            continue
        key, value = line.split(separator, 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            result[key] = value
    return result


def parse_os_release(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    raw = read_text(path)
    if raw is None:
        return values
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        try:
            tokens = shlex.split(value, posix=True)
        except ValueError:
            tokens = [value.strip("\"'")]
        values[key] = tokens[0] if tokens else ""
    return values


def parse_cpuinfo(path: Path) -> dict[str, Any]:
    raw = read_text(path)
    if raw is None:
        return {"logical_processors": None, "hypervisor_flag": None}
    records: list[dict[str, str]] = []
    for block in re.split(r"\n\s*\n", raw):
        record: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            record[key.strip()] = value.strip()
        if record:
            records.append(record)
    if not records:
        return {"logical_processors": None, "hypervisor_flag": None}

    first = records[0]
    flags = set(first.get("flags", first.get("Features", "")).split())
    physical_ids = {r.get("physical id") for r in records if r.get("physical id") is not None}
    core_pairs = {
        (r.get("physical id", "0"), r.get("core id"))
        for r in records
        if r.get("core id") is not None
    }

    physical_cores: int | None = len(core_pairs) if core_pairs else None
    if physical_cores is None and first.get("cpu cores"):
        try:
            physical_cores = int(first["cpu cores"]) * max(1, len(physical_ids))
        except ValueError:
            physical_cores = None

    return {
        "vendor": first.get("vendor_id", first.get("CPU implementer")),
        "model_name": first.get("model name", first.get("Hardware")),
        "family": first.get("cpu family"),
        "model": first.get("model"),
        "stepping": first.get("stepping"),
        "microcode": first.get("microcode"),
        "logical_processors": sum(1 for r in records if "processor" in r) or len(records),
        "physical_cores_visible": physical_cores,
        "physical_packages_visible": len(physical_ids) if physical_ids else None,
        "threads_per_core_reported": first.get("siblings"),
        "cpu_flags": sorted(flags),
        "hypervisor_flag": "hypervisor" in flags,
    }


def parse_meminfo(path: Path) -> dict[str, int | None]:
    values = parse_assignments(path)
    total = values.get("MemTotal")
    try:
        total_bytes = int(total.split()[0]) * 1024 if total else None
    except (ValueError, IndexError):
        total_bytes = None
    return {"total_bytes": total_bytes}


def discover_policies(cpu_sysfs_root: Path) -> list[Path]:
    policy_root = cpu_sysfs_root / "cpufreq"
    policies = sorted(path for path in policy_root.glob("policy[0-9]*") if path.is_dir())
    if policies:
        return policies
    return sorted(
        path for path in cpu_sysfs_root.glob("cpu[0-9]*/cpufreq")
        if path.is_dir()
    )


def collect_frequency_policies(cpu_sysfs_root: Path) -> list[dict[str, Any]]:
    names = (
        "scaling_driver",
        "scaling_governor",
        "scaling_min_freq",
        "scaling_max_freq",
        "cpuinfo_min_freq",
        "cpuinfo_max_freq",
        "scaling_available_governors",
        "scaling_available_frequencies",
        "related_cpus",
        "affected_cpus",
        "energy_performance_preference",
        "energy_performance_available_preferences",
    )
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for policy in discover_policies(cpu_sysfs_root):
        identity = str(policy.resolve())
        if identity in seen:
            continue
        seen.add(identity)
        data = {name: read_text(policy / name) for name in names}
        minimum = data.get("scaling_min_freq")
        maximum = data.get("scaling_max_freq")
        pinned = False
        try:
            min_value = int(minimum or "", 10)
            max_value = int(maximum or "", 10)
            pinned = (
                min_value > 0
                and min_value == max_value
                and data.get("scaling_governor") == "performance"
            )
        except ValueError:
            pass
        result.append({
            "policy": policy.name,
            "sysfs_path": str(policy),
            **data,
            "pinned": pinned,
        })
    return result


def _millidegrees(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return round(int(raw, 10) / 1000.0, 2)
    except ValueError:
        return None


def collect_thermal_zones(thermal_sysfs_root: Path) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for zone in sorted(thermal_sysfs_root.glob("thermal_zone[0-9]*")):
        raw_temp = read_text(zone / "temp")
        zones.append({
            "zone": zone.name,
            "type": read_text(zone / "type"),
            "temperature_millidegrees_c": raw_temp,
            "temperature_c": _millidegrees(raw_temp),
            "mode": read_text(zone / "mode"),
        })
    return zones


def collect_hwmon(hwmon_sysfs_root: Path) -> list[dict[str, Any]]:
    sensors: list[dict[str, Any]] = []
    for chip in sorted(hwmon_sysfs_root.glob("hwmon[0-9]*")):
        chip_name = read_text(chip / "name")
        for input_path in sorted(chip.glob("temp*_input")):
            prefix = input_path.name.removesuffix("_input")
            raw_temp = read_text(input_path)
            sensors.append({
                "chip": chip.name,
                "chip_name": chip_name,
                "sensor": prefix,
                "label": read_text(chip / f"{prefix}_label"),
                "temperature_millidegrees_c": raw_temp,
                "temperature_c": _millidegrees(raw_temp),
                "maximum_millidegrees_c": read_text(chip / f"{prefix}_max"),
                "critical_millidegrees_c": read_text(chip / f"{prefix}_crit"),
            })
    return sensors


def collect_dmi(dmi_sysfs_root: Path) -> dict[str, str]:
    # Serial numbers, UUIDs, asset tags, and product identifiers are deliberately excluded.
    names = (
        "sys_vendor",
        "product_name",
        "product_version",
        "board_vendor",
        "board_name",
        "board_version",
        "bios_vendor",
        "bios_version",
        "bios_date",
    )
    return {
        name: value
        for name in names
        if (value := read_text(dmi_sysfs_root / name)) is not None
    }


def run_command(command: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": str(exc)}
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return {
        "available": True,
        "returncode": completed.returncode,
        "output": lines[:4],
    }


def collect_inventory(
    *,
    cpu_sysfs_root: Path = Path("/sys/devices/system/cpu"),
    thermal_sysfs_root: Path = Path("/sys/class/thermal"),
    hwmon_sysfs_root: Path = Path("/sys/class/hwmon"),
    dmi_sysfs_root: Path = Path("/sys/class/dmi/id"),
    cpuinfo_path: Path = Path("/proc/cpuinfo"),
    meminfo_path: Path = Path("/proc/meminfo"),
    os_release_path: Path = Path("/etc/os-release"),
    command_runner: Callable[[list[str]], dict[str, Any]] = run_command,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    cpu = parse_cpuinfo(cpuinfo_path)
    policies = collect_frequency_policies(cpu_sysfs_root)
    thermal_zones = collect_thermal_zones(thermal_sysfs_root)
    hwmon_sensors = collect_hwmon(hwmon_sysfs_root)
    flags = set(cpu.get("cpu_flags") or [])
    virtualization_command = command_runner(["systemd-detect-virt", "--vm"])
    virt_rc = virtualization_command.get("returncode")
    virt_output = virtualization_command.get("output") or []
    if virt_rc == 0:
        virtualization = {"detected": True, "type": virt_output[0] if virt_output else "unknown"}
    elif virt_rc == 1:
        virtualization = {
            "detected": bool(cpu.get("hypervisor_flag")),
            "type": "none" if "hypervisor" not in flags else "cpu-hypervisor-flag",
        }
    else:
        virtualization = {
            "detected": bool(cpu.get("hypervisor_flag")),
            "type": "unknown",
            "probe": virtualization_command,
        }

    commands = {
        "cmake": command_runner(["cmake", "--version"]),
        "ninja": command_runner(["ninja", "--version"]),
        "cxx": command_runner(["c++", "--version"]),
        "gcc": command_runner(["g++", "--version"]),
        "clang": command_runner(["clang++", "--version"]),
        "git": command_runner(["git", "--version"]),
        "python": command_runner([sys.executable, "--version"]),
        "lscpu": command_runner(["lscpu"]),
    }
    allowed_runner_env = (
        "GITHUB_ACTIONS",
        "RUNNER_OS",
        "RUNNER_ARCH",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_NUMBER",
        "GITHUB_WORKFLOW",
        "GITHUB_JOB",
    )
    env = os.environ if environment is None else environment

    warnings: list[str] = []
    if not policies:
        warnings.append("No CPU frequency policy was exposed; this host cannot pass the pinned-frequency preflight.")
    if not thermal_zones and not hwmon_sensors:
        warnings.append("No thermal sensor readings were exposed through sysfs; record an external sensor/telemetry source.")
    if not cpu.get("model_name"):
        warnings.append("CPU model could not be read from the supplied cpuinfo file.")
    if not collect_dmi(dmi_sysfs_root):
        warnings.append("DMI product/firmware information was unavailable; record it from the system firmware inventory.")

    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": {
            "architecture": platform.machine(),
            "kernel": platform.release(),
            "kernel_name": platform.system(),
            "os_release": parse_os_release(os_release_path),
            "virtualization": virtualization,
            "runner": {key: env[key] for key in allowed_runner_env if key in env},
        },
        "hardware": {
            "cpu": cpu,
            "memory": parse_meminfo(meminfo_path),
            "dmi": collect_dmi(dmi_sysfs_root),
        },
        "frequency_policies": policies,
        "thermal": {
            "thermal_zones": thermal_zones,
            "hwmon_sensors": hwmon_sensors,
        },
        "software": {
            "python_runtime": sys.version.splitlines()[0],
            "versions": commands,
        },
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write JSON to this path; default is stdout")
    parser.add_argument("--cpu-sysfs-root", type=Path, default=Path("/sys/devices/system/cpu"))
    parser.add_argument("--thermal-sysfs-root", type=Path, default=Path("/sys/class/thermal"))
    parser.add_argument("--hwmon-sysfs-root", type=Path, default=Path("/sys/class/hwmon"))
    parser.add_argument("--dmi-sysfs-root", type=Path, default=Path("/sys/class/dmi/id"))
    parser.add_argument("--cpuinfo", type=Path, default=Path("/proc/cpuinfo"))
    parser.add_argument("--meminfo", type=Path, default=Path("/proc/meminfo"))
    parser.add_argument("--os-release", type=Path, default=Path("/etc/os-release"))
    args = parser.parse_args()

    report = collect_inventory(
        cpu_sysfs_root=args.cpu_sysfs_root,
        thermal_sysfs_root=args.thermal_sysfs_root,
        hwmon_sysfs_root=args.hwmon_sysfs_root,
        dmi_sysfs_root=args.dmi_sysfs_root,
        cpuinfo_path=args.cpuinfo,
        meminfo_path=args.meminfo,
        os_release_path=args.os_release,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write inventory to {args.output}: {exc}", file=sys.stderr)
            return 1
        print(f"Inventory written to {args.output}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
