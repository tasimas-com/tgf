#include <chrono>
#include <tgf/core/profiler.hpp>

namespace tgf::core {

namespace {
constexpr u32 kRing = 2048;  // power of two

struct ThreadState {  // zero-initialised: no dynamic TLS init cost
  ZoneEvent ring[kRing];
  u64 count;
  u32 depth;
};
thread_local ThreadState t_state;
}  // namespace

u64 now_ns() noexcept {
  return static_cast<u64>(
      std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch())
          .count());
}

ScopedZone::ScopedZone(const char* name) noexcept : name_(name), begin_(now_ns()), depth_(t_state.depth++) {}

ScopedZone::~ScopedZone() noexcept {
  const u64 end = now_ns();
  --t_state.depth;
  t_state.ring[t_state.count & (kRing - 1)] = ZoneEvent{name_, begin_, end, depth_, 0};
  ++t_state.count;
}

usize profiler_thread_zones(ZoneEvent* out, usize max) noexcept {
  const u64 total = t_state.count;
  const usize avail = total < kRing ? static_cast<usize>(total) : static_cast<usize>(kRing);
  const usize n = avail < max ? avail : max;
  const u64 first = total - n;
  for (usize i = 0; i < n; ++i) out[i] = t_state.ring[(first + i) & (kRing - 1)];
  return n;
}

void profiler_thread_reset() noexcept {
  t_state.count = 0;
  t_state.depth = 0;
}

}  // namespace tgf::core
