#!/usr/bin/env python3
"""Positive and negative fixtures for the TGF dependency DAG checker."""
from __future__ import annotations

import importlib.util
import pathlib
import shutil
import sys
import tempfile

LAYERS = ("core", "platform", "rhi", "text", "render", "ui", "widgets", "pro")
ALLOWED = {
    "core": set(),
    "platform": {"core"},
    "rhi": {"core"},
    "text": {"core"},
    "render": {"core", "rhi", "text"},
    "ui": {"core", "text", "render", "platform"},
    "widgets": {"ui"},
    "pro": {"widgets", "ui"},
    "tools": set(LAYERS),
    "host": set(LAYERS),
    "c": set(LAYERS),
    "bindings": {"c"},
}
REQUIRED_DIRS = (
    "core", "platform", "rhi", "render", "text", "ui", "widgets", "pro",
    "tools", "host", "c", "bindings", "samples", "benchmarks", "tests",
    "docs", "third_party", "cmake",
)
SOURCE_SUFFIXES = {".h", ".hpp", ".hh", ".hxx", ".c", ".cc", ".cpp", ".cxx", ".m", ".mm", ".s", ".asm", ".inl", ".ipp", ".inc", ".tpp", ".txx", ".cppm", ".ixx", ".ccm", ".cxxm", ".mpp", ".cu", ".cuh", ".hip"}
TABLE = """**★ Explicit dependency table (fixtures)**
| Module | May depend on |
|---|---|
| core | std only |
| platform | core (opaque native handles only) |
| rhi | core |
| text | core |
| render | core, rhi, text |
| ui | core, text, render (display-list API only), platform (event kinds, defined in core) |
| widgets | ui (public API only) |
| pro | widgets, ui (public API only) |
| tools, host, c | any of the above through public headers |
| bindings | c (stable C ABI only) |
**Dependency rules:**
"""


def load_checker(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("tgf_check_deps", path)
    if not spec or not spec.loader:
        raise AssertionError("could not load dependency checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(root: pathlib.Path, relative: str, content: str) -> pathlib.Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def prepare(root: pathlib.Path) -> None:
    for directory in REQUIRED_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "TODO.md").write_text(TABLE, encoding="utf-8")
    for module in ALLOWED:
        public = root / module / "include" / "tgf" / module
        public.mkdir(parents=True, exist_ok=True)
        (public / "api.hpp").write_text("// public fixture\n", encoding="utf-8")
        (root / module / "src").mkdir(parents=True, exist_ok=True)


def reset_sources(root: pathlib.Path) -> None:
    for module in ALLOWED:
        for source in (root / module).rglob("*"):
            if source.is_symlink():
                source.unlink()
            elif source.is_file() and source.suffix.lower() in SOURCE_SUFFIXES:
                if "include" not in source.relative_to(root / module).parts:
                    source.unlink()
    for consumer in ("samples", "benchmarks", "tests"):
        for source in (root / consumer).rglob("*"):
            if source.is_symlink():
                source.unlink()
            elif source.is_file() and source.suffix.lower() in SOURCE_SUFFIXES:
                source.unlink()


def include(root: pathlib.Path, importer: str, dependency: str, name: str) -> None:
    write(root, f"{importer}/src/{name}", f"#include <tgf/{dependency}/api.hpp>\n")


def expect(errors: list[str], fragment: str, label: str) -> None:
    if not any(fragment in error for error in errors):
        raise AssertionError(f"{label}: expected diagnostic containing {fragment!r}, got:\n" + "\n".join(errors))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: test_check_deps.py path/to/check_deps.py")
        return 2
    checker = load_checker(pathlib.Path(sys.argv[1]).resolve())
    module_names = set(ALLOWED)
    allowed_count = sum(len(deps - {module}) for module, deps in ALLOWED.items())
    forbidden_count = sum(len(module_names - {module} - deps) for module, deps in ALLOWED.items())

    with tempfile.TemporaryDirectory(prefix="tgf-deps-policy-") as temporary:
        root = pathlib.Path(temporary)
        prepare(root)

        # Every edge in the policy table is accepted.
        for importer, dependencies in ALLOWED.items():
            for dependency in dependencies:
                if importer != dependency:
                    include(root, importer, dependency, f"allow_{dependency}.cpp")
        errors = checker.check(root)
        if errors:
            raise AssertionError("permitted edges failed:\n" + "\n".join(errors))

        # Same-module TGF headers can be quoted because this is not a module edge.
        reset_sources(root)
        write(root, "core/src/same_module.cpp", '#include "tgf/core/api.hpp"' + chr(10))
        errors = checker.check(root)
        if errors:
            raise AssertionError(f"same-module public header should be valid: {errors!r}")

        reset_sources(root)
        write(root, "core/src/private.hpp", "// internal implementation header")
        write(root, "core/src/same_module.cpp", '#include "private.hpp"' + chr(10))
        errors = checker.check(root)
        if errors:
            raise AssertionError(f"same-module private quoted include should be valid: {errors!r}")

        reset_sources(root)
        write(root, "render/src/quoted.cpp", '#include "tgf/core/api.hpp"\n')
        expect(checker.check(root), "canonical angle-bracket spelling", "quoted TGF include")

        # Every forbidden directed module edge is rejected.
        reset_sources(root)
        for importer, dependencies in ALLOWED.items():
            for dependency in module_names - {importer} - dependencies:
                include(root, importer, dependency, f"deny_{dependency}.cpp")
        errors = checker.check(root)
        rejected = [error for error in errors if "may not depend on" in error]
        if len(rejected) != forbidden_count:
            raise AssertionError(
                f"expected {forbidden_count} rejected edges, observed {len(rejected)}:\n"
                + "\n".join(errors)
            )

        # Relative paths cannot bypass module layering or the public-header rule.
        reset_sources(root)
        # A public header cannot reach its private src tree through parent traversal.
        reset_sources(root)
        write(root, "core/src/private.hpp", "// private")
        write(root, "core/include/tgf/core/leak.hpp", '#include "../../../src/private.hpp"')
        expect(
            checker.check(root),
            "empty or traversal component",
            "public-to-private same-module bypass",
        )
        (root / "core/include/tgf/core/leak.hpp").unlink()

        write(root, "ui/src/private.hpp", "// private\n")
        write(root, "platform/src/bypass.cpp", '#include "../../ui/src/private.hpp"\n')
        expect(checker.check(root), "empty or traversal component", "forbidden relative module edge")

        reset_sources(root)
        write(root, "c/src/private.h", "/* private */\n")
        write(root, "bindings/src/private.cpp", '#include "../../c/src/private.h"\n')
        expect(checker.check(root), "empty or traversal component", "bindings private-header bypass")

        reset_sources(root)
        write(root, "bindings/src/missing.cpp", "#include <tgf/c/not_public.hpp>\n")
        expect(checker.check(root), "existing public header", "non-existent public header")

        reset_sources(root)
        write(root, "core/src/private.hpp", "// private\n")
        write(root, "samples/app/src/main.cpp", '#include "../../../core/src/private.hpp"\n')
        expect(checker.check(root), "empty or traversal component", "sample private-header bypass")

        reset_sources(root)
        write(root, "core/src/private.hpp", "// private\n")
        write(root, "benchmarks/app/bench.cpp", "#include <core/src/private.hpp>\n")
        expect(checker.check(root), "consumer may not include module-private paths", "benchmark private-header bypass")

        # Application, benchmark, and test targets are scanned as public consumers.
        reset_sources(root)
        write(root, "samples/app/src/main.cpp", "#include <tgf/core/api.hpp>\n")
        write(root, "benchmarks/app/bench.cpp", "#include <tgf/ui/api.hpp>\n")
        write(root, "tests/consumer/test.cpp", "#include <tgf/c/api.hpp>\n")
        errors = checker.check(root)
        if errors:
            raise AssertionError("valid public consumer includes failed:\n" + "\n".join(errors))

        reset_sources(root)
        write(root, "tests/consumer/test.cpp", '#include "tgf/core/api.hpp"\n')
        expect(checker.check(root), "canonical angle-bracket spelling", "test target quoted TGF include")

        reset_sources(root)
        write(root, "samples/app/src/main.cpp", '#include "missing_generated.hpp"\n')
        expect(checker.check(root), "does not resolve beside its source", "unresolved quoted include")

        # The public SDK boundary is a deny-list of platform, graphics, font,
        # immediate-mode GUI, framework, and common third-party SDK roots.
        forbidden_public_headers = (
            "windows.h", "winuser.h", "vulkan/vulkan.h", "vk_platform.h",
            "d3d12.h", "dxgi1_6.h", "GLFW/glfw3.h", "SDL3/SDL.h",
            "X11/Xlib.h", "xcb/xcb.h", "wayland-client.h",
            "Metal/Metal.h", "AppKit/AppKit.h", "CoreGraphics/CGContext.h",
            "ft2build.h", "hb.h", "imgui.h", "imgui_impl_glfw.h",
            "QtWidgets/QWidget", "QWidget", "third_party/foo.h",
            "vendor/foo.hpp", "stb_image.h", "glm/glm.hpp", "fmt/core.h",
            "mystery_sdk/api.hpp",
            "not_a_standard_header.hpp",
            "sys/types.h",
            "pthread.h",
            "spdlog/spdlog.h", "nlohmann/json.hpp", "boost/optional.hpp",
            "cairo.h", "pango/pango.h", "gtk/gtk.h", "glib.h", "gdk/gdk.h",
        )
        for header in forbidden_public_headers:
            reset_sources(root)
            write(root, "widgets/include/tgf/widgets/widget.hpp", f"#include <{header}>" + chr(10))
            expect(
                checker.check(root),
                "forbidden platform/graphics/third-party SDK header",
                f"public SDK leak {header}",
            )
        write(root, "widgets/include/tgf/widgets/widget.hpp", "// public fixture restored")
        write(root, "core/include/tgf/core/stdlib.hpp", chr(10).join(["#include <cstddef>", "#include <cstdint>", "#include <array>", "#include <algorithm>", "#include <string_view>"]) + chr(10))
        errors = checker.check(root)
        if errors: raise AssertionError(f"standard library includes must be accepted: {errors!r}")


        # Comment markers inside an angle-bracket header name are path characters,
        # not preprocessing comments, and must remain visible to path validation.
        for header, expected in (
            ("tgf//core/api.hpp", "TGF include path"),
            ("tgf/core/name/*part.hpp", "existing public header"),
        ):
            reset_sources(root)
            write(root, "ui/src/header_name.cpp", f"#include <{header}>" + chr(10))
            expect(checker.check(root), expected, "comment marker inside header name " + header)

        # Every TGF include has exact, canonical components and a real public file.
        invalid_tgf_paths = (
            "tgf/core/./api.hpp",
            "tgf//core/api.hpp",
            "tgf/core/../api.hpp",
            "tgf/core",
            "tgf\\core\\api.hpp",
            "tgf/Core/api.hpp",
            "tgf/unknown/api.hpp",
            "TGF/core/api.hpp",
            "./tgf/core/api.hpp",
            "../tgf/core/api.hpp",
            "folder/tgf/core/api.hpp",
        )
        for header in invalid_tgf_paths:
            reset_sources(root)
            write(root, "ui/src/invalid_path.cpp", f"#include <{header}>\n")
            if header == "tgf/Core/api.hpp":
                expected = "must be lowercase"
            elif header == "tgf/unknown/api.hpp":
                expected = "unknown TGF module"
            elif header == "tgf\\core\\api.hpp":
                expected = "forward slashes"
            else:
                expected = "TGF include path"
            expect(checker.check(root), expected, f"malformed TGF include {header}")

        reset_sources(root)
        write(root, "render/src/missing.cpp", "#include <tgf/core/not_real.hpp>\n")
        expect(checker.check(root), "existing public header", "missing public include")

        reset_sources(root)
        write(root, "ui/src/case.cpp", "#include <tgf/core/API.hpp>\n")
        expect(checker.check(root), "existing public header", "case-mismatched public include")

        # Macro includes, include_next, and named C++ modules fail closed.
        for directive, diagnostic in (
            ("#include GENERATED_HEADER\n", "non-literal or malformed include"),
            ("#include_next <tgf/core/api.hpp>\n", "#include_next is forbidden"),
            ("import tgf.core;\n", "named-module imports are prohibited"),
            ("export import tgf.core;\n", "named-module imports are prohibited"),
        ):
            reset_sources(root)
            write(root, "ui/src/uninspectable.cpp", directive)
            expect(checker.check(root), diagnostic, f"unsupported include form {directive.strip()}")

        # C/C++ translation phases splice backslash-newline before directives are read.
        reset_sources(root)
        split_include = "#inc" + chr(92) + chr(10) + "lude <tgf/ui/api.hpp>" + chr(10)
        write(root, "platform/src/split_include.cpp", split_include)
        expect(checker.check(root), "may not depend on 'ui'", "line-spliced include bypass")

        # A UTF-8 BOM at the beginning of a source file must not hide a directive.
        reset_sources(root)
        write(root, "platform/src/bom.cpp", "\ufeff#include <tgf/ui/api.hpp>" + chr(10))
        expect(checker.check(root), "may not depend on 'ui'", "UTF-8 BOM include")

        # Comments before a preprocessing token are removed before directive parsing.
        reset_sources(root)
        write(root, "platform/src/comment_prefix.cpp", "/* leading comment */ #include <tgf/ui/api.hpp>" + chr(10))
        expect(checker.check(root), "may not depend on 'ui'", "comment-prefixed include")

        # Comments between preprocessing tokens must not hide a forbidden include.
        for directive in (
            "# /* separator */ include <tgf/ui/api.hpp>" + chr(10),
            "#include /* separator */ <tgf/ui/api.hpp>" + chr(10),
        ):
            reset_sources(root)
            write(root, "platform/src/commented_directive.cpp", directive)
            expect(checker.check(root), "may not depend on 'ui'", "comment-separated include tokens")

        # A multiline comment must not hide an import after the comment closes.
        reset_sources(root)
        write(root, "ui/src/multiline_comment_import.cppm", "export /* comment begins" + chr(10) + "*/ import tgf.render;" + chr(10))
        expect(checker.check(root), "named-module imports are prohibited", "multiline comment around module import")

        # Module-looking text inside a multiline raw string is not an import.
        reset_sources(root)
        raw_string = 'constexpr auto example = R"tag(' + chr(10) + "import tgf.render;" + chr(10) + ')tag";' + chr(10)
        write(root, "ui/src/multiline_raw_string.cpp", raw_string)
        errors = checker.check(root)
        if errors: raise AssertionError(f"module-looking text inside raw string must be ignored: {errors!r}")

        # Ordinary string and character literals may contain text that looks like
        # preprocessing directives or module imports; those are not dependencies.
        reset_sources(root)
        literal_lookalikes = chr(10).join((
            'const char* include_text = "#include <tgf/ui/api.hpp>";',
            'const char* module_text = "import tgf.render;";',
            'const char* objc_text = "@import Foundation;";',
            'const char* comment_text = "/* #include <tgf/ui/api.hpp> */";',
            "constexpr char hash = '#';",
            "constexpr char slash = '/';",
            "constexpr char import_marker = 'i';",
            "constexpr char apostrophe = '\\\\'';",
        )) + chr(10)
        write(root, "ui/src/literal_lookalikes.cpp", literal_lookalikes)
        errors = checker.check(root)
        if errors: raise AssertionError(f"ordinary string/character literal lookalikes must not be treated as dependencies: {errors!r}")

        # Unterminated comments and raw strings fail closed.
        reset_sources(root)
        write(root, "ui/src/unterminated_comment.cpp", "/* unterminated" + chr(10))
        expect(checker.check(root), "unterminated block comment", "unterminated source comment")

        reset_sources(root)
        write(root, "ui/src/unterminated_raw.cpp", 'auto example = R"tag(' + chr(10) + "import tgf.render;" + chr(10))
        expect(checker.check(root), "unterminated raw string", "unterminated raw string")

        # An import keyword cannot be separated from its module name by a
        # multiline comment, or that first line would evade whole-line matching.
        for source, filename in (
            ("import /* comment begins" + chr(10) + "*/ tgf.render;" + chr(10), "split_import.cpp"),
            ("@import /* comment begins" + chr(10) + "*/ Foundation;" + chr(10), "split_objc_import.mm"),
        ):
            reset_sources(root)
            write(root, "ui/src/" + filename, source)
            expect(checker.check(root), "named-module imports are prohibited", "split module import token")

        # Comment-separated named-module imports are still recognized.
        reset_sources(root)
        write(root, "ui/src/commented_import.cppm", "export /* separator */ import tgf.render;" + chr(10))
        expect(checker.check(root), "named-module imports are prohibited", "comment-separated module import")

        # An unterminated block comment in a preprocessing directive fails closed.
        reset_sources(root)
        write(root, "platform/src/multiline_comment.cpp", "# /* unterminated" + chr(10) + "comment */ include <tgf/ui/api.hpp>" + chr(10))
        expect(checker.check(root), "multi-line comment", "multiline comment in include directive")

        # Objective-C modules are also imports and currently have no public/private
        # dependency declaration, so they must fail closed rather than bypass the DAG.
        reset_sources(root)
        write(root, "ui/src/objc_module.mm", "@import Foundation;" + chr(10))
        expect(checker.check(root), "named-module imports are prohibited", "Objective-C module import")

        # Named module interfaces and partitions have no declared module DAG yet.
        for declaration in ("export module tgf.ui;" + chr(10), "module tgf.ui:details;" + chr(10)):
            reset_sources(root)
            write(root, "ui/src/interface.cppm", declaration)
            expect(checker.check(root), "named module declarations are prohibited", "named module interface")

        # A global module fragment is not a named module declaration.
        reset_sources(root)
        write(root, "ui/src/global_fragment.cppm", "module;" + chr(10) + "#include <tgf/ui/api.hpp>" + chr(10))
        errors = checker.check(root)
        if errors: raise AssertionError(f"global module fragment should not declare a named module: {errors!r}")

        # Imports in all common C++ module-unit extensions fail closed.
        for suffix in (".cppm", ".ixx", ".ccm", ".cxxm", ".mpp"):
            reset_sources(root)
            write(root, "ui/src/module" + suffix, "export module tgf.ui;" + chr(10) + "import tgf.render;" + chr(10))
            expect(checker.check(root), "named-module imports are prohibited", "named module unit " + suffix)

        # The same token sequence inside a block comment is not an import.
        reset_sources(root)
        write(root, "ui/src/commented_module.cppm", "/*" + chr(10) + "import tgf.render;" + chr(10) + "*/" + chr(10))
        errors = checker.check(root)
        if errors: raise AssertionError(f"commented module example must not be parsed as an import: {errors!r}")

        # RHI backends cannot include another backend, including through the
        # canonical public namespace or an internal relative path.
        reset_sources(root)
        write(root, "rhi/include/tgf/rhi/backends/d3d12/device.hpp", "// public fixture\n")
        backend_dir = root / "rhi/backends/vulkan/src"
        backend_dir.mkdir(parents=True, exist_ok=True)
        write(root, "rhi/backends/vulkan/src/cross.cpp", "#include <tgf/rhi/backends/d3d12/device.hpp>\n")
        expect(checker.check(root), "may not include backend", "canonical RHI backend isolation")

        reset_sources(root)
        backend_dir = root / "rhi/backends/vulkan/src"
        backend_dir.mkdir(parents=True, exist_ok=True)
        write(root, "rhi/backends/d3d12/src/device.hpp", "// private fixture\n")
        write(root, "rhi/backends/vulkan/src/relative.cpp", '#include "../../d3d12/src/device.hpp"\n')
        expect(checker.check(root), "empty or traversal component", "relative RHI backend isolation")

        # Traversal is diagnosed even when the destination does not exist.
        reset_sources(root)
        write(root, "platform/src/escape_root.cpp", '#include "../../../outside.hpp"\n')
        expect(checker.check(root), "empty or traversal component", "repository-root traversal")

        reset_sources(root)
        write(root, "docs/private.hpp", "// fixture\n")
        write(root, "platform/src/escape_non_module.cpp", '#include "../../docs/private.hpp"\n')
        expect(checker.check(root), "empty or traversal component", "module traversal")

        reset_sources(root)
        write(root, "ui/src/windows_separator.cpp", "#include <foo\\bar.hpp>" + chr(10))
        expect(checker.check(root), "include paths must use forward slashes", "Windows separator in ordinary include")

        # All include forms reject dot segments, traversal, repeated separators,
        # and drive-relative Windows paths before include-search-path lookup.
        for header in (
            "../../core/src/private.hpp",
            "../outside.hpp",
            "foo/../bar.hpp",
            "./private.hpp",
            "foo//bar.hpp",
        ):
            reset_sources(root)
            write(root, "ui/src/traversal.cpp", f"#include <{header}>" + chr(10))
            expect(checker.check(root), "empty or traversal component", "angle include path traversal " + header)

        reset_sources(root)
        write(root, "ui/src/traversal.cpp", "#include <foo\\\\..\\\\bar.hpp>" + chr(10))
        expect(checker.check(root), "forward slashes", "backslash traversal path")

        reset_sources(root)
        write(root, "ui/src/drive_relative.cpp", "#include <C:private.hpp>" + chr(10))
        expect(checker.check(root), "absolute include path is forbidden", "Windows drive-relative include")

        # Include paths themselves may not be machine-specific.
        reset_sources(root)
        windows_include = "C:" + chr(92) + "Users" + chr(92) + "Developer" + chr(92) + "private.hpp"
        write(root, "core/src/absolute_windows.cpp", f'#include "{windows_include}"' + chr(10))
        expect(checker.check(root), "absolute include path is forbidden", "Windows absolute include")

        reset_sources(root)
        posix_include = chr(47) + "home" + chr(47) + "developer" + chr(47) + "private.hpp"
        write(root, "core/src/absolute_posix.cpp", f'#include "{posix_include}"\n')
        expect(checker.check(root), "absolute include path is forbidden", "POSIX absolute include")

        reset_sources(root)
        write(root, "ui/src/unknown.cpp", "#include <tgf/unknown/api.hpp>\n")
        expect(checker.check(root), "unknown TGF module", "unknown module")

        # Absolute machine paths are found in source and build metadata, including UNC.
        reset_sources(root)
        windows_path = "C:" + chr(92) + "Users" + chr(92) + "Developer"
        write(root, "tools/path.py", f'ROOT = "{windows_path}"\n')
        expect(checker.check(root), "absolute machine-specific path", "Windows drive path")

        reset_sources(root)
        posix_path = chr(47) + "home" + chr(47) + "developer" + chr(47) + "project"
        write(root, "tools/posix_path.py", f'ROOT = "{posix_path}"\n')
        expect(checker.check(root), "absolute machine-specific path", "POSIX home path")

        reset_sources(root)
        unc_path = chr(92) * 2 + "build-server" + chr(92) + "workspace"
        for fixture in ("path.py", "posix_path.py", "unc_path.py"):
            (root / "tools" / fixture).unlink(missing_ok=True)
        write(root, "tools/ci_path.py", 'ROOT = "/home/runner/work/tgf/tgf"')
        write(root, "tools/mac_path.py", 'ROOT = "/Users/runner/hostedtoolcache"')
        write(root, "tools/url.py", 'URL = "https://example.com/path"')
        errors = checker.check(root)
        if errors: raise AssertionError(f"portable runner paths and URLs must be accepted: {errors!r}")

        write(root, "tools/unc_path.py", f'ROOT = "{unc_path}"\n')
        expect(checker.check(root), "absolute machine-specific path", "UNC path")

        reset_sources(root)
        widened_consumer_policy = TABLE.replace(
            "any of the above through public headers",
            "any of the above plus bindings through public headers",
        )
        write(root, "TODO.md", widened_consumer_policy)
        expect(checker.check(root), "unknown or empty dependency-table module", "policy wording drift")

        # The normative policy may not drift, omit rows, or duplicate module rows.
        reset_sources(root)
        changed_table = TABLE.replace("| render | core, rhi, text |", "| render | core |")
        write(root, "TODO.md", changed_table)
        expect(checker.check(root), "dependency table differs", "policy drift")

        reset_sources(root)
        duplicate_table = TABLE.replace(
            "| platform | core (opaque native handles only) |",
            "| platform | core (opaque native handles only) |\n| platform | core |",
        )
        write(root, "TODO.md", duplicate_table)
        expect(checker.check(root), "duplicate dependency row", "duplicate policy row")

        write(root, "TODO.md", TABLE)
        shutil.rmtree(root / "platform")
        expect(checker.check(root), "missing top-level directory 'platform/'", "required layout")

        missing_root = root / "does-not-exist"
        expect(checker.check(missing_root), "project root does not exist", "missing project root")

        missing_todo_root = root / "no-todo"
        prepare(missing_todo_root)
        (missing_todo_root / "TODO.md").unlink()
        expect(checker.check(missing_todo_root), "TODO.md is missing", "missing policy source")


        # Symlinks that stay inside their owning scan boundary are valid file aliases.
        # Escapes across the repository, module, and consumer roots must fail closed.
        with tempfile.TemporaryDirectory(prefix="tgf-deps-outside-") as outside:
            outside_root = pathlib.Path(outside)
            outside_file = outside_root / "escaped.cpp"
            outside_file.write_text("// external source" + chr(10), encoding="utf-8")
            outside_dir = outside_root / "external-dir"
            outside_dir.mkdir()

            reset_sources(root)
            module_target = write(root, "core/src/target.cpp", "// same module" + chr(10))
            (root / "core/src/safe_alias.cpp").symlink_to(
                module_target, target_is_directory=False
            )
            errors = checker.check(root)
            if errors:
                raise AssertionError(f"same-module source symlink should be accepted: {errors!r}")

            reset_sources(root)
            consumer_target = write(root, "tests/consumer/target.cpp", "// same consumer" + chr(10))
            (root / "tests/consumer/safe_alias.cpp").symlink_to(
                consumer_target, target_is_directory=False
            )
            errors = checker.check(root)
            if errors:
                raise AssertionError(f"same-consumer source symlink should be accepted: {errors!r}")

            reset_sources(root)
            (root / "core/src/outside_repository.cpp").symlink_to(
                outside_file, target_is_directory=False
            )
            expect(checker.check(root), "source symlink escapes repository root", "source file symlink escaping repository")

            reset_sources(root)
            module_target = write(root, "ui/src/foreign.cpp", "// another module" + chr(10))
            (root / "core/src/foreign.cpp").symlink_to(module_target, target_is_directory=False)
            expect(checker.check(root), "source symlink escapes its module/consumer boundary", "source file symlink crossing module boundary")

            reset_sources(root)
            consumer_target = write(root, "samples/app/src/shared.cpp", "// another consumer" + chr(10))
            (root / "tests/consumer/shared.cpp").symlink_to(consumer_target, target_is_directory=False)
            expect(checker.check(root), "source symlink escapes its module/consumer boundary", "source file symlink crossing consumer boundary")

            reset_sources(root)
            (root / "core/src/outside_directory").symlink_to(
                outside_dir, target_is_directory=True
            )
            expect(checker.check(root), "directory symlink escapes repository root", "directory symlink escaping repository")

            reset_sources(root)
            module_directory = root / "ui/src"
            (root / "core/src/foreign_directory").symlink_to(
                module_directory, target_is_directory=True
            )
            expect(checker.check(root), "directory symlink escapes its module/consumer boundary", "directory symlink crossing module boundary")

            reset_sources(root)
            consumer_directory = root / "samples/app"
            (root / "tests/consumer/foreign_directory").symlink_to(
                consumer_directory, target_is_directory=True
            )
            expect(checker.check(root), "directory symlink escapes its module/consumer boundary", "directory symlink crossing consumer boundary")

            # Top-level scan roots may never be aliases, even when the target
            # remains somewhere inside the repository.
            platform = root / "platform"
            platform.symlink_to(root / "core", target_is_directory=True)
            expect(checker.check(root), "top-level directory 'platform/' must not be a symlink", "top-level in-repository directory symlink")
            platform.unlink()

            platform.symlink_to(outside_dir, target_is_directory=True)
            expect(checker.check(root), "top-level directory 'platform/' symlink escapes repository root", "top-level directory symlink escaping repository")
            platform.unlink()

    print(
        f"dependency DAG regression tests passed: {allowed_count} allowed edges, "
        f"{forbidden_count} forbidden edges, all consumer roots, public/private headers, "
        "SDK leaks, canonical paths, RHI isolation, unsupported imports, traversal, "
        "absolute paths, safe/escaping symlinks, literal lookalikes, policy drift, and repository layout"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
