# MIT HW1 scope and execution checklist

Source: official Fall 2018 PDF, 18 pages, saved as `../../mit6172/materials/MIT6_172F18hw1.pdf`.
Teacher source: A1 PDF page 2. No other homework or project was used.

| Item | Official location | Scope / execution | Status |
|---|---|---|---|
| Section 1 | p.1 | Read maintainability, assertions and collaboration advice; no Git task executed | PASS |
| Section 2 | Between sections 1 and 4 | No section 2 body is present in the public PDF; do not invent its contents | NOT_REQUIRED |
| Section 3 | Between sections 1 and 4 | No section 3 body is present in the public PDF; do not invent its contents | NOT_REQUIRED |
| Section 4 | pp.2–8 | C primer; preprocessing, sizes, pointers, argument passing | PASS |
| Preprocessing exercise | p.3 | Both `clang -E` variants executed; NDEBUG removes the guarded statement | PASS |
| sizes exercise | pp.4–5 | All specified types, five-element int array and student measured | PASS |
| pointer exercise / Write-up 2 | pp.6–7 | Original six compiler errors preserved; invalid statements commented; rebuilt and run | PASS |
| Write-up 3 | p.7 | Type and pointer sizes printed, including `sizeof(&x)` and `sizeof(&you)` | PASS |
| Write-up 4 | p.8 | Pointer-based swap; official verifier ported to Python 3 without changing expected values; LGTM | PASS |
| Section 5 | pp.8–15 before section 6 heading | All current exercises executed; no large-matrix optimization | PASS |
| Write-up 5 | p.8 | O1 baseline, O3 rebuild and actual crash observed | PASS |
| GDB exercise | pp.8–10 | Release backtrace; debug source line and dimensions inspected | PASS |
| Assertions exercise | pp.10–11 | Original assertions enabled; SIGABRT with dimensions 5 vs 4 observed | PASS |
| Dimension correction | p.11 | A changed to 4×4; both -p and -pz executed before initialization fix | PASS |
| Write-up 6 | p.12 | ASan runtime obtained from official Ubuntu package; actual LeakSanitizer output saved | PASS |
| Valgrind / initialization | pp.12–13 | Uninitialized values detected with origin tracking; matrix rows changed to calloc | PASS |
| Write-up 7 | p.13 | Correct matrix output saved; independently checked against A and B | PASS |
| Memory management | p.13 | Leak evidence retained; all three matrices freed after use | PASS |
| Write-up 8 | p.14 | Valgrind reports zero errors and no remaining allocation | PASS |
| Coverage exercise | pp.14–15 before section 6 | gcov flags temporarily added; llvm-cov gcov run on both files; reports retained; flags removed and final release rebuilt | PASS |
| Section 6 | pp.15–16 | Entire section skipped, including 1000×1000 resizing, loop interchange and Write-ups 9/10 | NOT_REQUIRED |
| Section 7 | pp.16–17 | Read style guidance; kept starter layout and simple changes | PASS |
| clint.py | Section 7 | Suggested but explicitly not required by MIT; no download or lint task added | NOT_REQUIRED |
| AWSRUN / Git | Throughout | Excluded by teacher; no AWS job, clone, commit or push | NOT_REQUIRED |
| Exercise submission | Teacher A1 p.2 | Practice evidence retained internally; README only includes material supporting formal Write-ups | PASS |

The figure-1 caption contradicts its `#ifndef NDEBUG` code. The actual code and both real preprocessor outputs establish that defining NDEBUG removes the statement; no source change was needed.

Coverage evidence is from one normal-input run: testbed 75.29%, matrix source 100%. This is not a claim of all possible paths or inputs being covered. The zero-input case was tested separately by the final correctness check.
