#include <cstdlib>
#include <cstring>
#include <limits>
#include <tgf/core/mapped_file.hpp>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace tgf::core {

MappedFile::MappedFile(MappedFile&& other) noexcept
    : file_handle_(other.file_handle_),
      mapping_handle_(other.mapping_handle_),
      view_(other.view_),
      size_(other.size_),
      access_(other.access_) {
  other.file_handle_ = -1;
  other.mapping_handle_ = nullptr;
  other.view_ = nullptr;
  other.size_ = 0;
}

MappedFile& MappedFile::operator=(MappedFile&& other) noexcept {
  if (this == &other) return *this;
  close();
  file_handle_ = other.file_handle_;
  mapping_handle_ = other.mapping_handle_;
  view_ = other.view_;
  size_ = other.size_;
  access_ = other.access_;
  other.file_handle_ = -1;
  other.mapping_handle_ = nullptr;
  other.view_ = nullptr;
  other.size_ = 0;
  return *this;
}

bool MappedFile::open(const char* utf8_path, MappedFileAccess access) noexcept {
  close();
  if (!utf8_path || utf8_path[0] == '\0' ||
      (access != MappedFileAccess::ReadOnly && access != MappedFileAccess::ReadWrite))
    return false;

#if defined(_WIN32)
  const usize utf8_length = std::strlen(utf8_path);
  if (utf8_length > static_cast<usize>((std::numeric_limits<int>::max)())) return false;
  const int wide_length =
      MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, utf8_path, static_cast<int>(utf8_length), nullptr, 0);
  if (wide_length <= 0) return false;
  const usize wide_bytes = (static_cast<usize>(wide_length) + 1) * sizeof(wchar_t);
  auto* wide_path = static_cast<wchar_t*>(std::malloc(wide_bytes));
  if (!wide_path) return false;
  const int converted = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, utf8_path, static_cast<int>(utf8_length),
                                            wide_path, wide_length);
  if (converted != wide_length) {
    std::free(wide_path);
    return false;
  }
  wide_path[wide_length] = L'\0';

  const DWORD desired = GENERIC_READ | (access == MappedFileAccess::ReadWrite ? GENERIC_WRITE : 0);
  HANDLE file =
      CreateFileW(wide_path, desired, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
  std::free(wide_path);
  if (file == INVALID_HANDLE_VALUE) return false;
  LARGE_INTEGER file_size{};
  if (!GetFileSizeEx(file, &file_size) || file_size.QuadPart < 0 ||
      static_cast<unsigned long long>(file_size.QuadPart) >
          static_cast<unsigned long long>(std::numeric_limits<usize>::max())) {
    CloseHandle(file);
    return false;
  }
  file_handle_ = reinterpret_cast<std::intptr_t>(file);
  size_ = static_cast<usize>(file_size.QuadPart);
  access_ = access;
  if (size_ == 0) return true;

  const DWORD protection = access == MappedFileAccess::ReadWrite ? PAGE_READWRITE : PAGE_READONLY;
  HANDLE mapping = CreateFileMappingW(file, nullptr, protection, 0, 0, nullptr);
  if (!mapping) {
    close();
    return false;
  }
  const DWORD map_access = access == MappedFileAccess::ReadWrite ? FILE_MAP_WRITE : FILE_MAP_READ;
  void* view = MapViewOfFile(mapping, map_access, 0, 0, 0);
  if (!view) {
    CloseHandle(mapping);
    close();
    return false;
  }
  mapping_handle_ = mapping;
  view_ = view;
  return true;
#else
  const unsigned int flags = static_cast<unsigned int>(access == MappedFileAccess::ReadWrite ? O_RDWR : O_RDONLY);
#ifdef O_CLOEXEC
  const int file = ::open(utf8_path, static_cast<int>(flags | static_cast<unsigned int>(O_CLOEXEC)));
#else
  const int file = ::open(utf8_path, static_cast<int>(flags));
#endif
  if (file < 0) return false;
  struct stat info{};
  if (::fstat(file, &info) != 0 || info.st_size < 0 ||
      static_cast<unsigned long long>(info.st_size) >
          static_cast<unsigned long long>(std::numeric_limits<usize>::max())) {
    ::close(file);
    return false;
  }
  file_handle_ = static_cast<std::intptr_t>(file);
  size_ = static_cast<usize>(info.st_size);
  access_ = access;
  if (size_ == 0) return true;
  const int protection = PROT_READ | (access == MappedFileAccess::ReadWrite ? PROT_WRITE : 0);
  void* view = ::mmap(nullptr, size_, protection, MAP_SHARED, file, 0);
  if (view == MAP_FAILED) {
    close();
    return false;
  }
  view_ = view;
  return true;
#endif
}

void MappedFile::close() noexcept {
#if defined(_WIN32)
  if (view_) UnmapViewOfFile(view_);
  if (mapping_handle_) CloseHandle(static_cast<HANDLE>(mapping_handle_));
  if (file_handle_ != -1) CloseHandle(reinterpret_cast<HANDLE>(file_handle_));
#else
  if (view_ && size_ != 0) ::munmap(view_, size_);
  if (file_handle_ != -1) ::close(static_cast<int>(file_handle_));
#endif
  file_handle_ = -1;
  mapping_handle_ = nullptr;
  view_ = nullptr;
  size_ = 0;
}

bool MappedFile::flush() noexcept {
  if (!is_open()) return false;
  if (access_ == MappedFileAccess::ReadOnly || size_ == 0) return true;
#if defined(_WIN32)
  return FlushViewOfFile(view_, size_) != 0 && FlushFileBuffers(reinterpret_cast<HANDLE>(file_handle_)) != 0;
#else
  return ::msync(view_, size_, MS_SYNC) == 0;
#endif
}

}  // namespace tgf::core
