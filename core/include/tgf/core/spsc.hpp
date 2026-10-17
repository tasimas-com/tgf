// tgf/core/spsc.hpp — real-time-safe cross-thread primitives (P1.5.1, P1.5.5, ADR-0022).
//
// Both types have bounded data-path code, no dynamic allocation, and no mutexes.
// Their atomic types must be always-lock-free on the target (enforced below).
// Important: the C++ standard's lock-free guarantee is not itself a formal
// wait-free or hard-realtime deadline guarantee. Do not claim universal
// wait-freedom; validate generated code and timing on each supported target.
// Callers must construct and pre-touch these objects before entering callbacks.
#pragma once

#include <atomic>
#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>
#include <type_traits>

// MSVC C4324 ("structure was padded due to alignment specifier") is reported for every
// type below. The padding is the point: producer and consumer state sit on separate cache
// lines to avoid false sharing. Silenced here so every consumer of this header is clean,
// whatever warning flags their project uses.
#if defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4324)
#endif

namespace tgf::core {

// Bounded single-producer / single-consumer ring buffer. N must be a power of two.
// Producer-side and consumer-side state live on separate cache lines and each side
// caches the other's index, so the common case touches no shared line at all.
template <class T, usize N>
class SpscQueue {
  static_assert(N >= 2 && (N & (N - 1)) == 0, "SpscQueue capacity must be a power of two");
  static_assert(std::is_trivially_copyable_v<T>, "SpscQueue<T>: T must be trivially copyable");
  static_assert(std::atomic<usize>::is_always_lock_free,
                "SpscQueue requires always-lock-free size_t atomics on this target");

 public:
  SpscQueue() = default;
  SpscQueue(const SpscQueue&) = delete;
  SpscQueue& operator=(const SpscQueue&) = delete;

  // Producer thread only.
  bool try_push(const T& v) noexcept {
    const usize h = head_.load(std::memory_order_relaxed);
    if (h - tail_cache_ == N) {
      tail_cache_ = tail_.load(std::memory_order_acquire);
      if (h - tail_cache_ == N) return false;
    }
    buf_[h & (N - 1)] = v;
    head_.store(h + 1, std::memory_order_release);
    return true;
  }

  // Consumer thread only.
  bool try_pop(T& out) noexcept {
    const usize t = tail_.load(std::memory_order_relaxed);
    if (t == head_cache_) {
      head_cache_ = head_.load(std::memory_order_acquire);
      if (t == head_cache_) return false;
    }
    out = buf_[t & (N - 1)];
    tail_.store(t + 1, std::memory_order_release);
    return true;
  }

  static constexpr usize capacity() noexcept { return N; }
  bool atomics_are_lock_free() const noexcept { return head_.is_lock_free() && tail_.is_lock_free(); }

 private:
  alignas(TGF_CACHE_LINE_SIZE) std::atomic<usize> head_{0};
  usize tail_cache_ = 0;  // producer's cached view of tail_
  alignas(TGF_CACHE_LINE_SIZE) std::atomic<usize> tail_{0};
  usize head_cache_ = 0;  // consumer's cached view of head_
  alignas(TGF_CACHE_LINE_SIZE) T buf_[N]{};
};

// Latest-value channel (playhead position, meter levels): the writer never waits,
// the reader always gets the newest complete value, nobody sees a torn write.
// Triple-buffered latest-value exchange. One writer thread, one reader thread.
// The bounded algorithm uses lock-free atomics on supported targets, but does not
// promise a portable formal wait-free bound from the C++ memory model alone.
template <class T>
class TripleBuffer {
  static_assert(std::is_trivially_copyable_v<T>, "TripleBuffer<T>: T must be trivially copyable");
  static_assert(std::atomic<u32>::is_always_lock_free,
                "TripleBuffer requires always-lock-free uint32_t atomics on this target");

 public:
  TripleBuffer() = default;
  TripleBuffer(const TripleBuffer&) = delete;
  TripleBuffer& operator=(const TripleBuffer&) = delete;

  // Writer: fill the back slot in place, then publish().
  T& write_slot() noexcept { return slots_[back_]; }
  void publish() noexcept {
    const u32 old = shared_.exchange(back_ | kDirty, std::memory_order_acq_rel);
    back_ = old & 3u;
  }
  void publish(const T& v) noexcept {
    slots_[back_] = v;
    publish();
  }

  // Reader: returns the newest published value; *fresh (optional) says whether it
  // changed since the previous call.
  bool atomics_are_lock_free() const noexcept { return shared_.is_lock_free(); }

  const T& read(bool* fresh = nullptr) noexcept {
    bool got = false;
    if (shared_.load(std::memory_order_relaxed) & kDirty) {
      const u32 old = shared_.exchange(front_, std::memory_order_acq_rel);
      front_ = old & 3u;
      got = true;
    }
    if (fresh) *fresh = got;
    return slots_[front_];
  }

 private:
  static constexpr u32 kDirty = 4u;

  alignas(TGF_CACHE_LINE_SIZE) T slots_[3]{};
  alignas(TGF_CACHE_LINE_SIZE) std::atomic<u32> shared_{1};  // index of the middle slot (+dirty bit)
  alignas(TGF_CACHE_LINE_SIZE) u32 back_ = 2;                // writer-owned
  alignas(TGF_CACHE_LINE_SIZE) u32 front_ = 0;               // reader-owned
};

}  // namespace tgf::core

#if defined(_MSC_VER)
#pragma warning(pop)
#endif
