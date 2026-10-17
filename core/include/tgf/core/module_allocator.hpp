// tgf/core/module_allocator.hpp — cross-module allocator ownership (P1.2.5).
#pragma once

#include <tgf/core/config.hpp>
#include <tgf/core/memory.hpp>
#include <tgf/core/result.hpp>
#include <tgf/core/types.hpp>

namespace tgf::core {

inline constexpr u32 kModuleAllocatorAbiVersion = 1;

struct ModuleAllocatorDesc {
  u32 struct_size;
  u32 abi_version;
  void* context;
  ExternalAllocateFn allocate;
  ExternalDeallocateFn deallocate;

  constexpr ModuleAllocatorDesc() noexcept
      : struct_size(static_cast<u32>(sizeof(ModuleAllocatorDesc))),
        abi_version(kModuleAllocatorAbiVersion),
        context(nullptr),
        allocate(nullptr),
        deallocate(nullptr) {}
};

struct ModuleAllocatorHandle {
  u32 index = 0xFFFFFFFFu;
  u32 generation = 0;
  constexpr bool valid() const noexcept { return index != 0xFFFFFFFFu && generation != 0; }
};
static_assert(sizeof(ModuleAllocatorHandle) == 8);

// The registry is fixed-capacity and allocation-free. A module must successfully
// unregister before it unloads. Unregister returns Error::Busy while any wrapped
// allocations are outstanding, preventing TGF from retaining callbacks into an
// unloaded DLL/shared library/plugin.
TGF_API Result<ModuleAllocatorHandle> register_module_allocator(const ModuleAllocatorDesc& desc) noexcept;
TGF_API Status unregister_module_allocator(ModuleAllocatorHandle handle) noexcept;
TGF_API u64 module_allocator_outstanding_allocations(ModuleAllocatorHandle handle) noexcept;

// Allocations are owned by the registered module allocator but tracked by TGF.
// Release only with aligned_free_bytes(); the wrapper routes the raw block back
// through the matching module callback before its registration can be removed.
TGF_API void* module_alloc_bytes(ModuleAllocatorHandle allocator, usize size, usize alignment, MemoryTag tag) noexcept;

}  // namespace tgf::core
