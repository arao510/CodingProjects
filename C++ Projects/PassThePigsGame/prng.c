#include <stdio.h>
#include <stdlib.>
#define SEED 2023
int main(void) {
    for (int i = 0; i < 3; i += 1) {
        printf("Set the random seed.\n");
        srandom(SEED);
        for (int j = 0; j < 5; j += 1) {
            printf(" - generated %lu\n", random());
        }
        return 0;
    }
