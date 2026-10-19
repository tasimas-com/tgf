#!/usr/bin/env python3
"""Exhaustive positive/negative fixtures for the TGF dependency DAG checker."""
from __future__ import annotations
import importlib.util
import pathlib
import shutil
import sys
import tempfile

LAYERS = ("core", "platform", "rhi", "text", "render", "ui", "widgets", "pro")
ALLOWED = {
    "core": set(),
    "platform": {"core"},
    "rhi": {"core"},
    "text": {"core"},
    "render": {"core", "rhi", "text"},
    "ui": {"core", "text", "render", "platform"},
    "widgets": {"ui"},
    "pro": {"widgets", "ui"},
    "tools": set(LAYERS),
    "host": set(LAYERS),
    "c": set(LAYERS),
    "bindings": {"c"},
}
REQUIRED_DIRS = (
    "core", "platform", "rhi", "render", "text", "ui", "widgets", "pro",
    "tools", "host", "c", "bindings", "samples", "benchmarks", "tests",
    "docs", "third_party", "cmake",
)
TABLE = """**★ Explicit dependency table (fixtures)**
| Module | May depend on |
|---|---|
| core | std only |
| platform | core |
| rhi | core |
| text | core |
| render | core, rhi, text |
| ui | core, text, render, platform |
| widgets | ui (public API only) |
| pro | widgets, ui (public API only) |
| tools, host, c | any of the above through public headers |
| bindings | c (stable C ABI only) |
**Dependency rules:**
"""

def load_checker(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("tgf_check_deps", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def prepare(root: pathlib.Path) -> None:
    for directory in REQUIRED_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "TODO.md").write_text(TABLE, encoding="utf-8")
    for module in ALLOWED:
        public = root / module / "include" / "tgf" / module
        public.mkdir(parents=True, exist_ok=True)
        (public / "api.hpp").write_text("// public fixture\n", encoding="utf-8")
        (root / module / "src").mkdir(parents=True, exist_ok=True)

def reset_sources(root: pathlib.Path) -> None:
    for module in ALLOWED:
        for source in (root / module).rglob("*"):
            if source.is_file() and source.suffix in {".h", ".hpp", ".cpp"}:
                if "include" not in source.relative_to(root / module).parts:
                    source.unlink()

def include(root: pathlib.Path, importer: str, dependency: str, name: str) -> None:
    (root / importer / "src" / name).write_text(
        f"#include <tgf/{dependency}/api.hpp>\n", encoding="utf-8"
    )

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: test_check_deps.py path/to/check_deps.py")
        return 2
    checker = load_checker(pathlib.Path(sys.argv[1]).resolve())
    module_names = set(ALLOWED)
    allowed_count = sum(len(deps - {module}) for module, deps in ALLOWED.items())
    forbidden_count = sum(
        len(module_names - {module} - deps) for module, deps in ALLOWED.items()
    )

    with tempfile.TemporaryDirectory(prefix="tgf-deps-policy-") as temporary:
        root = pathlib.Path(temporary)
        prepare(root)

        # All 38 permitted directed edges are accepted.
        for importer, dependencies in ALLOWED.items():
            for dependency in dependencies:
                if importer != dependency:
                    include(root, importer, dependency, f"allow_{dependency}.cpp")
        errors = checker.check(root)
        assert not errors, "allowed edges failed:\n" + "\n".join(errors)

        # All 94 forbidden directed edges are rejected, not just one example.
        reset_sources(root)
        for importer, dependencies in ALLOWED.items():
            for dependency in module_names - {importer} - dependencies:
                include(root, importer, dependency, f"deny_{dependency}.cpp")
        errors = checker.check(root)
        rejected = [error for error in errors if "may not depend on" in error]
        assert len(rejected) == forbidden_count, (
            f"expected {forbidden_count} rejected edges, observed {len(rejected)}:\n"
            + "\n".join(errors)
        )

        reset_sources(root)
        (root / "platform/src/bypass.cpp").write_text(
            '#include "../../ui/src/private.hpp"\n', encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("relative include bypass" in error for error in errors), errors

        reset_sources(root)
        (root / "bindings/src/private.cpp").write_text(
            '#include "../../c/src/private.h"\n', encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("relative include bypass" in error for error in errors), errors

        reset_sources(root)
        (root / "bindings/src/missing.cpp").write_text(
            "#include <tgf/c/not_public.hpp>\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("existing public header" in error for error in errors), errors

        reset_sources(root)
        widget_header = root / "widgets/include/tgf/widgets/widget.hpp"
        widget_header.write_text("#include <windows.h>\n", encoding="utf-8")
        errors = checker.check(root)
        assert any("forbidden platform/graphics" in error for error in errors), errors
        widget_header.write_text("#include <vulkan/vulkan.h>\n", encoding="utf-8")
        errors = checker.check(root)
        assert any("forbidden platform/graphics" in error for error in errors), errors

        reset_sources(root)
        backend_dir = root / "rhi/backends/vulkan/src"
        backend_dir.mkdir(parents=True)
        (backend_dir / "cross.cpp").write_text(
            "#include <tgf/rhi/backends/d3d12/device.hpp>\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("may not include backend" in error for error in errors), errors

        reset_sources(root)
        d3d_source = root / "rhi/backends/d3d12/src"
        d3d_source.mkdir(parents=True)
        (d3d_source / "device.hpp").write_text("// backend-private fixture\\n", encoding="utf-8")
        (backend_dir / "relative.cpp").write_text(
            '#include "../../d3d12/src/device.hpp"\\n', encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("may not include backend" in error for error in errors), errors

        reset_sources(root)
        (root / "ui/src/unknown.cpp").write_text(
            "#include <tgf/unknown/api.hpp>\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("unknown TGF module" in error for error in errors), errors

        reset_sources(root)
        (root / "ui/src/case.cpp").write_text(
            "#include <tgf/Core/api.hpp>\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("must be lowercase" in error for error in errors), errors

        reset_sources(root)
        (root / "ui/src/traversal.cpp").write_text(
            "#include <tgf/widgets/../../core/api.hpp>\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("escapes its module namespace" in error for error in errors), errors

        reset_sources(root)
        (root / "ui/src/macro.cpp").write_text(
            "#include GENERATED_HEADER\n", encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("non-literal include" in error for error in errors), errors

        reset_sources(root)
        machine_path = "C:" + chr(92) + "Users" + chr(92) + "Developer"
        (root / "tools/path.py").write_text(
            f'ROOT = "{machine_path}"\n', encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("absolute machine-specific path" in error for error in errors), errors

        reset_sources(root)
        posix_path = chr(47) + "home" + chr(47) + "rayen" + chr(47) + "project"
        (root / "tools/posix_path.py").write_text(
            f'ROOT = "{posix_path}"\\n', encoding="utf-8"
        )
        errors = checker.check(root)
        assert any("absolute machine-specific path" in error for error in errors), errors

        reset_sources(root)
        changed_table = TABLE.replace("| render | core, rhi, text |", "| render | core |")
        (root / "TODO.md").write_text(changed_table, encoding="utf-8")
        errors = checker.check(root)
        assert any("dependency table differs" in error for error in errors), errors

        (root / "TODO.md").write_text(TABLE, encoding="utf-8")
        shutil.rmtree(root / "platform")
        errors = checker.check(root)
        assert any("missing top-level directory 'platform/'" in error for error in errors), errors

    print(
        f"dependency DAG regression tests passed: {allowed_count} allowed edges, "
        f"{forbidden_count} forbidden edges, public/private boundaries, SDK leakage, "
        "RHI isolation, malformed includes, policy drift, absolute paths, and layout"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
