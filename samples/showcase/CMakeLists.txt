add_executable(tgf_showcase
  main.cpp
  alloc_hook.cpp
  checks_core.cpp
  bench_core.cpp)
target_link_libraries(tgf_showcase PRIVATE TGF::Core)
find_package(Threads REQUIRED)
target_link_libraries(tgf_showcase PRIVATE Threads::Threads)
# The showcase is an ordinary *user* of TGF: exceptions and RTTI stay ON (proves ADR-0001).
tgf_apply_policy(tgf_showcase)

# GCC 13 emits a known false positive (-Wstringop-overflow) for std::string concatenation under LTO.
# It only affects this test executable, never the library.
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  target_compile_options(tgf_showcase PRIVATE -Wno-stringop-overflow)
  target_link_options(tgf_showcase PRIVATE -Wno-stringop-overflow)  # LTO re-runs the warning at link time
endif()

# MemorySanitizer supplies its own global new/delete interceptors. The showcase's
# process-wide TGF hook is disabled in this configuration; explicit TGF allocator
# and tracked-external-allocator tests remain active.
if(TGF_SANITIZER STREQUAL "Memory")
  target_compile_definitions(tgf_showcase PRIVATE TGF_SHOWCASE_MEMORY_SANITIZER=1)
endif()
