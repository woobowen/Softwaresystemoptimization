// Copyright (c) 2012 MIT License by 6.172 Staff

#ifndef TESTS_H
#define TESTS_H

#include "./util.h"

struct testFunc_t {
  void (*func)(data_t*, int, int);
  char* name;
};

#define RANGE_BITS 31
#define RANGE (1U << RANGE_BITS)

typedef void (*test_case)(int printFlag, int N, int R, struct testFunc_t* testFunc, int numFunc);

extern int test_failures;
extern int input_type;  // -1: both, 0: random, 1: inverted
void set_test_seed(unsigned int seed);

#endif  // TESTS_H
