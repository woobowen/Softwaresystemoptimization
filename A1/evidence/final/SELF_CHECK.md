# A1-FULL-001 final self-check

| Check | Result | Evidence / boundary |
|---|---|---|
| A. Teacher requirements covered | PASS | A1_REQUIREMENT_MATRIX.md; old environment requirements superseded only by provided newer environment document |
| B. Later coursework started? | NO | No A2/A3/A4/A5/P1/P2/P3 artifacts, SPECjvm2008, oneAPI, auto-tuning or cross-compilation work |
| C. Experiment results from current machine | PASS | Timestamped terminal logs and local program runs; no borrowed matrices or hardware output |
| D. Code compiled and run | PASS | Baseline failures, each repair, official verifier, ASan/Valgrind and final release logs |
| E. README formal contents | PASS | All Linux answers and Write-up 2–8; Exercise detail kept internal |
| F. Local Markdown links | PASS | submission_validation.txt |
| G. Boilerplate / process narrative avoided | PASS | README focuses on results and interpretation; no reviewer status pasted into report |
| H. Overdesign avoided | PASS | Original C functions and two Makefiles retained; one small independent correctness script |
| I. Readable code | PASS | Six illegal pointer assignments commented, direct pointer swap, simple sizes macro, calloc and three frees |
| J. Write-up 2–8 | PASS | Seven sections, with genuine output and code where required |
| K. Section 6 skipped | YES | No 1000×1000 resize, loop interchange or Write-up 9/10 |
| L. AWSRUN/Git ignored | YES | Official download rather than clone; no commit/push/PR or remote submission |
| M. Exercises not submitted as extra Write-ups | YES | Preprocessing, GDB/assertions and coverage detailed evidence stored internally |
| N. Environment differences disclosed | PASS | PMU unsupported, DMI interfaces absent, protected sysctl values, PID namespace and guest topology |

## Explicit limitations, not fabricated successes

- dmidecode actually failed to read a table. DIMM count/capacity/vendor and host physical topology remain UNVERIFIED. The command exercise and explanation are complete; no sudo dmidecode result is claimed. Since both /dev/mem and DMI sysfs interfaces are absent, no password-dependent command was needed merely to repeat this observation.
- sysctl -a returned 0 while reporting permission errors for some protected keys. These values are not claimed as read.
- Interactive top sees the execution terminal's PID namespace, not all WSL/Windows processes. pidstat 1 had no nonzero task rows during sampling; this is retained, not filled with invented data.
- Hardware PMU counters and ordinary-user CPU-wide perf collection remain limited as recorded in the established environment evidence. The environment script itself was not modified this turn.
- Preprocessing example is deliberately a fragment; it was preprocessed, not claimed to be a complete executable. Original pointer compilation errors and matrix crashes are intended educational baselines.
- GDB's exit 0 is the debugger's exit, not proof that its inferior ran successfully; SIGSEGV/SIGABRT are explicitly recorded.
- ASan's intermediate 224-byte leak report and Valgrind's 336-byte leak accounting are distinct observed reports. Final Valgrind has zero errors/leaks; this does not prove correctness for arbitrary huge or allocation-failing inputs beyond HW1.
- The final correctness check uses the required 4×4 normal and zero modes. No speedup was claimed from rounded microsecond-scale timings or instrumented builds.
- Optional runtime/coverage tools are extracted under the task's temporary directory. Global Clang ASan support and global llvm-cov installation remain absent; exact reproduction instructions are provided. No installed package changes were needed.

No blocking or unfinished teacher-required item remains. No high-risk host action was attempted or required.
