#include <tgf/core/assert.hpp>
#include <tgf/core/log.hpp>

#include <cstdio>
#include <cstdlib>

namespace tgf::core::detail {

void assert_fail(const char* expr, const char* msg, const char* file, int line) noexcept {
  log_write(LogLevel::Fatal, "assertion failed: %s - %s (%s:%d)", expr, msg, file, line);
  std::fflush(stderr);
  std::abort();
}

}  // namespace tgf::core::detail
