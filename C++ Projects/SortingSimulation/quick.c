#include "quick.h"

#include <stdio.h>

int partition(Stats *stats, int *A, int lo, int hi) {
    int pivot = A[hi];
    int i = lo - 1;

    for (int j = lo; j < hi; j++) {
        if (cmp(stats, A[j], pivot) < 0) {
            i++;
            swap(stats, &A[i], &A[j]);
        }
    }
    i++;
    swap(stats, &A[i], &A[hi]);
    return i;
}

void quick_sorter(Stats *stats, int *A, int lo, int hi) {
    if (lo < hi) {
        int p = partition(stats, A, lo, hi);
        quick_sorter(stats, A, lo, p - 1);
        quick_sorter(stats, A, p + 1, hi);
    }
}

void quick_sort(Stats *stats, int *A, int n) {
    quick_sorter(stats, A, 0, n - 1);
}
