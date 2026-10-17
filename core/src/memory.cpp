#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <limits>
#include <memory>
#include <tgf/core/memory.hpp>
#include "tgf/core/assert.hpp"
#include "tgf/core/config.hpp"
#include "tgf/core/types.hpp"

namespace tgf::core {
namespace {
constexpr u64 kAllocationMagic = 0x5447464D454D3031ull;  // "TGFMEM01"

struct AllocationHeader {
  u64 magic;
  void* raw;
  usize requested_bytes;
  MemoryTag tag;
  usize backend_bytes;
  usize backend_alignment;
  ExternalDeallocateFn external_deallocate;
  void* external_context;
};
static_assert(sizeof(AllocationHeader) % alignof(AllocationHeader) == 0);

struct AtomicMemoryStats {
  std::atomic<u64> allocation_count{0};
  std::atomic<u64> free_count{0};
  std::atomic<u64> cumulative_allocated_bytes{0};
  std::atomic<u64> cumulative_freed_bytes{0};
  std::atomic<u64> live_allocations{0};
  std::atomic<u64> live_bytes{0};
  std::atomic<u64> peak_live_bytes{0};
  std::atomic<usize> budget_bytes{0};
  std::atomic<u64> budget_exceeded{0};
};

std::atomic<u64> g_alloc_count{0};
std::atomic<u64> g_alloc_bytes{0};
thread_local u64 g_thread_alloc_count = 0;
thread_local MemoryTag g_memory_tag = MemoryTag::Unspecified;
AtomicMemoryStats g_stats[kMemoryTagCount];

bool valid_tag(MemoryTag tag) noexcept {
  return static_cast<usize>(tag) < kMemoryTagCount;
}

void note_event(usize bytes, MemoryTag tag) noexcept {
  g_alloc_count.fetch_add(1, std::memory_order_relaxed);
  g_alloc_bytes.fetch_add(static_cast<u64>(bytes), std::memory_order_relaxed);
  ++g_thread_alloc_count;
  const usize i = valid_tag(tag) ? static_cast<usize>(tag) : 0;
  g_stats[i].allocation_count.fetch_add(1, std::memory_order_relaxed);
  g_stats[i].cumulative_allocated_bytes.fetch_add(static_cast<u64>(bytes), std::memory_order_relaxed);
}

bool reserve_budget(AtomicMemoryStats& stats, usize bytes, u64& live_after_reserve) noexcept {
  u64 current = stats.live_bytes.load(std::memory_order_relaxed);
  for (;;) {
    const usize budget = stats.budget_bytes.load(std::memory_order_relaxed);
    if (budget != 0 && (current > budget || bytes > budget - static_cast<usize>(current))) {
      stats.budget_exceeded.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    if (bytes > std::numeric_limits<u64>::max() - current) {
      stats.budget_exceeded.fetch_add(1, std::memory_order_relaxed);
      return false;
    }
    if (stats.live_bytes.compare_exchange_weak(current, current + static_cast<u64>(bytes), std::memory_order_acq_rel,
                                               std::memory_order_relaxed)) {
      live_after_reserve = current + static_cast<u64>(bytes);
      return true;
    }
  }
}

void update_peak(AtomicMemoryStats& stats, u64 value) noexcept {
  u64 peak = stats.peak_live_bytes.load(std::memory_order_relaxed);
  while (peak < value && !stats.peak_live_bytes.compare_exchange_weak(peak, value, std::memory_order_relaxed,
                                                                      std::memory_order_relaxed)) {
  }
}

MemoryStats load_stats(MemoryTag tag) noexcept {
  const usize i = valid_tag(tag) ? static_cast<usize>(tag) : 0;
  const AtomicMemoryStats& a = g_stats[i];
  return {a.allocation_count.load(std::memory_order_relaxed),
          a.free_count.load(std::memory_order_relaxed),
          a.cumulative_allocated_bytes.load(std::memory_order_relaxed),
          a.cumulative_freed_bytes.load(std::memory_order_relaxed),
          a.live_allocations.load(std::memory_order_relaxed),
          a.live_bytes.load(std::memory_order_relaxed),
          a.peak_live_bytes.load(std::memory_order_relaxed),
          a.budget_bytes.load(std::memory_order_relaxed),
          a.budget_exceeded.load(std::memory_order_relaxed)};
}
}  // namespace

const char* memory_tag_name(MemoryTag tag) noexcept {
  switch (tag) {
    case MemoryTag::Unspecified:
      return "Unspecified";
    case MemoryTag::Core:
      return "Core";
    case MemoryTag::Platform:
      return "Platform";
    case MemoryTag::Renderer:
      return "Renderer";
    case MemoryTag::Text:
      return "Text";
    case MemoryTag::UI:
      return "UI";
    case MemoryTag::Widgets:
      return "Widgets";
    case MemoryTag::Host:
      return "Host";
    case MemoryTag::Sample:
      return "Sample";
    case MemoryTag::Count:
      break;
  }
  return "Invalid";
}

MemoryTag current_memory_tag() noexcept {
  return g_memory_tag;
}

ScopedMemoryTag::ScopedMemoryTag(MemoryTag tag) noexcept : previous_(g_memory_tag) {
  g_memory_tag = valid_tag(tag) ? tag : MemoryTag::Unspecified;
}
ScopedMemoryTag::~ScopedMemoryTag() noexcept {
  g_memory_tag = previous_;
}

MemoryStats memory_stats(MemoryTag tag) noexcept {
  return load_stats(tag);
}

MemorySnapshot memory_snapshot() noexcept {
  MemorySnapshot result{};
  for (usize i = 0; i < kMemoryTagCount; ++i) result.tags[i] = load_stats(static_cast<MemoryTag>(i));
  return result;
}

MemoryLeakReport memory_leaks_since(const MemorySnapshot& baseline, MemoryTag tag) noexcept {
  if (!valid_tag(tag)) return {};
  const MemoryStats now = load_stats(tag);
  const MemoryStats& before = baseline.tags[static_cast<usize>(tag)];
  return {now.live_allocations > before.live_allocations ? now.live_allocations - before.live_allocations : 0,
          now.live_bytes > before.live_bytes ? now.live_bytes - before.live_bytes : 0};
}

ScopedMemoryLeakReport::ScopedMemoryLeakReport(MemoryLeakCallback callback, void* context) noexcept
    : baseline_(memory_snapshot()), callback_(callback), context_(context) {}

ScopedMemoryLeakReport::~ScopedMemoryLeakReport() noexcept {
  if (!callback_) return;
  for (usize i = 0; i < kMemoryTagCount; ++i) {
    const MemoryTag tag = static_cast<MemoryTag>(i);
    const MemoryLeakReport report = memory_leaks_since(baseline_, tag);
    if (report.live_allocations != 0 || report.live_bytes != 0) callback_(tag, report, context_);
  }
}

void set_memory_budget(MemoryTag tag, usize budget_bytes) noexcept {
  if (!valid_tag(tag)) return;
  g_stats[static_cast<usize>(tag)].budget_bytes.store(budget_bytes, std::memory_order_relaxed);
}

void heap_note_allocation(usize bytes) noexcept {
  note_event(bytes, current_memory_tag());
}
u64 heap_allocation_count() noexcept {
  return g_alloc_count.load(std::memory_order_relaxed);
}
u64 heap_allocated_bytes() noexcept {
  return g_alloc_bytes.load(std::memory_order_relaxed);
}
u64 heap_thread_allocation_count() noexcept {
  return g_thread_alloc_count;
}

namespace {
void* allocate_tracked(usize size, usize alignment, MemoryTag tag, const ExternalAllocator* external) noexcept {
  if (size == 0 || alignment == 0 || (alignment & (alignment - 1)) != 0 || !valid_tag(tag) ||
      (external && (!external->allocate || !external->deallocate)))
    return nullptr;
  const usize effective_alignment = alignment < alignof(AllocationHeader) ? alignof(AllocationHeader) : alignment;
  constexpr usize header_size = sizeof(AllocationHeader);
  if (effective_alignment - 1 > std::numeric_limits<usize>::max() - header_size ||
      size > std::numeric_limits<usize>::max() - header_size - (effective_alignment - 1))
    return nullptr;
  const usize total = size + header_size + effective_alignment - 1;
  AtomicMemoryStats& stats = g_stats[static_cast<usize>(tag)];
  u64 live_after_reserve = 0;
  if (!reserve_budget(stats, size, live_after_reserve)) return nullptr;

  void* raw = external ? external->allocate(external->context, total, effective_alignment) : std::malloc(total);
  if (!raw) {
    stats.live_bytes.fetch_sub(static_cast<u64>(size), std::memory_order_acq_rel);
    return nullptr;
  }
  void* aligned = static_cast<std::byte*>(raw) + header_size;
  usize available = total - header_size;
  if (!std::align(effective_alignment, size, aligned, available)) {
    if (external)
      external->deallocate(external->context, raw, total, effective_alignment);
    else
      std::free(raw);
    stats.live_bytes.fetch_sub(static_cast<u64>(size), std::memory_order_acq_rel);
    return nullptr;
  }
  auto* header = reinterpret_cast<AllocationHeader*>(static_cast<std::byte*>(aligned) - header_size);
  header->magic = kAllocationMagic;
  header->raw = raw;
  header->requested_bytes = size;
  header->tag = tag;
  header->backend_bytes = total;
  header->backend_alignment = effective_alignment;
  header->external_deallocate = external ? external->deallocate : nullptr;
  header->external_context = external ? external->context : nullptr;

  note_event(size, tag);
  stats.live_allocations.fetch_add(1, std::memory_order_relaxed);
  update_peak(stats, live_after_reserve);
  return aligned;
}
}  // namespace

void* aligned_alloc_bytes(usize size, usize alignment) noexcept {
  return aligned_alloc_bytes(size, alignment, current_memory_tag());
}

void* aligned_alloc_bytes(usize size, usize alignment, MemoryTag tag) noexcept {
  return allocate_tracked(size, alignment, tag, nullptr);
}

void* tracked_external_alloc_bytes(const ExternalAllocator& allocator, usize size, usize alignment,
                                   MemoryTag tag) noexcept {
  return allocate_tracked(size, alignment, tag, &allocator);
}

void aligned_free_bytes(void* p) noexcept {
  if (!p) return;
  auto* header = reinterpret_cast<AllocationHeader*>(p) - 1;
  // Passing anything except a pointer returned by aligned_alloc_bytes() is a
  // contract violation; TGF cannot safely probe arbitrary memory for ownership.
  TGF_CHECK(header->magic == kAllocationMagic, "aligned_free_bytes received a foreign pointer");
  const usize bytes = header->requested_bytes;
  const MemoryTag tag = header->tag;
  void* raw = header->raw;
  const usize backend_bytes = header->backend_bytes;
  const usize backend_alignment = header->backend_alignment;
  const ExternalDeallocateFn external_deallocate = header->external_deallocate;
  void* external_context = header->external_context;
  header->magic = 0;
  if (valid_tag(tag)) {
    AtomicMemoryStats& stats = g_stats[static_cast<usize>(tag)];
    stats.free_count.fetch_add(1, std::memory_order_relaxed);
    stats.cumulative_freed_bytes.fetch_add(static_cast<u64>(bytes), std::memory_order_relaxed);
    stats.live_allocations.fetch_sub(1, std::memory_order_relaxed);
    stats.live_bytes.fetch_sub(static_cast<u64>(bytes), std::memory_order_acq_rel);
  }
  if (external_deallocate)
    external_deallocate(external_context, raw, backend_bytes, backend_alignment);
  else
    std::free(raw);
}

bool LinearArena::init(usize capacity_bytes) noexcept {
  release();
  if (capacity_bytes == 0) return false;
  base_ = static_cast<u8*>(aligned_alloc_bytes(capacity_bytes, TGF_CACHE_LINE_SIZE));
  if (!base_) return false;
  capacity_ = capacity_bytes;
  offset_ = high_water_ = 0;
  failed_ = 0;
  return true;
}

void LinearArena::release() noexcept {
  aligned_free_bytes(base_);
  base_ = nullptr;
  capacity_ = offset_ = high_water_ = 0;
  failed_ = 0;
}

}  // namespace tgf::core
