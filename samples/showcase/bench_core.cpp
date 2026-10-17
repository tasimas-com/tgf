// Micro-benchmarks for tgf::core. These are smoke-level numbers for the showcase;
// the statistically gated suite (P0.3) will replace them.
#include <cstdlib>
#include <tgf/core/hash.hpp>
#include <tgf/core/memory.hpp>
#include <tgf/core/profiler.hpp>
#include <tgf/core/slot_map.hpp>
#include <tgf/core/spsc.hpp>
#include <vector>

#include "harness.hpp"

using namespace tgf;
using namespace tgf::core;

namespace showcase {
namespace {

template <class F>
double time_ns_per_op(u64 ops, F&& body) {
  const u64 t0 = now_ns();
  body();
  const u64 t1 = now_ns();
  return static_cast<double>(t1 - t0) / static_cast<double>(ops);
}

double bench_arena() {
  LinearArena a;
  a.init(1 << 20);
  constexpr u64 kOps = 8'000'000;
  return time_ns_per_op(kOps, [&] {
    for (u64 i = 0; i < kOps; ++i) {
      if ((i & 16383) == 0) a.reset();
      g_sink = g_sink + reinterpret_cast<std::uintptr_t>(a.allocate(64, 16));
    }
  });
}

double bench_malloc_baseline() {
  constexpr u64 kOps = 2'000'000;
  return time_ns_per_op(kOps, [&] {
    for (u64 i = 0; i < kOps; ++i) {
      void* p = std::malloc(64);
      g_sink = g_sink + reinterpret_cast<std::uintptr_t>(p);
      std::free(p);
    }
  });
}

struct Item {
  u64 a, b;
};

double bench_pool() {
  Pool<Item> pool;
  pool.init(1024);
  constexpr u64 kOps = 8'000'000;
  return time_ns_per_op(kOps, [&] {
    for (u64 i = 0; i < kOps; ++i) {
      Item* it = pool.create(Item{i, i});
      g_sink = g_sink + it->a;
      pool.destroy(it);
    }
  });
}

double bench_slotmap_insert_erase() {
  SlotMap<Item> m(GrowPolicy::Fixed);
  m.reserve(1024);
  constexpr u64 kOps = 4'000'000;
  return time_ns_per_op(kOps * 2, [&] {
    for (u64 i = 0; i < kOps; ++i) {
      auto h = m.insert(Item{i, i}).value();
      m.erase(h);
    }
  });
}

double bench_slotmap_get() {
  SlotMap<Item> m(GrowPolicy::Fixed);
  m.reserve(100000);
  std::vector<Handle<Item>> hs;
  for (u32 i = 0; i < 100000; ++i) hs.push_back(m.insert(Item{i, i}).value());
  constexpr u64 kOps = 20'000'000;
  return time_ns_per_op(kOps, [&] {
    u64 acc = 0;
    u32 idx = 12345;
    for (u64 i = 0; i < kOps; ++i) {
      idx = idx * 1664525u + 1013904223u;  // cheap LCG: random access pattern
      acc += m.get(hs[idx % 100000])->a;
    }
    g_sink = g_sink + acc;
  });
}

double bench_spsc_single_thread() {
  static SpscQueue<u64, 1024> q;
  constexpr u64 kOps = 20'000'000;
  return time_ns_per_op(kOps * 2, [&] {
    u64 v = 0;
    for (u64 i = 0; i < kOps; ++i) {
      (void)q.try_push(i);
      (void)q.try_pop(v);
      g_sink = g_sink + v;
    }
  });
}

double bench_hash() {
  const char* s = "button.primary.hover";
  constexpr u64 kOps = 20'000'000;
  return time_ns_per_op(kOps, [&] {
    u64 acc = 0;
    for (u64 i = 0; i < kOps; ++i) acc += fnv1a64(s + (i & 1), 19);
    g_sink = g_sink + acc;
  });
}

double bench_zone() {
  constexpr u64 kOps = 5'000'000;
  return time_ns_per_op(kOps, [&] {
    for (u64 i = 0; i < kOps; ++i) ScopedZone z("bench");
  });
}

}  // namespace

void register_core_benches(Suite& s) {
  s.benches.push_back({"core", "LinearArena::allocate(64B)  [ns/op]", bench_arena});
  s.benches.push_back({"core", "malloc+free(64B) baseline   [ns/op]", bench_malloc_baseline});
  s.benches.push_back({"core", "Pool create+destroy         [ns/op]", bench_pool});
  s.benches.push_back({"core", "SlotMap insert / erase      [ns/op]", bench_slotmap_insert_erase});
  s.benches.push_back({"core", "SlotMap::get (random,100k)  [ns/op]", bench_slotmap_get});
  s.benches.push_back({"core", "SpscQueue push+pop (1 thr)  [ns/op]", bench_spsc_single_thread});
  s.benches.push_back({"core", "fnv1a64(19 bytes)           [ns/op]", bench_hash});
  s.benches.push_back({"core", "ScopedZone begin+end        [ns/op]", bench_zone});
}

}  // namespace showcase
