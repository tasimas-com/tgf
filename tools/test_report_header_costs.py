#!/usr/bin/env python3
"""Unit tests for parsing isolated public-header Clang time traces."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_header_costs  # noqa: E402


class HeaderCostReportTests(unittest.TestCase):
    def test_aggregates_isolated_compile_time_and_source_parse_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "build"
            trace_dir = build / "tests" / "CMakeFiles" / "tgf_header_check.dir"
            trace_dir.mkdir(parents=True)
            header_a = root / "core" / "include" / "tgf" / "core" / "a.hpp"
            header_b = root / "core" / "include" / "tgf" / "core" / "b.hpp"
            header_a.parent.mkdir(parents=True)
            header_a.write_text("#pragma once\n", encoding="utf-8")
            header_b.write_text("#pragma once\n", encoding="utf-8")
            manifest = [
                {
                    "generated_name": "hdr_core__tgf__core__a.hpp.cpp",
                    "include_name": "tgf/core/a.hpp",
                    "absolute_path": str(header_a.resolve()),
                },
                {
                    "generated_name": "hdr_core__tgf__core__b.hpp.cpp",
                    "include_name": "tgf/core/b.hpp",
                    "absolute_path": str(header_b.resolve()),
                },
            ]
            for item, compile_us, source_us in (
                (manifest[0], 4100, 900),
                (manifest[1], 2500, 300),
            ):
                trace_path = trace_dir / f"{item['generated_name']}.o.json"
                trace_path.write_text(
                    json.dumps(
                        {
                            "traceEvents": [
                                {"name": "Total ExecuteCompiler", "ph": "X", "dur": compile_us},
                                {
                                    "name": "Source",
                                    "ph": "X",
                                    "dur": source_us,
                                    "args": {"detail": item["absolute_path"]},
                                },
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
            rows = report_header_costs.collect_header_costs(build, manifest)
            self.assertEqual(rows[0]["header"], "tgf/core/a.hpp")
            self.assertEqual(rows[0]["isolated_translation_unit_us"], 4100)
            self.assertEqual(rows[0]["header_source_us"], 900)
            self.assertEqual(rows[1]["header"], "tgf/core/b.hpp")

    def test_rejects_missing_time_trace_for_a_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "build"
            trace_dir = build / "CMakeFiles" / "tgf_header_check.dir"
            trace_dir.mkdir(parents=True)
            header = root / "header.hpp"
            header.write_text("#pragma once\n", encoding="utf-8")
            manifest = [
                {
                    "generated_name": "hdr_missing.cpp",
                    "include_name": "tgf/missing.hpp",
                    "absolute_path": str(header.resolve()),
                }
            ]
            (trace_dir / "different.cpp.o.json").write_text(
                json.dumps({"traceEvents": []}), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                report_header_costs.collect_header_costs(build, manifest)

    def test_report_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "reports"
            rows = [
                {
                    "header": "tgf/core/example.hpp",
                    "isolated_translation_unit_us": 1234.0,
                    "isolated_translation_unit_ms": 1.234,
                    "header_source_us": None,
                    "source_event_count": 0,
                    "trace_file": "example.json",
                }
            ]
            json_path, md_path = report_header_costs.write_report(
                output, rows, "Clang 23", "Release"
            )
            self.assertTrue(json.loads(json_path.read_text(encoding="utf-8"))["headers"])
            self.assertIn("tgf/core/example.hpp", md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
