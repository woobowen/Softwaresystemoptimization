#include <cilk/cilk.h>
#include <stdio.h>

int main(void) {
  int values[64];
  cilk_for (int i = 0; i < 64; ++i) {
    values[i] = i * i;
  }
  int sum = 0;
  for (int i = 0; i < 64; ++i) {
    sum += values[i];
  }
  printf("sum = %d\n", sum);
  return sum != 85344;
}
