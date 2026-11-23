#!/usr/bin/env python3
"""Positive and negative regression tests for the compiler policy guard."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from check_compiler_policy import check_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_FILES = (
    "cmake/compiler-support.json",
    "cmake/TgfCompileOptions.cmake",
    "cmake/TgfQualityTools.cmake",
    "CMakeLists.txt",
    "CMakePresets.json",
    ".github/workflows/ci.yml",
    ".github/workflows/source-quality.yml",
    ".clang-format",
    ".clang-tidy",
    "docs/COMPILER_SUPPORT.md",
    "tools/check_format.py",
)


class CompilerPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        for relative in FIXTURE_FILES:
            source = REPOSITORY_ROOT / relative
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_current_repository_policy_and_matrix_pass(self) -> None:
        self.assertEqual(check_repository(self.root), [])

    def test_policy_review_date_must_be_valid_iso_date(self) -> None:
        path = self.root / "cmake/compiler-support.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["policy_date"] = "18/11/2026"
        path.write_text(json.dumps(policy), encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("policy_date must be a valid ISO-8601 date" in error for error in errors))

    def test_msvc_install_must_use_channel_aware_waiting_bootstrapper(self) -> None:
        path = self.root / ".github/workflows/ci.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("VisualStudio.18.Release.LTSC.18.11", "VisualStudio.18.Stable")
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("modify operation must set the Visual Studio 18.11 LTSC channel" in error for error in errors))

    def test_msvc_install_must_request_explicit_14_52_component(self) -> None:
        path = self.root / ".github/workflows/ci.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("Microsoft.VisualStudio.Component.VC.14.52.18.11.x86.x64", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", 1)
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("explicit MSVC 14.52 x64/x86 component" in error for error in errors))

    def test_stale_compiler_manifest_is_rejected(self) -> None:
        path = self.root / "cmake/compiler-support.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["tier_one_compilers"]["msvc"] = ["14.51", "14.50"]
        path.write_text(json.dumps(policy), encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("Tier-1 policy" in error for error in errors))

    def test_manifest_and_ci_matrix_must_agree(self) -> None:
        path = self.root / ".github/workflows/ci.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace('toolset: "14.52"', 'toolset: "14.50"', 1)
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("msvc-14.52 must set toolset" in error for error in errors))

    def test_a_missing_compiler_target_is_rejected(self) -> None:
        path = self.root / ".github/workflows/ci.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("compiler-key: msvc-14.51", "compiler-key: msvc-14.50", 1)
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("exactly seven unique targets" in error for error in errors))

    def test_ci_must_keep_warnings_as_errors_for_every_target(self) -> None:
        path = self.root / ".github/workflows/ci.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace('TGF_WARNINGS_AS_ERRORS: "ON"', 'TGF_WARNINGS_AS_ERRORS: "OFF"', 1)
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any("every matrix job" in error for error in errors))

    def test_clang_analysis_must_keep_both_llvm_generations(self) -> None:
        path = self.root / ".github/workflows/source-quality.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace('llvm-version: "22"', 'llvm-version: "21"', 1)
        path.write_text(text, encoding="utf-8")
        errors = check_repository(self.root)
        self.assertTrue(any('llvm-version: "22"' in error for error in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
