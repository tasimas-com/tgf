// tgf/core/log.hpp — minimal logging (P1.6.1). Compile-time level filtering,
// replaceable sink, formatting on the stack (no heap).
#pragma once

#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

namespace tgf::core {

enum class LogLevel : u8 { Trace = 0, Debug, Info, Warn, Error, Fatal, Off };

// The sink receives a fully formatted, NUL-terminated message. It may be called
// from any thread and must not call back into the logger.
using LogSink = void (*)(LogLevel level, const char* message, void* user) noexcept;

// Passing nullptr restores the default stderr sink.
TGF_API void set_log_sink(LogSink sink, void* user) noexcept;
TGF_API void set_log_level(LogLevel min_level) noexcept;
TGF_API LogLevel log_level() noexcept;
TGF_API void log_write(LogLevel level, const char* fmt, ...) noexcept TGF_PRINTF_LIKE(2, 3);

}  // namespace tgf::core

#if !defined(TGF_LOG_COMPILE_LEVEL)
#define TGF_LOG_COMPILE_LEVEL 0  // 0 = keep everything; raise to strip lower levels at compile time
#endif

namespace tgf::core {
constexpr int log_compile_level = TGF_LOG_COMPILE_LEVEL;
}

// The level is compared through a named constant so the always-true comparison at the
// default compile level does not trip -Wtype-limits in user code.
#define TGF_LOG(level, ...)                                                                         \
  do {                                                                                              \
    if constexpr (static_cast<int>(::tgf::core::LogLevel::level) >= ::tgf::core::log_compile_level) \
      ::tgf::core::log_write(::tgf::core::LogLevel::level, __VA_ARGS__);                            \
  } while (0)
