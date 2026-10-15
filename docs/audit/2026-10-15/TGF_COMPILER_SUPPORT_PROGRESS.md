# TGF compiler support and quality tooling — Revision 11

**Date:** 2026-10-15  
**Task:** P0.1.3  
**Overall status:** Partial; policy and tool wiring are implemented, full Tier-1 matrix and analyzer runs remain open.

## Implemented

- Defined the Tier-1 compiler target generations in `docs/COMPILER_SUPPORT.md` and the machine-readable `cmake/compiler-support.json`.
- Kept `TGF_WARNINGS_AS_ERRORS=ON` as the default and added a CTest policy regression test that checks the MSVC `/W4` + `/WX` path and GCC/Clang warning flags + `-Werror`.
- Added `.clang-tidy` with focused bugprone, static-analyzer, performance, and portability checks.
- Added optional `TGF_ENABLE_CLANG_TIDY` and `TGF_ENABLE_IWYU` CMake integrations. Enabling either without its executable fails during configure instead of silently skipping analysis.
- Added `tools/check_format.py` and conditional `format-check` / `format-fix` targets when clang-format is installed. The checker accepts the supported major versions 22 and 23.
- Enabled `CMAKE_EXPORT_COMPILE_COMMANDS` in the Ninja preset base for tidy and IWYU tooling.
- Registered `compiler_policy` in CTest.
- Updated `TODO.md`, `README.md`, `docs/BUILDING.md`, and `docs/STATUS.md`.

## Verification performed

| Toolchain/configuration | Result |
|---|---|
| GCC 14.2 Release, warnings-as-errors | Build passed; CTest 5/5 |
| GCC 14.2 Debug, warnings-as-errors | Build passed; CTest 5/5 |
| GCC 14.2 shared Release, warnings-as-errors | Build passed; CTest 5/5 |
| Clang 17 Release, warnings-as-errors | Build passed; CTest 5/5 |
| Preset graph and dependency regression tests | Passed |
| `.clang-format` and `.clang-tidy` YAML syntax | Passed with PyYAML 6.0.3 |
| Ninja `compile_commands.json` export | Verified |
| `TGF_ENABLE_CLANG_TIDY=ON` with no tool installed | Correctly fails configuration with explicit message |
| `TGF_ENABLE_IWYU=ON` with no tool installed | Correctly fails configuration with explicit message |
| `tools/check_format.py` Python syntax/help/error handling | Passed |

## Not verified / remaining

- MSVC 14.51 and 14.50: no Windows/MSVC host in this execution environment.
- Clang 23 and 22: only Clang 17 is installed here.
- GCC 16 and 15: only GCC 14.2 is installed here.
- clang-format 23/22: not installed, so no full source formatting pass was performed.
- clang-tidy 23/22: not installed, so no analyzer pass was performed.
- Include-What-You-Use 0.27/0.26: not installed, so no include analysis was performed.

The available GCC 14.2 and Clang 17 builds are additional backward-compatibility evidence. They are not substitutes for the Tier-1 matrix. P0.1.3 must remain `[p]` until the supported compiler generations and quality tools run in CI/native environments.
