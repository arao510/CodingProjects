#include "gaps.h"
#include "stats.h"

#include <stdio.h>

void shell_sort(Stats *stats, int *A, int length) {
    int k, j, temp;
    for (int gap_index = 0; gap_index < GAPS; gap_index++) {
        int gap = gaps[gap_index];
        for (k = gap; k < length; k++) {
            temp = move(stats, A[k]);
            j = k;
            while (j >= gap && cmp(stats, A[j - gap], temp) > 0) {
                A[j] = move(stats, A[j - gap]);
                j -= gap;
            }
            A[j] = move(stats, temp);
        }
    }
}
