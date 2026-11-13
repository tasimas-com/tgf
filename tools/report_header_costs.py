#!/usr/bin/env python3
"""Turn Clang -ftime-trace output into a per-public-header compilation report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_manifest(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 3 or not all(fields):
            raise ValueError(f"{path}:{line_number}: expected generated-name, include-name, absolute-path")
        generated_name, include_name, absolute_path = fields
        entries.append(
            {
                "generated_name": generated_name,
                "include_name": include_name,
                "absolute_path": str(Path(absolute_path).resolve()),
            }
        )
    if not entries:
        raise ValueError(f"header manifest is empty: {path}")
    return entries


def collect_header_costs(build_dir: Path, manifest: list[dict[str, str]]) -> list[dict[str, Any]]:
    trace_files = sorted(
        path for path in build_dir.rglob("*.json")
        if "tgf_header_check.dir" in path.as_posix()
    )
    if not trace_files:
        raise ValueError(
            f"no Clang time-trace JSON files found under {build_dir}; "
            "configure with -DTGF_ENABLE_HEADER_TIME_TRACE=ON and build tgf_header_check"
        )

    results: list[dict[str, Any]] = []
    for header in manifest:
        matching = [
            trace for trace in trace_files
            if header["generated_name"] in trace.name
        ]
        if len(matching) != 1:
            raise ValueError(
                f"expected one time-trace for {header['include_name']}, found {len(matching)}"
            )
        trace_path = matching[0]
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read Clang trace {trace_path}: {exc}") from exc
        events = trace.get("traceEvents")
        if not isinstance(events, list):
            raise ValueError(f"Clang trace has no traceEvents array: {trace_path}")

        compiler_events = [
            event for event in events
            if isinstance(event, dict)
            and event.get("name") == "Total ExecuteCompiler"
            and isinstance(event.get("dur"), (int, float))
            and not isinstance(event.get("dur"), bool)
        ]
        if not compiler_events:
            raise ValueError(f"Clang trace lacks Total ExecuteCompiler duration: {trace_path}")
        compile_us = float(compiler_events[0]["dur"])

        source_us = 0.0
        source_event_count = 0
        expected_path = header["absolute_path"].replace("\\", "/")
        for event in events:
            if not isinstance(event, dict) or event.get("name") != "Source":
                continue
            duration = event.get("dur")
            detail = event.get("args", {}).get("detail", "")
            if (
                isinstance(duration, (int, float))
                and not isinstance(duration, bool)
                and expected_path in str(detail).replace("\\", "/")
            ):
                source_us += float(duration)
                source_event_count += 1

        results.append(
            {
                "header": header["include_name"],
                "isolated_translation_unit_us": round(compile_us, 3),
                "isolated_translation_unit_ms": round(compile_us / 1000.0, 3),
                "header_source_us": round(source_us, 3) if source_event_count else None,
                "source_event_count": source_event_count,
                "trace_file": str(trace_path.relative_to(build_dir)),
            }
        )

    results.sort(key=lambda item: item["isolated_translation_unit_us"], reverse=True)
    return results


def write_report(
    output_dir: Path,
    costs: list[dict[str, Any]],
    compiler: str,
    configuration: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "tool": "Clang -ftime-trace",
        "compiler": compiler,
        "configuration": configuration,
        "metric": (
            "Total ExecuteCompiler duration for one isolated translation unit "
            "that includes the named public header twice"
        ),
        "headers": costs,
    }
    json_path = output_dir / "header-costs.json"
    markdown_path = output_dir / "header-costs.md"
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# TGF public-header compile-cost report",
        "",
        f"- Compiler: {compiler}",
        f"- Configuration: {configuration}",
        f"- Public headers measured: {len(costs)}",
        "",
        "The primary metric is the compiler's Total ExecuteCompiler duration for an isolated translation unit containing one public header twice. It includes fixed frontend/driver overhead and transitive includes; compare headers from the same run/compiler rather than treating these values as pure header-only CPU time.",
        "",
        "| Header | Isolated TU | Header Source event |",
        "|---|---:|---:|",
    ]
    for item in costs:
        source_time = (
            f"{item['header_source_us']:.1f} microseconds"
            if item["header_source_us"] is not None
            else "not emitted"
        )
        rows.append(
            f"| {item['header']} | "
            f"{item['isolated_translation_unit_us']:.1f} microseconds | {source_time} |"
        )
    rows.append("")
    markdown_path.write_text("\n".join(rows), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--compiler", default="Clang 23")
    parser.add_argument("--configuration", default="Release")
    args = parser.parse_args()

    try:
        entries = read_manifest(args.manifest)
        costs = collect_header_costs(args.build_dir.resolve(), entries)
        json_path, markdown_path = write_report(
            args.output_dir, costs, args.compiler, args.configuration
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"header cost report failed: {exc}", file=sys.stderr)
        return 1

    print(f"Measured {len(costs)} public headers")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
