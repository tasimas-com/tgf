# Third-party components and SBOM

TGF is licensed under [Apache-2.0](../LICENSE), with the project notice in [NOTICE](../NOTICE).
The intake rules, approved future candidates, and reviewed direct-dependency inventory are in
[third_party/POLICY.md](../third_party/POLICY.md) and
[third_party/dependencies.json](../third_party/dependencies.json).

## Generate the SBOM

Requires Python 3.10 or newer; the tools use only the standard library:

```sh
python tools/check_third_party.py .
python tools/generate_sbom.py --root . --output build/sbom/tgf.spdx.json
```

The output is SPDX 2.3 JSON. Its document namespace derives from the TGF version and
registry content. Set `SOURCE_DATE_EPOCH` to a fixed Unix timestamp for reproducible
creation metadata.

The **TGF SBOM** GitHub Actions workflow generates and uploads
`tgf-spdx-sbom-<commit-sha>` for pushes, pull requests, and manual dispatches.

## Scope and known exclusions

The SBOM contains the framework and every direct component registered in the JSON
inventory. Current external entries are CI-only GitHub Actions, sccache, and pinned IWYU 0.26/0.27 source-quality tools; no direct
third-party C++ runtime package or vendored source is used.

It is not a recursive inventory of JavaScript packages bundled inside upstream Actions,
hosted runner images, operating-system packages, compiler distributions, CMake, or
Python itself. Those host/toolchain contents are not delivered as TGF dependencies and
are not claimed as audited by this document. The IWYU source releases bundle GoogleTest
under its own MIT license; TGF builds the IWYU executable only, not IWYU's test target.
The nested GoogleTest files are not treated as independently integrated TGF dependencies.


## Current verification (2026-11-17)

The policy and SBOM workflow [run #13](https://github.com/tasimas-com/tgf/actions/runs/44089512739)
passed on current `main` commit `7e9dad1581be59e1df6adf9caa7572a1129d518e` and uploaded the
SPDX 2.3 JSON artifact. The same commit's current compiler/OS CI matrix [run #412](https://github.com/tasimas-com/tgf/actions/runs/44089512975)
passed all 14 configured jobs. The registry describes TGF's direct repository dependencies and
vendored material; it is not a recursive inventory of transitive components inside GitHub Actions,
hosted runner images, operating-system packages, or compiler/Python installations. The accepted
decision record is [ADR-0016](adr/0016-third-party-dependencies-and-sbom.md).
