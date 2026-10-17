// tgf/core/build_info.hpp — lets an application (and the showcase) ask the
// *compiled library* how it was built, independent of the application's own flags.
#pragma once

#include <tgf/core/config.hpp>

namespace tgf::core {

struct BuildInfo {
  const char* version;
  const char* compiler;
  const char* configuration;  // "debug" / "release"
  const char* linkage;        // "static" / "shared"
  bool exceptions_enabled;    // inside the library (ADR-0001: must be false)
  bool rtti_enabled;          // inside the library (ADR-0001: must be false)
  bool asserts_enabled;
  bool profiler_enabled;
  bool lto;
};

TGF_API const BuildInfo& build_info() noexcept;

}  // namespace tgf::core
