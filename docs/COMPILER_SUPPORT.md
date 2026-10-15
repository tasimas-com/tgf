# TGF compiler and source-quality policy

**Policy reviewed: 2026-10-15**

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

## What is verified in the current development environment

The available Linux environment has GCC 14.2 and Clang 17. Both are older than
the two target generations listed above. They are useful additional backward-
compatibility checks, but they do not satisfy the current Tier-1 compiler matrix.
No native MSVC environment is available here. Consequently, this document
records the intended policy, not a claim that the complete matrix has passed.

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
