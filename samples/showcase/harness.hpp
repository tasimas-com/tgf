// Showcase harness: tiny, dependency-free check + benchmark registry.
// Each phase adds a new checks_<module>.cpp / bench_<module>.cpp and registers it here,
// so one executable always shows the state of EVERYTHING built so far (ADR-0030).
#pragma once

#include <string>
#include <tgf/core/types.hpp>
#include <vector>

namespace showcase {

struct Context {
  std::string note;  // human-readable evidence for the report line
};

using CheckFn = bool (*)(Context&);
struct Check {
  const char* area;
  const char* name;
  CheckFn fn;
};

// A benchmark runs its workload once and returns nanoseconds per operation.
using BenchFn = double (*)();
struct Bench {
  const char* area;
  const char* name;
  BenchFn fn;
};

struct Suite {
  std::vector<Check> checks;
  std::vector<Bench> benches;
};

void register_core_checks(Suite&);
void register_core_benches(Suite&);

// Optimisation barrier: results are folded into a volatile so loops are not elided.
extern volatile tgf::u64 g_sink;

}  // namespace showcase

#define SC_REQUIRE(ctx, cond, text)                                                     \
  do {                                                                                  \
    if (!(cond)) {                                                                      \
      (ctx).note = std::string(text) + " [" #cond "] line " + std::to_string(__LINE__); \
      return false;                                                                     \
    }                                                                                   \
  } while (0)
