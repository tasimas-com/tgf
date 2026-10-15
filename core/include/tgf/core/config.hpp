// tgf/core/config.hpp — compiler/platform abstraction (P1.1.1).
// Macro-only, no includes: safe to include from anywhere.
#pragma once

#define TGF_VERSION_MAJOR 0
#define TGF_VERSION_MINOR 1
#define TGF_VERSION_PATCH 0
#define TGF_VERSION_STRING "0.1.0"

// ---- compiler ---------------------------------------------------------------
#if defined(_MSC_VER)
#define TGF_COMPILER_MSVC 1
#elif defined(__clang__)
#define TGF_COMPILER_CLANG 1
#elif defined(__GNUC__)
#define TGF_COMPILER_GCC 1
#else
#error "TGF: unsupported compiler (need MSVC, Clang or GCC)"
#endif

// ---- symbol export (ADR-0028) ------------------------------------------------
// Static builds (the default) export nothing. Shared builds define TGF_SHARED
// publicly and TGF_BUILDING while compiling the library itself.
#if defined(TGF_SHARED)
#if defined(_WIN32)
#if defined(TGF_BUILDING)
#define TGF_API __declspec(dllexport)
#else
#define TGF_API __declspec(dllimport)
#endif
#else
#define TGF_API __attribute__((visibility("default")))
#endif
#else
#define TGF_API
#endif

// ---- inlining / branch hints -------------------------------------------------
#if defined(TGF_COMPILER_MSVC)
#define TGF_FORCE_INLINE __forceinline
#define TGF_NOINLINE __declspec(noinline)
#define TGF_UNREACHABLE() __assume(0)
#define TGF_LIKELY(x) (x)
#define TGF_UNLIKELY(x) (x)
#else
#define TGF_FORCE_INLINE inline __attribute__((always_inline))
#define TGF_NOINLINE __attribute__((noinline))
#define TGF_UNREACHABLE() __builtin_unreachable()
#define TGF_LIKELY(x) __builtin_expect(!!(x), 1)
#define TGF_UNLIKELY(x) __builtin_expect(!!(x), 0)
#endif

// ---- misc ---------------------------------------------------------------------
#define TGF_CACHE_LINE_SIZE 64  // fixed on purpose: layout must not vary by compiler

#define TGF_CONCAT_IMPL(a, b) a##b
#define TGF_CONCAT(a, b) TGF_CONCAT_IMPL(a, b)

#if defined(__GNUC__) || defined(__clang__)
#define TGF_PRINTF_LIKE(fmt_idx, first_arg) __attribute__((format(printf, fmt_idx, first_arg)))
#else
#define TGF_PRINTF_LIKE(fmt_idx, first_arg)
#endif

// Asserts are on in debug builds unless overridden with -DTGF_ASSERT_ENABLED=0/1.
#if !defined(TGF_ASSERT_ENABLED)
#if defined(NDEBUG)
#define TGF_ASSERT_ENABLED 0
#else
#define TGF_ASSERT_ENABLED 1
#endif
#endif

// Profiler zones compile to nothing unless TGF_PROFILE_ENABLED=1 (set by CMake option).
#if !defined(TGF_PROFILE_ENABLED)
#define TGF_PROFILE_ENABLED 0
#endif
