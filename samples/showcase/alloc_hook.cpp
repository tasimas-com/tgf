#if !defined(TGF_SHOWCASE_MEMORY_SANITIZER)
// Routes the showcase's global C++ allocations through TGF's tagged allocator.
// This gives the verification executable process-wide live-byte/leak accounting,
// rather than merely counting calls to operator new. Production hosts may install
// an equivalent hook or explicitly use aligned_alloc_bytes at subsystem boundaries.
#include <tgf/core/memory.hpp>

#include <new>

void* operator new(std::size_t n) {
  if (void* p = tgf::core::aligned_alloc_bytes(n ? n : 1, alignof(std::max_align_t))) return p;
  throw std::bad_alloc();
}
void* operator new[](std::size_t n) { return operator new(n); }
void* operator new(std::size_t n, std::align_val_t a) {
  if (void* p = tgf::core::aligned_alloc_bytes(n ? n : 1, static_cast<std::size_t>(a))) return p;
  throw std::bad_alloc();
}
void* operator new[](std::size_t n, std::align_val_t a) { return operator new(n, a); }

void operator delete(void* p) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete[](void* p) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete(void* p, std::size_t) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete[](void* p, std::size_t) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete(void* p, std::align_val_t) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete[](void* p, std::align_val_t) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete(void* p, std::size_t, std::align_val_t) noexcept { tgf::core::aligned_free_bytes(p); }
void operator delete[](void* p, std::size_t, std::align_val_t) noexcept { tgf::core::aligned_free_bytes(p); }

#endif  // !TGF_SHOWCASE_MEMORY_SANITIZER
