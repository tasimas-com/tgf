#include <tgf/core/build_info.hpp>

#include <tgf/core/config.hpp>

// These describe how *the library* was compiled; CMake supplies the TGF_LIB_* values.
#ifndef TGF_LIB_CONFIG
#define TGF_LIB_CONFIG "unknown"
#endif
#ifndef TGF_LIB_LTO
#define TGF_LIB_LTO 0
#endif

#if defined(TGF_SHARED)
#define TGF_LINKAGE_NAME "shared"
#else
#define TGF_LINKAGE_NAME "static"
#endif

#if defined(__clang__)
#define TGF_COMPILER_NAME "clang " __clang_version__
#elif defined(_MSC_VER)
#define TGF_COMPILER_NAME "msvc"
#elif defined(__GNUC__)
#define TGF_COMPILER_NAME "gcc " __VERSION__
#else
#define TGF_COMPILER_NAME "unknown"
#endif

#if defined(__cpp_exceptions) || defined(_CPPUNWIND)
#define TGF_LIB_EXCEPTIONS true
#else
#define TGF_LIB_EXCEPTIONS false
#endif

#if defined(__cpp_rtti) || defined(__GXX_RTTI) || defined(_CPPRTTI)
#define TGF_LIB_RTTI true
#else
#define TGF_LIB_RTTI false
#endif

namespace tgf::core {

const BuildInfo& build_info() noexcept {
  static constexpr BuildInfo info{TGF_VERSION_STRING,      TGF_COMPILER_NAME,        TGF_LIB_CONFIG,
                                  TGF_LINKAGE_NAME,        TGF_LIB_EXCEPTIONS,       TGF_LIB_RTTI,
                                  TGF_ASSERT_ENABLED != 0, TGF_PROFILE_ENABLED != 0, TGF_LIB_LTO != 0};
  return info;
}

}  // namespace tgf::core
