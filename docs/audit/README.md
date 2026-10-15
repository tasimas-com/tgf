# TGF source audit archive

The `2026-10-14/` directory contains the evidence package for the audit of the exact
`tgf-project.tar.gz` snapshot supplied on 14 October 2026:

- `TGF_AUDIT_REPORT.md` — full findings, verification results, code-level risks, and the
  272-entry task-by-task assessment.
- `TGF_TASK_AUDIT.csv` — machine-readable task assessment with evidence/gap notes.

These two files are a **historical snapshot** of the audit, not a live status ledger. Their
TODO line numbers refer to the input TODO revision as audited. The canonical, updated task
status is now in the root `TODO.md`; the current project summary is `docs/STATUS.md`.

The update to `tools/check_deps.py` and its regression test was made after the audit findings
were recorded. It closes the narrow bindings-dependency inconsistency; it does not close the
whole P0.1.6 task because CI integration and other Phase 0 requirements are still outstanding.


The first safety-remediation implementation is documented in [`2026-10-14/TGF_CORE_REMEDIATION.md`](2026-10-14/TGF_CORE_REMEDIATION.md). The subsequent tagged-memory diagnostics and their current verification are documented in [`2026-10-14/TGF_MEMORY_DIAGNOSTICS.md`](2026-10-14/TGF_MEMORY_DIAGNOSTICS.md). The original audit report and CSV remain the immutable baseline for the supplied archive.

The Revision 13 hosted-CI preparation and local verification are documented in
[`2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md`](2026-10-15/TGF_CI_REMOTE_EXECUTION_PREP.md).
This report records the Windows MSVC/Ninja cache correction and distinguishes local checks
from the still-pending GitHub-hosted Actions execution.
