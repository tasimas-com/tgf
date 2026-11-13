# ADR-NNNN: Short decision title

**Status:** Proposed  
**Date:** YYYY-MM-DD  
**Deciders:** [roles or people who made the decision]  
**Supersedes:** [ADR IDs, or "None"]  
**Superseded by:** [ADR ID, or "None"]

> Copy this file to `docs/adr/NNNN-short-kebab-case-title.md`. Keep the status accurate.
> A proposal is not an accepted decision. Replace every bracketed instruction before
> changing the status to Accepted.

## Context

Describe the problem, forces, background, and constraints that make a decision necessary.
Include relevant TGF modules, users, supported platforms, existing behavior, and references
to the applicable `TODO.md` task or earlier ADRs.

## Decision drivers

List the requirements that matter when comparing options. Include measurable constraints
when they exist (for example, latency, memory, binary size, portability, ABI compatibility,
security, accessibility, or maintenance cost). Distinguish mandatory constraints from
preferences.

## Considered options

Describe the credible alternatives, including keeping the current behavior or making no
change. For each option, record the important benefits, costs, risks, and reasons for
acceptance or rejection.

## Decision

State the selected approach precisely enough that implementation and review can determine
whether it follows the decision. Include the boundary of the decision and any behavior it
explicitly does not cover.

## Consequences

### Positive consequences

- [Benefits and problems this decision resolves.]

### Negative consequences and trade-offs

- [Costs, limitations, risks, and newly introduced constraints.]

### Compatibility and migration

Explain source/API/ABI, file-format, dependency, platform, and data migration effects.
State how existing users or modules move to the new behavior. Use "Not applicable" with
a reason when there is no migration.

### Security, privacy, and reliability

Describe relevant trust boundaries, failure modes, data exposure, and mitigations. Use
"Not applicable" with a reason only when those concerns genuinely do not apply.

## Validation and rollout

Define the evidence needed to show that the decision works: tests, benchmarks, platform
runs, security review, compatibility checks, or operational observations. Give exact
commands or acceptance criteria where possible. Do not record planned validation as
completed validation.

Describe rollout, fallback, and rollback strategy when relevant. Link the implementing
pull request and the completed evidence once available.

## References

- [Relevant TODO.md task or section]
- [Related ADRs, design documents, issues, specifications, or measurements]
