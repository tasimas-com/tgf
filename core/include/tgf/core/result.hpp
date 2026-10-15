// tgf/core/result.hpp — exception-free error model (P1.1.4, ADR-0001).
// Result<T> holds either a value or an Error. T must be trivially copyable and
// default constructible so a Result is cheap, constexpr-friendly and can cross
// lock-free queues; larger payloads travel through handles or out-parameters.
#pragma once

#include <tgf/core/assert.hpp>
#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

#include <type_traits>

namespace tgf::core {

enum class Error : u16 {
  None = 0,
  OutOfMemory,
  InvalidArgument,
  CapacityExceeded,
  StaleHandle,
  NotFound,
  Unsupported,
  Overflow,
  Busy,
};

TGF_API const char* error_name(Error e) noexcept;

template <class T>
class [[nodiscard]] Result {
  static_assert(std::is_trivially_copyable_v<T>, "Result<T>: T must be trivially copyable");
  static_assert(std::is_default_constructible_v<T>, "Result<T>: T must be default constructible");

 public:
  constexpr Result(T value) noexcept : value_(value) {}
  constexpr Result(Error error) noexcept : error_(error) {}

  constexpr bool ok() const noexcept { return error_ == Error::None; }
  constexpr explicit operator bool() const noexcept { return ok(); }
  constexpr Error error() const noexcept { return error_; }

  constexpr const T& value() const noexcept {
    TGF_ASSERT(ok(), "Result::value() called on an error");
    return value_;
  }
  constexpr T value_or(T fallback) const noexcept { return ok() ? value_ : fallback; }

 private:
  T value_{};
  Error error_ = Error::None;
};

// Result without a payload.
class [[nodiscard]] Status {
 public:
  constexpr Status() noexcept = default;
  constexpr Status(Error error) noexcept : error_(error) {}
  constexpr bool ok() const noexcept { return error_ == Error::None; }
  constexpr explicit operator bool() const noexcept { return ok(); }
  constexpr Error error() const noexcept { return error_; }

 private:
  Error error_ = Error::None;
};

}  // namespace tgf::core
