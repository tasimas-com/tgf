# Third-party components

This directory is the authoritative home for TGF's third-party intake records.

- [POLICY.md](POLICY.md) defines license approval, provenance, pinning, attribution,
  and vendored-file requirements.
- [dependencies.json](dependencies.json) is the machine-readable inventory consumed by
  the fail-closed policy checker and SPDX generator.
- [../docs/THIRD_PARTY.md](../docs/THIRD_PARTY.md) documents SBOM generation and scope.

The audited baseline has **no vendored third-party files and no direct third-party C++
runtime/library dependencies** in the CMake graph. The registry records the GitHub
Actions, sccache, and pinned IWYU releases used by CI. They are development/build
tools, not libraries linked into TGF distributable binaries.

IWYU's upstream source tree includes GoogleTest under its own MIT license. The TGF
source-quality workflow builds only the IWYU executable target, not the GoogleTest
unit-test target; the nested upstream files are documented as bundled but not built.

Do not place downloaded source, assets, fonts, generated tables, or upstream notice
files here until origin, immutable revision, license, attribution, SHA-256, purpose,
scope, and policy approval have been recorded in the registry.
