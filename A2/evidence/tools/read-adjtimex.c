#include <stdio.h>
#include <sys/timex.h>
#include <unistd.h>

int main(void) {
    struct timex value = {0}; /* modes = 0 queries; it does not change the clock. */
    int state = adjtimex(&value);
    if (state < 0) {
        perror("adjtimex");
        return 1;
    }
    printf("state=%d status=%d tick=%ld freq_scaled_ppm=%ld offset=%ld "
           "tolerance=%ld constant=%ld precision=%ld\n",
           state, value.status, value.tick, value.freq, value.offset,
           value.tolerance, value.constant, value.precision);
    return 0;
}
