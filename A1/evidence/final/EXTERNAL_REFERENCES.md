# External references used for current A1

| Source | Why needed / current A1 use | Changes teacher requirements? |
|---|---|---|
| [MIT OCW Fall 2018 Assignments](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/pages/assignments/) | Teacher's old PDF resource URL returned 404. Used the official current HW1 link; did not open or download other assignments. | No |
| [HW1 PDF page](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/resources/homework-1-getting-started/) and [official PDF](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/2724d8594cb413754669fc4e9c6ce7db_MIT6_172F18hw1.pdf) | Local teacher files refer to MIT but do not include its handout. Read the whole public PDF to identify precise sections and Write-ups. | No |
| [Official HW1 ZIP](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/7775d22df8bc896b87c593f24f7366eb_MIT6_172F18_hw1.zip) | No local starter existed. Used original two-directory C/Makefile structure and preserved the ZIP. Extraction omitted only macOS metadata. | No |
| Installed man pages for uname, sysctl, top, dmidecode, numactl, lscpu, proc_cpuinfo, free, vmstat, mpstat, pidstat, iostat and sar | Required by the teacher. Establish current option/field meanings, including free's KiB unit and distinct first-report semantics. Full outputs saved in linux_commands/man_*.txt. | No |
| Ubuntu noble-updates official packages, via configured Tsinghua mirror: llvm-18 and libclang-rt-18-dev 1:18.1.3-1ubuntu1 | Installed Clang lacked optional sanitizer/profile runtime and llvm-cov. Temporary extraction supplied these tools without upgrading libc or changing the system. Apt metadata, download URLs and hashes retained. | No; local tool location differs |
| [LLVM AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) | Confirm runtime/linking and symbolizer requirements for the actual missing-runtime build error. | No |
| [LLVM LeakSanitizer](https://clang.llvm.org/docs/LeakSanitizer.html) | Explain why the ASan run reports leaks through its integrated leak detector. | No |
| [LLVM MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html) | Distinguish uninitialized-value detection from ASan's checks. No MemorySanitizer experiment was added. | No |

No blogs, student solutions, nonofficial answer repositories, or later ECNU/MIT assignments were used. No Windows/BIOS recommendations were executed.
