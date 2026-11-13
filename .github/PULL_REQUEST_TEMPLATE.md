## Summary

<!-- Explain the problem and the observable result of this change. -->

## Related issue or task

<!-- Link an issue or TODO.md task. Use closing keywords only when this PR truly closes an issue. -->

## Change type

- [ ] Bug fix
- [ ] Feature or capability
- [ ] Refactor with no intended behavior change
- [ ] Build, CI, or tooling
- [ ] Documentation or policy
- [ ] Other (explain below)

## Design and compatibility

- What alternatives were considered, and why was this approach selected?
- Does this change affect a public header, public API, ABI, file format, dependency, or module boundary?
- Is an ADR required or updated? Link it, or explain why not.
- Are migration, compatibility, security, privacy, performance, or platform consequences relevant?

## Validation performed

List the exact commands and results. Distinguish local tests from hosted CI.

| Command / check | Result | Environment |
|---|---|---|
| `cmake --preset ...` | | |
| `cmake --build --preset ... --parallel` | | |
| `ctest --preset ...` | | |
| `cmake --build build/release --target format-check` | | |
| Other analysis or manual checks | | |

## Review checklist

- [ ] I read and followed [CONTRIBUTING.md](../CONTRIBUTING.md) and [CODING_STANDARD.md](../docs/CODING_STANDARD.md).
- [ ] The change is focused and contains no unrelated generated files, build output, secrets, or machine-specific paths.
- [ ] I added or updated regression tests for changed behavior and new invariants.
- [ ] I updated user-facing and engineering documentation where necessary.
- [ ] I checked module dependencies, public/private header boundaries, ownership, lifetime, and error handling.
- [ ] I considered threading, realtime behavior, performance, portability, accessibility, and security where relevant.
- [ ] I updated or linked an ADR for architectural or project-wide decisions, or explained why none is needed.
- [ ] I identified unsupported platforms, unverified claims, limitations, and remaining work.
- [ ] I have the right to submit this contribution and have checked the applicable license of any included third-party material.

## Remaining work or risks

<!-- List what is not done or not verified. Write "None" only when that is accurate. -->
