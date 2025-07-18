#include "batcher.h"
#include "heap.h"
#include "insert.h"
#include "quick.h"
#include "shell.h"
#include "stats.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void print_help(const char *program_name) {
    printf("SYNOPSIS\n");
    printf("   A collection of comparison-based sorting algorithms.\n");
    printf("\nUSAGE\n");
    printf("   %s [-Hahbsqi] [-n length] [-p elements] [-r seed]\n", program_name);
    printf("\nOPTIONS\n");
    printf("   -H              Display program help and usage.\n");
    printf("   -a              Enable all sorts.\n");
    printf("   -h              Enable Heap Sort.\n");
    printf("   -b              Enable Batcher Sort.\n");
    printf("   -s              Enable Shell Sort.\n");
    printf("   -q              Enable Quick Sort.\n");
    printf("   -i              Enable Insertion Sort.\n");
    printf("   -n length       Specify the number of array elements (default: 100).\n");
    printf("   -p elements     Specify the number of elements to print (default: 100).\n");
    printf("   -r seed         Specify the random seed (default: 13371453).\n");
}
void print_array(const int *arr, int arr_size, int print_count) {
    for (int i = 0; i < arr_size && i < print_count; i++) {
        printf("%13d", arr[i]);
        if ((i + 1) % 5 == 0) {
            printf("\n");
        }
    }
    if (arr_size % 5 != 0) {
        printf("\n");
    }
    /*if (arr_size >= print_count) {
        printf("\n");
    }*/
    /*if ((print_count < 5) || (arr_size > 4 & arr_size < 11)) {
        printf("\n");
    }*/
}

int main(int argc, char *argv[]) {
    int arr_size = 100;
    int print_count = 100;
    unsigned int seed = 13371453;
    bool run_algorithms[] = { false, false, false, false, false };

    int opt;
    while ((opt = getopt(argc, argv, "Hahbsqin:p:r:")) != -1) {
        switch (opt) {
        case 'H': print_help(argv[0]); return 0;
        case 'a':
            for (int i = 0; i < 5; i++) {
                run_algorithms[i] = true;
            }
            break;
        case 'i': run_algorithms[0] = true; break;
        case 'h': run_algorithms[1] = true; break;
        case 's': run_algorithms[2] = true; break;
        case 'q': run_algorithms[3] = true; break;
        case 'b': run_algorithms[4] = true; break;
        case 'n': arr_size = atoi(optarg); break;
        case 'p': print_count = atoi(optarg); break;
        case 'r': seed = (unsigned int) atoi(optarg); break;
        default:
            fprintf(stderr, "Usage: %s [-Hahbsqi] [-n length] [-p elements] [-r seed]\n", argv[0]);
            exit(EXIT_FAILURE);
        }
    }

    if (optind == 1
        || (!run_algorithms[0] && !run_algorithms[1] && !run_algorithms[2] && !run_algorithms[3]
            && !run_algorithms[4])) {
        print_help(argv[0]);
        return 1;
    }

    if (optind == 1
        || (!run_algorithms[0] && !run_algorithms[1] && !run_algorithms[2] && !run_algorithms[3]
            && !run_algorithms[4])) {
        printf("Select at least one sort to perform.\n");
        printf("Use -H for help.\n");
        exit(EXIT_FAILURE);
    }

    int *arr = (int *) malloc(arr_size * sizeof(int));
    Stats stats;

    srandom(seed);

    for (int i = 0; i < arr_size; i++) {
        arr[i] = (int) (random() & 0x3FFFFFFF);
    }

    if (run_algorithms[0]) {
        insertion_sort(&stats, arr, arr_size);
        print_stats(&stats, "Insertion Sort", arr_size);
        print_array(arr, arr_size, print_count);
    }

    if (run_algorithms[1]) {
        reset(&stats);
        heap_sort(&stats, arr, arr_size);
        print_stats(&stats, "Heap Sort", arr_size);
        print_array(arr, arr_size, print_count);
    }

    if (run_algorithms[2]) {
        reset(&stats);
        shell_sort(&stats, arr, arr_size);
        print_stats(&stats, "Shell Sort", arr_size);
        print_array(arr, arr_size, print_count);
    }

    if (run_algorithms[3]) {
        reset(&stats);
        quick_sort(&stats, arr, arr_size);
        print_stats(&stats, "Quick Sort", arr_size);
        print_array(arr, arr_size, print_count);
    }

    if (run_algorithms[4]) {
        reset(&stats);
        batcher_sort(&stats, arr, arr_size);
        print_stats(&stats, "Batcher Sort", arr_size);
        print_array(arr, arr_size, print_count);
        //printf("\n");
    }

    free(arr);
    return 0;
}
