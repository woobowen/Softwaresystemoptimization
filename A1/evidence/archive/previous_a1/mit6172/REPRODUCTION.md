# A1 HW1 reproduction notes

These notes concern local tooling and retained intermediate failures, not extra course exercises.

## Final source

From the course root:

```bash
make -C A1/mit6172/c-primer
(cd A1/mit6172/c-primer && python3 -B verifier.py)
make -C A1/mit6172/matrix-multiply
python3 -B A1/scripts/check_matrix.py
```

For the final Valgrind check, use `make DEBUG=1` in `matrix-multiply`, followed by:

```bash
valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=all --error-exitcode=97 ./matrix_multiply -p
```

Use `make clean` before changing instrumentation. Final delivered source uses ordinary release flags `-O3 -DNDEBUG`, original i/j/k loop order and 4×4 matrices. No performance claim is based on these tiny timings.

## Temporary official tools

Clang 18 was already installed, but its optional ASan/profile runtime and llvm-cov were absent. Installing the full runtime package via apt would also have upgraded seven libc/locale packages. The chosen reversible alternative was to download and extract two official Ubuntu packages without installing them or changing global PATH.

The original temporary location and full download log remain local. Published package versions and SHA-256 values are in [PUBLISH_NOTES.md](../final/PUBLISH_NOTES.md). To recreate the tools:

```bash
tools_dir=$(mktemp -d /tmp/a1-full-tools.XXXXXX)
(
  cd "$tools_dir" || exit 1
  apt-get download llvm-18=1:18.1.3-1ubuntu1 libclang-rt-18-dev=1:18.1.3-1ubuntu1
  for package in ./*.deb; do dpkg-deb -x "$package" root; done
)
resource_dir="$tools_dir/root/usr/lib/llvm-18/lib/clang/18"
llvm_cov="$tools_dir/root/usr/lib/llvm-18/bin/llvm-cov"
symbolizer="$tools_dir/root/usr/lib/llvm-18/bin/llvm-symbolizer"
```

If these exact versions cease to be available, consult the current official package metadata and use a matching runtime/compiler version; do not silently replace the recorded evidence. No package maintainer scripts or sudo were executed by extraction.

From a matrix-multiply working copy, the actual ASan method was:

```bash
make clean
make ASAN=1 LDFLAGS="-lrt -flto -fuse-ld=gold -fsanitize=address -resource-dir=$resource_dir"
ASAN_SYMBOLIZER_PATH="$symbolizer" ./matrix_multiply
```

`-resource-dir` is passed at link time so compiler headers still come from the already installed compiler. The official gold linker emitted local-symbol export warnings when linking the Ubuntu ASan runtime; the link succeeded and ASan executed. Warnings are preserved in the logs, not suppressed. No Makefile-wide linker replacement was made.

`writeup6_evidence.txt` is intentionally from the intermediate buggy source, not the final fixed source. To recreate it without overwriting final code, download the [official ZIP](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/7775d22df8bc896b87c593f24f7366eb_MIT6_172F18_hw1.zip) (SHA-256 in [PUBLISH_NOTES.md](../final/PUBLISH_NOTES.md)), extract `matrix-multiply` into a separate temporary directory, then apply `stage_dimensions_fixed.patch` with `patch -p1` from that extraction root. Build and run there with the ASan command above. The patched stage has compatible dimensions and assertions, but no calloc or free fixes. Runtime addresses and conservative leak detection totals may vary; the stored 224-byte report is the actual historical observation, not a universal expected output.

Similarly, `stage_initialized.patch` reconstructs the initialized-but-leaking stage. `final_from_official.patch` records all final starter-code edits. The original ZIP remains unchanged locally and is excluded from the repository.

## Coverage

The actual temporary Makefile changes are in `coverage_flags.patch`. Add `-fprofile-arcs -ftest-coverage` to both compile and link flags, clean, then build DEBUG=1. Supply the same link-time resource directory when the profile runtime is not installed:

```bash
make clean
make DEBUG=1 LDFLAGS="-lrt -flto -fuse-ld=gold -fprofile-arcs -ftest-coverage -resource-dir=$resource_dir"
./matrix_multiply -p
"$llvm_cov" gcov testbed.c
"$llvm_cov" gcov matrix_multiply.c
```

The above assumes the compile-side coverage flags from the patch are present. Generated `.gcda`, `.gcno` and `.gcov` files were copied to `coverage/`; then the original non-coverage Makefile was restored, `make clean` removed instrumented objects, and final code was rebuilt. Only the readable `.gcov` reports are published; binary intermediates remain local. This is a Section 5 exercise, not a Section 6 benchmark.

## Compatibility changes and limits

- `verifier.py`: Python 2 print statements converted, subprocess output read as text, string argument check made with isinstance. Expected outputs and required type sizes unchanged.
- The compiler is Ubuntu Clang 18.1.3, rather than MIT's historical Tapir distribution; the required starter is sequential C and builds with the original link flags. No Tapir/Cilk work added.
- GDB baseline used the user's existing initialization, which enabled colored dashboard output; subsequent commands used `gdb -nx --batch` for plain, reproducible traces without modifying `.gdbinit`.
- A download-shell footer initially used a relative path after `cd` into the temporary directory and exited 1 at its final `cat`. Download, extraction and llvm-cov itself had succeeded; their independent exit codes were checked and the footer issue recorded in the tooling log.
- No installed system or language package was added, upgraded or removed during A1-FULL-001. The new temporary extracted tools remain available for reproduction; previous environment packages and perf symlink remain untouched.
