// tgf/core/types.hpp — fixed-width types, generational handles, strong typedefs
// (P1.1.2). Header-only, no allocation.
#pragma once

#include <compare>
#include <cstddef>
#include <cstdint>
#include <tgf/core/config.hpp>
#include <type_traits>

namespace tgf {

using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using i8 = std::int8_t;
using i16 = std::int16_t;
using i32 = std::int32_t;
using i64 = std::int64_t;
using f32 = float;
using f64 = double;
using usize = std::size_t;

}  // namespace tgf

namespace tgf::core {

// Opaque, generational handle. generation == 0 means "invalid", so a
// value-initialised Handle is always safely invalid. 8 bytes, trivially copyable:
// safe to pass across the future C ABI and through lock-free queues.
template <class Tag>
struct Handle {
  u32 index = 0;
  u32 generation = 0;

  constexpr bool valid() const noexcept { return generation != 0; }
  friend constexpr bool operator==(Handle, Handle) = default;
};
static_assert(sizeof(Handle<int>) == 8);
static_assert(std::is_trivially_copyable_v<Handle<int>>);

// Zero-cost strong typedef: stops Dip/Px/Seconds being mixed by accident.
template <class T, class Tag>
struct Strong {
  T value{};

  constexpr Strong() = default;
  constexpr explicit Strong(T v) noexcept : value(v) {}

  friend constexpr auto operator<=>(Strong, Strong) = default;
  friend constexpr Strong operator+(Strong a, Strong b) noexcept { return Strong{a.value + b.value}; }
  friend constexpr Strong operator-(Strong a, Strong b) noexcept { return Strong{a.value - b.value}; }
  friend constexpr Strong operator*(Strong a, T s) noexcept { return Strong{a.value * s}; }
  friend constexpr Strong operator*(T s, Strong a) noexcept { return Strong{s * a.value}; }
};

struct DipTag;      // device-independent pixels (layout space, ADR-0017)
struct PxTag;       // physical device pixels
struct SecondsTag;  // wall-clock seconds (UI animation time)

using Dip = Strong<f32, DipTag>;
using Px = Strong<f32, PxTag>;
using Seconds = Strong<f64, SecondsTag>;

static_assert(sizeof(Dip) == sizeof(f32));
static_assert(std::is_trivially_copyable_v<Dip>);

}  // namespace tgf::core
