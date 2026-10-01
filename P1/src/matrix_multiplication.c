#define _POSIX_C_SOURCE 200809L
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <assert.h>

#define n 4096

double A[n][n];
double B[n][n];
double C[n][n];

float tdiff(struct timespec *start,
            struct timespec *end) {
    return(end->tv_sec-start->tv_sec) +
        1e-9*(end->tv_nsec-start->tv_nsec);
}

int main(int argc, const char *argv[]){
    if (argc != 2) {
        fprintf(stderr, "Usage: %s block_size\n", argv[0]);
        return 1;
    }
    char *tail;
    long block = strtol(argv[1], &tail, 10);
    if (tail == argv[1] || *tail != '\0' || block < 1 || block > n) {
        printf("Invalid input values.\n");
        return -1;
    }

    int s = (int)block;

    for(int i = 0; i < n; ++i){
        for(int j = 0; j < n; ++j) {
            A[i][j] = (double)rand() / (double)RAND_MAX;
            B[i][j] = (double)rand() / (double)RAND_MAX;
            C[i][j] = 0;
        }
    }

    struct timespec start, end;
    if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) return 1;

    for(int ih = 0; ih < n; ih += s)
        for(int jh = 0; jh < n; jh += s)
            for(int kh = 0; kh < n; kh += s)
                for(int il = 0; il < s && ih + il < n; ++il)
                    for(int kl = 0; kl < s && kh + kl < n; ++kl)
                        for(int jl = 0; jl < s && jh + jl < n; ++jl)
                            C[ih+il][jh+jl] += A[ih+il][kh+kl] * B[kh+kl][jh+jl];

    if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) return 1;
    printf("%0.6f\n",tdiff(&start, &end));
    /* Consume the result after timing so every build computes C. */
    double checksum = 0.0;
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j)
            checksum += C[i][j];
    printf("checksum=%.17g\n", checksum);
    return 0;
}
