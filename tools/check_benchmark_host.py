#!/usr/bin/env python3
"""Fail closed unless a Linux x86-64 benchmark host is explicitly frequency-pinned.

Use --require-bare-metal in the dedicated-runner workflow. That mode requires
systemd-detect-virt to positively establish that no VM is detected.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import platform
import subprocess
import sys
from typing import Callable


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def discover_policies(cpu_sysfs_root: Path) -> list[Path]:
    policy_root = cpu_sysfs_root / "cpufreq"
    policies = sorted(policy_root.glob("policy[0-9]*"))
    if policies:
        return policies
    return sorted(
        path for path in cpu_sysfs_root.glob("cpu[0-9]*/cpufreq")
        if path.is_dir()
    )


def verify_pinned_frequency(cpu_sysfs_root: Path) -> tuple[bool, list[str]]:
    policies = discover_policies(cpu_sysfs_root)
    if not policies:
        return False, [
            f"No CPU frequency policy found under {cpu_sysfs_root}; "
            "this runner cannot prove that frequency is pinned."
        ]

    problems: list[str] = []
    for policy in policies:
        governor = _read(policy / "scaling_governor")
        minimum = _read(policy / "scaling_min_freq")
        maximum = _read(policy / "scaling_max_freq")
        label = policy.name

        if governor is None:
            problems.append(f"{label}: scaling_governor is unavailable")
        elif governor != "performance":
            problems.append(f"{label}: governor is {governor!r}, expected 'performance'")

        if minimum is None or maximum is None:
            problems.append(f"{label}: scaling_min_freq/scaling_max_freq are unavailable")
        else:
            try:
                min_khz = int(minimum, 10)
                max_khz = int(maximum, 10)
            except ValueError:
                problems.append(f"{label}: frequency values are not integers")
            else:
                if min_khz <= 0 or max_khz <= 0:
                    problems.append(f"{label}: frequency limits must be positive")
                elif min_khz != max_khz:
                    problems.append(
                        f"{label}: frequency is not pinned ({min_khz} != {max_khz} kHz)"
                    )

    if problems:
        return False, problems
    return True, [
        f"{policy.name}: performance governor and fixed frequency verified"
        for policy in policies
    ]


def verify_bare_metal(
    *,
    machine: str | None = None,
    cpuinfo_path: Path = Path("/proc/cpuinfo"),
    detector: Callable[[], tuple[int, str]] | None = None,
) -> tuple[bool, list[str]]:
    architecture = (machine or platform.machine()).lower()
    problems: list[str] = []
    if architecture not in {"x86_64", "amd64"}:
        problems.append(f"architecture is {architecture!r}; dedicated benchmark host must be x86_64")

    cpuinfo = _read(cpuinfo_path) or ""
    hypervisor_flag = False
    for line in cpuinfo.splitlines():
        if line.lstrip().startswith(("flags", "Features")) and ":" in line:
            _, value = line.split(":", 1)
            if "hypervisor" in value.split():
                hypervisor_flag = True
                break
    if hypervisor_flag:
        problems.append("/proc/cpuinfo exposes the hypervisor flag; virtualized CPUs are not accepted")

    try:
        if detector is None:
            result = subprocess.run(
                ["systemd-detect-virt", "--vm"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
            )
            returncode, output = result.returncode, result.stdout.strip()
        else:
            returncode, output = detector()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, problems + [
            f"cannot prove bare-metal execution because systemd-detect-virt failed: {exc}"
        ]

    if returncode == 0:
        problems.append(f"systemd-detect-virt identified a virtual machine: {output or 'unknown'}")
    elif returncode != 1:
        problems.append(
            f"systemd-detect-virt returned {returncode}; bare-metal status is unknown"
        )

    if problems:
        return False, problems
    return True, ["x86_64 architecture verified; systemd-detect-virt reports no VM"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpu-sysfs-root",
        type=Path,
        default=Path("/sys/devices/system/cpu"),
        help="CPU sysfs root (default: /sys/devices/system/cpu)",
    )
    parser.add_argument(
        "--require-bare-metal",
        action="store_true",
        help="also require x86-64 and positive systemd evidence that this is not a VM",
    )
    args = parser.parse_args()

    checks = [verify_pinned_frequency(args.cpu_sysfs_root)]
    if args.require_bare_metal:
        checks.append(verify_bare_metal())

    all_ok = True
    for ok, messages in checks:
        all_ok = all_ok and ok
        for message in messages:
            print(("PASS: " if ok else "ERROR: ") + message)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
