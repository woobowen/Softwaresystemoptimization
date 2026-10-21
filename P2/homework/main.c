/**
 * Copyright (c) 2013-2014 MIT License by 6.172 Staff
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 **/

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <limits.h>

#include "./fasttime.h"
#include "./tests.h"

// Extern variables
extern test_case test_cases[];


static void run_test_suite(int start_idx, int printFlag, int N, int R, int benchOnly,
                           struct testFunc_t* testFunc, int numFunc) {
  for (int i = 0; test_cases[i] != NULL; i++) {
    if (i < start_idx) {
      continue;
    }
    fprintf(stderr, "\nRunning test #%d...\n", i);
    (*test_cases[i])(printFlag, N, R, testFunc, numFunc);
    if (benchOnly) break;
  }
  fprintf(stderr, "Done testing.\n");
}


extern void sort_a(data_t*, int, int);
extern void sort_i(data_t*, int, int);
extern void sort_p(data_t*, int, int);
extern void sort_c(data_t*, int, int);
extern void sort_m(data_t*, int, int);
extern void sort_f(data_t*, int, int);

int main(int argc, char** argv) {
  int N, R, optchar, printFlag = 0, benchOnly = 0;
  unsigned int seed = 42;
  char* version = NULL;

  // an array of struct testFunc_t indicating the sort functions to test
  // the struct contains two fields --- the function pointer to the sort function
  // and its name (for printing)
  struct testFunc_t testFunc[] = {
    {&sort_a, "sort_a"},
    {&sort_i, "sort_i"},
    {&sort_p, "sort_p"},
    {&sort_c, "sort_c"},
    {&sort_m, "sort_m"},
    {&sort_f, "sort_f"},
  };
  const int kNumOfFunc = sizeof(testFunc) / sizeof(testFunc[0]);

  // process command line options
  while ((optchar = getopt(argc, argv, "s:pv:t:b")) != -1) {
    switch (optchar) {
    case 's':
      seed = (unsigned int) atoi(optarg);
      break;
    case 'p':
      printFlag = 1;
      break;
    case 'v':
      version = optarg;
      break;
    case 't':
      if (strcmp(optarg, "random") == 0) input_type = 0;
      else if (strcmp(optarg, "inverted") == 0) input_type = 1;
      else if (strcmp(optarg, "all") == 0) input_type = -1;
      else { fprintf(stderr, "Unknown input type: %s\n", optarg); return 1; }
      break;
    case 'b':
      benchOnly = 1;
      break;
    default:
      return 1;
    }
  }

  // shift remaining arguments over
  int remaining_args = argc - optind;
  for (int i = 1; i <= remaining_args; ++i) {
    argv[i] = argv[i + optind - 1];
  }

  // check to make sure number of arguments is correct
  if (remaining_args != 2) {
    printf("Usage: %s [-p] [-s seed] [-v sort_a] [-t random|inverted|all] [-b] <num_elements> <num_repeats>\n", argv[0]);
    printf("-p : print before/after arrays\n");
    exit(-1);
  }

  char* end;
  long n = strtol(argv[1], &end, 10);
  if (*end || n < 1 || n > INT_MAX) return 1;
  N = (int)n;
  long repeats = strtol(argv[2], &end, 10);
  if (*end || repeats < 1 || repeats > INT_MAX) return 1;
  R = (int)repeats;

  set_test_seed(seed);
  printf("Using seed: %u\n", seed);
  struct testFunc_t* selected = testFunc;
  int numFunc = kNumOfFunc;
  if (version) {
    int i;
    for (i = 0; i < kNumOfFunc; i++) {
      if (strcmp(version, testFunc[i].name) == 0) break;
    }
    if (i == kNumOfFunc) { fprintf(stderr, "Unknown version: %s\n", version); return 1; }
    selected = &testFunc[i];
    numFunc = 1;
  }
  run_test_suite(0, printFlag, N, R, benchOnly, selected, numFunc);

  return test_failures ? 1 : 0;
}
