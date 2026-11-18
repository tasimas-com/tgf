# TGF source audit archive

The `2026-10-14/` directory contains the evidence package for the audit of the exact
`tgf-project.tar.gz` snapshot supplied on 14 October 2026:

- `TGF_AUDIT_REPORT.md` — full findings, verification results, code-level risks, and the
  272-entry task-by-task assessment.
- `TGF_TASK_AUDIT.csv` — machine-readable task assessment with evidence/gap notes.

These two files are a **historical snapshot** of the audit, not a live status ledger. Their
TODO line numbers refer to the input TODO revision as audited. The canonical, updated task
status is now in the root `TODO.md`; the current project summary is `docs/STATUS.md`.

The 14 October audit predates later repository work. Its note about `tools/check_deps.py`
and the bindings-dependency inconsistency describes the state at that historical capture only.
P0.1.6 was subsequently completed: the checker now has broad positive/negative module-edge
and symlink-boundary regression fixtures, mandatory CTest integration, and hosted 14-job
matrix evidence. See [`P0_1_6_DEPENDENCY_DAG_EVIDENCE.md`](2026-11-13/P0_1_6_DEPENDENCY_DAG_EVIDENCE.md).


The first safety-remediation implementation is documented in [`2026-10-14/TGF_CORE_REMEDIATION.md`](2026-10-14/TGF_CORE_REMEDIATION.md). The subsequent tagged-memory diagnostics and their current verification are documented in [`2026-10-14/TGF_MEMORY_DIAGNOSTICS.md`](2026-10-14/TGF_MEMORY_DIAGNOSTICS.md). The original audit report and CSV remain the immutable baseline for the supplied archive.

The Revision 13 hosted-CI preparation and local verification are documented in
[`2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md`](2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md).
This report records the Windows MSVC/Ninja cache correction and distinguishes local checks
from the still-pending GitHub-hosted Actions execution.


## Current Phase 0 reassessment — 18 November 2026

[`2026-11-18/PHASE_0_REASSESSMENT.md`](2026-11-18/PHASE_0_REASSESSMENT.md) records the independent re-read of the current `tasimas-com/tgf` code, CMake/test infrastructure, workflows, policy scripts, ADRs, and task requirements. It deliberately does not rely on the prior checkbox states. Its findings supersede earlier status summaries where later implementation or newly current toolchain releases changed the assessment. The original 14 October report and CSV remain immutable historical snapshots.
