# Architecture Decision Records

ADRs record project decisions, their rationale, alternatives, consequences, and the
evidence needed to validate them. Read [CONTRIBUTING.md](../../CONTRIBUTING.md) before
proposing or changing an architecture decision.

## Status of the decision record set

ADR-0001 through ADR-0027 are currently specified in the master plan
([`TODO.md` §3](../../TODO.md)) and are intended to become individual records during P0.5.
Their presence in the plan does not mean that the corresponding standalone ADR files have
already been written or accepted.

The standalone records currently present are:

| ADR | Title | Status |
|---|---|---|
| [0012](0012-allocator-ownership-across-modules.md) | Allocator ownership across modules and mapped files | Accepted for the current C++ core implementation; stable cross-toolchain C ABI remains future work |
| [0028](0028-library-linkage-and-artifacts.md) | Library linkage and build artifacts | Accepted |
| [0029](0029-compiler-flags-and-floating-point.md) | Compiler policy, optimisation flags, floating-point determinism | Accepted |
| [0030](0030-showcase-executable.md) | One showcase executable that grows with every phase | Accepted |

## Creating a new ADR

1. Read the relevant decisions in `TODO.md` §3 and search this index for related records.
2. Copy [`TEMPLATE.md`](TEMPLATE.md) to
   `docs/adr/NNNN-short-kebab-case-title.md`.
3. Use the next unused numeric ID. ADR-0001 through ADR-0030 are already assigned or
   reserved by the master plan and existing records; **0031 is the next new ADR ID**.
   Never reuse an ID, even if a proposal is rejected or superseded.
4. Begin with status **Proposed**. Use **Accepted**, **Rejected**, **Deprecated**, or
   **Superseded** only when that status accurately reflects a maintainer decision.
5. Include the ADR in this index and link it from the implementing issue/pull request.
6. Once accepted, preserve the record. A material change to an accepted decision requires
   a new ADR that names the record it supersedes.

An ADR must not turn a proposal into an implementation claim. Planned validation remains
planned until its tests, benchmarks, reviews, or supported-platform evidence have actually
been completed and linked.
