# ADR-0016: Project license, third-party intake, and SPDX SBOM

**Status:** Accepted  
**Date:** 2026-11-17  
**Deciders:** TASIMAS project owner and repository maintainers  
**Supersedes:** None  
**Superseded by:** None

## Context

TGF's master plan records Apache-2.0 as its intended license, subject to this audit.
The repository needs an explicit grant, reviewed third-party intake rules, provenance
records, and a machine-readable SBOM. The current CMake graph has no third-party C++
library dependency and the source tree has no vendored third-party implementation files.
GitHub Actions and the sccache executable used in CI are still external components and
must be inventoried, although they are not linked into TGF runtime binaries.

## Decision drivers

- Publish an explicit license for TGF-owned project material.
- Reject unknown/unreviewed dependency licenses by default.
- Record upstream identity, version, immutable revision, license, scope, and purpose.
- Pin CI actions and downloaded tools.
- Generate a standard SBOM without adding a Python package dependency.
- Distinguish CI-only tooling from runtime dependencies.

## Considered options

1. Leave licensing and inventory informal. Rejected because downstream users cannot
   reliably determine the grant or dependency obligations.
2. Depend on an external package manager or SBOM SaaS. Rejected for this initial scope:
   it adds another dependency and does not replace a reviewed source registry.
3. Keep a reviewed JSON registry, stdlib SPDX 2.3 generator, and fail-closed tests.
   **Selected** for low toolchain impact and version-controlled evidence.

## Decision

### Project license

TGF project material that TASIMAS is authorized to license is released under the
**Apache License, Version 2.0**. The full text is in the repository-root `LICENSE`;
`NOTICE` records the project notice scope. SPDX identifier: `Apache-2.0`.

This does not assert that TASIMAS owns work authored by other contributors or third
parties. Only material for which the project has sufficient licensing authority may
be included under this grant. Third-party terms remain in force.

### Third-party intake

- Every direct external component must be registered in
  `third_party/dependencies.json` and comply with `third_party/POLICY.md`.
- The narrow SPDX allowlist is `Apache-2.0`, `MIT`, `FTL`, and `BSD-3-Clause`.
  This implements the master plan's future dependency candidates: HarfBuzz (MIT),
  FreeType (FTL option only), Vulkan Memory Allocator (MIT), and zstd (BSD-3-Clause
  option only). These are approved candidates, not current dependencies; they enter the
  SBOM only after a specific revision is selected and the component is integrated.
  FreeType's alternate GPL choice and zstd's GPL choice are not approved. The FTL credit
  and product-documentation clause, and all upstream subcomponent notices, must be
  reviewed and satisfied. Any other license/expression requires an accepted maintainer
  decision and policy/ADR change before introduction.
- Records contain upstream source, version/tag, immutable commit, PURL, license, scope,
  purpose, and workflow references where applicable.
- Workflow actions use full 40-character commit SHAs with human-readable release tags in
  comments. Downloaded tools use explicit versions; nightly sccache is pinned to
  `v0.16.0`, not an unspecified latest release.
- Vendored files require an approved license, retained license/NOTICE material, exact
  source revision, per-file SHA-256, and attribution. No vendored code is in this
  initial inventory.
- Transitive code bundled inside upstream actions, hosted-runner packages, OS packages,
  and compiler/Python distributions is outside this repository-level direct SBOM and is
  not claimed to be recursively audited here.

### SBOM format and generation

The project SBOM is SPDX 2.3 JSON. `tools/generate_sbom.py` generates it from the
reviewed registry; `tools/check_third_party.py` validates the registry and live
workflow/CMake declarations. Both use Python's standard library. CTest runs the policy
gate and regressions. `.github/workflows/sbom.yml` publishes the generated artifact.

## Consequences

New dependencies require synchronized registry, license, provenance, workflow/build
configuration, tests, and SBOM updates. Immutable action pins prevent mutable release
tags from silently changing CI code. The inventory distinguishes CI tooling from runtime
libraries. The SBOM is direct-component, not a recursive host-image inventory.

## Compatibility and migration

This decision changes no public C++ API, ABI, CMake target, or runtime behavior.
Redistributors must preserve Apache-2.0 and applicable third-party notices.

## Security, privacy, and reliability

The policy check fails on missing metadata, unapproved identifiers, mutable or
unregistered actions, mismatched action pins, undeclared CMake packages, and unrecorded
vendored source files. The SBOM contains public dependency metadata only.

## Validation and rollout

Run the policy checker and unit tests, configure/build/test the complete compiler
matrix, run source-quality checks, and inspect the SPDX artifact from the dedicated
workflow before closing P0.1.8.

## References

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [Apache applying the license guidance](https://www.apache.org/legal/apply-license)
- [SPDX 2.3](https://spdx.org/rdf/ontology/spdx-2-3/)
- [SPDX License List](https://spdx.org/licenses/)
- [FreeType license selection](https://freetype.org/license) and [SPDX FTL identifier](https://spdx.org/licenses/FTL.html)
- [HarfBuzz upstream COPYING](https://github.com/harfbuzz/harfbuzz/blob/main/COPYING)
- [Vulkan Memory Allocator upstream README](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator)
- [zstd upstream BSD license](https://github.com/facebook/zstd/blob/dev/LICENSE)
- [Third-party policy](../../third_party/POLICY.md)
- [Dependency registry](../../third_party/dependencies.json)
- [SBOM documentation](../THIRD_PARTY.md)
