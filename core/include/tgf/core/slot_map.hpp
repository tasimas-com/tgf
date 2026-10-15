// tgf/core/slot_map.hpp — generational arena with dense storage (P1.3.3, ADR-0003).
//
//  * insert/erase/lookup are O(1); iteration is a linear scan of a dense array
//    (cache friendly; order is unstable because erase swap-removes).
//  * Handles carry a generation, so a stale handle is detected, never dereferenced.
//  * Growth is explicit and counted. With GrowPolicy::Fixed, insert on a full map
//    fails with Error::CapacityExceeded and the hot path can never allocate.
#pragma once

#include <tgf/core/assert.hpp>
#include <tgf/core/memory.hpp>
#include <tgf/core/result.hpp>
#include <tgf/core/types.hpp>

#include <new>
#include <limits>
#include <type_traits>
#include <utility>

namespace tgf::core {

enum class GrowPolicy : u8 { Fixed, Double };

template <class T, class Tag = T>
class SlotMap {
  // Relocation and swap-erase run in noexcept functions. Restrict T rather than
  // risking std::terminate if a user move operation throws half-way through.
  static_assert(std::is_nothrow_move_constructible_v<T> && std::is_nothrow_move_assignable_v<T> &&
                    std::is_nothrow_destructible_v<T>,
                "SlotMap<T> requires noexcept move construction, move assignment, and destruction");

 public:
  using handle_type = Handle<Tag>;

  explicit SlotMap(GrowPolicy policy = GrowPolicy::Double) noexcept : policy_(policy) {}
  ~SlotMap() { destroy_storage(); }
  SlotMap(const SlotMap&) = delete;
  SlotMap& operator=(const SlotMap&) = delete;

  // Grows capacity (never shrinks). Counted as a growth event.
  bool reserve(u32 new_capacity) noexcept {
    if (new_capacity <= capacity_) return true;
    const usize max_size = std::numeric_limits<usize>::max();
    if (static_cast<usize>(new_capacity) > max_size / sizeof(Slot) ||
        static_cast<usize>(new_capacity) > max_size / sizeof(T) ||
        static_cast<usize>(new_capacity) > max_size / sizeof(u32)) return false;
    Slot* ns = static_cast<Slot*>(aligned_alloc_bytes(sizeof(Slot) * static_cast<usize>(new_capacity), alignof(Slot)));
    T* nv = static_cast<T*>(aligned_alloc_bytes(sizeof(T) * static_cast<usize>(new_capacity), alignof(T) < 16 ? 16 : alignof(T)));
    u32* no = static_cast<u32*>(aligned_alloc_bytes(sizeof(u32) * static_cast<usize>(new_capacity), alignof(u32)));
    if (!ns || !nv || !no) {
      aligned_free_bytes(ns);
      aligned_free_bytes(nv);
      aligned_free_bytes(no);
      return false;
    }
    for (u32 i = 0; i < capacity_; ++i) ns[i] = slots_[i];
    for (u32 i = 0; i < size_; ++i) {
      ::new (static_cast<void*>(nv + i)) T(std::move(values_[i]));
      values_[i].~T();
      no[i] = owner_[i];
    }
    // Thread the new slots onto the free list, lowest index first.
    for (u32 i = new_capacity; i-- > capacity_;) {
      ns[i].generation = 1;
      ns[i].index = free_head_;
      free_head_ = i;
    }
    aligned_free_bytes(slots_);
    aligned_free_bytes(values_);
    aligned_free_bytes(owner_);
    slots_ = ns;
    values_ = nv;
    owner_ = no;
    capacity_ = new_capacity;
    ++growth_events_;
    return true;
  }

  Result<handle_type> insert(T value) noexcept {
    if (TGF_UNLIKELY(size_ == capacity_)) {
      if (policy_ == GrowPolicy::Fixed) return Error::CapacityExceeded;
      if (capacity_ >= 0x40000000u) return Error::CapacityExceeded;
      if (!reserve(capacity_ ? capacity_ * 2 : 16)) return Error::OutOfMemory;
    }
    const u32 s = free_head_;
    Slot& slot = slots_[s];
    free_head_ = slot.index;
    const u32 di = size_++;
    ::new (static_cast<void*>(values_ + di)) T(std::move(value));
    owner_[di] = s;
    slot.index = di;
    return handle_type{s, slot.generation};
  }

  bool erase(handle_type h) noexcept {
    if (!contains(h)) return false;
    Slot& slot = slots_[h.index];
    const u32 di = slot.index;
    const u32 last = size_ - 1;
    if (di != last) {
      values_[di] = std::move(values_[last]);
      owner_[di] = owner_[last];
      slots_[owner_[di]].index = di;
    }
    values_[last].~T();
    --size_;
    slot.generation = next_generation(slot.generation);
    slot.index = free_head_;
    free_head_ = h.index;
    return true;
  }

  TGF_FORCE_INLINE bool contains(handle_type h) const noexcept {
    return h.generation != 0 && h.index < capacity_ && slots_[h.index].generation == h.generation;
  }

  TGF_FORCE_INLINE T* get(handle_type h) noexcept {
    return contains(h) ? values_ + slots_[h.index].index : nullptr;
  }
  TGF_FORCE_INLINE const T* get(handle_type h) const noexcept {
    return contains(h) ? values_ + slots_[h.index].index : nullptr;
  }

  void clear() noexcept {
    while (size_ > 0) {
      const u32 s = owner_[size_ - 1];
      erase(handle_type{s, slots_[s].generation});
    }
  }

  u32 size() const noexcept { return size_; }
  u32 capacity() const noexcept { return capacity_; }
  u32 growth_events() const noexcept { return growth_events_; }

  T* begin() noexcept { return values_; }
  T* end() noexcept { return values_ + size_; }
  const T* begin() const noexcept { return values_; }
  const T* end() const noexcept { return values_ + size_; }

 private:
  struct Slot {
    u32 generation;
    u32 index;  // dense index while live; next free slot while free
  };
  static constexpr u32 kNone = 0xFFFFFFFFu;

  static constexpr u32 next_generation(u32 g) noexcept { return g + 1 == 0 ? 1 : g + 1; }

  void destroy_storage() noexcept {
    clear();
    aligned_free_bytes(slots_);
    aligned_free_bytes(values_);
    aligned_free_bytes(owner_);
    slots_ = nullptr;
    values_ = nullptr;
    owner_ = nullptr;
    capacity_ = 0;
  }

  Slot* slots_ = nullptr;
  T* values_ = nullptr;
  u32* owner_ = nullptr;  // dense index -> slot index
  u32 size_ = 0;
  u32 capacity_ = 0;
  u32 free_head_ = kNone;
  u32 growth_events_ = 0;
  GrowPolicy policy_;
};

}  // namespace tgf::core
