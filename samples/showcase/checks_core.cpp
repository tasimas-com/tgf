// Verification of tgf::core (Phase 1 slice). Each check states the rule it proves.
#include "harness.hpp"

#include <tgf/core/build_info.hpp>
#include <tgf/core/hash.hpp>
#include <tgf/core/log.hpp>
#include <tgf/core/math.hpp>
#include <tgf/core/memory.hpp>
#include <tgf/core/module_allocator.hpp>
#include <tgf/core/mapped_file.hpp>
#include <tgf/core/profiler.hpp>
#include <tgf/core/result.hpp>
#include <tgf/core/slot_map.hpp>
#include <tgf/core/spsc.hpp>
#include <tgf/core/time.hpp>
#include <tgf/core/types.hpp>

#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>
#include <stdexcept>
#include <limits>
#if defined(TGF_SHOWCASE_MEMORY_SANITIZER) && !defined(_WIN32)
#include <fcntl.h>
#include <unistd.h>
#endif

using namespace tgf;
using namespace tgf::core;

namespace showcase {
volatile u64 g_sink = 0;

namespace {

struct Widget {
  u32 id;
  f32 x;
  f32 y;
};
using WidgetHandle = Handle<Widget>;

// ---- build / ABI ---------------------------------------------------------------
bool check_build_policy(Context& c) {
  const BuildInfo& bi = build_info();
  SC_REQUIRE(c, !bi.exceptions_enabled, "library must be compiled without exceptions (ADR-0001)");
  SC_REQUIRE(c, !bi.rtti_enabled, "library must be compiled without RTTI (ADR-0001)");
  // This TU is an ordinary user TU: exceptions on, proving public headers work with them.
  bool caught = false;
  try {
    throw 42;
  } catch (int) {
    caught = true;
  }
  SC_REQUIRE(c, caught, "user code keeps exceptions");
  c.note = std::string(bi.linkage) + " / " + bi.configuration + (bi.lto ? " / LTO" : "") + " / lib exceptions=off rtti=off";
  return true;
}

bool check_layout(Context& c) {
  static_assert(sizeof(WidgetHandle) == 8);
  static_assert(sizeof(Dip) == 4 && sizeof(Seconds) == 8);
  static_assert(sizeof(SampleTime) == 8);
  SC_REQUIRE(c, !WidgetHandle{}.valid(), "default handle is invalid");
  SC_REQUIRE(c, (WidgetHandle{1, 1}.valid()), "generation>0 is valid");
  c.note = "Handle=8B Dip=4B Seconds=8B SampleTime=8B";
  return true;
}

bool check_result(Context& c) {
  Result<u32> good(7u);
  Result<u32> bad(Error::NotFound);
  SC_REQUIRE(c, good.ok() && good.value() == 7, "value round-trips");
  SC_REQUIRE(c, !bad.ok() && bad.error() == Error::NotFound, "error round-trips");
  SC_REQUIRE(c, bad.value_or(9u) == 9u, "value_or");
  Status s;
  SC_REQUIRE(c, s.ok() && !Status(Error::Overflow).ok(), "Status");
  c.note = std::string("error_name(Overflow)=") + error_name(Error::Overflow);
  return true;
}

// ---- allocation rules -----------------------------------------------------------
bool check_aligned_allocation(Context& c) {
  SC_REQUIRE(c, aligned_alloc_bytes(32, 0) == nullptr, "zero alignment rejected");
  SC_REQUIRE(c, aligned_alloc_bytes(32, 3) == nullptr, "non-power-of-two alignment rejected");
  SC_REQUIRE(c, aligned_alloc_bytes(std::numeric_limits<usize>::max(), 64) == nullptr,
             "size-rounding overflow rejected");
  void* p = aligned_alloc_bytes(37, 64);
  SC_REQUIRE(c, p != nullptr, "valid aligned allocation succeeds");
  SC_REQUIRE(c, reinterpret_cast<std::uintptr_t>(p) % 64 == 0, "requested alignment honoured");
  aligned_free_bytes(p);
  c.note = "invalid alignment and overflow rejected; valid 64-byte-aligned allocation succeeds";
  return true;
}

bool check_memory_tags_budgets_and_leaks(Context& c) {
  SC_REQUIRE(c, current_memory_tag() == MemoryTag::Unspecified, "default memory tag is Unspecified");
  {
    ScopedMemoryTag core_tag(MemoryTag::Core);
    SC_REQUIRE(c, current_memory_tag() == MemoryTag::Core, "scoped tag becomes current");
    {
      ScopedMemoryTag ui_tag(MemoryTag::UI);
      SC_REQUIRE(c, current_memory_tag() == MemoryTag::UI, "nested tag overrides parent");
    }
    SC_REQUIRE(c, current_memory_tag() == MemoryTag::Core, "nested tag restores parent");
  }
  SC_REQUIRE(c, current_memory_tag() == MemoryTag::Unspecified, "scope restores original tag");
  SC_REQUIRE(c, std::string(memory_tag_name(MemoryTag::Renderer)) == "Renderer", "tag names are stable");

#if !defined(TGF_SHOWCASE_MEMORY_SANITIZER)
  const MemorySnapshot global_new_baseline = memory_snapshot();
  {
    ScopedMemoryTag core_tag(MemoryTag::Core);
    int* via_global_new = new int(42);
    SC_REQUIRE(c, *via_global_new == 42, "showcase global operator new remains usable");
    delete via_global_new;
  }
  const MemoryLeakReport global_new_leaks = memory_leaks_since(global_new_baseline, MemoryTag::Core);
  SC_REQUIRE(c, global_new_leaks.live_allocations == 0 && global_new_leaks.live_bytes == 0,
             "showcase global new/delete are included in live tracking");
#else
  c.note = "MSan owns global new/delete interceptors; explicit TGF allocator paths remain tested";
#endif

  set_memory_budget(MemoryTag::Core, 128);
  const MemorySnapshot baseline = memory_snapshot();
  void* first = aligned_alloc_bytes(80, 64, MemoryTag::Core);
  void* second = aligned_alloc_bytes(40, 32, MemoryTag::Core);
  void* over_budget = aligned_alloc_bytes(16, 16, MemoryTag::Core);
  SC_REQUIRE(c, first && second, "allocations within budget succeed");
  SC_REQUIRE(c, over_budget == nullptr, "allocation that exceeds budget is rejected");
  SC_REQUIRE(c, reinterpret_cast<std::uintptr_t>(first) % 64 == 0, "tagged allocation preserves alignment");

  MemoryStats stats = memory_stats(MemoryTag::Core);
  SC_REQUIRE(c, stats.live_allocations == baseline.tags[static_cast<usize>(MemoryTag::Core)].live_allocations + 2,
             "live allocation count tracks successful tagged allocations exactly");
  SC_REQUIRE(c, stats.live_bytes == baseline.tags[static_cast<usize>(MemoryTag::Core)].live_bytes + 120,
             "live bytes track requested bytes exactly");
  SC_REQUIRE(c, stats.budget_bytes == 128 && stats.budget_exceeded >
                 baseline.tags[static_cast<usize>(MemoryTag::Core)].budget_exceeded,
             "budget and exceeded-allocation counter are reported");
  MemoryLeakReport leaks = memory_leaks_since(baseline, MemoryTag::Core);
  SC_REQUIRE(c, leaks.live_allocations == 2 && leaks.live_bytes == 120,
             "snapshot reports outstanding tracked allocations as leaks");

  aligned_free_bytes(first);
  leaks = memory_leaks_since(baseline, MemoryTag::Core);
  SC_REQUIRE(c, leaks.live_allocations == 1 && leaks.live_bytes == 40,
             "free updates live counters and leak delta");
  aligned_free_bytes(second);
  leaks = memory_leaks_since(baseline, MemoryTag::Core);
  SC_REQUIRE(c, leaks.live_allocations == 0 && leaks.live_bytes == 0,
             "freeing all allocations clears the snapshot leak delta");
  stats = memory_stats(MemoryTag::Core);
  SC_REQUIRE(c, stats.live_bytes == baseline.tags[static_cast<usize>(MemoryTag::Core)].live_bytes,
             "live bytes return to their baseline");
  set_memory_budget(MemoryTag::Core, 0);

  // Concurrent reservations against one tag must never exceed its byte budget.
  set_memory_budget(MemoryTag::UI, 64);
  void* concurrent_blocks[8]{};
  std::thread allocators[8];
  std::atomic<u32> concurrent_successes{0};
  for (u32 i = 0; i < 8; ++i) {
    allocators[i] = std::thread([&, i] {
      concurrent_blocks[i] = aligned_alloc_bytes(64, 16, MemoryTag::UI);
      if (concurrent_blocks[i]) concurrent_successes.fetch_add(1, std::memory_order_relaxed);
    });
  }
  for (std::thread& worker : allocators) worker.join();
  const u32 successful_reservations = concurrent_successes.load(std::memory_order_relaxed);
  for (void* block : concurrent_blocks) aligned_free_bytes(block);
  const MemoryStats ui_stats = memory_stats(MemoryTag::UI);
  set_memory_budget(MemoryTag::UI, 0);
  SC_REQUIRE(c, successful_reservations == 1, "concurrent allocations cannot collectively exceed a 64-byte budget");
  SC_REQUIRE(c, ui_stats.live_bytes == 0 && ui_stats.live_allocations == 0,
             "concurrent tagged allocations all return to zero live usage");
  SC_REQUIRE(c, ui_stats.budget_exceeded >= 7, "concurrent budget rejections are counted");

  c.note = "nested tags; budgets enforced under contention; live/peak accounting and snapshot leak deltas verified";
  return true;
}

bool check_slotmap_semantics(Context& c) {
  SlotMap<Widget> m;
  std::vector<WidgetHandle> hs;
  for (u32 i = 0; i < 1000; ++i) {
    auto r = m.insert(Widget{i, static_cast<f32>(i), 0});
    SC_REQUIRE(c, r.ok(), "insert");
    hs.push_back(r.value());
  }
  SC_REQUIRE(c, m.size() == 1000, "size after inserts");
  for (u32 i = 0; i < 1000; i += 2) SC_REQUIRE(c, m.erase(hs[i]), "erase even");
  SC_REQUIRE(c, m.size() == 500, "size after erase");
  for (u32 i = 0; i < 1000; ++i) {
    const Widget* w = m.get(hs[i]);
    if (i % 2 == 0) {
      SC_REQUIRE(c, w == nullptr, "stale handle must resolve to null");
    } else {
      SC_REQUIRE(c, w && w->id == i, "survivor data intact after swap-remove");
    }
  }
  SC_REQUIRE(c, !m.erase(hs[0]), "double erase rejected");
  // Slot reuse must bump the generation, so the old handle stays dead.
  auto fresh = m.insert(Widget{9999, 0, 0});
  SC_REQUIRE(c, fresh.ok() && m.get(fresh.value()) && m.get(hs[0]) == nullptr, "reused slot, old handle still dead");
  SC_REQUIRE(c, !WidgetHandle{}.valid() && m.get(WidgetHandle{}) == nullptr, "invalid handle -> null");
  c.note = "1000 inserts, 500 erases, stale+double-erase rejected, generations bump on reuse";
  return true;
}

bool check_slotmap_zero_alloc(Context& c) {
  SlotMap<Widget> m(GrowPolicy::Fixed);
  SC_REQUIRE(c, m.reserve(4096), "reserve");
  std::vector<WidgetHandle> hs(2048);
  const u32 growth_before = m.growth_events();
  ScopedAllocationCheck guard;
  for (int round = 0; round < 200; ++round) {
    for (u32 i = 0; i < 2048; ++i) hs[i] = m.insert(Widget{i, 0, 0}).value();
    for (u32 i = 0; i < 2048; ++i) m.erase(hs[i]);
  }
  SC_REQUIRE(c, guard.allocations() == 0, "steady-state insert/erase must not allocate");
  SC_REQUIRE(c, m.growth_events() == growth_before, "no growth events in steady state");
  c.note = "819,200 insert+erase pairs, 0 heap allocations, 0 growth events";
  return true;
}

bool check_slotmap_growth(Context& c) {
  SlotMap<Widget> grow;
  for (u32 i = 0; i < 5000; ++i) SC_REQUIRE(c, grow.insert(Widget{i, 0, 0}).ok(), "auto-grow insert");
  SC_REQUIRE(c, grow.growth_events() > 0 && grow.size() == 5000, "growth is counted");
  // Handles survive a reallocation of the backing arrays.
  SlotMap<Widget> m;
  auto first = m.insert(Widget{1, 0, 0}).value();
  for (u32 i = 0; i < 100; ++i) (void)m.insert(Widget{i, 0, 0});
  SC_REQUIRE(c, m.get(first) && m.get(first)->id == 1, "handle valid across growth");
  SlotMap<Widget> fixed(GrowPolicy::Fixed);
  auto r = fixed.insert(Widget{});
  SC_REQUIRE(c, !r.ok() && r.error() == Error::CapacityExceeded, "Fixed policy refuses to grow");
  c.note = "growth events=" + std::to_string(grow.growth_events()) + "; Fixed policy -> CapacityExceeded";
  return true;
}

bool check_arena(Context& c) {
  LinearArena a;
  SC_REQUIRE(c, a.init(4096), "init");
  ScopedAllocationCheck guard;
  void* first = nullptr;
  for (int round = 0; round < 1000; ++round) {
    a.reset();
    for (usize al : {1u, 2u, 4u, 8u, 16u, 32u, 64u}) {
      void* p = a.allocate(24, al);
      SC_REQUIRE(c, p != nullptr, "allocate");
      SC_REQUIRE(c, reinterpret_cast<std::uintptr_t>(p) % al == 0, "alignment honoured");
      if (!first) first = p;
    }
  }
  SC_REQUIRE(c, guard.allocations() == 0, "arena hot path must not allocate");
  guard.assert_no_allocations();
  a.reset();
  SC_REQUIRE(c, a.allocate(24, 1) == first, "reset reuses memory from the start");
  SC_REQUIRE(c, a.allocate(1u << 20) == nullptr && a.failed_allocations() == 1, "exhaustion returns null, is counted");
  SC_REQUIRE(c, a.allocate(8, 3) == nullptr, "non-power-of-two alignment rejected in every build");
  SC_REQUIRE(c, a.allocate(8, 128) == nullptr, "alignment above arena guarantee rejected");
  LinearArena uninitialized;
  SC_REQUIRE(c, uninitialized.allocate(8) == nullptr, "uninitialized arena rejects allocation");
  SC_REQUIRE(c, a.failed_allocations() == 3, "invalid requests are counted");
  c.note = "valid alignments honored; exhaustion and invalid requests safely rejected";
  return true;
}

struct Tracked {
  static inline int alive = 0;
  int v;
  explicit Tracked(int x) : v(x) { ++alive; }
  ~Tracked() { --alive; }
};

struct MayThrow {
  static inline bool should_throw = false;
  int value = 0;
  explicit MayThrow(int v) : value(v) {
    if (should_throw) throw std::runtime_error("intentional test exception");
  }
};

bool check_pool(Context& c) {
  Pool<Tracked> pool;
  SC_REQUIRE(c, pool.init(64), "init");
  ScopedAllocationCheck guard;
  Tracked* ptrs[64];
  for (int round = 0; round < 100; ++round) {
    for (int i = 0; i < 64; ++i) {
      ptrs[i] = pool.create(i);
      SC_REQUIRE(c, ptrs[i] != nullptr, "create");
    }
    SC_REQUIRE(c, pool.create(0) == nullptr, "pool exhausted -> null");
    SC_REQUIRE(c, Tracked::alive == 64 && pool.live() == 64, "constructors ran");
    for (int i = 0; i < 64; ++i) SC_REQUIRE(c, pool.destroy(ptrs[i]), "destroy owned live object");
    SC_REQUIRE(c, Tracked::alive == 0 && pool.live() == 0, "destructors ran");
  }
  SC_REQUIRE(c, guard.allocations() == 0, "pool create/destroy must not allocate");

  Tracked* once = pool.create(7);
  SC_REQUIRE(c, once && pool.destroy(once), "first destroy succeeds");
  SC_REQUIRE(c, !pool.destroy(once), "double destroy is rejected");
  {
    Tracked outsider(99);
    Tracked* owned = pool.create(8);
    SC_REQUIRE(c, owned && !pool.destroy(&outsider), "foreign pointer is rejected");
    SC_REQUIRE(c, pool.destroy(owned), "valid object remains destroyable");
  }
  Tracked* left_live = pool.create(10);
  SC_REQUIRE(c, left_live && pool.live() == 1, "live object before release");
  pool.release();
  SC_REQUIRE(c, Tracked::alive == 0 && pool.live() == 0, "release destroys live objects");
  SC_REQUIRE(c, !pool.destroy(left_live), "pointer from released pool is rejected");

  Pool<MayThrow> throwing;
  SC_REQUIRE(c, throwing.init(1), "throwing pool init");
  MayThrow::should_throw = true;
  bool caught = false;
  try { (void)throwing.create(1); } catch (const std::runtime_error&) { caught = true; }
  MayThrow::should_throw = false;
  SC_REQUIRE(c, caught && throwing.live() == 0, "throwing constructor leaves pool unchanged");
  SC_REQUIRE(c, throwing.create(2) != nullptr && throwing.live() == 1, "pool remains reusable after constructor throws");
  throwing.release();
  c.note = "6,400 create/destroy; foreign/double destroy rejected; release cleans live objects; ctor exception is safe";
  return true;
}

// ---- real-time-safe channels ------------------------------------------------------
bool check_spsc(Context& c) {
  static_assert(std::atomic<usize>::is_always_lock_free, "test target must support realtime queue atomics");
  static SpscQueue<u64, 1024> q;
  SC_REQUIRE(c, q.atomics_are_lock_free(), "queue atomics are lock-free at runtime");
  SpscQueue<u32, 4> bounded;
  u32 value = 0;
  SC_REQUIRE(c, !bounded.try_pop(value), "empty queue reports no item");
  for (u32 i = 0; i < 4; ++i) SC_REQUIRE(c, bounded.try_push(i), "queue accepts up to capacity");
  SC_REQUIRE(c, !bounded.try_push(99), "full queue rejects another item");
  for (u32 i = 0; i < 4; ++i) {
    SC_REQUIRE(c, bounded.try_pop(value) && value == i, "queue preserves FIFO order");
  }
  {
    ScopedAllocationCheck guard;
    for (u32 i = 0; i < 10000; ++i) {
      (void)bounded.try_push(i);
      (void)bounded.try_pop(value);
    }
    SC_REQUIRE(c, guard.allocations() == 0, "queue data path does not allocate");
  }
  static_assert(noexcept(bounded.try_push(value)) && noexcept(bounded.try_pop(value)),
                "realtime queue calls are noexcept");
  constexpr u64 kCount = 3'000'000;
  std::atomic<bool> bad{false};
  std::thread consumer([&] {
    u64 expect = 0, v;
    while (expect < kCount) {
      if (q.try_pop(v)) {
        if (v != expect) {
          bad = true;
          return;
        }
        ++expect;
      }
    }
  });
  std::thread producer([&] {
    for (u64 i = 0; i < kCount;) {
      if (q.try_push(i)) ++i;
    }
  });
  producer.join();
  consumer.join();
  SC_REQUIRE(c, !bad.load(), "items must arrive in order, none lost or duplicated");
  c.note = "3,000,000 items across 2 threads, FIFO order preserved";
  return true;
}

struct Pair {
  u64 a;
  u64 b;  // always ~a: a torn read is detectable
};

bool check_triple_buffer(Context& c) {
  static_assert(std::atomic<u32>::is_always_lock_free, "test target must support realtime triple-buffer atomics");
  static TripleBuffer<Pair> tb;
  SC_REQUIRE(c, tb.atomics_are_lock_free(), "triple-buffer atomic is lock-free at runtime");
  static_assert(noexcept(tb.publish(Pair{})) && noexcept(tb.read()), "triple-buffer calls are noexcept");
  {
    TripleBuffer<Pair> scratch;
    ScopedAllocationCheck guard;
    for (u32 i = 0; i < 10000; ++i) {
      scratch.publish(Pair{i, ~static_cast<u64>(i)});
      (void)scratch.read();
    }
    SC_REQUIRE(c, guard.allocations() == 0, "triple-buffer data path does not allocate");
  }
  constexpr u64 kWrites = 2'000'000;
  std::atomic<bool> done{false};
  std::atomic<u64> torn{0}, backwards{0}, reads{0};
  std::thread writer([&] {
    for (u64 i = 1; i <= kWrites; ++i) tb.publish(Pair{i, ~i});
    done = true;
  });
  std::thread reader([&] {
    u64 last = 0;
    while (!done.load(std::memory_order_acquire)) {
      const Pair& p = tb.read();
      if (p.a == 0) continue;  // nothing published yet: the zero-initialised slot is not a valid Pair
      if (p.a != ~p.b) ++torn;
      if (p.a < last) ++backwards;
      last = p.a;
      ++reads;
    }
  });
  writer.join();
  reader.join();
  SC_REQUIRE(c, torn.load() == 0, "no torn reads");
  SC_REQUIRE(c, backwards.load() == 0, "reader never sees time go backwards");
  c.note = "2,000,000 writes, " + std::to_string(reads.load()) + " reads, 0 torn, 0 out-of-order";
  return true;
}

// ---- numeric model (ADR-0017) --------------------------------------------------------
bool check_numeric_model(Context& c) {
  constexpr i64 kRate = 192000;
  constexpr i64 kHours100 = 100LL * 3600 * kRate;  // 69,120,000,000 samples
  const SampleTime playhead{kHours100};
  // 1) f32 cannot even tell adjacent samples apart at hour 100 ...
  // `hours` is volatile so the comparison below is evaluated at run time. With constants on
  // both sides MSVC reports C4127 ("conditional expression is constant").
  const volatile i64 hours = kHours100;
  const f32 f0 = static_cast<f32>(hours);
  const f32 f1 = static_cast<f32>(hours + 1);
  SC_REQUIRE(c, f0 == f1, "f32 collapses adjacent samples at 100h@192kHz (this is the bug ADR-0017 prevents)");
  // 2) ... SampleTime (i64) is exact ...
  auto next = checked_add(playhead, SampleTime{1});
  SC_REQUIRE(c, next.ok() && next.value().samples == kHours100 + 1, "i64 sample time is exact");
  // 3) ... and camera-relative rendering keeps sub-pixel accuracy.
  const f64 px_per_sample = 0.01;
  const Vec2d clip{static_cast<f64>(kHours100 + 12345), 0};
  const Vec2d camera{static_cast<f64>(kHours100), 0};
  const f32 naive = static_cast<f32>(clip.x * px_per_sample) - static_cast<f32>(camera.x * px_per_sample);
  const f32 relative = to_camera_relative(clip, camera, px_per_sample).x;
  const f64 truth = 12345 * px_per_sample;
  const f64 naive_err = std::fabs(static_cast<f64>(naive) - truth);
  const f64 rel_err = std::fabs(static_cast<f64>(relative) - truth);
  SC_REQUIRE(c, naive_err > 1.0, "naive float pipeline visibly jitters (>1 px)");
  SC_REQUIRE(c, rel_err < 1e-3, "camera-relative error is far below a pixel");
  char buf[160];
  std::snprintf(buf, sizeof(buf), "at 100h@192kHz: naive f32 error %.1f px, camera-relative error %.2g px", naive_err, rel_err);
  c.note = buf;
  return true;
}

bool check_sample_time(Context& c) {
  constexpr i64 kMax = std::numeric_limits<i64>::max();
  SC_REQUIRE(c, !checked_add(SampleTime{kMax}, SampleTime{1}).ok(), "overflow detected on add");
  SC_REQUIRE(c, checked_add(SampleTime{kMax}, SampleTime{1}).error() == Error::Overflow, "Overflow error code");
  SC_REQUIRE(c, !checked_sub(SampleTime{std::numeric_limits<i64>::min()}, SampleTime{1}).ok(), "underflow detected on sub");
  SC_REQUIRE(c, checked_add(SampleTime{5}, SampleTime{-7}).value().samples == -2, "negative arithmetic");
  const auto seconds = to_seconds(SampleTime{192000LL * 3600}, 192000);
  SC_REQUIRE(c, seconds.ok() && seconds.value() == 3600.0, "samples -> seconds");
  const auto zero_rate = to_seconds(SampleTime{1}, 0);
  SC_REQUIRE(c, !zero_rate.ok() && zero_rate.error() == Error::InvalidArgument,
             "zero sample rate is an InvalidArgument error");
  c.note = "checked add/sub; zero sample rate returns InvalidArgument";
  return true;
}

bool check_color(Context& c) {
  for (int v = 0; v <= 255; ++v) {
    const f32 s = static_cast<f32>(v) / 255.0f;
    const f32 round_trip = linear_to_srgb(srgb_to_linear(s));
    SC_REQUIRE(c, std::fabs(round_trip - s) < 1e-4f, "sRGB round trip");
  }
  const Color half = color_from_srgb8(255, 255, 255, 128);
  SC_REQUIRE(c, std::fabs(half.r - half.a) < 1e-5f, "premultiplied alpha");
  c.note = "256 sRGB<->linear round trips < 1e-4; premultiplied output";
  return true;
}

bool check_rect(Context& c) {
  const Rectf r{10, 10, 20, 20};
  SC_REQUIRE(c, r.contains({10, 10}) && !r.contains({30, 30}), "half-open containment");
  SC_REQUIRE(c, r.intersects({25, 25, 10, 10}) && !r.intersects({30, 10, 5, 5}), "intersection");
  c.note = "contains / intersects";
  return true;
}

bool check_hash(Context& c) {
  static_assert(fnv1a64("") == 0xcbf29ce484222325ull);
  static_assert(fnv1a64("a") == 0xaf63dc4c8601ec8cull);
  static_assert(fnv1a64("foobar") == 0x85944171f73967e8ull);
  SC_REQUIRE(c, fnv1a64("tgf") != fnv1a64("tgg"), "differs");
  c.note = "FNV-1a 64 matches published vectors at compile time";
  return true;
}

bool check_strong_types(Context& c) {
  const Dip a{2.0f}, b{3.0f};
  SC_REQUIRE(c, (a + b).value == 5.0f && (a * 4.0f).value == 8.0f && a < b, "Dip arithmetic");
  c.note = "Dip/Px/Seconds typed arithmetic (mixing is a compile error)";
  return true;
}


struct ExternalAllocatorState {
  u32 allocate_calls = 0;
  u32 deallocate_calls = 0;
  usize last_bytes = 0;
  usize last_alignment = 0;
};

void* test_external_allocate(void* context, usize bytes, usize alignment) noexcept {
  auto* state = static_cast<ExternalAllocatorState*>(context);
  ++state->allocate_calls;
  state->last_bytes = bytes;
  state->last_alignment = alignment;
  return std::malloc(bytes);
}

void test_external_deallocate(void* context, void* block, usize bytes,
                              usize alignment) noexcept {
  auto* state = static_cast<ExternalAllocatorState*>(context);
  if (bytes == state->last_bytes && alignment == state->last_alignment)
    ++state->deallocate_calls;
  std::free(block);
}

struct LeakCapture {
  u32 calls = 0;
  u64 allocations = 0;
  u64 bytes = 0;
  MemoryTag last_tag = MemoryTag::Unspecified;
};

void capture_memory_leak(MemoryTag tag, MemoryLeakReport report,
                          void* context) noexcept {
  auto* capture = static_cast<LeakCapture*>(context);
  ++capture->calls;
  capture->allocations += report.live_allocations;
  capture->bytes += report.live_bytes;
  capture->last_tag = tag;
}

bool check_external_allocator_and_shutdown_report(Context& c) {
  ExternalAllocatorState backend{};
  const ExternalAllocator external{&backend, &test_external_allocate,
                                   &test_external_deallocate};
  set_memory_budget(MemoryTag::Host, 96);
  const MemoryStats before = memory_stats(MemoryTag::Host);
  LeakCapture capture{};
  void* outstanding = nullptr;
  {
    ScopedMemoryLeakReport reporter(&capture_memory_leak, &capture);
    outstanding = tracked_external_alloc_bytes(external, 80, 256,
                                                MemoryTag::Host);
    void* over_budget = tracked_external_alloc_bytes(external, 32, 64,
                                                       MemoryTag::Host);
    SC_REQUIRE(c, outstanding != nullptr, "tracked external allocation succeeds inside budget");
    SC_REQUIRE(c, over_budget == nullptr, "tracked external allocator obeys TGF byte budgets");
    SC_REQUIRE(c, reinterpret_cast<std::uintptr_t>(outstanding) % 256 == 0,
               "adapter provides requested payload alignment");
    const MemoryStats during = memory_stats(MemoryTag::Host);
    SC_REQUIRE(c, during.live_bytes == before.live_bytes + 80 &&
                     during.live_allocations == before.live_allocations + 1,
               "external allocations participate in live accounting");
  }
  SC_REQUIRE(c, capture.calls == 1 && capture.last_tag == MemoryTag::Host &&
                   capture.allocations == 1 && capture.bytes == 80,
             "scoped shutdown reporter emits positive outstanding per-tag deltas");
  SC_REQUIRE(c, backend.allocate_calls == 1 && backend.deallocate_calls == 0,
             "budget rejection does not call the external backend");
  aligned_free_bytes(outstanding);
  const MemoryStats after = memory_stats(MemoryTag::Host);
  set_memory_budget(MemoryTag::Host, 0);
  SC_REQUIRE(c, backend.deallocate_calls == 1,
             "TGF returns external blocks through the matching backend callback");
  SC_REQUIRE(c, after.live_bytes == before.live_bytes &&
                   after.live_allocations == before.live_allocations,
             "external free restores the original live counters");
  c.note = "custom host allocator is wrapped with aligned tracking headers, tags, budgets, leak callback and paired free";
  return true;
}


bool check_module_allocator_lifetime(Context& c) {
  ExternalAllocatorState backend{};
  ModuleAllocatorDesc desc{};
  desc.context = &backend;
  desc.allocate = &test_external_allocate;
  desc.deallocate = &test_external_deallocate;
  const auto registered = register_module_allocator(desc);
  SC_REQUIRE(c, registered.ok(), "module allocator registration succeeds");
  const ModuleAllocatorHandle handle = registered.value();
  void* block = module_alloc_bytes(handle, 512, 128, MemoryTag::Host);
  SC_REQUIRE(c, block != nullptr, "allocation through registered module backend succeeds");
  SC_REQUIRE(c, module_allocator_outstanding_allocations(handle) == 1,
             "TGF tracks a live allocation against its owning module");
  const Status premature_unload = unregister_module_allocator(handle);
  SC_REQUIRE(c, !premature_unload.ok() && premature_unload.error() == Error::Busy &&
                   std::string(error_name(premature_unload.error())) == "Busy",
             "module cannot unregister while one of its allocations is outstanding");
  aligned_free_bytes(block);
  SC_REQUIRE(c, backend.deallocate_calls == 1 &&
                   module_allocator_outstanding_allocations(handle) == 0,
             "free uses the original module callback and releases its unload pin");
  SC_REQUIRE(c, unregister_module_allocator(handle).ok(),
             "module can unregister after every allocation is returned");
  SC_REQUIRE(c, module_alloc_bytes(handle, 16, 16, MemoryTag::Host) == nullptr,
             "stale module allocator handles cannot allocate after unregister");
  const auto re_registered = register_module_allocator(desc);
  SC_REQUIRE(c, re_registered.ok() && re_registered.value().generation != handle.generation,
             "slot reuse changes generation and rejects stale identities");
  SC_REQUIRE(c, unregister_module_allocator(re_registered.value()).ok(),
             "unused re-registered module can unload immediately");

  ModuleAllocatorHandle handles[64]{};
  for (u32 i = 0; i < 64; ++i) {
    const auto item = register_module_allocator(desc);
    SC_REQUIRE(c, item.ok(), "fixed registry accepts all 64 supported registrations");
    handles[i] = item.value();
  }
  const auto over_capacity = register_module_allocator(desc);
  SC_REQUIRE(c, !over_capacity.ok() && over_capacity.error() == Error::CapacityExceeded,
             "fixed registry rejects a 65th simultaneous module");
  for (ModuleAllocatorHandle item : handles)
    SC_REQUIRE(c, unregister_module_allocator(item).ok(), "all registry test slots unregister cleanly");
  c.note = "callback lifetime pinned, Busy blocks early unload, stale generations rejected, 64-slot limit enforced";
  return true;
}


struct ConcurrentExternalState {
  std::atomic<u64> allocate_calls{0};
  std::atomic<u64> deallocate_calls{0};
};

void* concurrent_external_allocate(void* context, usize bytes,
                                   usize) noexcept {
  auto* state = static_cast<ConcurrentExternalState*>(context);
  void* block = std::malloc(bytes);
  if (block) state->allocate_calls.fetch_add(1, std::memory_order_relaxed);
  return block;
}

void concurrent_external_deallocate(void* context, void* block, usize,
                                    usize) noexcept {
  auto* state = static_cast<ConcurrentExternalState*>(context);
  state->deallocate_calls.fetch_add(1, std::memory_order_relaxed);
  std::free(block);
}

bool check_module_allocator_concurrency(Context& c) {
  ConcurrentExternalState backend{};
  ModuleAllocatorDesc desc{};
  desc.context = &backend;
  desc.allocate = &concurrent_external_allocate;
  desc.deallocate = &concurrent_external_deallocate;
  const auto registered = register_module_allocator(desc);
  SC_REQUIRE(c, registered.ok(), "concurrent module allocator registers");
  const ModuleAllocatorHandle handle = registered.value();
  constexpr u32 kThreads = 4;
  constexpr u32 kIterations = 256;
  std::thread workers[kThreads];
  std::atomic<u32> failures{0};
  for (u32 i = 0; i < kThreads; ++i) {
    workers[i] = std::thread([&, i] {
      for (u32 n = 0; n < kIterations; ++n) {
        void* block = module_alloc_bytes(handle, 32 + i, 64, MemoryTag::Platform);
        if (!block || reinterpret_cast<std::uintptr_t>(block) % 64 != 0) {
          failures.fetch_add(1, std::memory_order_relaxed);
          continue;
        }
        aligned_free_bytes(block);
      }
    });
  }
  for (std::thread& worker : workers) worker.join();
  const u64 expected = static_cast<u64>(kThreads) * kIterations;
  const MemoryStats platform_stats = memory_stats(MemoryTag::Platform);
  SC_REQUIRE(c, failures.load(std::memory_order_relaxed) == 0,
             "all concurrent cross-module allocations preserve alignment");
  SC_REQUIRE(c, backend.allocate_calls.load(std::memory_order_relaxed) == expected &&
                   backend.deallocate_calls.load(std::memory_order_relaxed) == expected,
             "concurrent backend allocations and frees are paired exactly");
  SC_REQUIRE(c, module_allocator_outstanding_allocations(handle) == 0 &&
                   platform_stats.live_bytes == 0 && platform_stats.live_allocations == 0,
             "concurrent module allocations leave no outstanding blocks or live bytes");
  SC_REQUIRE(c, unregister_module_allocator(handle).ok(),
             "module can unload after concurrent allocations have drained");
  c.note = "1,024 allocations/frees across 4 threads; callback context safe, all pins released, no leaks";
  return true;
}

bool check_memory_mapped_file(Context& c) {
#if defined(TGF_SHOWCASE_MEMORY_SANITIZER) && !defined(_WIN32)
  // The system libstdc++ in many Linux distributions is not MSan-instrumented.
  // Keep this MSan path on plain POSIX strings/file descriptors so a standard-
  // library false positive does not hide findings in TGF's mapping implementation.
  char path[] = "/tmp/tgf_memory_map_p1_2_5_XXXXXX";
  const int temp_fd = ::mkstemp(path);
  SC_REQUIRE(c, temp_fd >= 0, "temporary file can be created");
  const char original[] = "TGF mapped-file integration test";
  constexpr std::size_t original_size = sizeof(original) - 1;
  const ssize_t written = ::write(temp_fd, original, original_size);
  const int close_result = ::close(temp_fd);
  SC_REQUIRE(c, written == static_cast<ssize_t>(original_size) && close_result == 0,
             "test payload is written");
  {
    MappedFile read_only;
    SC_REQUIRE(c, read_only.open(path, MappedFileAccess::ReadOnly),
               "read-only mapping opens an existing UTF-8 path");
    SC_REQUIRE(c, read_only.size() == original_size && read_only.data() != nullptr,
               "mapping exposes the exact file size and mapped view");
    SC_REQUIRE(c, read_only.writable_data() == nullptr,
               "read-only mappings never expose a writable pointer");
    SC_REQUIRE(c, std::memcmp(read_only.data(), original, original_size) == 0,
               "mapped bytes match the file payload");
    SC_REQUIRE(c, read_only.flush(), "flush on read-only mapping is a successful no-op");
  }
  {
    MappedFile read_write;
    SC_REQUIRE(c, read_write.open(path, MappedFileAccess::ReadWrite),
               "read-write mapping opens the file");
    auto* bytes = static_cast<char*>(read_write.writable_data());
    SC_REQUIRE(c, bytes != nullptr, "read-write mapping exposes writable bytes");
    bytes[0] = 't';
    SC_REQUIRE(c, read_write.flush(), "mapped modifications flush to the file");
    MappedFile moved(std::move(read_write));
    SC_REQUIRE(c, moved.is_open() && !read_write.is_open(),
               "move construction transfers mapping ownership exactly once");
    MappedFile assigned;
    assigned = std::move(moved);
    SC_REQUIRE(c, assigned.is_open() && !moved.is_open(),
               "move assignment transfers mapping ownership exactly once");
  }
  {
    const int input_fd = ::open(path, O_RDONLY);
    SC_REQUIRE(c, input_fd >= 0, "mapped file can be reopened through ordinary file I/O");
    char first = '\0';
    const ssize_t count = ::read(input_fd, &first, 1);
    const int input_close = ::close(input_fd);
    SC_REQUIRE(c, count == 1 && first == 't' && input_close == 0,
               "flushed mapped modification is visible through normal file I/O");
  }
  char empty_path[sizeof(path) + 8]{};
  const int path_chars = std::snprintf(empty_path, sizeof(empty_path), "%s.empty", path);
  SC_REQUIRE(c, path_chars > 0 && static_cast<std::size_t>(path_chars) < sizeof(empty_path),
             "empty-file path fits in its buffer");
  const int empty_fd = ::open(empty_path, O_CREAT | O_TRUNC | O_WRONLY, 0600);
  SC_REQUIRE(c, empty_fd >= 0, "empty temporary file can be created");
  SC_REQUIRE(c, ::close(empty_fd) == 0, "empty temporary file can be closed");
  {
    MappedFile empty;
    SC_REQUIRE(c, empty.open(empty_path), "zero-length files open successfully");
    SC_REQUIRE(c, empty.size() == 0 && empty.data() == nullptr && empty.flush(),
               "zero-length mapping has no view and flushes as a no-op");
  }
  (void)::unlink(path);
  (void)::unlink(empty_path);
  c.note = "MSan-safe POSIX file setup; read-only/read-write views, flush, moves and empty files verified";
  return true;
#else
  const std::filesystem::path path =
      std::filesystem::temp_directory_path() / "tgf_memory_map_p1_2_5_test.bin";
  const std::string original = "TGF mapped-file integration test";
  {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    SC_REQUIRE(c, output.good(), "temporary file can be created");
    output.write(original.data(), static_cast<std::streamsize>(original.size()));
    SC_REQUIRE(c, output.good(), "test payload is written");
  }
  const std::u8string path_u8 = path.u8string();
  const std::string utf8_path(reinterpret_cast<const char*>(path_u8.data()),
                              path_u8.size());
  {
    MappedFile read_only;
    SC_REQUIRE(c, read_only.open(utf8_path.c_str(), MappedFileAccess::ReadOnly),
               "read-only mapping opens an existing UTF-8 path");
    SC_REQUIRE(c, read_only.size() == original.size() && read_only.data() != nullptr,
               "mapping exposes the exact file size and mapped view");
    SC_REQUIRE(c, read_only.writable_data() == nullptr,
               "read-only mappings never expose a writable pointer");
    SC_REQUIRE(c, std::memcmp(read_only.data(), original.data(), original.size()) == 0,
               "mapped bytes match the file payload");
    SC_REQUIRE(c, read_only.flush(), "flush on read-only mapping is a successful no-op");
  }
  {
    MappedFile read_write;
    SC_REQUIRE(c, read_write.open(utf8_path.c_str(), MappedFileAccess::ReadWrite),
               "read-write mapping opens the file");
    auto* bytes = static_cast<char*>(read_write.writable_data());
    SC_REQUIRE(c, bytes != nullptr, "read-write mapping exposes writable bytes");
    bytes[0] = 't';
    SC_REQUIRE(c, read_write.flush(), "mapped modifications flush to the file");
    MappedFile moved(std::move(read_write));
    SC_REQUIRE(c, moved.is_open() && !read_write.is_open(),
               "move construction transfers mapping ownership exactly once");
    MappedFile assigned;
    assigned = std::move(moved);
    SC_REQUIRE(c, assigned.is_open() && !moved.is_open(),
               "move assignment transfers mapping ownership exactly once");
  }
  {
    std::ifstream input(path, std::ios::binary);
    char first = '\0';
    input.get(first);
    SC_REQUIRE(c, first == 't', "flushed mapped modification is visible through normal file I/O");
  }
  const std::filesystem::path empty_path = path.string() + ".empty";
  { std::ofstream empty(empty_path, std::ios::binary | std::ios::trunc); }
  const std::u8string empty_u8 = empty_path.u8string();
  const std::string empty_utf8(reinterpret_cast<const char*>(empty_u8.data()),
                                empty_u8.size());
  {
    MappedFile empty;
    SC_REQUIRE(c, empty.open(empty_utf8.c_str()), "zero-length files open successfully");
    SC_REQUIRE(c, empty.size() == 0 && empty.data() == nullptr && empty.flush(),
               "zero-length mapping has no view and flushes as a no-op");
  }
  std::error_code ignored;
  std::filesystem::remove(path, ignored);
  std::filesystem::remove(empty_path, ignored);
  c.note = "UTF-8 path, read-only/read-write views, flush persistence, move ownership and empty-file handling";
  return true;
#endif
}

#if !defined(TGF_SHOWCASE_MEMORY_SANITIZER)
bool check_warmup_steady_state_boundary(Context& c) {
  std::vector<u64> frame_items;
  frame_items.reserve(128);  // warm-up: permitted one-time allocation
  for (u64 i = 0; i < 128; ++i) frame_items.push_back(i);
  frame_items.clear();

  u64 steady_allocations = 0;
  {
    ScopedAllocationCheck steady_state;
    for (u32 frame = 0; frame < 1000; ++frame) {
      frame_items.clear();
      for (u64 item = 0; item < 128; ++item) frame_items.push_back(item);
    }
    steady_allocations = steady_state.allocations();
  }
  SC_REQUIRE(c, steady_allocations == 0,
             "warmed-up steady-state frame loop performs zero heap allocations");

  u64 boundary_allocations = 0;
  {
    ScopedAllocationCheck frame_boundary;
    frame_items.reserve(256);  // deliberate growth outside paint/layout/event loops
    boundary_allocations = frame_boundary.allocations();
  }
  SC_REQUIRE(c, boundary_allocations == 1,
             "a deliberate capacity growth at a frame boundary is visible to the counter");
  c.note = "warm-up allocation separated from 1,000 zero-allocation steady frames; boundary growth counted";
  return true;
}
#endif  // !TGF_SHOWCASE_MEMORY_SANITIZER

// ---- diagnostics ---------------------------------------------------------------------
struct Captured {
  std::string last;
  int count = 0;
};
void capture_sink(LogLevel, const char* msg, void* user) noexcept {
  auto* cap = static_cast<Captured*>(user);
  ++cap->count;
  cap->last.assign(msg);
}

bool check_scoped_allocation_thread_local(Context& c) {
  std::atomic<bool> go{false};
  std::atomic<bool> done{false};
  std::thread worker([&] {
    while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
    void* p = aligned_alloc_bytes(128, 64);
    aligned_free_bytes(p);
    done.store(true, std::memory_order_release);
  });
  ScopedAllocationCheck guard;
  go.store(true, std::memory_order_release);
  while (!done.load(std::memory_order_acquire)) std::this_thread::yield();
  worker.join();
  SC_REQUIRE(c, guard.allocations() == 0,
             "allocations on unrelated worker threads do not affect this thread's scoped check");
  c.note = "worker-thread allocation does not create a false positive on the guarded thread";
  return true;
}

bool check_log(Context& c) {
  Captured cap;
  const LogLevel old = log_level();
  set_log_sink(&capture_sink, &cap);
  set_log_level(LogLevel::Warn);
  TGF_LOG(Info, "filtered out %d", 1);
  TGF_LOG(Error, "kept %d", 2);
  set_log_sink(nullptr, nullptr);
  set_log_level(old);
  SC_REQUIRE(c, cap.count == 1 && cap.last == "kept 2", "level filter + custom sink + formatting");
  c.note = "runtime level filter, custom sink, printf formatting";
  return true;
}

bool check_profiler(Context& c) {
  profiler_thread_reset();
  {
    ScopedZone outer("outer");
    {
      ScopedZone inner("inner");
      g_sink = g_sink + now_ns();
    }
  }
  ZoneEvent ev[8];
  const usize n = profiler_thread_zones(ev, 8);
  SC_REQUIRE(c, n == 2, "two zones recorded");
  SC_REQUIRE(c, std::string(ev[0].name) == "inner" && ev[0].depth == 1, "inner finishes first at depth 1");
  SC_REQUIRE(c, std::string(ev[1].name) == "outer" && ev[1].depth == 0, "outer at depth 0");
  SC_REQUIRE(c, ev[1].begin_ns <= ev[0].begin_ns && ev[0].end_ns <= ev[1].end_ns, "inner nested inside outer");
  // Ring buffer wraps without allocating.
  ScopedAllocationCheck guard;
  for (int i = 0; i < 10000; ++i) ScopedZone z("spin");
  SC_REQUIRE(c, guard.allocations() == 0, "profiling must not allocate");
  c.note = "nesting/depth/timestamps correct, ring wraps over 10,000 zones with 0 allocations";
  return true;
}

}  // namespace

void register_core_checks(Suite& s) {
  s.checks.push_back({"core", "build policy: lib no-exceptions/no-RTTI, user code unaffected", check_build_policy});
  s.checks.push_back({"core", "type layout (handles, strong types)", check_layout});
  s.checks.push_back({"core", "Result / Status error model", check_result});
  s.checks.push_back({"core", "aligned allocation validation and overflow", check_aligned_allocation});
  s.checks.push_back({"core", "memory tags, budgets, live tracking and leak snapshots", check_memory_tags_budgets_and_leaks});
  s.checks.push_back({"core", "tracked external allocator and scoped shutdown leak report", check_external_allocator_and_shutdown_report});
#if !defined(TGF_SHOWCASE_MEMORY_SANITIZER)
  // MSan runtime owns global new/delete interceptors. The warm-up test depends on
  // the showcase's process-wide operator-new hook, so it is not meaningful there.
  s.checks.push_back({"core", "warm-up / steady-state allocation boundary", check_warmup_steady_state_boundary});
#endif
  s.checks.push_back({"core", "cross-module allocator lifetime and unload safety", check_module_allocator_lifetime});
  s.checks.push_back({"core", "cross-module allocator concurrent allocation/free", check_module_allocator_concurrency});
  s.checks.push_back({"core", "memory-mapped file read/write/flush/empty behavior", check_memory_mapped_file});
  s.checks.push_back({"core", "strong typedef arithmetic", check_strong_types});
  s.checks.push_back({"core", "SlotMap semantics (stale handles, swap-remove)", check_slotmap_semantics});
  s.checks.push_back({"core", "SlotMap steady state: zero allocations", check_slotmap_zero_alloc});
  s.checks.push_back({"core", "SlotMap growth counted, Fixed policy", check_slotmap_growth});
  s.checks.push_back({"core", "LinearArena alignment/reset/exhaustion", check_arena});
  s.checks.push_back({"core", "Pool create/destroy", check_pool});
  s.checks.push_back({"core", "SpscQueue 2-thread stress", check_spsc});
  s.checks.push_back({"core", "TripleBuffer no torn reads (ADR-0022)", check_triple_buffer});
  s.checks.push_back({"core", "numeric model f32 vs i64/camera-relative (ADR-0017)", check_numeric_model});
  s.checks.push_back({"core", "SampleTime overflow-checked arithmetic and zero-rate behavior", check_sample_time});
  s.checks.push_back({"core", "thread-local scoped allocation guard", check_scoped_allocation_thread_local});
  s.checks.push_back({"core", "colour: sRGB round trip, premultiplied", check_color});
  s.checks.push_back({"core", "Rectf geometry", check_rect});
  s.checks.push_back({"core", "constexpr FNV-1a hashing", check_hash});
  s.checks.push_back({"core", "logging: filter + sink", check_log});
  s.checks.push_back({"core", "profiler zones", check_profiler});
}

}  // namespace showcase
