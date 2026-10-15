#!/usr/bin/env python3
"""Fail unless Linux CPU frequency policies are explicitly pinned.

The nightly benchmark job must run on a dedicated host configured by its
administrator. This check intentionally refuses ordinary virtualized or
frequency-scaling machines rather than producing misleading benchmark data.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


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

    # Some kernels expose per-CPU cpufreq links instead of policy directories.
    return sorted(
        path
        for path in cpu_sysfs_root.glob("cpu[0-9]*/cpufreq")
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
    return True, [f"{policy.name}: performance governor and fixed frequency verified" for policy in policies]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpu-sysfs-root",
        type=Path,
        default=Path("/sys/devices/system/cpu"),
        help="CPU sysfs root (default: /sys/devices/system/cpu)",
    )
    args = parser.parse_args()

    ok, messages = verify_pinned_frequency(args.cpu_sysfs_root)
    for message in messages:
        print(("PASS: " if ok else "ERROR: ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
