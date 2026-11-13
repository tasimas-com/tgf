# ---- public-header self-containment (P0.1.9 / P1.1.5) -------------------------
# Compile every first-party public header in isolation, twice in one TU, with
# exceptions and RTTI enabled. This catches missing direct includes and broken
# include guards without imposing the library's private no-exceptions/no-RTTI mode.
file(GLOB _tgf_module_dirs LIST_DIRECTORIES TRUE "${PROJECT_SOURCE_DIR}/*")
set(_tgf_public_headers "")
set(_tgf_public_include_roots "")
foreach(_module_dir IN LISTS _tgf_module_dirs)
  if(NOT IS_DIRECTORY "${_module_dir}/include/tgf")
    continue()
  endif()
  file(GLOB_RECURSE _module_headers CONFIGURE_DEPENDS LIST_DIRECTORIES FALSE
    "${_module_dir}/include/tgf/*.h"
    "${_module_dir}/include/tgf/*.hh"
    "${_module_dir}/include/tgf/*.hpp"
    "${_module_dir}/include/tgf/*.hxx")
  list(APPEND _tgf_public_headers ${_module_headers})
  list(APPEND _tgf_public_include_roots "${_module_dir}/include")
endforeach()
list(REMOVE_DUPLICATES _tgf_public_headers)
list(REMOVE_DUPLICATES _tgf_public_include_roots)
list(SORT _tgf_public_headers)
if(NOT _tgf_public_headers)
  message(FATAL_ERROR "No first-party public headers found under */include/tgf/")
endif()

set(_tgf_hdr_srcs "")
set(_tgf_header_manifest "${CMAKE_CURRENT_BINARY_DIR}/header-check-manifest.tsv")
file(WRITE "${_tgf_header_manifest}" "")
foreach(_header IN LISTS _tgf_public_headers)
  string(REGEX REPLACE "^(.*)/include/tgf/.*$" "\\1" _module_root "${_header}")
  get_filename_component(_module_name "${_module_root}" NAME)
  file(RELATIVE_PATH _include_name "${_module_root}/include" "${_header}")
  string(REPLACE "/" "__" _stem "${_include_name}")
  set(_generated_name "hdr_${_module_name}__${_stem}.cpp")
  set(_generated_source "${CMAKE_CURRENT_BINARY_DIR}/${_generated_name}")
  file(WRITE "${_generated_source}"
    "#include <${_include_name}>\n#include <${_include_name}>  // include guard check\n")
  file(APPEND "${_tgf_header_manifest}"
    "${_generated_name}\t${_include_name}\t${_header}\n")
  list(APPEND _tgf_hdr_srcs "${_generated_source}")
endforeach()

add_library(tgf_header_check OBJECT ${_tgf_hdr_srcs})
target_link_libraries(tgf_header_check PRIVATE TGF::Core)
target_include_directories(tgf_header_check PRIVATE ${_tgf_public_include_roots})
# This generated harness intentionally includes each public header twice and
# uses no symbols: IWYU would report the test includes as unused. Real source
# and showcase translation units remain checked by strict IWYU.
if(TGF_ENABLE_IWYU)
  set_property(TARGET tgf_header_check PROPERTY CXX_INCLUDE_WHAT_YOU_USE "")
endif()
# Deliberately NOT tgf_apply_policy(CORE): exceptions + RTTI stay enabled here.
tgf_apply_policy(tgf_header_check)

if(TGF_ENABLE_HEADER_TIME_TRACE)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang|AppleClang")
    message(FATAL_ERROR "TGF_ENABLE_HEADER_TIME_TRACE requires Clang or AppleClang (-ftime-trace).")
  endif()
  target_compile_options(tgf_header_check PRIVATE -ftime-trace -ftime-trace-granularity=0 -ftime-trace-verbose)
endif()

# ---- CTest entries -------------------------------------------------------------
if(TGF_BUILD_SHOWCASE)
  add_test(NAME showcase_checks COMMAND tgf_showcase --checks-only)
endif()

# Dependency policy is a required test gate, not an optional best-effort check.
# Failing configuration when Python is unavailable prevents CI from silently
# dropping the DAG checks on one of the supported operating systems.
find_package(Python3 3.10 COMPONENTS Interpreter REQUIRED)

add_test(NAME dependency_dag
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_deps.py ${PROJECT_SOURCE_DIR})
add_test(NAME dependency_dag_policy_regressions
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_check_deps.py ${PROJECT_SOURCE_DIR}/tools/check_deps.py)
add_test(NAME cmake_preset_matrix
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_presets.py ${PROJECT_SOURCE_DIR}/CMakePresets.json)
add_test(NAME ci_workflow_contract
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_ci_workflows.py ${PROJECT_SOURCE_DIR})
add_test(NAME benchmark_host_policy
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_check_benchmark_host.py)
add_test(NAME benchmark_host_inventory
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_collect_benchmark_host_inventory.py)
add_test(NAME compiler_policy
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_compiler_policy.py ${PROJECT_SOURCE_DIR})
add_test(NAME coding_standard_policy
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_coding_standard.py ${PROJECT_SOURCE_DIR})
add_test(NAME source_quality_workflow
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_source_quality_workflow.py ${PROJECT_SOURCE_DIR})
add_test(NAME format_checker_discovery
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_check_format.py)
add_test(NAME community_governance_policy
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_community_files.py ${PROJECT_SOURCE_DIR})
add_test(NAME build_measurement_tool
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_measure_build.py)
add_test(NAME header_cost_reporter
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/test_report_header_costs.py)
add_test(NAME build_performance_policy
         COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_build_performance.py ${PROJECT_SOURCE_DIR})
