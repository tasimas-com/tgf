# ---- header self-containment (P0.1.9 / P1.1.5) ---------------------------------
# Each public header is compiled alone in a TU built WITH exceptions and RTTI on,
# proving headers are self-contained and usable from user code (ADR-0001).
file(GLOB _tgf_core_headers RELATIVE ${PROJECT_SOURCE_DIR}/core/include ${PROJECT_SOURCE_DIR}/core/include/tgf/core/*.hpp)
set(_hdr_srcs "")
foreach(h IN LISTS _tgf_core_headers)
  string(REPLACE "/" "_" _stem "${h}")
  set(_f "${CMAKE_CURRENT_BINARY_DIR}/hdr_${_stem}.cpp")
  file(WRITE "${_f}" "#include <${h}>\n#include <${h}>  // include guard check\n")
  list(APPEND _hdr_srcs "${_f}")
endforeach()
add_library(tgf_header_check OBJECT ${_hdr_srcs})
target_link_libraries(tgf_header_check PRIVATE TGF::Core)
# Deliberately NOT tgf_apply_policy(CORE): exceptions + RTTI stay on here.
tgf_apply_policy(tgf_header_check)

# ---- CTest entries -------------------------------------------------------------
if(TGF_BUILD_SHOWCASE)
  add_test(NAME showcase_checks COMMAND tgf_showcase --checks-only)
endif()

find_package(Python3 COMPONENTS Interpreter)
if(Python3_FOUND)
  add_test(NAME dependency_dag COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/tools/check_deps.py ${PROJECT_SOURCE_DIR})
  add_test(NAME dependency_dag_bindings_rule
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
endif()
