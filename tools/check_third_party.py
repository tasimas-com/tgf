#!/usr/bin/env python3
"""Fail-closed third-party dependency and workflow provenance policy (P0.1.8)."""
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
from typing import Any

APPROVED_LICENSES = frozenset({"Apache-2.0", "MIT"})
ALLOWED_SCOPES = frozenset({"runtime", "build", "test", "dev", "ci"})
ALLOWED_KINDS = frozenset({"github-action", "tool", "cmake-package", "vendored"})
# These are built-in CMake modules backed by the host interpreter/platform,
# not third-party packages that need a registry license record.
CMAKE_BUILTIN_PACKAGES = frozenset({"Python3", "Threads"})
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
PURL_RE = re.compile(r"^pkg:github/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[A-Za-z0-9.+_-]+$")
USES_RE = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)(?:\s+#\s*(\S+))?\s*$")
SOURCE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".mm", ".m"})


def validate_manifest(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["dependency registry root must be a JSON object"]
    if value.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    project = value.get("project")
    if not isinstance(project, dict) or project.get("name") != "TASIMAS GUI Framework":
        errors.append("project name must be TASIMAS GUI Framework")
    elif project.get("spdxLicense") != "Apache-2.0" or not str(project.get("repository", "")).startswith("https://"):
        errors.append("project must declare Apache-2.0 and an HTTPS repository URL")
    approved = value.get("approvedSpdxLicenses")
    if not isinstance(approved, list) or not approved:
        errors.append("approvedSpdxLicenses must be a non-empty list")
        approved = []
    if any(not isinstance(item, str) or item not in APPROVED_LICENSES for item in approved):
        errors.append("approvedSpdxLicenses may contain only policy-coded Apache-2.0 and MIT")
    if "Apache-2.0" not in approved:
        errors.append("approvedSpdxLicenses must include Apache-2.0")
    deps = value.get("dependencies")
    if not isinstance(deps, list):
        errors.append("dependencies must be a JSON array")
        deps = []
    seen: set[str] = set()
    for index, dep in enumerate(deps):
        prefix = f"dependencies[{index}]"
        if not isinstance(dep, dict):
            errors.append(f"{prefix} must be an object")
            continue
        fields = ("name","repository","version","commit","kind","scope","license","sourceUrl","purl","purpose")
        missing = [field for field in fields if not isinstance(dep.get(field), str) or not dep[field].strip()]
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
            continue
        repository = dep["repository"]
        if repository in seen:
            errors.append(f"{prefix}: duplicate repository {repository!r}")
        seen.add(repository)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            errors.append(f"{prefix}.repository must be owner/name")
        if dep["license"] not in approved or dep["license"] not in APPROVED_LICENSES:
            errors.append(f"{prefix}: license {dep['license']!r} is not approved")
        if dep["kind"] not in ALLOWED_KINDS or dep["scope"] not in ALLOWED_SCOPES:
            errors.append(f"{prefix}: unsupported kind/scope")
        if not COMMIT_RE.fullmatch(dep["commit"]):
            errors.append(f"{prefix}.commit must be a full lowercase 40-character SHA")
        if dep["sourceUrl"].rstrip("/") != "https://github.com/" + repository:
            errors.append(f"{prefix}.sourceUrl must identify the registered GitHub repository")
        expected = f"pkg:github/{repository}@{dep['version']}"
        if dep["purl"] != expected or not PURL_RE.fullmatch(dep["purl"]):
            errors.append(f"{prefix}.purl must be {expected}")
        if dep["kind"] == "github-action":
            workflows = dep.get("workflows")
            if not isinstance(workflows, list) or not workflows or any(
                not isinstance(x, str) or not x.startswith(".github/workflows/") for x in workflows
            ):
                errors.append(f"{prefix}.workflows must list workflow paths")
        if dep["kind"] == "vendored":
            items = dep.get("files")
            if not isinstance(items, list) or not items or any(
                not isinstance(x, dict) or not isinstance(x.get("path"), str)
                or not isinstance(x.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", x["sha256"])
                for x in items
            ):
                errors.append(f"{prefix}.files must list each vendored path and SHA-256")
    return errors


def validate_workflows(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actions = {d["repository"]: d for d in manifest.get("dependencies", [])
               if isinstance(d, dict) and d.get("kind") == "github-action"}
    observed = {name: set() for name in actions}
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        return ["missing .github/workflows directory"]
    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not re.match(r"^\s*uses:\s*", line):
                continue
            match = USES_RE.fullmatch(line)
            if not match:
                errors.append(f"{relative}:{number}: action must be owner/repo@40-character-SHA with tag comment")
                continue
            repository, commit, tag = match.groups()
            if not COMMIT_RE.fullmatch(commit):
                errors.append(f"{relative}:{number}: mutable action ref {repository}@{commit} is forbidden")
                continue
            dep = actions.get(repository)
            if dep is None:
                errors.append(f"{relative}:{number}: action {repository!r} is not registered")
                continue
            if commit != dep["commit"] or tag != dep["version"]:
                errors.append(f"{relative}:{number}: action pin/tag does not match registry for {repository}")
            observed[repository].add(relative)
    for repository, dep in actions.items():
        if observed[repository] != set(dep.get("workflows", [])):
            errors.append(f"{repository}: workflow inventory mismatch")
    action = actions.get("mozilla-actions/sccache-action")
    tool = next((d for d in manifest.get("dependencies", [])
                 if isinstance(d, dict) and d.get("repository") == "mozilla/sccache"), None)
    nightly = directory / "nightly-benchmarks.yml"
    if action and tool and nightly.is_file():
        text = nightly.read_text(encoding="utf-8")
        pattern = (r"uses:\s*mozilla-actions/sccache-action@" + re.escape(action["commit"]) +
                   r"\s+#\s*" + re.escape(action["version"]) +
                   r"\s*\n\s*with:\s*\n\s*version:\s*['\"]?" + re.escape(tool["version"]) + r"['\"]?\s*(?:\n|$)")
        if not re.search(pattern, text):
            errors.append("nightly workflow must pin the sccache action input to the registry version")
    return errors


def validate_cmake(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    registered = {d.get("name") for d in manifest.get("dependencies", []) if isinstance(d, dict)}
    ignored = {".git","build","out","third_party"}
    paths = [root / "CMakeLists.txt", *root.rglob("CMakeLists.txt"), *root.rglob("*.cmake")]
    seen: set[Path] = set()
    for path in paths:
        if path in seen or not path.is_file() or any(part in ignored for part in path.parts):
            continue
        seen.add(path)
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        for package in re.findall(r"\bfind_package\s*\(\s*([A-Za-z0-9_]+)", source, re.I):
            if package not in CMAKE_BUILTIN_PACKAGES and package not in registered:
                errors.append(f"{relative}: unregistered find_package({package})")
        for expr in (r"\bFetchContent_Declare\s*\(\s*([A-Za-z0-9_.+-]+)",
                     r"\bExternalProject_Add\s*\(\s*([A-Za-z0-9_.+-]+)"):
            for name in re.findall(expr, source, re.I):
                if name not in registered:
                    errors.append(f"{relative}: unregistered external component {name!r}")
    return errors


def validate_vendored_files(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    declared: dict[str, str] = {}
    for dep in manifest.get("dependencies", []):
        if isinstance(dep, dict) and dep.get("kind") == "vendored":
            for item in dep.get("files", []):
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    declared[item["path"]] = item.get("sha256", "")
    for path in (root / "third_party").rglob("*"):
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
            relative = path.relative_to(root).as_posix()
            expected = declared.get(relative)
            if expected is None:
                errors.append(f"{relative}: vendored source is not registered")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(f"{relative}: vendored SHA-256 mismatch")
    for relative in declared:
        path = root / relative
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            errors.append(f"declared vendored file missing or escapes repository: {relative}")
    return errors


def check_repository(root: Path) -> list[str]:
    errors: list[str] = []
    for name, marker in (("LICENSE","Apache License"),("NOTICE","TASIMAS GUI Framework")):
        try:
            content = (root / name).read_text(encoding="utf-8")
            if marker not in content:
                errors.append(f"{name}: expected marker {marker!r} missing")
        except OSError as exc:
            errors.append(f"{name}: {exc}")
    try:
        manifest = json.loads((root / "third_party" / "dependencies.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"cannot read third_party/dependencies.json: {exc}"]
    errors.extend(validate_manifest(manifest))
    if isinstance(manifest, dict):
        errors.extend(validate_workflows(root, manifest))
        errors.extend(validate_cmake(root, manifest))
        errors.extend(validate_vendored_files(root, manifest))
    return errors


def main() -> int:
    if len(sys.argv) > 2:
        print("usage: check_third_party.py [repository-root]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parents[1]
    errors = check_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: project license, dependency registry, immutable Actions, CMake declarations, vendored hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
