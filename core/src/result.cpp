#include <tgf/core/result.hpp>

namespace tgf::core {

const char* error_name(Error e) noexcept {
  switch (e) {
    case Error::None:
      return "None";
    case Error::OutOfMemory:
      return "OutOfMemory";
    case Error::InvalidArgument:
      return "InvalidArgument";
    case Error::CapacityExceeded:
      return "CapacityExceeded";
    case Error::StaleHandle:
      return "StaleHandle";
    case Error::NotFound:
      return "NotFound";
    case Error::Unsupported:
      return "Unsupported";
    case Error::Overflow:
      return "Overflow";
    case Error::Busy:
      return "Busy";
  }
  return "Unknown";
}

}  // namespace tgf::core
