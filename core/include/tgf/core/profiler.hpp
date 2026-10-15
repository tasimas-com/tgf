// tgf/core/profiler.hpp — scoped CPU zones (P1.6.2). Per-thread ring buffer,
// no locks, no allocation. Zone names must be string literals (pointer stored).
// Build with TGF_PROFILE=ON to enable TGF_ZONE; otherwise it compiles to nothing.
#pragma once

#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

namespace tgf::core {

TGF_API u64 now_ns() noexcept;  // monotonic, nanoseconds

struct ZoneEvent {
  const char* name;
  u64 begin_ns;
  u64 end_ns;
  u32 depth;
  u32 reserved;
};

class TGF_API ScopedZone {
 public:
  explicit ScopedZone(const char* name) noexcept;
  ~ScopedZone() noexcept;
  ScopedZone(const ScopedZone&) = delete;
  ScopedZone& operator=(const ScopedZone&) = delete;

 private:
  const char* name_;
  u64 begin_;
  u32 depth_;
};

// Copies up to max most recent zones of the *calling thread* (oldest first).
TGF_API usize profiler_thread_zones(ZoneEvent* out, usize max) noexcept;
TGF_API void profiler_thread_reset() noexcept;

}  // namespace tgf::core

#if TGF_PROFILE_ENABLED
#define TGF_ZONE(name) ::tgf::core::ScopedZone TGF_CONCAT(tgf_zone_, __LINE__)(name)
#else
#define TGF_ZONE(name) static_cast<void>(0)
#endif
