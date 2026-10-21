/**
 * Copyright (c) 2012 MIT License by 6.172 Staff
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


#include "./sort.h"
#include "./coarsen.h"

// Function prototypes
static void merge_m(data_t* A, int p, int q, int r);
static void copy_m(data_t* source, data_t* dest, int n);

// A basic merge sort routine that sorts the subarray A[p..r]
void sort_m(data_t* A, int p, int r) {
  assert(A);
  if (p >= r) return;
  if (r - p + 1 <= COARSE_THRESHOLD) {
    isort(A + p, A + r);
    return;
  }
  if (p < r) {
    int q = (p + r) / 2;
    sort_m(A, p, q);
    sort_m(A, q + 1, r);
    merge_m(A, p, q, r);
  }
}

// A merge routine. Merges the sub-arrays A [p..q] and A [q + 1..r].
// Copy only the left half; read the right half directly from A.
static void merge_m(data_t* A, int p, int q, int r) {
  assert(A);
  assert(p <= q);
  assert((q + 1) <= r);
  int n1 = q - p + 1;
  data_t* left = 0;
  mem_alloc(&left, n1);
  if (left == NULL) return;
  copy_m(A + p, left, n1);

  int i = 0, j = q + 1, k = p;
  // While left remains, k < j: writing A[k] cannot overwrite unread A[j].
  while (i < n1 && j <= r) {
    if (left[i] <= A[j]) A[k++] = left[i++];
    else A[k++] = A[j++];
  }
  while (i < n1) A[k++] = left[i++];
  // Any remaining right-side elements are already in their final positions.
  mem_free(&left);
}

static void copy_m(data_t* source, data_t* dest, int n) {
  assert(dest);
  assert(source);

  for (int i = 0 ; i < n ; i++) {
    dest[i] = source[i];
  }
}
