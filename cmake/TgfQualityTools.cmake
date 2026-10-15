# Optional source-quality tools. They are deliberately opt-in so a normal build
# does not require developers to install LLVM tooling or Include-What-You-Use.

option(TGF_ENABLE_CLANG_TIDY "Run clang-tidy during C++ compilation" OFF)
option(TGF_ENABLE_IWYU "Run Include-What-You-Use during C++ compilation" OFF)

if(TGF_ENABLE_CLANG_TIDY)
  find_program(TGF_CLANG_TIDY_EXECUTABLE NAMES clang-tidy-23 clang-tidy-22 clang-tidy)
  if(NOT TGF_CLANG_TIDY_EXECUTABLE)
    message(FATAL_ERROR
      "TGF_ENABLE_CLANG_TIDY=ON but clang-tidy was not found. Install clang-tidy 22 or 23.")
  endif()
  set(_tgf_clang_tidy_command "${TGF_CLANG_TIDY_EXECUTABLE}")
  if(TGF_WARNINGS_AS_ERRORS)
    list(APPEND _tgf_clang_tidy_command "--warnings-as-errors=*")
  endif()
  set(CMAKE_CXX_CLANG_TIDY "${_tgf_clang_tidy_command}" CACHE STRING
      "clang-tidy command applied to TGF C++ targets" FORCE)
  message(STATUS "TGF: clang-tidy enabled: ${TGF_CLANG_TIDY_EXECUTABLE}")
endif()

if(TGF_ENABLE_IWYU)
  if(MSVC)
    message(FATAL_ERROR "TGF_ENABLE_IWYU currently requires a Clang-compatible compilation database; use Clang or GCC.")
  endif()
  find_program(TGF_IWYU_EXECUTABLE NAMES include-what-you-use iwyu)
  if(NOT TGF_IWYU_EXECUTABLE)
    message(FATAL_ERROR
      "TGF_ENABLE_IWYU=ON but include-what-you-use was not found. Install the IWYU release matching LLVM 22/23.")
  endif()
  set(CMAKE_CXX_INCLUDE_WHAT_YOU_USE "${TGF_IWYU_EXECUTABLE};-Xiwyu;--error"
      CACHE STRING "Include-What-You-Use command applied to TGF C++ targets" FORCE)
  message(STATUS "TGF: Include-What-You-Use enabled: ${TGF_IWYU_EXECUTABLE}")
endif()

# A format-check target is available when clang-format is installed. Formatting
# is never silently skipped by the explicit `format-check` command.
find_program(TGF_CLANG_FORMAT_EXECUTABLE
  NAMES clang-format-23 clang-format-22 clang-format)
find_package(Python3 COMPONENTS Interpreter QUIET)
if(TGF_CLANG_FORMAT_EXECUTABLE AND Python3_Interpreter_FOUND)
  add_custom_target(format-check
    COMMAND "${Python3_EXECUTABLE}" "${PROJECT_SOURCE_DIR}/tools/check_format.py"
            --clang-format "${TGF_CLANG_FORMAT_EXECUTABLE}"
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    COMMENT "Checking C/C++ formatting with clang-format"
    VERBATIM)
  add_custom_target(format-fix
    COMMAND "${Python3_EXECUTABLE}" "${PROJECT_SOURCE_DIR}/tools/check_format.py"
            --clang-format "${TGF_CLANG_FORMAT_EXECUTABLE}" --fix
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    COMMENT "Formatting C/C++ sources with clang-format"
    VERBATIM)
else()
  message(STATUS "TGF: clang-format not found; format-check/format-fix targets are unavailable")
endif()
