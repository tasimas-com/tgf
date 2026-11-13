#!/usr/bin/env python3
"""Regression guard for TGF contributor, moderation, GitHub-template, and ADR policy."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_FILES = (
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/adr/TEMPLATE.md",
    "docs/adr/README.md",
)

REQUIRED_SECTIONS = {
    "CONTRIBUTING.md": (
        "## 1. Before you start",
        "## 2. Development environment",
        "## 3. Coding and design expectations",
        "## 4. Architecture Decision Records",
        "## 5. Pull request process",
        "## 7. Dependencies and licensing",
        "## 8. Community expectations",
    ),
    "CODE_OF_CONDUCT.md": (
        "## 1. Our commitment",
        "## 2. Expected behavior",
        "## 3. Unacceptable behavior",
        "## 4. Scope",
        "## 5. Reporting a concern",
        "## 6. Enforcement and corrective action",
        "## 7. Retaliation and privacy",
        "## 8. Attribution",
    ),
    ".github/PULL_REQUEST_TEMPLATE.md": (
        "## Summary",
        "## Related issue or task",
        "## Change type",
        "## Design and compatibility",
        "## Validation performed",
        "## Review checklist",
        "## Remaining work or risks",
    ),
    "docs/adr/TEMPLATE.md": (
        "## Context",
        "## Decision drivers",
        "## Considered options",
        "## Decision",
        "## Consequences",
        "## Compatibility and migration",
        "## Security, privacy, and reliability",
        "## Validation and rollout",
        "## References",
    ),
}

ISSUE_FORM_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes", "upload"}


def fail(message: str) -> int:
    print(f"community policy check FAILED: {message}", file=sys.stderr)
    return 1


def read_required(root: Path, relative: str) -> str:
    path = root / relative
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read required file {relative}: {exc}") from exc
    if not text.strip():
        raise RuntimeError(f"required file is empty: {relative}")
    return text


def check_issue_form(root: Path, relative: str, errors: list[str]) -> None:
    try:
        source = read_required(root, relative)
    except RuntimeError as exc:
        errors.append(str(exc))
        return

    for key in ("name:", "description:", "body:"):
        if not re.search(rf"(?m)^{re.escape(key)}", source):
            errors.append(f"{relative}: missing required top-level key {key[:-1]}")

    field_types = re.findall(r"(?m)^\s*- type:\s*([a-z]+)\s*$", source)
    if not field_types:
        errors.append(f"{relative}: body must define at least one issue-form field")
    for field_type in field_types:
        if field_type not in ISSUE_FORM_TYPES:
            errors.append(f"{relative}: unsupported issue-form field type {field_type!r}")

    field_ids = re.findall(r"(?m)^\s+id:\s*([A-Za-z0-9_-]+)\s*$", source)
    if len(field_ids) != len(set(field_ids)):
        errors.append(f"{relative}: field IDs must be unique")

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        yaml = None

    if yaml is not None:
        try:
            document = yaml.safe_load(source)
        except yaml.YAMLError as exc:
            errors.append(f"{relative}: invalid YAML: {exc}")
            return
        if not isinstance(document, dict):
            errors.append(f"{relative}: YAML root must be a mapping")
            return
        for key in ("name", "description", "body"):
            if key not in document:
                errors.append(f"{relative}: parsed form is missing {key!r}")
        if not isinstance(document.get("body"), list):
            errors.append(f"{relative}: body must be a list")
            return
        parsed_ids: set[str] = set()
        for index, field in enumerate(document["body"]):
            if not isinstance(field, dict) or field.get("type") not in ISSUE_FORM_TYPES:
                errors.append(f"{relative}: body entry {index} has an invalid field type")
                continue
            field_id = field.get("id")
            if field_id is not None:
                if not isinstance(field_id, str) or field_id in parsed_ids:
                    errors.append(f"{relative}: field IDs must be unique non-empty strings")
                parsed_ids.add(field_id)
        name = document.get("name")
        description = document.get("description")
        if not isinstance(name, str) or len(name.strip()) <= 3:
            errors.append(f"{relative}: GitHub issue-form name must contain more than three characters")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{relative}: description must be a non-empty string")


def main() -> int:
    if len(sys.argv) > 2:
        return fail("usage: check_community_files.py [repository-root]")
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parents[1]
    errors: list[str] = []

    contents: dict[str, str] = {}
    for relative in REQUIRED_FILES:
        try:
            contents[relative] = read_required(root, relative)
        except RuntimeError as exc:
            errors.append(str(exc))

    for relative, sections in REQUIRED_SECTIONS.items():
        content = contents.get(relative, "")
        for section in sections:
            if section not in content:
                errors.append(f"{relative}: missing required section {section!r}")

    coc = contents.get("CODE_OF_CONDUCT.md", "")
    for phrase in (
        "Report to repository admins",
        "Report abuse to GitHub Support",
        "retaliation",
        "Contributor Covenant, version 2.1",
    ):
        if phrase.casefold() not in coc.casefold():
            errors.append(f"CODE_OF_CONDUCT.md: missing reporting or policy contract {phrase!r}")
    if re.search(r"\[(?:insert|add|replace|todo)[^\]]*\]", coc, re.IGNORECASE):
        errors.append("CODE_OF_CONDUCT.md: unresolved contact or policy placeholder")

    contributing = contents.get("CONTRIBUTING.md", "")
    for phrase in (
        "Python 3.10",
        "cmake --preset release",
        "ctest --preset release",
        "format-check",
        "docs/adr/TEMPLATE.md",
        "P0.1.8",
        "Apache-2.0",
        "No Contributor License Agreement (CLA)",
    ):
        if phrase.casefold() not in contributing.casefold():
            errors.append(f"CONTRIBUTING.md: missing repository-specific guidance {phrase!r}")

    config = contents.get(".github/ISSUE_TEMPLATE/config.yml", "")
    if not re.search(r"(?m)^blank_issues_enabled:\s*false\s*$", config):
        errors.append(".github/ISSUE_TEMPLATE/config.yml: blank_issues_enabled must be false")

    check_issue_form(root, ".github/ISSUE_TEMPLATE/bug_report.yml", errors)
    check_issue_form(root, ".github/ISSUE_TEMPLATE/feature_request.yml", errors)

    adr_template = contents.get("docs/adr/TEMPLATE.md", "")
    for phrase in ("**Status:** Proposed", "**Date:**", "**Deciders:**", "Supersedes:", "Superseded by:"):
        if phrase not in adr_template:
            errors.append(f"docs/adr/TEMPLATE.md: missing decision metadata {phrase!r}")

    adr_index = contents.get("docs/adr/README.md", "")
    for phrase in ("TEMPLATE.md", "docs/adr/NNNN-", "0031", "Proposed", "Accepted", "Superseded"):
        if phrase not in adr_index:
            errors.append(f"docs/adr/README.md: missing ADR process contract {phrase!r}")

    readme_path = root / "README.md"
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"cannot read README.md: {exc}")
        readme = ""
    for link in ("CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/adr/"):
        if link not in readme:
            errors.append(f"README.md: missing community/governance link {link!r}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    parser_note = " (PyYAML schema-level syntax check enabled)" if _has_yaml() else " (static schema-contract check; PyYAML not installed)"
    print("PASS: contributor guide, code of conduct, GitHub issue/PR templates, and ADR process" + parser_note)
    return 0


def _has_yaml() -> bool:
    try:
        import yaml  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
