cmake_minimum_required(VERSION 3.25)
project(TGF VERSION 0.1.0 DESCRIPTION "TASIMAS GUI Framework" LANGUAGES CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# ---- options (ADR-0028, ADR-0029) ---------------------------------------------
option(TGF_BUILD_SHARED     "Build TGF as shared libraries (.dll/.so/.dylib). Default is static (.lib/.a)." OFF)
option(TGF_BUILD_SHOWCASE   "Build the tgf_showcase verification executable"                              ON)
option(TGF_BUILD_TESTS      "Register CTest tests (showcase checks, dependency DAG, header hygiene)"      ON)
option(TGF_WARNINGS_AS_ERRORS "Treat warnings as errors"                                                  ON)
option(TGF_ENABLE_LTO       "Enable link-time optimisation in Release builds"                             ON)
option(TGF_PROFILE          "Compile TGF_ZONE instrumentation (default: on outside Release)"              OFF)
set(TGF_SANITIZER "None" CACHE STRING "Sanitizer: None, Address, Undefined, Thread, Memory, or AddressUndefined")
set_property(CACHE TGF_SANITIZER PROPERTY STRINGS None Address Undefined Thread Memory AddressUndefined)
if(NOT TGF_SANITIZER MATCHES "^(None|Address|Undefined|Thread|Memory|AddressUndefined)$")
  message(FATAL_ERROR "Unsupported TGF_SANITIZER='${TGF_SANITIZER}'. See TGF_SANITIZER cache documentation.")
endif()
option(TGF_NATIVE_ARCH      "Tune for the build machine (-march=native). NEVER for distributed binaries." OFF)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Everything lands in <build>/bin (exe + dll side by side) and <build>/lib (static libs / import libs).
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

include(TgfCompileOptions)
include(TgfQualityTools)

add_subdirectory(core)

if(TGF_BUILD_SHOWCASE)
  add_subdirectory(samples/showcase)
endif()

if(TGF_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()

include(TgfInstall)
