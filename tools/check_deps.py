#!/usr/bin/env python3
"""TGF dependency-DAG and hygiene checker (P0.1.6, ADR-0013).

Fails (exit 1) when:
  * a module includes a tgf/<module>/ header it is not allowed to depend on
    (table from TODO section 4),
  * a PUBLIC header includes a third-party / platform / graphics header,
  * a source or build file contains an absolute, machine-specific Windows path.
"""
import pathlib
import re
import sys

ALLOWED = {
    "core": set(),
    "platform": {"core"},
    "rhi": {"core"},
    "text": {"core"},
    "render": {"core", "rhi", "text"},
    "ui": {"core", "text", "render", "platform"},
    "widgets": {"ui", "core"},
    "pro": {"widgets", "ui", "core"},
    "tools": None, "host": None, "c": None, "bindings": {"c"},  # language bindings use the stable C ABI only
}
FORBIDDEN_PUBLIC = re.compile(
    r'#\s*include\s*[<"](imgui[^>"]*|GLFW/[^>"]*|SDL[^>"]*|windows\.h|vulkan/[^>"]*|d3d1[12][^>"]*|dxgi[^>"]*|'
    r'Metal/[^>"]*|X11/[^>"]*|wayland[^>"]*|hb\.h|ft2build\.h)[>"]')
INCLUDE_TGF = re.compile(r'#\s*include\s*[<"]tgf/([a-z_]+)/')
ABS_PATH = re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:\\+[A-Za-z]')
ABS_PATH2 = re.compile(r'(?<![A-Za-z0-9"\'/])[A-Z]:/(Libraries|Users|Program)')

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors = []

# P0.1.1: the monorepo layout from the master plan must always exist.
REQUIRED_DIRS = ["core", "platform", "rhi", "render", "text", "ui", "widgets", "pro", "tools", "host", "c",
                 "bindings", "samples", "benchmarks", "tests", "docs", "third_party", "cmake"]
for d in REQUIRED_DIRS:
    if not (root / d).is_dir():
        errors.append(f"missing top-level directory '{d}/' (monorepo layout, P0.1.1)")

for module, allowed in ALLOWED.items():
    mdir = root / module
    if not mdir.is_dir():
        continue
    for f in mdir.rglob("*"):
        if f.suffix not in {".hpp", ".h", ".cpp", ".cc", ".inl"}:
            continue
        is_public = "include" in f.relative_to(mdir).parts
        for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            m = INCLUDE_TGF.search(line)
            if m and allowed is not None:
                dep = m.group(1)
                if dep != module and dep not in allowed:
                    errors.append(f"{f.relative_to(root)}:{n}: module '{module}' may not depend on '{dep}'")
            if is_public and FORBIDDEN_PUBLIC.search(line):
                errors.append(f"{f.relative_to(root)}:{n}: public header includes a forbidden third-party/platform header")

for pattern in ("*.cpp", "*.hpp", "*.h", "CMakeLists.txt", "*.cmake", "*.json", "*.py", "*.in"):
    for f in root.rglob(pattern):
        rel = f.relative_to(root)
        if rel.parts[0] in {"build", "docs", ".git"} or f.name == "check_deps.py":
            continue
        if rel.parts[0].startswith("build"):
            continue
        for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            if ABS_PATH.search(line) or ABS_PATH2.search(line):
                errors.append(f"{rel}:{n}: absolute machine-specific path")

if errors:
    print("dependency/hygiene check FAILED:")
    print("\n".join("  " + e for e in errors))
    sys.exit(1)
print("dependency/hygiene check passed")
