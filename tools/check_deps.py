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
    "tools": LAYERS,
    "host": LAYERS,
    "c": LAYERS,
    "bindings": frozenset({"c"}),
}
PUBLIC_ONLY = frozenset({"widgets", "pro", "tools", "host", "c", "bindings"})
# These are ordinary application/test consumers, not framework implementation
# modules. They may use any documented module API, but never a private header.
CONSUMER_DIRS = ("samples", "benchmarks", "tests")
REQUIRED_DIRS = (
    "core", "platform", "rhi", "render", "text", "ui", "widgets", "pro",
    "tools", "host", "c", "bindings", "samples", "benchmarks", "tests",
    "docs", "third_party", "cmake",
)
SOURCE_SUFFIXES = {
    ".h", ".hpp", ".hh", ".hxx", ".c", ".cc", ".cpp", ".cxx",
    ".m", ".mm", ".inl", ".ipp", ".inc",
}
POLICY_SUFFIXES = SOURCE_SUFFIXES | {
    ".cmake", ".json", ".py", ".in", ".ps1", ".cmd", ".bat", ".sh",
    ".mk", ".make", ".bzl", ".bazel", ".yml", ".yaml", ".txt",
    ".toml", ".ini", ".xml", ".rc", ".props", ".targets", ".vcxproj",
}
# Standard C++20 library headers and the C compatibility headers. Public headers
# may include these or another TGF public header; every other angle include is
# rejected, which is safer than trying to maintain a third-party SDK deny-list.
STANDARD_HEADERS = frozenset({
    "algorithm", "any", "array", "atomic", "barrier", "bit", "bitset",
    "cassert", "ccomplex", "cctype", "cerrno", "cfenv", "cfloat", "charconv",
    "chrono", "cinttypes", "ciso646", "climits", "clocale", "cmath", "codecvt",
    "compare", "complex", "concepts", "condition_variable", "coroutine",
    "csetjmp", "csignal", "cstdarg", "cstddef", "cstdint", "cstdio", "cstdlib",
    "cstring", "ctgmath", "ctime", "cuchar", "cwchar", "cwctype", "deque",
    "exception", "execution", "filesystem", "forward_list", "fstream",
    "functional", "future", "initializer_list", "iomanip", "ios", "iosfwd",
    "iostream", "istream", "iterator", "latch", "limits", "list", "locale",
    "map", "memory", "memory_resource", "mutex", "new", "numbers", "numeric",
    "optional", "ostream", "queue", "random", "ranges", "ratio", "regex",
    "scoped_allocator", "semaphore", "set", "shared_mutex", "source_location",
    "span", "sstream", "stack", "stdexcept", "stop_token", "streambuf",
    "string", "string_view", "syncstream", "system_error", "thread", "tuple",
    "type_traits", "typeindex", "typeinfo", "unordered_map", "unordered_set",
    "utility", "valarray", "variant", "vector", "version",
    "assert.h", "complex.h", "ctype.h", "errno.h", "fenv.h", "float.h",
    "inttypes.h", "iso646.h", "limits.h", "locale.h", "math.h", "setjmp.h",
    "signal.h", "stdarg.h", "stdatomic.h", "stdbool.h", "stddef.h", "stdint.h",
    "stdio.h", "stdlib.h", "string.h", "tgmath.h", "threads.h", "time.h",
    "uchar.h", "wchar.h", "wctype.h",
})
EXCLUDED = {".git", ".venv", "venv", "__pycache__", "build", "out", "third_party"}

INCLUDE_DIRECTIVE = re.compile(r"^\s*#\s*(include_next|include|import)\b")
INCLUDE_LITERAL = re.compile(
    r'^\s*#\s*(?:include|import)\s*(?:<([^>]+)>|"([^"]+)")\s*(?:(?://.*)|(?:/\*.*\*/\s*))?$'
)
MODULE_IMPORT = re.compile(r"^\s*(?:export\s+)?import\s+([^;]+);")
INCLUDE_TGF_PREFIX = re.compile(r"(?:^|/)tgf(?:/|$)", re.IGNORECASE)
ABS_WINDOWS = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]+[A-Za-z]")
ABS_POSIX = re.compile(
    r"(?<![A-Za-z0-9:/])/(?:Users/(?!runner(?:/|$)|actions(?:/|$)|github(?:/|$)|buildagent(?:/|$)|oai(?:/|$))[A-Za-z0-9_.-]+|root|mnt|Volumes|workspace|workspaces|Libraries|Program Files)(?:/|\\)|"
    r"(?<![A-Za-z0-9:/])/home/(?!runner(?:/|$)|actions(?:/|$)|github(?:/|$)|buildagent(?:/|$)|oai(?:/|$))[A-Za-z0-9_.-]+(?:/|\\)",
    re.IGNORECASE,
)
ABS_UNC = re.compile(
    r"(?<![A-Za-z0-9:])(?:\\\\|//)[A-Za-z0-9_.-]+[\\/][^\\/\s]+",
    re.IGNORECASE,
)


def is_within(path: pathlib.Path, base: pathlib.Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def exact_file_exists(path: pathlib.Path) -> bool:
    """Check spelling component-by-component, including on case-insensitive Windows."""
    try:
        absolute = path.absolute()
        current = pathlib.Path(absolute.anchor)
        components = absolute.parts[1:] if absolute.anchor else absolute.parts
        for component in components:
            if not current.is_dir():
                return False
            if component not in {entry.name for entry in current.iterdir()}:
                return False
            current = current / component
        return current.is_file()
    except OSError:
        return False


def parse_documented_policy(root: pathlib.Path) -> list[str]:
    todo = root / "TODO.md"
    if not todo.is_file():
        return ["TODO.md is missing; cannot verify dependency policy"]
    try:
        lines = todo.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"TODO.md cannot be read: {exc}"]
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("**★ Explicit dependency table"))
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("**Dependency rules:"))
    except StopIteration:
        return ["TODO.md is missing the explicit dependency table or its Dependency rules terminator"]

    actual = {}
    for number, line in enumerate(lines[start + 1:end], start + 2):
        if not line.startswith("|"):
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "Module" or set(cells[0]) <= {"-", ":", " "}:
            continue
        modules = [part.strip().strip(chr(96)) for part in cells[0].split(",")]
        # Strip each explanatory parenthetical before splitting the module list.
        value = re.sub(r"\s*\([^)]*\)", "", cells[1]).strip()
        if value == "std only":
            permitted = frozenset()
        elif value.startswith("any of the above"):
            permitted = LAYERS
        else:
            permitted = frozenset(
                part.split(" (", 1)[0].strip().strip(chr(96))
                for part in value.split(",")
            )
        if not modules or set(modules) - ALLOWED.keys() or permitted - ALLOWED.keys():
            return [f"TODO.md:{number}: unknown or empty dependency-table module"]
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


def foreign_target(
    root: pathlib.Path,
    source: pathlib.Path,
    include: str,
    quoted: bool,
) -> tuple[str, pathlib.Path] | None:
    path = pathlib.Path(include.replace("\\", "/"))
    if path.is_absolute() or pathlib.PureWindowsPath(include).is_absolute():
        candidates = (path,)
    elif quoted:
        candidates = (source.parent / path, root / path)
    else:
        candidates = (root / path,)
    for candidate in candidates:
        resolved = candidate.resolve()
        for module in ALLOWED:
            try:
                return module, resolved.relative_to((root / module).resolve())
            except ValueError:
                pass
    return None


def validate_tgf_include(
    root: pathlib.Path,
    source: pathlib.Path,
    relative: pathlib.Path,
    line_number: int,
    name: str,
    quoted: bool,
    importer_module: str | None,
    allowed: frozenset[str],
    importing_backend: str | None,
    errors: list[str],
) -> bool:
    """Validate a canonical <tgf/module/public/header> include; return True if handled."""
    if not INCLUDE_TGF_PREFIX.search(name.replace("\\", "/")):
        return False

    if "\\" in name:
        errors.append(f"{relative}:{line_number}: TGF include paths must use forward slashes")
        return True

    parts = name.split("/")
    if len(parts) < 3 or parts[0] != "tgf" or any(part in {"", ".", ".."} for part in parts):
        errors.append(f"{relative}:{line_number}: malformed or traversing TGF include path")
        return True

    dependency = parts[1]
    if dependency != dependency.lower():
        errors.append(f"{relative}:{line_number}: TGF module name must be lowercase")
        return True
    if dependency not in ALLOWED:
        errors.append(f"{relative}:{line_number}: unknown TGF module '{dependency}'")
        return True

    if quoted and (importer_module is None or importer_module != dependency):
        errors.append(
            f"{relative}:{line_number}: cross-module or consumer TGF headers must use canonical angle-bracket spelling <tgf/module/...>"
        )

    if importer_module is not None and dependency != importer_module:
        if dependency not in allowed:
            errors.append(f"{relative}:{line_number}: module '{importer_module}' may not depend on '{dependency}'")
        if importer_module in PUBLIC_ONLY:
            # Consumer modules may cross a boundary only through an actual public header.
            pass

    public_root = (root / dependency / "include").resolve()
    header = root / dependency / "include" / "tgf" / dependency
    for component in parts[2:]:
        header = header / component
    resolved_header = header.resolve()
    if not is_within(resolved_header, public_root):
        errors.append(f"{relative}:{line_number}: TGF public header resolves outside its public header tree")
    elif not exact_file_exists(header):
        errors.append(f"{relative}:{line_number}: TGF include does not name an existing public header")

    if importer_module == "rhi" and importing_backend:
        included_backend = backend(tuple(parts))
        if included_backend and included_backend != importing_backend:
            errors.append(
                f"{relative}:{line_number}: RHI backend '{importing_backend}' may not include backend '{included_backend}'"
            )
    return True


def scan_source_tree(
    root: pathlib.Path,
    base: pathlib.Path,
    importer_module: str | None,
    errors: list[str],
) -> None:
    allowed = ALLOWED[importer_module] if importer_module else LAYERS
    public_only = importer_module in PUBLIC_ONLY if importer_module else True
    for source in sorted(base.rglob("*")):
        if source.is_symlink() and source.is_dir():
            errors.append(
                f"{source.relative_to(root)}: directory symlink is not allowed in a scanned source tree"
            )
            continue
        if not source.is_file() or source.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        relative = source.relative_to(root)
        if any(part in EXCLUDED or part.startswith("build-") for part in relative.parts):
            continue
        resolved_source = source.resolve()
        if not is_within(resolved_source, root.resolve()):
            errors.append(f"{relative}: source symlink escapes repository root")
            continue
        if not is_within(resolved_source, base.resolve()):
            errors.append(f"{relative}: source symlink escapes its module/consumer boundary")
            continue

        public = importer_module is not None and "include" in source.relative_to(base).parts
        importing_backend = backend(relative.parts) if importer_module == "rhi" else None
        try:
            source_lines = source.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative}: cannot read source: {exc}")
            continue

        for number, line in enumerate(source_lines, 1):
            module_import = MODULE_IMPORT.match(line)
            if module_import:
                errors.append(
                    f"{relative}:{number}: C++ named-module imports are not yet covered by the header DAG; "
                    "use checked headers or extend the policy checker first"
                )
                continue

            directive = INCLUDE_DIRECTIVE.match(line)
            if not directive:
                continue
            directive_name = directive.group(1)
            if directive_name == "include_next":
                errors.append(f"{relative}:{number}: #include_next is forbidden because it bypasses include policy")
                continue

            match = INCLUDE_LITERAL.match(line)
            if not match:
                errors.append(f"{relative}:{number}: non-literal or malformed include cannot be checked")
                continue
            name = match.group(1) or match.group(2)
            quoted = match.group(2) is not None

            if pathlib.Path(name).is_absolute() or pathlib.PureWindowsPath(name).is_absolute():
                errors.append(f"{relative}:{number}: absolute include path is forbidden")
                continue

            if validate_tgf_include(
                root, source, relative, number, name, quoted,
                importer_module, allowed, importing_backend, errors,
            ):
                continue

            foreign = foreign_target(root, source, name, quoted)
            if foreign:
                dependency, target = foreign
                if importer_module is None:
                    errors.append(
                        f"{relative}:{number}: {relative.parts[0]} consumer may not include module-private paths; "
                        f"use <tgf/{dependency}/...> public headers"
                    )
                elif dependency != importer_module:
                    if dependency not in allowed:
                        errors.append(
                            f"{relative}:{number}: module '{importer_module}' may not depend on '{dependency}' "
                            "(relative include bypass)"
                        )
                    if public_only and (not target.parts or target.parts[0] != "include"):
                        errors.append(
                            f"{relative}:{number}: module '{importer_module}' may include '{dependency}' "
                            "only through its public header tree"
                        )
                    errors.append(
                        f"{relative}:{number}: cross-module include must use canonical <tgf/{dependency}/...> spelling"
                    )
                elif not quoted and (not target.parts or target.parts[0] != "include"):
                    errors.append(
                        f"{relative}:{number}: angle-bracket include of a private header is forbidden; "
                        "use a source-relative quoted include within the owning module"
                    )

                if importer_module == "rhi" and importing_backend:
                    included_backend = backend(target.parts)
                    if included_backend and included_backend != importing_backend:
                        errors.append(
                            f"{relative}:{number}: RHI backend '{importing_backend}' may not include backend '{included_backend}'"
                        )

            if quoted:
                include_path = pathlib.Path(name.replace("\\", "/"))
                local_candidate = (source.parent / include_path).resolve()
                if not local_candidate.exists():
                    if ".." in include_path.parts and not is_within(local_candidate, root.resolve()):
                        errors.append(f"{relative}:{number}: relative include escapes repository root")
                    elif ".." in include_path.parts and not is_within(local_candidate, base.resolve()):
                        errors.append(f"{relative}:{number}: relative include escapes its module/consumer boundary")
                    else:
                        errors.append(
                            f"{relative}:{number}: quoted include does not resolve beside its source; "
                            "implicit include-search-path resolution is forbidden"
                        )
                else:
                    if not is_within(local_candidate, root.resolve()):
                        errors.append(f"{relative}:{number}: relative include escapes repository root")
                    elif not is_within(local_candidate, base.resolve()):
                        errors.append(f"{relative}:{number}: relative include escapes its module/consumer boundary")

            if public and not quoted and name not in STANDARD_HEADERS:
                errors.append(
                    f"{relative}:{number}: public header includes forbidden platform/graphics/third-party SDK header "
                    "or an unapproved non-standard header"
                )
            if public and quoted:
                local_candidate = (source.parent / pathlib.Path(name.replace(chr(92), "/"))).resolve()
                if is_within(local_candidate, base.resolve()):
                    target = local_candidate.relative_to(base.resolve())
                    if target.parts and target.parts[0] != "include":
                        errors.append(
                            f"{relative}:{number}: public header may not include a private header from its own module"
                        )


def check(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"project root does not exist: {root}"]
    root = root.resolve()
    errors.extend(parse_documented_policy(root))

    for directory in REQUIRED_DIRS:
        path = root / directory
        if not path.is_dir():
            errors.append(f"missing top-level directory '{directory}/' (P0.1.1)")
        elif path.is_symlink() and not is_within(path.resolve(), root):
            errors.append(f"top-level directory '{directory}/' resolves outside repository root")

    for module in ALLOWED:
        base = root / module
        if base.is_dir():
            scan_source_tree(root, base, module, errors)

    for consumer in CONSUMER_DIRS:
        base = root / consumer
        if base.is_dir():
            scan_source_tree(root, base, None, errors)

    # Reject machine-specific paths in repository-owned source and build metadata.
    # Documentation and vendored third-party material are intentionally excluded.
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in POLICY_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if relative.parts[0] == "docs" or any(
            part in EXCLUDED or part.startswith("build-") for part in relative.parts
        ):
            continue
        if relative.as_posix() == "tools/check_deps.py":
            continue  # This file necessarily contains the path patterns it enforces.
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative}: cannot inspect policy file: {exc}")
            continue
        for number, line in enumerate(lines, 1):
            if ABS_WINDOWS.search(line) or ABS_POSIX.search(line) or ABS_UNC.search(line):
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

