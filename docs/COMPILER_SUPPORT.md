# TGF compiler and source-quality policy

**Policy reviewed: 2026-10-17**

TGF uses C++20 (`CMAKE_CXX_STANDARD=20`) with language extensions disabled. The
following are the two current stable/in-support compiler generations targeted
for first-class support. A generation is not considered verified merely because
it appears in this table: its CI job must build the library, showcase, and tests
with warnings treated as errors.

| Compiler family | Current target | Previous target | Required CI status |
|---|---:|---:|---|
| Microsoft MSVC Build Tools | 14.51 (`_MSC_VER=1951`) | 14.50 (`_MSC_VER=1950`) | Windows x64 build and CTest |
| LLVM Clang | 23.x | 22.x | Linux build and CTest; macOS Clang coverage separately |
| GNU GCC | 16.x | 15.x | Linux build and CTest |

MSVC 14.52 is preview as of this policy date and is not a release-gate toolset.
The compiler version policy must be reviewed when vendors publish new stable
releases or change support lifetimes.

## Hosted Tier-1 verification (2026-10-17)

The latest complete matrix passed in GitHub Actions [run #193](https://github.com/tasimas-com/tgf/actions/runs/39056856383)
on commit `f9674c393c8ff09ed46625b4b4334350b413b6c2`: **14/14 jobs** across Debug and Release. An earlier baseline is retained in the project history.

| Compiler | Exact version reported | Toolset | Debug | Release |
|---|---|---|---:|---:|
| MSVC | 19.51.36260.0 | 14.51.36231 | Pass | Pass |
| MSVC | 19.50.35739.0 | 14.50.35717 | Pass | Pass |
| LLVM Clang | 23.1.4 | — | Pass | Pass |
| LLVM Clang | 22.1.2 | — | Pass | Pass |
| GNU GCC | 16.0.1 | — | Pass | Pass |
| GNU GCC | 15.2.0 | — | Pass | Pass |

The native macOS compatibility lane also passed Debug and Release with AppleClang
17.0.0. Every matrix build used `TGF_WARNINGS_AS_ERRORS=ON`. The workflow verifies
the GCC/Clang major version before CMake configuration; on Windows it checks both
the `cl /Bv` compiler version and the actual `VCToolsVersion`, then configures the
matching MSVC/Ninja preset.

All 14 CTest artifacts from run #193 were downloaded and inspected. Every ZIP is valid, every
`LastTest.log` contains **11/11 passing CTest entries**, and every showcase reports
26 checks with zero failures (**154/154 CTest test executions passed**).

## Local developer environment

The available local Linux environment has GCC 14.2 and Clang 17. Those are useful
additional backward-compatibility checks, but they are older than the supported
Tier-1 targets. No native MSVC environment is available locally; the MSVC evidence
above comes from the native Windows GitHub-hosted runner, not from a local
cross-compiler.

## Hosted source-quality verification (2026-10-17)

GitHub Actions [run #119](https://github.com/tasimas-com/tgf/actions/runs/39056856378)
passed both source-quality jobs on commit `f9674c393c8ff09ed46625b4b4334350b413b6c2`.

| Tool | LLVM 22 lane | LLVM 23 lane |
|---|---|---|
| clang-format | 22.1.8 — pass | 23.1.4 — pass |
| clang-tidy | 22.1.8 — full TGF build passed | 23.1.4 — full TGF build passed |
| Include-What-You-Use | 0.26 — strict full build passed | 0.27 — strict full build passed |

The formatter checked all 29 repository-owned C/C++ source files. Both static
analysis builds used `TGF_WARNINGS_AS_ERRORS=ON`. The IWYU lane uses
`-Xiwyu;--error`, verifies the exact IWYU release, and checks implementation and
showcase translation units. Only the generated public-header self-containment
harness is excluded: it intentionally includes each header twice without using
symbols, so IWYU would otherwise ask to delete the includes being tested. The
normal compiler/CTest matrix still compiles that harness in every configuration.


## Warnings are errors

`TGF_WARNINGS_AS_ERRORS` defaults to `ON`.

- MSVC: `/W4` and `/WX`; C4324 is narrowly disabled because cache-line padding
  from intentional `alignas` is expected in the concurrency primitives.
- GCC/Clang: `-Wall -Wextra -Wpedantic -Wshadow -Wconversion
  -Wsign-conversion -Wnon-virtual-dtor -Wold-style-cast -Wcast-align
  -Wformat=2` and `-Werror`.
- Core implementation targets also disable exceptions and RTTI according to
  ADR-0001. Public-header compatibility checks deliberately retain them.

Developers may turn warnings-as-errors off temporarily for local investigation,
but CI and release validation must leave it enabled. Suppressions must be narrow,
commented, and compiler-specific where possible.

## Formatting

`.clang-format` is the single source of formatting rules. The supported formatter
major versions are 22 and 23. When `clang-format` is installed, CMake provides:

```sh
cmake --build build/release --target format-check
cmake --build build/release --target format-fix
```

The equivalent direct check is:

```sh
python tools/check_format.py --clang-format clang-format
```

Do not reformat generated files, build output, or third-party code.

## Static analysis

`.clang-tidy` enables focused `bugprone`, `clang-analyzer`, `performance`, and
`portability` checks. Enable it at configure time:

```sh
cmake -S . -B build/tidy -G Ninja \
  -DTGF_ENABLE_CLANG_TIDY=ON -DTGF_WARNINGS_AS_ERRORS=ON
cmake --build build/tidy
```

Include-What-You-Use can be enabled independently:

```sh
cmake -S . -B build/iwyu -G Ninja \
  -DTGF_ENABLE_IWYU=ON -DTGF_WARNINGS_AS_ERRORS=ON
cmake --build build/iwyu
```

Use IWYU 0.27 with LLVM/Clang 23 or IWYU 0.26 with LLVM/Clang 22. The tools are
opt-in for ordinary local builds, but must be run in the quality-analysis jobs
when those jobs are available. Tool absence is never reported as a successful
analysis run.

## Official version references

- [Microsoft MSVC compiler versions](https://learn.microsoft.com/en-us/cpp/overview/compiler-versions)
- [What's new for MSVC Build Tools](https://learn.microsoft.com/en-us/cpp/overview/what-s-new-for-msvc)
- [GCC release timeline](https://gcc.gnu.org/releases.html)
- [LLVM releases](https://releases.llvm.org/)
- [Clang release notes](https://releases.llvm.org/23.1.0/tools/clang/docs/ReleaseNotes.html)
- [clang-format documentation](https://clang.llvm.org/docs/ClangFormat.html)
- [Include-What-You-Use releases and compatibility](https://include-what-you-use.org/)
