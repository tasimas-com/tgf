// tgf/core/memory.hpp — allocation primitives (P1.2).
//
// Rules and limits:
//  * TGF-routed allocations carry a fixed MemoryTag and update per-tag live,
//    cumulative, peak, and budget counters. Diagnostics allocate no memory.
//  * A ScopedAllocationCheck observes the calling thread. Complete host-wide
//    coverage requires global allocation/deallocation hooks to route through
//    aligned_alloc_bytes(), or an equivalent paired host integration.
//  * Snapshot leak deltas describe outstanding TGF-tracked allocations; capture
//    and compare snapshots at a quiescent point for meaningful reports.
//  * Arena/pool allocators never grow implicitly; failure is reported, not hidden.
#pragma once

#include <tgf/core/assert.hpp>
#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

#include <cstddef>
#include <cstdint>
#include <limits>
#include <new>
#include <type_traits>
#include <utility>

namespace tgf::core {

// ---- allocation tags, tracking and counted raw allocation ----------------------
// Tags are stable subsystem identifiers, not user-owned strings. Keeping them
// fixed-size makes accounting allocation-free and safe to query in diagnostics.
// ScopedMemoryTag is thread-local; explicitly set a tag on worker threads because
// a scope on the launching thread is not automatically inherited.
enum class MemoryTag : u8 {
  Unspecified = 0,
  Core,
  Platform,
  Renderer,
  Text,
  UI,
  Widgets,
  Host,
  Sample,
  Count
};
inline constexpr usize kMemoryTagCount = static_cast<usize>(MemoryTag::Count);

struct MemoryStats {
  u64 allocation_count = 0;          // successful/observed allocation events
  u64 free_count = 0;                // frees reported by TGF's allocator
  u64 cumulative_allocated_bytes = 0;
  u64 cumulative_freed_bytes = 0;
  u64 live_allocations = 0;          // tracked TGF aligned allocations only
  u64 live_bytes = 0;                // tracked TGF aligned allocations only
  u64 peak_live_bytes = 0;
  usize budget_bytes = 0;             // 0 means unlimited
  u64 budget_exceeded = 0;
};

struct MemorySnapshot {
  MemoryStats tags[kMemoryTagCount]{};
};

struct MemoryLeakReport {
  u64 live_allocations = 0;
  u64 live_bytes = 0;
};

// Host allocator adapter. The callbacks receive the complete backing-block size
// and alignment requested by TGF. TGF places its tracking header inside that
// block and returns an independently aligned payload. Both callbacks must be
// noexcept, must use the same allocator family, and must remain valid until all
// blocks returned by tracked_external_alloc_bytes() have been freed.
using ExternalAllocateFn = void* (*)(void* context, usize bytes, usize alignment) noexcept;
using ExternalDeallocateFn = void (*)(void* context, void* block, usize bytes,
                                      usize alignment) noexcept;
struct ExternalAllocator {
  void* context = nullptr;
  ExternalAllocateFn allocate = nullptr;
  ExternalDeallocateFn deallocate = nullptr;
};

// Reports positive per-tag live-allocation deltas relative to construction.
// Destroy this object at the host/plugin shutdown boundary, while TGF and the
// callback's code are still loaded. The callback should not allocate. This is
// intentionally scoped rather than process-global/atexit, so unloading a host
// plugin cannot leave a shutdown callback pointing into an unloaded module.
using MemoryLeakCallback = void (*)(MemoryTag tag, MemoryLeakReport report,
                                    void* context) noexcept;
class TGF_API ScopedMemoryLeakReport {
 public:
  explicit ScopedMemoryLeakReport(MemoryLeakCallback callback,
                                  void* context = nullptr) noexcept;
  ~ScopedMemoryLeakReport() noexcept;
  ScopedMemoryLeakReport(const ScopedMemoryLeakReport&) = delete;
  ScopedMemoryLeakReport& operator=(const ScopedMemoryLeakReport&) = delete;

 private:
  MemorySnapshot baseline_{};
  MemoryLeakCallback callback_ = nullptr;
  void* context_ = nullptr;
};

TGF_API const char* memory_tag_name(MemoryTag tag) noexcept;
TGF_API MemoryTag current_memory_tag() noexcept;
TGF_API MemoryStats memory_stats(MemoryTag tag) noexcept;
TGF_API MemorySnapshot memory_snapshot() noexcept;
TGF_API MemoryLeakReport memory_leaks_since(const MemorySnapshot& baseline, MemoryTag tag) noexcept;
// A zero budget disables the limit. Lowering a budget below current live usage
// is permitted, but subsequent allocations for that tag will be rejected.
TGF_API void set_memory_budget(MemoryTag tag, usize budget_bytes) noexcept;

class TGF_API ScopedMemoryTag {
 public:
  explicit ScopedMemoryTag(MemoryTag tag) noexcept;
  ~ScopedMemoryTag() noexcept;
  ScopedMemoryTag(const ScopedMemoryTag&) = delete;
  ScopedMemoryTag& operator=(const ScopedMemoryTag&) = delete;

 private:
  MemoryTag previous_;
};

// alignment must be a power of two. Returns nullptr on invalid input, budget
// exhaustion, or allocation failure (never throws). The explicit-tag overload
// is useful at subsystem boundaries; otherwise the current scoped tag is used.
TGF_API void* aligned_alloc_bytes(usize size, usize alignment) noexcept;
TGF_API void* aligned_alloc_bytes(usize size, usize alignment, MemoryTag tag) noexcept;
// Adapts a host/custom allocator while retaining TGF tags, budgets, live-byte
// accounting, leak snapshots, and hot-path event tracking. Free returned blocks
// with aligned_free_bytes(); never call the backend deallocator directly.
TGF_API void* tracked_external_alloc_bytes(const ExternalAllocator& allocator,
                                          usize size, usize alignment,
                                          MemoryTag tag) noexcept;
TGF_API void aligned_free_bytes(void* p) noexcept;

// Event-only compatibility hook for hosts that cannot use the tracked adapter.
// It contributes to cumulative/thread-local allocation counts, but does NOT
// contribute to live-byte budgets or leak snapshots because no paired pointer
// and deallocation are provided. Prefer tracked_external_alloc_bytes().
TGF_API void heap_note_allocation(usize bytes) noexcept;
TGF_API u64 heap_allocation_count() noexcept;  // process-wide cumulative event count
TGF_API u64 heap_allocated_bytes() noexcept;  // process-wide cumulative requested bytes
TGF_API u64 heap_thread_allocation_count() noexcept;

// Snapshot-based check: construct before a region, then inspect allocations().
// assert_no_allocations() is opt-in so diagnostic/reporting code after the hot
// region does not accidentally become part of the measured region.
class ScopedAllocationCheck {
 public:
  ScopedAllocationCheck() noexcept : start_(heap_thread_allocation_count()) {}
  u64 allocations() const noexcept { return heap_thread_allocation_count() - start_; }
  bool passed() const noexcept { return allocations() == 0; }
  void assert_no_allocations() const noexcept {
    TGF_CHECK(passed(), "allocation detected in guarded hot path");
  }

 private:
  u64 start_;
};

// ---- linear (frame) arena -----------------------------------------------------
// Fixed capacity, O(1) allocate, O(1) reset. Objects created in an arena must be
// trivially destructible: reset() does not run destructors.
class TGF_API LinearArena {
 public:
  LinearArena() noexcept = default;
  ~LinearArena() { release(); }
  LinearArena(const LinearArena&) = delete;
  LinearArena& operator=(const LinearArena&) = delete;

  // (Re)initialises with capacity_bytes of storage. This is the only allocation.
  bool init(usize capacity_bytes) noexcept;
  void release() noexcept;

  TGF_FORCE_INLINE void* allocate(usize size, usize alignment = alignof(std::max_align_t)) noexcept {
    // These are input checks, not debug assertions: callers must get the same
    // safe failure behavior in Debug and Release builds.
    if (TGF_UNLIKELY(!base_ || size == 0 || alignment == 0 ||
                     (alignment & (alignment - 1)) != 0 || alignment > TGF_CACHE_LINE_SIZE ||
                     offset_ > std::numeric_limits<usize>::max() - (alignment - 1))) {
      ++failed_;
      return nullptr;
    }
    const usize aligned = (offset_ + alignment - 1) & ~(alignment - 1);
    if (TGF_UNLIKELY(aligned > capacity_ || size > capacity_ - aligned)) {
      ++failed_;
      return nullptr;
    }
    offset_ = aligned + size;
    if (offset_ > high_water_) high_water_ = offset_;
    return base_ + aligned;
  }

  template <class T, class... Args>
  T* create(Args&&... args) noexcept {
    static_assert(std::is_trivially_destructible_v<T>, "arena objects must be trivially destructible");
    void* p = allocate(sizeof(T), alignof(T));
    return p ? ::new (p) T(std::forward<Args>(args)...) : nullptr;
  }

  void reset() noexcept { offset_ = 0; }

  usize used() const noexcept { return offset_; }
  usize capacity() const noexcept { return capacity_; }
  usize high_water() const noexcept { return high_water_; }
  u64 failed_allocations() const noexcept { return failed_; }

 private:
  u8* base_ = nullptr;
  usize capacity_ = 0;
  usize offset_ = 0;
  usize high_water_ = 0;
  u64 failed_ = 0;
};

// ---- fixed-capacity object pool -----------------------------------------------
// One upfront allocation; create()/destroy() are O(1) pointer pops/pushes.
template <class T>
class Pool {
  static_assert(std::is_nothrow_destructible_v<T>,
                "Pool<T> requires a noexcept destructor so release() is safe");

 public:
  Pool() noexcept = default;
  ~Pool() noexcept { release(); }
  Pool(const Pool&) = delete;
  Pool& operator=(const Pool&) = delete;

  bool init(u32 capacity) noexcept {
    release();
    if (capacity == 0 || static_cast<usize>(capacity) > std::numeric_limits<usize>::max() / sizeof(Node))
      return false;
    nodes_ = static_cast<Node*>(aligned_alloc_bytes(sizeof(Node) * static_cast<usize>(capacity), alignof(Node)));
    if (!nodes_) return false;
    capacity_ = capacity;
    for (u32 i = 0; i < capacity; ++i) {
      ::new (static_cast<void*>(nodes_ + i)) Node{};
      nodes_[i].next = (i + 1 < capacity) ? &nodes_[i + 1] : nullptr;
      nodes_[i].live = false;
    }
    free_ = nodes_;
    live_ = 0;
    return true;
  }

  // Destroys every still-live object before releasing the backing allocation.
  // This makes release()/re-init deterministic even when the caller forgets
  // to destroy an object explicitly.
  void release() noexcept {
    if (nodes_) {
      for (u32 i = 0; i < capacity_; ++i) {
        Node& node = nodes_[i];
        if (node.live) {
          object_at(node)->~T();
          node.live = false;
        }
      }
    }
    aligned_free_bytes(nodes_);
    nodes_ = nullptr;
    free_ = nullptr;
    capacity_ = live_ = 0;
  }

  template <class... Args>
  T* create(Args&&... args) noexcept(std::is_nothrow_constructible_v<T, Args...>) {
    if (TGF_UNLIKELY(!free_)) return nullptr;
    Node* n = free_;
    // Do not remove the node from the free list until construction succeeds.
    // If T's constructor throws, the pool remains unchanged and reusable.
    T* object = ::new (static_cast<void*>(n->storage)) T(std::forward<Args>(args)...);
    free_ = n->next;
    n->next = nullptr;
    n->live = true;
    ++live_;
    return object;
  }

  // Returns false for null, foreign, or already-destroyed pointers. Callers must
  // discard a pointer after destroy(): after that slot is reused, a stale raw
  // pointer has the same address as the new object and cannot encode its age.
  bool destroy(T* p) noexcept {
    Node* n = find_node(p);
    if (!n || !n->live) return false;
    p->~T();
    n->live = false;
    n->next = free_;
    free_ = n;
    --live_;
    return true;
  }

  u32 live() const noexcept { return live_; }
  u32 capacity() const noexcept { return capacity_; }

 private:
  static constexpr usize kNodeAlign = alignof(T) > alignof(void*) ? alignof(T) : alignof(void*);
  struct alignas(kNodeAlign) Node {
    Node* next = nullptr;
    bool live = false;
    alignas(T) unsigned char storage[sizeof(T)];
  };

  static T* object_at(Node& node) noexcept { return std::launder(reinterpret_cast<T*>(node.storage)); }

  Node* find_node(T* p) noexcept {
    if (!p || !nodes_ || capacity_ == 0) return nullptr;
    const std::uintptr_t base = reinterpret_cast<std::uintptr_t>(nodes_);
    const std::uintptr_t address = reinterpret_cast<std::uintptr_t>(p);
    const usize bytes = sizeof(Node) * static_cast<usize>(capacity_);
    if (address < base || address - base >= bytes) return nullptr;
    const usize offset = static_cast<usize>(address - base);
    Node* node = nodes_ + (offset / sizeof(Node));
    if (reinterpret_cast<std::uintptr_t>(node->storage) != address) return nullptr;
    return node;
  }

  Node* nodes_ = nullptr;
  Node* free_ = nullptr;
  u32 capacity_ = 0;
  u32 live_ = 0;
};

}  // namespace tgf::core
