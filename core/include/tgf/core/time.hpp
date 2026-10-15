// tgf/core/time.hpp — sample-accurate time (P1.4.5, ADR-0017).
// Timeline positions are integer sample counts, never floats. 100 hours at
// 192 kHz is 6.9e10 samples: far beyond f32's 2^24 exact range, comfortably
// inside i64.
#pragma once

#include <tgf/core/result.hpp>
#include <tgf/core/types.hpp>

#include <limits>

namespace tgf::core {

struct SampleTime {
  i64 samples = 0;
  friend constexpr auto operator<=>(SampleTime, SampleTime) = default;
};

constexpr Result<SampleTime> checked_add(SampleTime a, SampleTime b) noexcept {
  constexpr i64 kMax = std::numeric_limits<i64>::max();
  constexpr i64 kMin = std::numeric_limits<i64>::min();
  if ((b.samples > 0 && a.samples > kMax - b.samples) || (b.samples < 0 && a.samples < kMin - b.samples))
    return Error::Overflow;
  return SampleTime{a.samples + b.samples};
}

constexpr Result<SampleTime> checked_sub(SampleTime a, SampleTime b) noexcept {
  constexpr i64 kMax = std::numeric_limits<i64>::max();
  constexpr i64 kMin = std::numeric_limits<i64>::min();
  if ((b.samples < 0 && a.samples > kMax + b.samples) || (b.samples > 0 && a.samples < kMin + b.samples))
    return Error::Overflow;
  return SampleTime{a.samples - b.samples};
}

// A zero sample rate is invalid; callers must check the Result before using it.
constexpr Result<f64> to_seconds(SampleTime t, u32 sample_rate) noexcept {
  if (sample_rate == 0) return Error::InvalidArgument;
  return static_cast<f64>(t.samples) / static_cast<f64>(sample_rate);
}

}  // namespace tgf::core
