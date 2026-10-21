// Link-time wrapping counts allocations inside one sort, without timing it.
#include "sort.h"

void* __real_malloc(size_t size);
void __real_free(void* ptr);
static unsigned long allocations, releases;
static int counting;

void* __wrap_malloc(size_t size) {
  if (counting) allocations++;
  return __real_malloc(size);
}

void __wrap_free(void* ptr) {
  if (counting && ptr) releases++;
  __real_free(ptr);
}

int main(void) {
  void (*versions[])(data_t*, int, int) = {sort_a, sort_i, sort_p, sort_c, sort_m, sort_f};
  const char* names[] = {"sort_a", "sort_i", "sort_p", "sort_c", "sort_m", "sort_f"};
  int n = 1048576;
  data_t* data = malloc(n * sizeof(data_t));
  if (!data) return 1;
  for (int v = 0; v < 6; v++) {
    unsigned int seed = 42;
    for (int i = 0; i < n; i++) data[i] = rand_r(&seed);
    allocations = releases = 0;
    counting = 1;
    versions[v](data, 0, n - 1);
    counting = 0;
    for (int i = 1; i < n; i++) if (data[i - 1] > data[i]) return 1;
    printf("%s n=%d malloc=%lu free=%lu\n", names[v], n, allocations, releases);
  }
  free(data);
  return 0;
}
