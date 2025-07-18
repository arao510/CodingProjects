#include "insert.h"

#include "stats.h"

#include <stdio.h>

void insertion_sort(Stats *stats, int *arr, int length) {
    int k, j, key;
    for (k = 1; k < length; k++) {
        key = arr[k];
        j = k - 1;

        while (j >= 0 && cmp(stats, arr[j], key) > 0) {
            arr[j + 1] = move(stats, arr[j]);
            j = j - 1;
        }
        arr[j + 1] = move(stats, key);
    }
}
