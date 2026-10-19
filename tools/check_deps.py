#!/usr/bin/env python3
"""Fail-closed enforcement of the TGF module dependency contract (P0.1.6)."""
from __future__ import annotations
import pathlib
import re
import sys

LAYERS = frozenset({"core", "platform", "rhi", "text", "render", "ui", "widgets", "pro"})
ALLOWED = {
    "core": frozenset(),
    "platform": frozenset({"core"}),
    "rhi": frozenset({"core"}),
    "text": frozenset({"core"}),
    "render": frozenset({"core", "rhi", "text"}),
    "ui": frozenset({"core", "text", "render", "platform"}),
    "widgets": frozenset({"ui"}),
    "pro": frozenset({"widgets", "ui"}),
    "tools": LAYERS, "host": LAYERS, "c": LAYERS,
    "bindings": frozenset({"c"}),
}
PUBLIC_ONLY = frozenset({"widgets", "pro", "tools", "host", "c", "bindings"})
REQUIRED_DIRS = ("core", "platform", "rhi", "render", "text", "ui", "widgets", "pro",
                 "tools", "host", "c", "bindings", "samples", "benchmarks", "tests",
                 "docs", "third_party", "cmake")
SOURCE_SUFFIXES = {".h", ".hpp", ".hh", ".hxx", ".c", ".cc", ".cpp", ".cxx", ".inl"}
POLICY_SUFFIXES = SOURCE_SUFFIXES | {".cmake", ".json", ".py", ".in", ".ps1", ".cmd", ".bat", ".yml", ".yaml"}
EXCLUDED = {".git", ".venv", "venv", "__pycache__", "build", "out", "third_party"}
INCLUDE_START = re.compile(r"^\s*#\s*include\b")
INCLUDE_LITERAL = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')
INCLUDE_TGF = re.compile(r"^tgf/([^/]+)/(.+)$")
FORBIDDEN_PUBLIC = re.compile(
    r"^(?:imgui(?:\.h|/)|GLFW(?:\.h|/)|glfw3\.h|SDL(?:\.h|/|2/|3/)|"
    r"windows(?:\.h|x\.h)|winuser\.h|vulkan/|d3d[^/]*\.h|d3d(?:11|12)/|"
    r"dxgi(?:\.h|[0-9_]*\.h)|Metal/|QuartzCore/|AppKit/|CoreGraphics/|"
    r"X11/|xcb/|wayland(?:-client|-server)?\.h|hb(?:-ft)?\.h|ft2build\.h|"
    r"GL/|EGL/|GLES[0-9]*/)", re.IGNORECASE)
ABS_WINDOWS = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]+[A-Za-z]")
ABS_POSIX = re.compile(r"(?<![A-Za-z0-9\"'])/(?:Users|home|mnt|Volumes|workspace|workspaces|Libraries|Program Files)/", re.I)

def parse_documented_policy(root: pathlib.Path) -> list[str]:
    todo = root / "TODO.md"
    if not todo.is_file():
        return ["TODO.md is missing; cannot verify dependency policy"]
    lines = todo.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("**★ Explicit dependency table"))
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("**Dependency rules:"))
    except StopIteration:
        return ["TODO.md is missing the explicit dependency table"]
    actual = {}
    for number, line in enumerate(lines[start + 1:end], start + 2):
        if not line.startswith("|"):
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "Module" or set(cells[0]) <= {"-", ":", " "}:
            continue
        modules = [part.strip().strip(chr(96)) for part in cells[0].split(",")]
        value = cells[1].split(" (", 1)[0].strip()
        if value == "std only":
            permitted = frozenset()
        elif value.startswith("any of the above"):
            permitted = LAYERS
        else:
            permitted = frozenset(part.strip().strip(chr(96)) for part in value.split(","))
        if set(modules) - ALLOWED.keys() or permitted - ALLOWED.keys():
            return [f"TODO.md:{number}: unknown dependency-table module"]
        for module in modules:
            if module in actual:
                return [f"TODO.md:{number}: duplicate dependency row for {module}"]
            actual[module] = permitted
    if actual != ALLOWED:
        return ["TODO.md dependency table differs from checker; update both together"]
    return []

def backend(parts: tuple[str, ...]) -> str | None:
    for marker in ("backends", "backend"):
        if marker in parts and parts.index(marker) + 1 < len(parts):
            return parts[parts.index(marker) + 1]
    return None

def foreign_target(root: pathlib.Path, source: pathlib.Path, include: str):
    path = pathlib.Path(include)
    candidates = (path,) if path.is_absolute() else (source.parent / path, root / path)
    for candidate in candidates:
        resolved = candidate.resolve()
        for module in ALLOWED:
            try:
                return module, resolved.relative_to((root / module).resolve())
            except ValueError:
                pass
    return None

def check(root: pathlib.Path) -> list[str]:
    errors = []
    if not root.is_dir():
        return [f"project root does not exist: {root}"]
    errors.extend(parse_documented_policy(root))
    for directory in REQUIRED_DIRS:
        if not (root / directory).is_dir():
            errors.append(f"missing top-level directory '{directory}/' (P0.1.1)")

    for module, allowed in ALLOWED.items():
        base = root / module
        if not base.is_dir():
            continue
        for source in sorted(base.rglob("*")):
            if not source.is_file() or source.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            relative = source.relative_to(root)
            if any(part in EXCLUDED or part.startswith("build-") for part in relative.parts):
                continue
            public = "include" in source.relative_to(base).parts
            importing_backend = backend(relative.parts) if module == "rhi" else None
            try:
                source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exc:
                errors.append(f"{relative}: cannot read source: {exc}")
                continue
            for number, line in enumerate(source_lines, 1):
                if not INCLUDE_START.match(line):
                    continue
                match = INCLUDE_LITERAL.match(line)
                if not match:
                    errors.append(f"{relative}:{number}: non-literal include cannot be checked")
                    continue
                name = match.group(1).replace("\\", "/")
                tgf = INCLUDE_TGF.fullmatch(name)
                if tgf:
                    dependency, remainder = tgf.groups()
                    parts = pathlib.PurePosixPath(name).parts
                    if "." in parts or ".." in parts:
                        errors.append(f"{relative}:{number}: TGF include path escapes its module namespace")
                        continue
                    if dependency != dependency.lower():
                        errors.append(f"{relative}:{number}: TGF module name must be lowercase")
                        continue
                    if dependency not in ALLOWED:
                        errors.append(f"{relative}:{number}: unknown TGF module '{dependency}'")
                        continue
                    if dependency != module and dependency not in allowed:
                        errors.append(f"{relative}:{number}: module '{module}' may not depend on '{dependency}'")
                    if dependency != module and module in PUBLIC_ONLY:
                        header = root / dependency / "include" / pathlib.Path(*pathlib.PurePosixPath(remainder).parts)
                        if not header.is_file():
                            errors.append(f"{relative}:{number}: module '{module}' must include '{dependency}' through an existing public header")
                    if module == "rhi" and importing_backend:
                        included_backend = backend(parts)
                        if included_backend and included_backend != importing_backend:
                            errors.append(f"{relative}:{number}: RHI backend '{importing_backend}' may not include backend '{included_backend}'")
                else:
                    foreign = foreign_target(root, source, name)
                    if foreign and foreign[0] != module:
                        dependency, target = foreign
                        if dependency not in allowed:
                            errors.append(f"{relative}:{number}: module '{module}' may not depend on '{dependency}' (relative include bypass)")
                        if module == "rhi" and importing_backend:
                            included_backend = backend(target.parts)
                            if included_backend and included_backend != importing_backend:
                                errors.append(f"{relative}:{number}: RHI backend '{importing_backend}' may not include backend '{included_backend}'")
                        errors.append(f"{relative}:{number}: cross-module include must use canonical <tgf/{dependency}/...> spelling")
                if public and FORBIDDEN_PUBLIC.match(name):
                    errors.append(f"{relative}:{number}: public header includes forbidden platform/graphics/third-party header")

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in POLICY_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if relative.parts[0] == "docs" or any(part in EXCLUDED or part.startswith("build-") for part in relative.parts):
            continue
        if relative.as_posix() == "tools/check_deps.py":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ABS_WINDOWS.search(line) or ABS_POSIX.search(line):
                errors.append(f"{relative}:{number}: absolute machine-specific path")
    return errors

def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: check_deps.py [project-root]", file=sys.stderr)
        return 2
    errors = check(pathlib.Path(argv[1] if len(argv) == 2 else ".").resolve())
    if errors:
        print("dependency DAG FAILED:\n" + "\n".join("  " + item for item in errors))
        return 1
    print("dependency DAG passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
