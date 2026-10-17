// tgf_showcase — the executable that shows everything built so far (ADR-0030).
//   tgf_showcase                 run checks + benchmarks
//   tgf_showcase --checks-only   run checks only (used by CTest; non-zero exit on failure)
//   tgf_showcase --json out.json write machine-readable results (seed of P0.3.5)
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <tgf/core/build_info.hpp>
#include <tgf/core/profiler.hpp>
#include <vector>

#include "harness.hpp"
#include "tgf/core/types.hpp"

namespace {

struct CheckResult {
  const showcase::Check* check;
  bool ok;
  std::string note;
  double ms;
};
struct BenchResultRow {
  const showcase::Bench* bench;
  double median_ns, min_ns;
};

std::string json_escape(const std::string& s) {
  std::string o;
  for (char ch : s) {
    if (ch == '"' || ch == '\\') o += '\\';
    o += (ch == '\n') ? ' ' : ch;
  }
  return o;
}

}  // namespace

int main(int argc, char** argv) {
  bool checks_only = false;
  std::string json_path;
  for (int i = 1; i < argc; ++i) {
    if (!std::strcmp(argv[i], "--checks-only"))
      checks_only = true;
    else if (!std::strcmp(argv[i], "--json") && i + 1 < argc)
      json_path = argv[++i];
    else {
      std::fprintf(stderr, "usage: %s [--checks-only] [--json <file>]\n", argv[0]);
      return 2;
    }
  }

  const tgf::core::BuildInfo& bi = tgf::core::build_info();
  std::printf("TGF %s showcase\n", bi.version);
  std::printf("  library : %s, %s%s%s\n", bi.linkage, bi.configuration, bi.lto ? ", LTO" : "",
              bi.asserts_enabled ? ", asserts on" : "");
  std::printf("  compiler: %s\n", bi.compiler);
  std::printf("  profiler: %s\n\n", bi.profiler_enabled ? "enabled" : "disabled");

  showcase::Suite suite;
  showcase::register_core_checks(suite);
  showcase::register_core_benches(suite);

  // ---- checks ----
  std::vector<CheckResult> results;
  int failed = 0;
  std::printf("== CHECKS ==\n");
  for (const auto& c : suite.checks) {
    showcase::Context ctx;
    const tgf::u64 t0 = tgf::core::now_ns();
    const bool ok = c.fn(ctx);
    const double ms = static_cast<double>(tgf::core::now_ns() - t0) / 1e6;
    results.push_back({&c, ok, ctx.note, ms});
    if (!ok) ++failed;
    std::printf("[%s] %-4s %-58s %7.1f ms\n", ok ? "PASS" : "FAIL", c.area, c.name, ms);
    if (!ctx.note.empty()) std::printf("       %s%s\n", ok ? "" : "-> ", ctx.note.c_str());
  }

  // ---- benchmarks ----
  std::vector<BenchResultRow> bench_rows;
  bench_rows.reserve(suite.benches.size());
  if (!checks_only) {
    std::printf("\n== BENCHMARKS (median of 9 runs, release builds only are meaningful) ==\n");
    for (const auto& b : suite.benches) {
      std::vector<double> runs;
      runs.reserve(9);
      (void)b.fn();  // warm-up
      for (int i = 0; i < 9; ++i) runs.push_back(b.fn());
      std::sort(runs.begin(), runs.end());
      bench_rows.push_back({&b, runs[runs.size() / 2], runs.front()});
      std::printf("  %-4s %-42s median %8.2f  min %8.2f\n", b.area, b.name, runs[runs.size() / 2], runs.front());
    }
  }

  std::printf("\n== SUMMARY ==\n  %zu checks, %d failed\n  %s\n", results.size(), failed,
              failed == 0 ? "ALL GREEN - safe to proceed to the next phase" : "NOT GREEN - fix before going forward");

  if (!json_path.empty()) {
    std::ofstream out(json_path);
    out << "{\n  \"version\": \"" << bi.version << "\",\n  \"linkage\": \"" << bi.linkage
        << "\",\n  \"configuration\": \"" << bi.configuration << "\",\n  \"checks\": [\n";
    for (size_t i = 0; i < results.size(); ++i)
      out << "    {\"area\": \"" << results[i].check->area << "\", \"name\": \"" << json_escape(results[i].check->name)
          << "\", \"ok\": " << (results[i].ok ? "true" : "false") << ", \"ms\": " << results[i].ms << "}"
          << (i + 1 < results.size() ? "," : "") << "\n";
    out << "  ],\n  \"benchmarks\": [\n";
    for (size_t i = 0; i < bench_rows.size(); ++i)
      out << "    {\"area\": \"" << bench_rows[i].bench->area << "\", \"name\": \""
          << json_escape(bench_rows[i].bench->name) << "\", \"median_ns\": " << bench_rows[i].median_ns
          << ", \"min_ns\": " << bench_rows[i].min_ns << "}" << (i + 1 < bench_rows.size() ? "," : "") << "\n";
    out << "  ]\n}\n";
  }
  return failed == 0 ? 0 : 1;
}
