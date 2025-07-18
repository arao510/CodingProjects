#include "bmp.h"
#include "io.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function prototypes
void bmp_free(BMP **ppbmp);
void print_help(void);
void process_file(const char *input_filename, const char *output_filename);

int main(int argc, char *argv[]) {
    // Check the number of command-line arguments
    if (argc != 5) {
        fprintf(stderr, "Error: Incorrect number of arguments.\n");
        print_help();
        return EXIT_FAILURE;
    }

    // Command-line options
    const char *input_option = argv[1];
    const char *input_filename = argv[2];
    const char *output_option = argv[3];
    const char *output_filename = argv[4];

    // Check input option
    if (strcmp(input_option, "-i") != 0) {
        fprintf(stderr, "Error: Invalid input option.\n");
        print_help();
        return EXIT_FAILURE;
    }

    // Check output option
    if (strcmp(output_option, "-o") != 0) {
        fprintf(stderr, "Error: Invalid output option.\n");
        print_help();
        return EXIT_FAILURE;
    }

    // Process the file
    process_file(input_filename, output_filename);

    return EXIT_SUCCESS;
}

void print_help(void) {
    printf("Usage: colorb -i <input_file> -o <output_file>\n");
    printf("-i : Sets the name of the input file. Requires a filename as an argument.\n");
    printf("-o : Sets the name of the output file. Requires a filename as an argument.\n");
    printf("-h : Prints a help message to stdout.\n");
}

void process_file(const char *input_filename, const char *output_filename) {
    // Open the input file
    FILE *input_file = fopen(input_filename, "rb");
    if (!input_file) {
        perror("Error opening input file");
        exit(EXIT_FAILURE);
    }

    // Create BMP structure from input file
    BMP *image = bmp_create(input_file);

    // Close the input file
    fclose(input_file);

    // Perform some operation on the BMP data (e.g., reduce palette)
    bmp_reduce_palette(image);

    // Open the output file
    FILE *output_file = fopen(output_filename, "wb");
    if (!output_file) {
        perror("Error opening output file");
        bmp_free(&image);
        exit(EXIT_FAILURE);
    }

    // Write the modified BMP data to the output file
    bmp_write(image, output_file);

    // Close the output file
    fclose(output_file);

    // Free the BMP structure
    bmp_free(&image);
}
