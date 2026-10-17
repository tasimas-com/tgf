#include <array>
#include <mutex>
#include <tgf/core/module_allocator.hpp>

namespace tgf::core {
namespace {
constexpr u32 kModuleAllocatorSlots = 64;

struct ModuleAllocatorSlot {
  ModuleAllocatorDesc desc{};
  u32 generation = 1;
  u64 outstanding = 0;
  bool active = false;
};

std::array<ModuleAllocatorSlot, kModuleAllocatorSlots> g_slots{};
std::mutex g_slots_mutex;
thread_local u64 g_adapter_allocate_calls = 0;

bool matches(const ModuleAllocatorSlot& slot, ModuleAllocatorHandle handle) noexcept {
  return handle.index < kModuleAllocatorSlots && slot.active && slot.generation == handle.generation;
}

void release_pin(ModuleAllocatorSlot* slot) noexcept {
  std::lock_guard<std::mutex> lock(g_slots_mutex);
  if (slot->outstanding != 0) --slot->outstanding;
}

ModuleAllocatorDesc descriptor_copy(ModuleAllocatorSlot* slot) noexcept {
  // A block may be freed on a different thread from the one that allocated it.
  // Take the registry lock before reading the callback/context pair so the
  // descriptor publication has an explicit happens-before edge on that thread.
  std::lock_guard<std::mutex> lock(g_slots_mutex);
  return slot->desc;
}

void* module_backend_allocate(void* context, usize bytes, usize alignment) noexcept {
  auto* slot = static_cast<ModuleAllocatorSlot*>(context);
  ++g_adapter_allocate_calls;
  const ModuleAllocatorDesc desc = descriptor_copy(slot);
  void* block = desc.allocate(desc.context, bytes, alignment);
  // The pin acquired by module_alloc_bytes() is held by a successful block.
  // If the backend itself fails, release it here; otherwise the paired free
  // callback releases it after the backend deallocator has returned.
  if (!block) release_pin(slot);
  return block;
}

void module_backend_deallocate(void* context, void* block, usize bytes, usize alignment) noexcept {
  auto* slot = static_cast<ModuleAllocatorSlot*>(context);
  const ModuleAllocatorDesc desc = descriptor_copy(slot);
  desc.deallocate(desc.context, block, bytes, alignment);
  release_pin(slot);
}
}  // namespace

Result<ModuleAllocatorHandle> register_module_allocator(const ModuleAllocatorDesc& desc) noexcept {
  if (desc.struct_size < sizeof(ModuleAllocatorDesc) || desc.abi_version != kModuleAllocatorAbiVersion ||
      !desc.allocate || !desc.deallocate)
    return Error::InvalidArgument;

  std::lock_guard<std::mutex> lock(g_slots_mutex);
  for (u32 i = 0; i < kModuleAllocatorSlots; ++i) {
    ModuleAllocatorSlot& slot = g_slots[i];
    if (!slot.active && slot.outstanding == 0) {
      slot.desc = desc;
      slot.active = true;
      return ModuleAllocatorHandle{i, slot.generation};
    }
  }
  return Error::CapacityExceeded;
}

Status unregister_module_allocator(ModuleAllocatorHandle handle) noexcept {
  if (!handle.valid() || handle.index >= kModuleAllocatorSlots) return Error::InvalidArgument;
  std::lock_guard<std::mutex> lock(g_slots_mutex);
  ModuleAllocatorSlot& slot = g_slots[handle.index];
  if (!matches(slot, handle)) return Error::StaleHandle;
  if (slot.outstanding != 0) return Error::Busy;
  slot.active = false;
  slot.desc = {};
  ++slot.generation;
  if (slot.generation == 0) ++slot.generation;
  return {};
}

u64 module_allocator_outstanding_allocations(ModuleAllocatorHandle handle) noexcept {
  if (!handle.valid() || handle.index >= kModuleAllocatorSlots) return 0;
  std::lock_guard<std::mutex> lock(g_slots_mutex);
  const ModuleAllocatorSlot& slot = g_slots[handle.index];
  return matches(slot, handle) ? slot.outstanding : 0;
}

void* module_alloc_bytes(ModuleAllocatorHandle handle, usize size, usize alignment, MemoryTag tag) noexcept {
  if (!handle.valid() || handle.index >= kModuleAllocatorSlots || size == 0 || alignment == 0 ||
      (alignment & (alignment - 1)) != 0)
    return nullptr;

  ModuleAllocatorSlot* slot = nullptr;
  {
    std::lock_guard<std::mutex> lock(g_slots_mutex);
    ModuleAllocatorSlot& candidate = g_slots[handle.index];
    if (!matches(candidate, handle)) return nullptr;
    ++candidate.outstanding;  // pins callbacks until failure or aligned_free_bytes()
    slot = &candidate;
  }

  const u64 calls_before = g_adapter_allocate_calls;
  const ExternalAllocator backend{slot, &module_backend_allocate, &module_backend_deallocate};
  void* result = tracked_external_alloc_bytes(backend, size, alignment, tag);
  // A rejected budget/invalid allocation never calls the backend adapter.
  // In that case no callback released our pin.
  if (!result && g_adapter_allocate_calls == calls_before) release_pin(slot);
  return result;
}

}  // namespace tgf::core
