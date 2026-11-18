# Based on CppPerformanceBenchmarks makefile; only loop_fusion is built.
CC = gcc
CXX = g++
OPTLEVEL = -O2
CFLAGS = -I. $(OPTLEVEL)
CPPFLAGS = -std=c++14 -I. $(OPTLEVEL)
CPPLIBS = -lm
BINARIES = loop_fusion
ITERATIONS = 1
REPORT_FILE = report.txt

.PHONY: all clean report
all: $(BINARIES)
loop_fusion: loop_fusion.cpp benchmark_stdint.hpp benchmark_results.h benchmark_timer.h benchmark_shared_tests.h benchmark_typenames.h
	$(CXX) $(CPPFLAGS) -o $@ loop_fusion.cpp $(CPPLIBS)
report: $(BINARIES)
	@echo '##Compiler: $(CC) $(CXX)' > $(REPORT_FILE)
	@echo '##CFlags: $(CFLAGS)' >> $(REPORT_FILE)
	@echo '##CPPFlags: $(CPPFLAGS)' >> $(REPORT_FILE)
	./loop_fusion $(ITERATIONS) >> $(REPORT_FILE)
clean:
	rm -f $(BINARIES) *.o
