# P0.1.7 — Contributor and governance workflow evidence

**Verification date:** 13 November 2026  
**Repository:** [tasimas-com/tgf](https://github.com/tasimas-com/tgf)  
**Verified implementation commit:** `852d724fae3e74f33b78e05ab20cc72de19e0f53`  
**Task:** P0.1.7 — Contribution guide, Code of Conduct, issue/PR templates, ADR template

## Delivered files

| File | Purpose |
|---|---|
| `CONTRIBUTING.md` | Contributor workflow, supported CMake/Python setup, test and formatter commands, engineering expectations, ADR process, PR/review hygiene, dependency and licensing guidance |
| `CODE_OF_CONDUCT.md` | Expected and unacceptable behavior, scope, reporting instructions, enforcement, privacy and anti-retaliation |
| `.github/ISSUE_TEMPLATE/config.yml` | Disables blank issue creation so contributors use structured forms |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Reproducible bug report with revision, environment, steps, expected/actual results, regression status and optional log/repro |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Problem, desired result, alternatives, architecture constraints, evidence and acceptance criteria |
| `.github/PULL_REQUEST_TEMPLATE.md` | Scope, related task/issue, compatibility/ADR impact, exact validation evidence, review checklist and remaining risks |
| `docs/adr/TEMPLATE.md` | Proposed ADR with context, decision drivers, alternatives, decision, consequences, migration, security/reliability, validation and references |
| `docs/adr/README.md` | Existing-record inventory, next free ID (0031), lifecycle/status guidance, and superseding rules |
| `README.md` | Direct links to the contributor guide and Code of Conduct |
| `tools/check_community_files.py` | Regression guard for governance file existence, policy sections, unique issue field IDs, supported form-field types and README links |
| `tests/CMakeLists.txt` | Mandatory `community_governance_policy` CTest registration |
| `docs/CI.md` | Documents the governance policy test and its hosted evidence |

## Implementation details

The contributor guide states the actual project baseline: C++20/CMake, Python 3.10+ for
CTest, supported commands, coding standard, module boundaries, required evidence, ADR rules
and PR hygiene. It does not claim that higher-level framework modules are already
implemented. It also distinguishes the stated Apache-2.0 intent from an operative published
license: the formal license, SBOM tooling and third-party policy remain P0.1.8. No CLA or
DCO process is invented.

The Code of Conduct describes GitHub's **Report to repository admins** route when the
reported-content feature is available and GitHub Support as the fallback. The setting is
admin-managed and cannot be guaranteed by committing a file; the report guide does not
invent a private email address or promise a response time. Repository owners should keep
the reported-content setting enabled. The document's wording is adapted from Contributor
Covenant 2.1 and is not a verbatim reproduction.

The issue forms use GitHub's supported field types (`markdown`, `input`, `textarea`,
`dropdown`). `tools/check_community_files.py` uses Python's standard library by default;
it adds YAML parsing when PyYAML is available. The hosted runner did not have PyYAML, so
the CTest executed the static schema-contract path. During this audit both committed issue
forms and the configuration were independently parsed with **PyYAML 6.0.3**; all forms
loaded as YAML mappings/lists and field IDs were unique.

## Automated test integration

When `TGF_BUILD_TESTS=ON`, CMake requires Python 3.10+ and registers
`community_governance_policy`. The test checks the presence of all governance files,
required sections and project-specific facts, GitHub issue-field type/ID contracts, PR
template review/validation sections, ADR metadata/lifecycle, and README links. It does not
pretend to replace GitHub's server-side issue-form validation or the maintainers' conduct
review responsibilities.

## Hosted verification

### Full build/test matrix

[TGF CI run #392](https://github.com/tasimas-com/tgf/actions/runs/43429879957)  
Run ID: `43429879957` · run number: **392**  
Commit: `852d724fae3e74f33b78e05ab20cc72de19e0f53`  
Result: **14/14 jobs passed**

The matrix covers GCC 15 and 16, LLVM Clang 22 and 23, MSVC 14.50 and 14.51, and AppleClang,
each in Debug and Release.

### Source quality

[Source Quality run #318](https://github.com/tasimas-com/tgf/actions/runs/43429879999)  
Run ID: `43429879999` · run number: **318**  
Commit: `852d724fae3e74f33b78e05ab20cc72de19e0f53`  
Result: **2/2 LLVM jobs passed** (clang-format, clang-tidy with warnings-as-errors, and
strict Include-What-You-Use in the matched LLVM 22/23 toolchain lanes).

### CTest artifact register

All 14 artifacts from run #392 were downloaded. Every ZIP passed integrity validation,
contained exactly one `LastTest.log`, and recorded all **12/12** CTest cases as passed with
zero failure markers. Every log explicitly contains the passing
`community_governance_policy` result.

| Artifact | GitHub artifact ID | CTest result |
|---|---:|---:|
| `ctest-msvc-14.50-debug-Windows` | 14040390571 | 12/12 passed |
| `ctest-msvc-14.50-release-Windows` | 14039377335 | 12/12 passed |
| `ctest-msvc-14.51-debug-Windows` | 14038896334 | 12/12 passed |
| `ctest-msvc-14.51-release-Windows` | 14040140394 | 12/12 passed |
| `ctest-gcc-15-debug-Linux` | 14039201503 | 12/12 passed |
| `ctest-gcc-15-release-Linux` | 14040265219 | 12/12 passed |
| `ctest-gcc-16-debug-Linux` | 14038712010 | 12/12 passed |
| `ctest-gcc-16-release-Linux` | 14039031239 | 12/12 passed |
| `ctest-clang-22-debug-Linux` | 14039166606 | 12/12 passed |
| `ctest-clang-22-release-Linux` | 14038721479 | 12/12 passed |
| `ctest-clang-23-debug-Linux` | 14039641150 | 12/12 passed |
| `ctest-clang-23-release-Linux` | 14039366367 | 12/12 passed |
| `ctest-appleclang-debug-macOS` | 14039601044 | 12/12 passed |
| `ctest-appleclang-release-macOS` | 14039171562 | 12/12 passed |

**Aggregate:** 14 artifacts × 12 tests = **168/168 successful CTest executions**; zero
failures. The two LLVM source-quality jobs passed. P0.1.7 is therefore closed with
repository documentation, structured GitHub templates, policy regression coverage, and
hosted cross-platform evidence.

P0.1.7 closure does not complete P0.1.8 or the remaining Phase 0 work. Phase 0 remains open
and Phase 1 remains blocked.
