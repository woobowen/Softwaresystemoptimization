// Copyright (c) 2012 MIT License by 6.172 Staff

#include <stdio.h>
#include <stdint.h>

#define PRINT_SIZE(type) \
  printf("size of %s : %zu bytes\n", #type, sizeof(type)); \
  printf("size of %s* : %zu bytes\n", #type, sizeof(type*))

int main() {
  typedef struct {
    int id;
    int year;
  } student;

  student you;
  you.id = 12345;
  you.year = 4;
  int x[5];

  PRINT_SIZE(int);
  PRINT_SIZE(short);
  PRINT_SIZE(long);
  PRINT_SIZE(char);
  PRINT_SIZE(float);
  PRINT_SIZE(double);
  PRINT_SIZE(unsigned int);
  PRINT_SIZE(long long);
  PRINT_SIZE(uint8_t);
  PRINT_SIZE(uint16_t);
  PRINT_SIZE(uint32_t);
  PRINT_SIZE(uint64_t);
  PRINT_SIZE(uint_fast8_t);
  PRINT_SIZE(uint_fast16_t);
  PRINT_SIZE(uintmax_t);
  PRINT_SIZE(intmax_t);
  PRINT_SIZE(__int128);
  printf("size of student : %zu bytes\n", sizeof(you));
  printf("size of student* : %zu bytes\n", sizeof(&you));
  printf("size of x : %zu bytes\n", sizeof(x));
  // &x points to the entire array, rather than its first element.
  printf("size of &x : %zu bytes\n", sizeof(&x));

  return 0;
}
