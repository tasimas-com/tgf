# TGF third-party dependency policy

**Owner:** TASIMAS project maintainers  
**Effective date:** 2026-11-17  
**Decision record:** [ADR-0016](../docs/adr/0016-third-party-dependencies-and-sbom.md)

## 1. Scope

This policy covers source code, libraries, downloaded tools, build/test tools, GitHub
Actions, CI helpers, assets, fonts, test data, and documentation obtained externally.
CI actions/tools are recorded with `ci` scope and are distinguished from runtime
dependencies. `dependencies.json` is the machine-readable inventory.

Audited baseline: zero vendored third-party files (source, assets, fonts, or notices),
zero direct third-party C++ runtime/library dependencies in the CMake graph, and the
explicitly inventoried CI actions, sccache executable, and pinned IWYU 0.26/0.27 tools.

## 2. License approval

The automatic SPDX identifier allowlist is exactly:
- `Apache-2.0` — TGF project material.
- `MIT` — including HarfBuzz and Vulkan Memory Allocator.
- `FTL` — FreeType License; for FreeType, use the FTL option only.
- `BSD-3-Clause` — for the explicitly selected BSD option of zstd.
- `NCSA` — reserved solely for Include-What-You-Use 0.26/0.27 in source-quality CI, not a general dependency approval.

The four project-license identifiers plus the reserved NCSA CI-tool allowance form the narrow, project-specific baseline, not a blanket approval
for every upstream component that claims one of them. The master plan (section 9,
third-party policy decision) specifically identifies HarfBuzz, FreeType (FTL), VMA,
and zstd as future dependencies that may be used when required, vendored, wrapped behind
TGF interfaces, pinned, and included in the SBOM. The candidate list is machine-readable
in `approvedProjectCandidates` in `dependencies.json`; these candidates are **not current
dependencies** and do not appear in today's SBOM until actually introduced.

| Candidate | Approved SPDX choice | Required review |
|---|---|---|
| HarfBuzz | `MIT` | Review upstream COPYING and per-directory COPYING overrides at the pinned revision. |
| FreeType | `FTL` only | Do not select the alternate GPL choice. The FTL contains a credit/documentation clause that must be satisfied in product documentation; review bundled subcomponents too. |
| Vulkan Memory Allocator | `MIT` | Review the upstream license and all bundled material at the pinned revision. |
| zstd | `BSD-3-Clause` only | Select the BSD option, not the GPL option; verify the selected source files and bundled material. |

The `NCSA` allowance is restricted by the checker to
`include-what-you-use/include-what-you-use` versions `0.26` and `0.27`, used only in
source-quality CI. Their upstream `LICENSE.TXT` is the University of Illinois/NCSA
Open Source License. The upstream source tree also contains GoogleTest under
`vendor/googletest` with its own MIT license; TGF CI builds only the IWYU executable
target, not the GoogleTest-backed unit-test target. That nested source is documented as
bundled-but-not-built, rather than misrepresented as a TGF runtime dependency.

This conservative allowlist is not a statement that every unlisted license is
incompatible with Apache-2.0. Any unlisted license, SPDX exception, different dual-license
expression, custom license, or `NOASSERTION` requires documented maintainer review and
an accepted ADR/policy change before use.

Never infer a license from a repository name, README badge, package registry, or source
header alone. Review the actual upstream license text at the pinned revision and check
bundled assets/subcomponents, provenance, copyrights, attribution, patent, trademark,
NOTICE, and redistribution obligations. When review is incomplete, do not use the
component. This policy is not legal advice.

## 3. Required dependency record

Every direct external component must be recorded in `dependencies.json` with stable
name, owner/repository, upstream version/tag, immutable 40-character commit SHA, HTTPS
source URL, PURL, SPDX license, scope (`runtime`, `build`, `test`, `dev`, `ci`),
kind (`github-action`, `tool`, `cmake-package`, `vendored`), purpose, and workflow
references when relevant.

GitHub Actions must use the pinned commit SHA in `uses:` and keep the release tag in a
comment. Never use a moving tag or branch. Pin action inputs that download tools; do not
request an unspecified latest release.

Every file under `third_party/` other than the three policy metadata files (`README.md`,
`POLICY.md`, and `dependencies.json`) is treated as vendored material and must have a
registry record. This includes source, binary assets, fonts, upstream LICENSE/COPYING/
NOTICE files, generated tables, and test data. Symlinks are forbidden. The checker
verifies the SHA-256 of every registered file and fails on unregistered files.

Vendored material additionally requires each repository-relative path and SHA-256,
exact upstream revision, retained upstream license/copyright/patent/attribution/NOTICE
files, and clear disclosure of local modifications.

New `find_package`, `FetchContent_Declare`, or `ExternalProject_Add` CMake declarations
must have a matching registry record. Python 3 is the only current external interpreter
requirement; the test suite needs no third-party Python package.

## 4. Review checklist

Review the need, exact source and revision, license text and bundled components,
attribution/NOTICE/patent/trademark conditions, maintenance/security/update status,
platform support, transitive dependencies, runtime/build and binary-size impact,
distribution scope, SPDX record, and regression/CI results. Do not merge an unverified
"permissive" dependency.

## 5. SBOM

Generate the SPDX 2.3 JSON direct-component inventory with:

```sh
python tools/check_third_party.py .
python tools/generate_sbom.py --root . --output build/sbom/tgf.spdx.json
```

Set `SOURCE_DATE_EPOCH` to a fixed commit timestamp for reproducible creation metadata.
The SBOM includes TGF and declared direct components, including CI actions and sccache.
It does not recursively enumerate action-bundled JavaScript packages, hosted-runner
images, OS packages, or compiler/Python distributions. Do not describe it as an
exhaustive host-image SBOM.

## 6. Exceptions

There are no informal exceptions. Unapproved licenses, unavailable revisions, mutable
actions, unverified assets, or unsatisfied notices are blocked. Exceptions require a
separate documented maintainer decision and corresponding policy, registry, checker,
test, and ADR updates.
