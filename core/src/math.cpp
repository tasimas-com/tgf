#include <cmath>
#include <tgf/core/math.hpp>

namespace tgf::core {

f32 srgb_to_linear(f32 c) noexcept {
  return c <= 0.04045f ? c / 12.92f : std::pow((c + 0.055f) / 1.055f, 2.4f);
}

f32 linear_to_srgb(f32 c) noexcept {
  return c <= 0.0031308f ? c * 12.92f : 1.055f * std::pow(c, 1.0f / 2.4f) - 0.055f;
}

Color color_from_srgb8(u8 r, u8 g, u8 b, u8 a) noexcept {
  const f32 alpha = static_cast<f32>(a) / 255.0f;
  return Color{srgb_to_linear(static_cast<f32>(r) / 255.0f) * alpha,
               srgb_to_linear(static_cast<f32>(g) / 255.0f) * alpha,
               srgb_to_linear(static_cast<f32>(b) / 255.0f) * alpha, alpha};
}

}  // namespace tgf::core
