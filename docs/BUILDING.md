# Building and testing TGF

TGF uses CMake 3.25+ and CMake Presets. Ninja is used for single-configuration presets;
`vs2022` uses Visual Studio 2022's multi-configuration generator on Windows.

## Standard configurations

Run from the repository root:

```sh
cmake --list-presets
cmake --preset debug
cmake --build --preset debug --parallel
ctest --preset debug

cmake --preset release
cmake --build --preset release --parallel
ctest --preset release

cmake --preset relwithdebinfo
cmake --build --preset relwithdebinfo --parallel
ctest --preset relwithdebinfo

cmake --preset profiling
cmake --build --preset profiling --parallel
ctest --preset profiling
```

The `profiling` preset uses `RelWithDebInfo` and enables `TGF_ZONE` instrumentation.
It is separate from `relwithdebinfo` so normal profiling builds do not silently change
instrumentation behavior.

## Sanitizer configurations

| Preset | Purpose | Availability |
|---|---|---|
| `asan` | AddressSanitizer | GCC/Clang on non-Windows; use `vs2022-asan` on Windows |
| `ubsan` | UndefinedBehaviorSanitizer | GCC/Clang on non-Windows |
| `tsan` | ThreadSanitizer | GCC/Clang on non-Windows; target/runtime support varies |
| `msan` | MemorySanitizer | Clang on Linux only; standard library and dependencies must also be instrumented |
| `asan-ubsan` | Legacy combined address + undefined sanitizer | GCC/Clang on non-Windows |

Example:

```sh
cmake --preset asan
cmake --build --preset asan --parallel
ctest --preset asan
```

MemorySanitizer requires care because an uninstrumented system C++ library can produce
false positives. The `msan` preset selects Clang on Linux. In this configuration the showcase
does not replace global `new`/`delete` (MSan supplies its own interceptors). The global-new
accounting assertion and the separate warm-up test that depends on the process-wide hook are
therefore excluded. Direct TGF allocator, mapping, container, and concurrency checks remain
enabled. For stronger coverage,
use a fully instrumented C++ runtime and dependencies; a passing MSan run with uninstrumented
system libraries is useful but not equivalent to an all-instrumented system.

On Windows with Visual Studio 2022:

```powershell
cmake --preset vs2022
cmake --build --preset vs2022-release --parallel
ctest --preset vs2022-release

cmake --preset vs2022-asan
cmake --build --preset vs2022-asan --parallel
ctest --preset vs2022-asan
```

MSVC's preset enables AddressSanitizer only. UBSan, TSan and MSan are not claimed as
supported by this MSVC configuration.

## Sanitizer selection for custom builds

The presets set `TGF_SANITIZER` to one of:

- `None`
- `Address`
- `Undefined`
- `Thread`
- `Memory`
- `AddressUndefined`

Do not combine sanitizer presets in one build directory. Each preset has its own binary
folder to prevent stale compiler/linker flags from contaminating another configuration.

## Clean builds

To remove one preset's generated files, delete its matching directory under `build/`
(e.g. `build/asan`). Do not delete source files. Reconfigure after changing compiler or
sanitizer selection; CMake does not support changing the compiler in an existing build tree.

## Compiler and code-quality policy

See [`COMPILER_SUPPORT.md`](COMPILER_SUPPORT.md) for the supported compiler generations,
warnings-as-errors rules, and clang-format/clang-tidy/IWYU integration. Those tools are optional
for local builds but are enforced by the hosted source-quality workflow on every push and pull request. Ninja presets
export `compile_commands.json` for clang-tidy and Include-What-You-Use.

When clang-format 22 or 23 is installed, configure the project and run:

```sh
cmake --build build/release --target format-check
```

To run clang-tidy or Include-What-You-Use during compilation, configure a separate build
directory with `-DTGF_ENABLE_CLANG_TIDY=ON` or `-DTGF_ENABLE_IWYU=ON`. These switches are
opt-in and fail configuration clearly if the selected executable is missing.

## Continuous integration

The hosted Windows/Linux/macOS build-and-test matrix, compiler cache, test-log artifacts,
and guarded dedicated-runner benchmark workflow are documented in [`CI.md`](CI.md).
The workflows live in `.github/workflows/`. Local CTest also validates their required
contract and the pinned-frequency host check.
