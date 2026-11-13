#!/usr/bin/env python3
"""Unit tests for reproducible clean/incremental build measurement."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_build  # noqa: E402


class BuildMeasurementTests(unittest.TestCase):
    def test_valid_budget_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "core" / "src" / "probe.cpp"
            source.parent.mkdir(parents=True)
            source.write_text("int probe() { return 0; }\n", encoding="utf-8")
            data = {
                "schema_version": 1,
                "generator": "Ninja",
                "compiler_id": "Clang",
                "compiler_major": 23,
                "configuration": "Release",
                "parallel_jobs": 2,
                "incremental_probe": "core/src/probe.cpp",
                "budgets_seconds": {"clean": 180, "incremental": 45},
            }
            probe, budgets = measure_build.validate_configuration(data, root)
            self.assertEqual(probe, source.resolve())
            self.assertEqual(budgets, {"clean": 180.0, "incremental": 45.0})

    def test_rejects_invalid_or_escaping_incremental_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = {
                "schema_version": 1,
                "generator": "Ninja",
                "compiler_id": "Clang",
                "compiler_major": 23,
                "configuration": "Release",
                "parallel_jobs": 2,
                "incremental_probe": "../outside.cpp",
                "budgets_seconds": {"clean": 180, "incremental": 45},
            }
            with self.assertRaises(ValueError):
                measure_build.validate_configuration(data, root)

    def test_incremental_build_restores_source_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "probe.cpp"
            source.write_text("int probe() { return 0; }\n", encoding="utf-8")
            original = source.stat().st_mtime_ns
            with mock.patch.object(
                measure_build,
                "run_timed_build",
                return_value=(1.25, "clang++ -c probe.cpp"),
            ):
                elapsed, output = measure_build.run_incremental_build(
                    source, ["cmake"], root, root / "incremental.log"
                )
            self.assertEqual(elapsed, 1.25)
            self.assertIn("probe.cpp", output)
            self.assertEqual(source.stat().st_mtime_ns, original)

    def test_incremental_build_fails_when_probe_was_not_recompiled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "probe.cpp"
            source.write_text("int probe() { return 0; }\n", encoding="utf-8")
            original = source.stat().st_mtime_ns
            with mock.patch.object(
                measure_build,
                "run_timed_build",
                return_value=(0.01, "ninja: no work to do"),
            ):
                with self.assertRaises(RuntimeError):
                    measure_build.run_incremental_build(
                        source, ["cmake"], root, root / "incremental.log"
                    )
            self.assertEqual(source.stat().st_mtime_ns, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
