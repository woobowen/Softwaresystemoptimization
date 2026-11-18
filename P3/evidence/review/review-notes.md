# Review notes

- Initial cross compilation failed: relocated binutils could not load libbfd/libopcodes. Fixed by setting LD_LIBRARY_PATH to the extracted host libraries; all five final binaries built successfully.
- Initial zutty screenshot attempt failed due to missing font; downloaded and unpacked xterm, used Xvfb and an actual terminal instead.
- TCP GDB bind was denied; QEMU Unix-domain socket and GDB target remote succeeded. First GDB session loaded user initialization and was verbose; second used -nx and provided clean real terminal evidence. BFD reported a system-supplied DSO warning, but source break, step, variable, backtrace and normal exit worked.
- x86-64 GCC disassembly shows repeated vector stores of zero instead of additions. Corrected the report after inspecting all four main disassemblies; other three retain vector additions.
- Independent recomputation sorted the three values per group and checked the middle, minimum and maximum against the summary, covering all 60 records and 20 groups.
- Two requested reviewer agents lacked filesystem and command tools, so no non-author review is claimed. Final external review remains pending.
