# Third-party components

This directory is the authoritative home for TGF's third-party intake records.

- [POLICY.md](POLICY.md) defines the allowlist, review process, pinning, provenance,
  attribution, and SBOM requirements.
- [dependencies.json](dependencies.json) is the machine-readable registry used by the
  fail-closed policy checker and SPDX generator.
- [../docs/THIRD_PARTY.md](../docs/THIRD_PARTY.md) explains the SBOM scope and commands.

At the P0.1.8 baseline there are **no vendored third-party source files and no direct
third-party C++ runtime/library dependencies** in the TGF CMake graph. The registry
records GitHub Actions and the sccache binary used by CI; these are development tools,
not libraries linked into TGF distributable binaries.

Do not place downloaded code here until its origin, immutable revision, license, notices,
checksums, purpose, and approval have been registered.
