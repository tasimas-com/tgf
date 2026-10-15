# TGF — TASIMAS GUI Framework

**Repository:** https://github.com/tasimas-com/tgf  
**Organization:** TASIMAS  
**Language:** C++20  
**Build system:** CMake 3.25+  

TGF is intended to become a modular, retained-mode, data-oriented, cross-platform GUI framework for large professional applications and games.

## Project status

The current project is an early implementation of the `tgf::core` foundation. It is **not yet a complete graphical UI framework**: native platform windows, rendering backends, typography, retained UI, widgets, and professional components remain future implementation phases.

The authoritative development sequence and completion criteria are in [TODO.md](TODO.md). Phase 0 must be completed before Phase 1 receives new feature-development priority.

## Start here

- [Master TODO and roadmap](TODO.md)
- [Build instructions](docs/BUILDING.md)
- [Architecture and design](docs/DESIGN.md)
- [Current status](docs/STATUS.md)
- [Compiler support policy](docs/COMPILER_SUPPORT.md)
- [CI guide](docs/CI.md)

## Local build

Use the documented CMake presets and run the registered CTest suite. A passing local build does not count as hosted Windows/Linux/macOS verification; those results are recorded separately in the TODO and CI reports.

## Development rule

A task is marked complete only when its required implementation, tests, documentation, and evidence exist. Incomplete or unverified platform work remains explicitly partial.
