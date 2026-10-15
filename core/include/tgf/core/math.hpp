// tgf/core/math.hpp — vectors, rectangles, colour, and the camera-relative
// double -> float conversion mandated by ADR-0017 (P1.4.1, P1.4.3).
//
// Rule: domain coordinates (time, infinite canvas, score pages) are f64/i64.
// Floats are for screen space *after* subtracting a camera origin.
#pragma once

#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

namespace tgf::core {

struct Vec2f {
  f32 x = 0, y = 0;
  friend constexpr Vec2f operator+(Vec2f a, Vec2f b) noexcept { return {a.x + b.x, a.y + b.y}; }
  friend constexpr Vec2f operator-(Vec2f a, Vec2f b) noexcept { return {a.x - b.x, a.y - b.y}; }
  friend constexpr Vec2f operator*(Vec2f a, f32 s) noexcept { return {a.x * s, a.y * s}; }
  friend constexpr bool operator==(Vec2f, Vec2f) = default;
};

struct Vec2d {
  f64 x = 0, y = 0;
  friend constexpr Vec2d operator+(Vec2d a, Vec2d b) noexcept { return {a.x + b.x, a.y + b.y}; }
  friend constexpr Vec2d operator-(Vec2d a, Vec2d b) noexcept { return {a.x - b.x, a.y - b.y}; }
  friend constexpr Vec2d operator*(Vec2d a, f64 s) noexcept { return {a.x * s, a.y * s}; }
  friend constexpr bool operator==(Vec2d, Vec2d) = default;
};

struct Rectf {
  f32 x = 0, y = 0, w = 0, h = 0;
  constexpr f32 right() const noexcept { return x + w; }
  constexpr f32 bottom() const noexcept { return y + h; }
  constexpr bool contains(Vec2f p) const noexcept { return p.x >= x && p.y >= y && p.x < right() && p.y < bottom(); }
  constexpr bool intersects(const Rectf& o) const noexcept {
    return x < o.right() && o.x < right() && y < o.bottom() && o.y < bottom();
  }
  friend constexpr bool operator==(const Rectf&, const Rectf&) = default;
};

struct Rectd {
  f64 x = 0, y = 0, w = 0, h = 0;
  friend constexpr bool operator==(const Rectd&, const Rectd&) = default;
};

// Camera-relative conversion: subtract the origin in double precision, scale, and
// only then narrow to float. The subtraction is exact enough that the float result
// keeps sub-pixel accuracy at any absolute position.
constexpr Vec2f to_camera_relative(Vec2d p, Vec2d origin, f64 scale) noexcept {
  return {static_cast<f32>((p.x - origin.x) * scale), static_cast<f32>((p.y - origin.y) * scale)};
}

// Colour is stored linear, premultiplied alpha — what the GPU blends in.
struct Color {
  f32 r = 0, g = 0, b = 0, a = 1;
  friend constexpr bool operator==(const Color&, const Color&) = default;
};

TGF_API f32 srgb_to_linear(f32 c) noexcept;
TGF_API f32 linear_to_srgb(f32 c) noexcept;
TGF_API Color color_from_srgb8(u8 r, u8 g, u8 b, u8 a = 255) noexcept;  // returns premultiplied linear

}  // namespace tgf::core
