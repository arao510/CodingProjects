#include "bmp.h"

#include "io.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_COLORS 256

typedef struct color {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} Color;

typedef struct bmp {
    uint32_t height;
    uint32_t width;
    Color palette[MAX_COLORS];
    uint8_t **a;
} BMP;

uint32_t round_up(uint32_t x, uint32_t n) {
    while (x % n != 0) {
        x = x + 1;
    }
    return x;
}

BMP *bmp_create(FILE *fin) {
    (void) fin;

    BMP *pbmp = (BMP *) calloc(1, sizeof(BMP));
    if (pbmp == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        exit(EXIT_FAILURE);
    }

    // Read data from the input file
    // Implement the reading logic as described in the comments

    return pbmp;
}

void bmp_write(const BMP *pbmp, FILE *fout) {
    (void) pbmp;
    (void) fout;
    //uint32_t rounded_width = round_up(pbmp->width, 4);
    //int32_t image_size = pbmp->height * rounded_width;
    //int32_t file_header_size = 14;
    //int32_t bitmap_header_size = 40;
    //int32_t num_colors = MAX_COLORS;
    //int32_t palette_size = 4 * num_colors;
    //int32_t bitmap_offset = file_header_size + bitmap_header_size + palette_size;
    // Unused variable file_size removed.

    // Write data to the output file
    // Implement the writing logic as described in the comments
}

void bmp_free(BMP **ppbmp) {
    if (*ppbmp == NULL) {
        return; // Avoid dereferencing a NULL pointer
    }
    for (uint32_t i = 0; i < (*ppbmp)->width; ++i) {
        free((*ppbmp)->a[i]);
    }
    free((*ppbmp)->a);
    free(*ppbmp);
    *ppbmp = NULL;
}

uint8_t constrain(double x) {
    x = round(x);
    if (x < 0) {
        x = 0;
    }
    if (x > UINT8_MAX) {
        x = UINT8_MAX;
    }

    return (uint8_t) x;
}

void bmp_reduce_palette(BMP *pbmp) {
    for (int i = 0; i < MAX_COLORS; ++i) {
        uint8_t r = pbmp->palette[i].red;
        uint8_t g = pbmp->palette[i].green;
        uint8_t b = pbmp->palette[i].blue;

        double SqLe = 0.00999 * r + 0.0664739 * g + 0.7317 * b;
        double SeLq = 0.153384 * r + 0.316624 * g + 0.057134 * b;

        uint8_t r_new, g_new, b_new;

        if (SqLe < SeLq) {
            r_new = constrain(0.426331 * r + 0.875102 * g + 0.0801271 * b);
            g_new = constrain(0.281100 * r + 0.571195 * g + -0.0392627 * b);
            b_new = constrain(-0.0177052 * r + 0.0270084 * g + 1.00247 * b);
        } else {
            r_new = constrain(0.758100 * r + 1.45387 * g + -1.48060 * b);
            g_new = constrain(0.118532 * r + 0.287595 * g + 0.725501 * b);
            b_new = constrain(-0.00746579 * r + 0.0448711 * g + 0.954303 * b);
        }

        pbmp->palette[i].red = r_new;
        pbmp->palette[i].green = g_new;
        pbmp->palette[i].blue = b_new;
    }
}
