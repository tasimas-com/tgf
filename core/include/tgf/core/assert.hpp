// tgf/core/assert.hpp — contract system (P1.1.3).
//   TGF_ASSERT : debug-only (compiled out, expression unevaluated, in release)
//   TGF_CHECK  : always on; use for conditions that guard memory safety
// Both end in a non-returning handler that logs and aborts (no exceptions, ADR-0001).
#pragma once

#include <tgf/core/config.hpp>

namespace tgf::core::detail {

[[noreturn]] TGF_API void assert_fail(const char* expr, const char* msg, const char* file, int line) noexcept;

}  // namespace tgf::core::detail

#define TGF_CHECK(cond, msg) \
  (TGF_LIKELY(cond) ? static_cast<void>(0) : ::tgf::core::detail::assert_fail(#cond, (msg), __FILE__, __LINE__))

#if TGF_ASSERT_ENABLED
#define TGF_ASSERT(cond, msg) TGF_CHECK(cond, msg)
#else
#define TGF_ASSERT(cond, msg) static_cast<void>(sizeof(!(cond)))
#endif
