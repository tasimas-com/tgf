#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <tgf/core/log.hpp>

namespace tgf::core {

namespace {
struct SinkState {
  LogSink fn;
  void* user;
};
std::atomic<SinkState*> g_sink{nullptr};  // nullptr -> default stderr sink
std::atomic<u8> g_level{static_cast<u8>(LogLevel::Info)};
SinkState g_sink_storage;

const char* level_name(LogLevel l) noexcept {
  switch (l) {
    case LogLevel::Trace:
      return "TRACE";
    case LogLevel::Debug:
      return "DEBUG";
    case LogLevel::Info:
      return "INFO ";
    case LogLevel::Warn:
      return "WARN ";
    case LogLevel::Error:
      return "ERROR";
    case LogLevel::Fatal:
      return "FATAL";
    default:
      return "?";
  }
}
}  // namespace

void set_log_sink(LogSink sink, void* user) noexcept {
  // Intended to be called at startup before logging threads run.
  if (!sink) {
    g_sink.store(nullptr, std::memory_order_release);
    return;
  }
  g_sink_storage = SinkState{sink, user};
  g_sink.store(&g_sink_storage, std::memory_order_release);
}

void set_log_level(LogLevel l) noexcept {
  g_level.store(static_cast<u8>(l), std::memory_order_relaxed);
}
LogLevel log_level() noexcept {
  return static_cast<LogLevel>(g_level.load(std::memory_order_relaxed));
}

void log_write(LogLevel level, const char* fmt, ...) noexcept {
  if (static_cast<u8>(level) < g_level.load(std::memory_order_relaxed)) return;
  char buf[512];
  std::va_list args;
  va_start(args, fmt);
  std::vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  if (const SinkState* s = g_sink.load(std::memory_order_acquire)) {
    s->fn(level, buf, s->user);
  } else {
    std::fprintf(stderr, "[tgf %s] %s\n", level_name(level), buf);
  }
}

}  // namespace tgf::core
