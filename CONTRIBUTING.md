# Contributing to TGF

Thank you for considering a contribution to the TASIMAS GUI Framework (TGF).

TGF is an early-stage C++20 framework. The repository currently contains a working
`tgf::core` foundation and its verification tooling; most higher-level modules are still
architectural work in progress. Read the current implementation status and master checklist
before choosing a task:

- [Implementation status](docs/STATUS.md)
- [Master plan and task checklist](TODO.md)
- [Build and test instructions](docs/BUILDING.md)
- [Normative coding standard](docs/CODING_STANDARD.md)
- [Architecture Decision Records](docs/adr/README.md)

This guide describes the contribution process. It does not promise that every proposal will
be accepted or that every planned module is already implemented.

## 1. Before you start

1. Search existing issues and pull requests for related work.
2. For a bug, check whether it reproduces on the current `main` branch and identify the
   smallest useful reproduction.
3. For a feature or architecture change, open or join an issue before starting a large
   implementation.
4. Check the relevant Phase 0–13 task and acceptance criteria in `TODO.md`. Do not mark a
   task complete just because code exists; its written requirements and verification
   evidence must all be satisfied.
5. For a change affecting architecture, module boundaries, public API/ABI, threading,
   memory ownership, portability, security, performance budgets, or supported dependencies,
   follow the ADR process below.

Use the [bug report](https://github.com/tasimas-com/tgf/issues/new?template=bug_report.yml)
or [feature request](https://github.com/tasimas-com/tgf/issues/new?template=feature_request.yml)
form when applicable. Do not put credentials, private user data, crash dumps containing
personal information, or unreleased security details in a public issue.

## 2. Development environment

Use the supported CMake presets rather than inventing a separate build configuration.
Requirements and supported compiler generations are documented in
[BUILDING.md](docs/BUILDING.md) and [COMPILER_SUPPORT.md](docs/COMPILER_SUPPORT.md).

A standard local Release build is:

```sh
cmake --preset release
cmake --build --preset release --parallel
ctest --preset release
```

For Debug:

```sh
cmake --preset debug
cmake --build --preset debug --parallel
ctest --preset debug
```

With `TGF_BUILD_TESTS=ON`, CMake requires Python 3.10 or newer. The hosted workflow
explicitly sets up Python 3.13. Run commands from the repository root.

Before opening a pull request:

```sh
cmake --build build/release --target format-check
ctest --preset release
```

If you changed the build graph, compiler policy, CI workflows, dependency policy, or
documentation contracts, run the relevant Python policy checks through CTest as well.
Do not silence, skip, weaken, or mark required tests as allowed failures merely to get a
green result.

## 3. Coding and design expectations

The normative rules are in [CODING_STANDARD.md](docs/CODING_STANDARD.md). In particular:

- Keep C++ implementation code within its owning module and obey the dependency table in
  `TODO.md` §4. Use canonical public headers for cross-module dependencies.
- Keep public headers self-contained. Do not expose private implementation or third-party
  platform/graphics SDK headers through the public API.
- Follow the project's ownership, lifetime, allocator, error-handling, threading, and
  realtime constraints. Do not introduce exceptions or RTTI into the TGF library
  implementation.
- Keep changes focused. Avoid unrelated formatting, generated files, build output,
  vendored files, and machine-specific paths.
- Add or update regression tests for behavior changes and newly introduced invariants.
  A test should fail when the behavior is broken, not merely execute the code.
- Document externally visible API, compatibility, performance, and platform constraints.
  Never claim an optimization or guarantee that has not been demonstrated.

If a change affects a public interface or project-wide rule, explain its compatibility and
migration consequences in the pull request and, when appropriate, an ADR.

## 4. Architecture Decision Records

ADRs preserve important decisions so later contributors do not unknowingly reverse
architectural constraints.

Create an ADR when a change selects or changes a project-wide approach, including module
boundaries, public APIs/ABIs, ownership, threading, rendering backends, dependencies, file
formats, platform support, performance budgets, or security boundaries.

1. Read [the ADR index](docs/adr/README.md) and the relevant decision in `TODO.md` §3.
2. Copy [`docs/adr/TEMPLATE.md`](docs/adr/TEMPLATE.md) to
   `docs/adr/NNNN-short-kebab-case-title.md`, using the next available ID under the
   allocation rules in the ADR index.
3. Start with **Proposed** while the decision is under discussion. Do not label a decision
   **Accepted** until the maintainers have agreed to it.
4. Record the problem, constraints, alternatives, decision, trade-offs, validation plan,
   and references. If a section does not apply, explain why instead of deleting it.
5. Link the ADR from `docs/adr/README.md` and the implementing pull request.
6. Do not rewrite an accepted ADR to hide a changed decision. Write a superseding ADR and
   link both records.

A code change that contradicts an accepted ADR must include the replacement decision and
migration plan; implementation alone does not supersede an ADR.

## 5. Pull request process

Open a pull request against `main`. Use the repository pull request template and:

- State the problem and observable result of the change.
- Link the issue or task it addresses. Use GitHub closing keywords only when the PR really
  closes that issue.
- Keep one logical change per PR where practical. Split unrelated refactors and feature work.
- Explain design alternatives and trade-offs for non-trivial changes.
- List exact build, test, formatter, and analysis commands you ran, plus their results.
  Distinguish local results from hosted CI results.
- Add or update documentation and ADR links when behavior or policy changes.
- Call out untested platforms, missing evidence, compatibility risks, and follow-up work.
  Do not describe unverified work as complete.

Maintainers may ask for changes, additional tests, an ADR, or smaller scope. Be prepared to
explain the implementation and respond to review comments. A pull request is not merged
until required checks and maintainer review requirements are satisfied.

## 6. Commit and review hygiene

Use clear, descriptive commit messages. There is no enforced commit-message prefix scheme
at present; do not assume one is mandatory.

Before pushing, review the diff for accidental generated files, build directories, binaries,
editor files, secrets, absolute paths, local usernames, machine-specific configuration,
private data, unrelated changes, formatting churn, missing tests, and unsupported claims.

Do not force-push to or rewrite another contributor's branch without their agreement.
Do not bypass a failing required check. If a check is flaky or appears incorrect, report
the evidence and fix the underlying check or document a justified maintainer-approved
exception.

## 7. Dependencies and licensing

The project intends to use Apache-2.0, but the formal license, SBOM tooling, and third-party
policy are still tracked by P0.1.8 and have not yet been delivered in this repository.
That stated intent is not a substitute for a published license grant. Until the license
and third-party policy are present, do not assume that the source is already licensed
under Apache-2.0.

Only submit material you created or are authorized to contribute. Do not copy code,
assets, fonts, test data, or documentation from another project unless its license and
attribution requirements have been checked and its use approved by the maintainers.
Do not add dependencies without describing their purpose, version/source, license,
runtime/build impact, maintenance status, and security implications. The P0.1.8
license/SBOM work must be completed before third-party intake is treated as finalized.

No Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO) process is
currently defined. Do not claim that either has been signed or is required.

## 8. Community expectations

Participation is governed by the [TGF Code of Conduct](CODE_OF_CONDUCT.md). By taking part
in repository discussions, issues, reviews, or other project spaces, you agree to follow
that policy.

For sensitive conduct concerns, do not create a public issue containing private details.
Use GitHub's **Report content** flow on the relevant issue, pull request, or comment and
choose **Report to repository admins** when that option is available. If it is unavailable,
use **Report abuse to GitHub Support**. Maintainers should enable GitHub's repository
reported-content feature so reports can be received and reviewed privately; the setting is
managed in repository settings and cannot be enabled by a file in this repository.

Thank you for helping make TGF reliable, understandable, and maintainable.
