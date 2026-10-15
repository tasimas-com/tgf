// tgf/core/hash.hpp — constexpr string hashing for ids and style keys (P1.3.4, P1.7).
// FNV-1a 64: tiny, constexpr, adequate for short identifiers. Bulk-data hashing
// (xxhash-class) arrives with the asset/resource system.
#pragma once

#include <tgf/core/types.hpp>

#include <string_view>

namespace tgf::core {

constexpr u64 kFnvOffset = 0xcbf29ce484222325ull;
constexpr u64 kFnvPrime = 0x100000001b3ull;

constexpr u64 fnv1a64(const char* data, usize size, u64 seed = kFnvOffset) noexcept {
  u64 h = seed;
  for (usize i = 0; i < size; ++i) {
    h ^= static_cast<u64>(static_cast<u8>(data[i]));
    h *= kFnvPrime;
  }
  return h;
}

constexpr u64 fnv1a64(std::string_view s, u64 seed = kFnvOffset) noexcept { return fnv1a64(s.data(), s.size(), seed); }

constexpr u64 hash_combine(u64 a, u64 b) noexcept {
  a ^= b + 0x9e3779b97f4a7c15ull + (a << 6) + (a >> 2);
  return a;
}

}  // namespace tgf::core
