// tgf/core/mapped_file.hpp — portable read-only/read-write file mappings (P1.2.5).
#pragma once

#include <cstdint>
#include <tgf/core/config.hpp>
#include <tgf/core/types.hpp>

namespace tgf::core {

enum class MappedFileAccess : u8 { ReadOnly, ReadWrite };

// Maps a whole file into the process address space. The OS controls which pages
// become resident; a mapping is not a promise that the entire file fits in RAM.
// Paths are UTF-8 on every platform. Empty files open successfully with size()==0
// and data()==nullptr. This class is not thread-safe.
class TGF_API MappedFile {
 public:
  MappedFile() noexcept = default;
  ~MappedFile() noexcept { close(); }
  MappedFile(const MappedFile&) = delete;
  MappedFile& operator=(const MappedFile&) = delete;
  MappedFile(MappedFile&& other) noexcept;
  MappedFile& operator=(MappedFile&& other) noexcept;

  bool open(const char* utf8_path, MappedFileAccess access = MappedFileAccess::ReadOnly) noexcept;
  void close() noexcept;
  bool flush() noexcept;

  const void* data() const noexcept { return view_; }
  void* writable_data() noexcept { return access_ == MappedFileAccess::ReadWrite ? view_ : nullptr; }
  usize size() const noexcept { return size_; }
  bool is_open() const noexcept { return file_handle_ != -1; }
  MappedFileAccess access() const noexcept { return access_; }

 private:
  std::intptr_t file_handle_ = -1;
  void* mapping_handle_ = nullptr;
  void* view_ = nullptr;
  usize size_ = 0;
  MappedFileAccess access_ = MappedFileAccess::ReadOnly;
};

}  // namespace tgf::core
