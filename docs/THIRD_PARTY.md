# Third-party components and SBOM

TGF is licensed under [Apache-2.0](../LICENSE), with the project notice in [NOTICE](../NOTICE).
The intake rules and reviewed direct-dependency inventory are in
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
inventory. Current external entries are CI-only GitHub Actions and sccache; no direct
third-party C++ runtime package or vendored source is used.

It is not a recursive inventory of JavaScript packages bundled inside upstream Actions,
hosted runner images, operating-system packages, compiler distributions, CMake, or
Python itself. Those host/toolchain contents are not delivered as TGF dependencies and
are not claimed as audited by this document.
