if(TGF_BUILD_SHARED)
  set(_tgf_core_type SHARED)
else()
  set(_tgf_core_type STATIC)
endif()
add_library(tgf_core ${_tgf_core_type}
  src/assert.cpp
  src/build_info.cpp
  src/log.cpp
  src/math.cpp
  src/memory.cpp
  src/mapped_file.cpp
  src/module_allocator.cpp
  src/profiler.cpp
  src/result.cpp)
add_library(TGF::Core ALIAS tgf_core)
set_target_properties(tgf_core PROPERTIES EXPORT_NAME Core)  # installed as TGF::Core

target_include_directories(tgf_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(tgf_core PUBLIC cxx_std_20)
target_compile_definitions(tgf_core
  PRIVATE TGF_BUILDING TGF_LIB_LTO=$<AND:$<BOOL:${TGF_LTO_AVAILABLE}>,$<NOT:$<CONFIG:Debug>>>
          # Generator expression, so Visual Studio (multi-config) reports the configuration
          # actually being built instead of the empty CMAKE_BUILD_TYPE seen at configure time.
          TGF_LIB_CONFIG="$<IF:$<CONFIG:Debug>,debug,release>")
if(TGF_BUILD_SHARED)
  target_compile_definitions(tgf_core PUBLIC TGF_SHARED)
endif()
# Profiler zones: on in Debug, or anywhere with -DTGF_PROFILE=ON.
target_compile_definitions(tgf_core PUBLIC
  $<$<OR:$<BOOL:${TGF_PROFILE}>,$<CONFIG:Debug>>:TGF_PROFILE_ENABLED=1>)
tgf_apply_policy(tgf_core CORE)
