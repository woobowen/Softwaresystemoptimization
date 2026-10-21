// Additional uint32_t-domain checks for the two sentinel-free versions.
#include "sort.h"
#include <string.h>

static int compare(const void* a, const void* b) {
  data_t x = *(const data_t*)a, y = *(const data_t*)b;
  return (x > y) - (x < y);
}

int main(void) {
  void (*versions[])(data_t*, int, int) = {sort_m, sort_f};
  const int lengths[] = {0, 1, 2, 3, 31, 32, 33, 63, 64, 65, 255, 257, 1023};
  unsigned int seed = 7;
  int cases = 0;
  for (int v = 0; v < 2; v++) {
    for (int size = 0; size < sizeof(lengths) / sizeof(lengths[0]); size++) {
      for (int mode = 0; mode < 3; mode++) {
        data_t actual[1030], expected[1030];
        int n = lengths[size], p = 3, total = n + 6;
        for (int i = 0; i < total; i++) actual[i] = 0xabcdef01;
        for (int i = 0; i < n; i++) {
          actual[p + i] = mode == 0 ? UINT_MAX : mode == 1 ? (i % 2 ? UINT_MAX : 0)
              : ((data_t)rand_r(&seed) << 1) | (rand_r(&seed) & 1);
        }
        memcpy(expected, actual, total * sizeof(data_t));
        qsort(expected + p, n, sizeof(data_t), compare);
        versions[v](actual, p, p + n - 1);
        if (memcmp(actual, expected, total * sizeof(data_t))) return 1;
        cases++;
      }
    }
  }
  printf("m/f full uint32_t domain: %d qsort cases passed\n", cases);
  return 0;
}
