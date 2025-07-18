#include "bmp.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function declarations for bmp processing
BMP *bmp_create(FILE *fin);
void bmp_write(const BMP *pbmp, FILE *fout);
void bmp_free(BMP **pbmp);
void bmp_reduce_palette(BMP *pbmp);

// Function to print help message
void print_help(void);

int main(int argc, char *argv[]) {
    ///printf("Debug: Inside main function\n");

    if (strcmp(argv[1], "-h") == 0) {
        //printf("Debug: Help option detected\n"); // Debug message
        print_help();
        return EXIT_SUCCESS;
        //return EXIT_FAILURE;
    }

    if (argc < 5) {
        //fprintf(stderr, "Debug: Too few arguments\n"); // Debug message
        print_help();
        return EXIT_FAILURE;
    }

    char *input_filename = NULL;
    char *output_filename = NULL;

    // Parse command line argument

    for (int i = 1; i < argc; i += 2) {
        if (strcmp(argv[i], "-i") == 0) {
            input_filename = argv[i + 1];
        } else if (strcmp(argv[i], "-o") == 0) {
            output_filename = argv[i + 1];
        }
    }

    // Check if input and output files are provided
    if (input_filename == NULL || output_filename == NULL) {
        fprintf(stderr, "Debug: Input or output file not provided\n"); // Debug message
        print_help();
        return EXIT_FAILURE;
    }
    /*if (strcmp(argv[1], "-h") == 0) {
        printf("Debug: Help option detected\n"); // Debug message
        print_help();
        //return EXIT_SUCCESS;
        return EXIT_FAILURE;
    }*/

    // Open input file
    FILE *fin = fopen(input_filename, "rb");
    if (fin == NULL) {
        fprintf(stderr, "Error: Unable to open input file %s\n", input_filename);
        return EXIT_FAILURE;
    }

    // Create BMP struct from input file
    BMP *pbmp = bmp_create(fin);
    fclose(fin);
    if (pbmp == NULL) {
        fprintf(stderr, "Error: Unable to create BMP from input file\n");
        return EXIT_FAILURE;
    }

    // Process BMP file
    ////printf("Processing BMP file...\n");
    bmp_reduce_palette(pbmp);

    // Write processed BMP to output file
    FILE *fout = fopen(output_filename, "wb");
    if (fout == NULL) {
        fprintf(stderr, "Error: Unable to open output file %s\n", output_filename);
        bmp_free(&pbmp);
        return EXIT_FAILURE;
    }

    bmp_write(pbmp, fout);
    fclose(fout);

    // Clean up
    bmp_free(&pbmp);

    return EXIT_SUCCESS;
}

// Function to print help message
void print_help(void) {
    printf("Usage: colorb -i infile -o outfile\n");
    printf("       colorb -h\n");
    //printf("  -i    Sets the name of the input file.\n");
    //printf("  -o    Sets the name of the output file.\n");
    //printf("  -h    Prints this help message.\n");
}
