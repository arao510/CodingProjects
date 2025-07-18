#include "bmp.h"

#include "io.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

// Define MAX_COLORS and the Color structure
#define MAX_COLORS 256

typedef struct color {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} Color;

// Define the BMP structure
typedef struct bmp {
    uint32_t height;
    uint32_t width;
    ////Color palette[MAX_COLORS];
    Color *palette; // Change from array to pointer
    uint8_t **a;
} BMP;

static uint32_t round_up(uint32_t x, uint32_t n) {
    return (x + n - 1) & ~(n - 1);
}

static void local_read_uint8(FILE *fin, uint8_t *px) {
    fread(px, sizeof(uint8_t), 1, fin);
}

static void local_read_uint16(FILE *fin, uint16_t *px) {
    fread(px, sizeof(uint16_t), 1, fin);
}

static void local_read_uint32(FILE *fin, uint32_t *px) {
    fread(px, sizeof(uint32_t), 1, fin);
}

BMP *bmp_create(FILE *fin) {
    BMP *pbmp = calloc(1, sizeof(BMP));
    if (pbmp == NULL) {
        fprintf(stderr, "Fatal error: Memory allocation failed for BMP struct\n");
        return NULL;
    }

    uint8_t type1, type2;
    uint32_t dummy32;
    uint16_t dummy16;
    uint8_t dummy8;
    local_read_uint8(fin, &type1);
    local_read_uint8(fin, &type2);

    local_read_uint32(fin, &dummy32);
    local_read_uint8(fin, &dummy8);
    local_read_uint16(fin, &dummy16);

    uint32_t bitmap_header_size;
    fseek(fin, 14, SEEK_SET);
    local_read_uint32(fin, &bitmap_header_size);
    local_read_uint32(fin, &pbmp->width);
    local_read_uint32(fin, &pbmp->height);

    // Skip and read more header information
    local_read_uint16(fin, &dummy16);
    uint16_t bits_per_pixel;
    local_read_uint16(fin, &bits_per_pixel);
    uint32_t compression;
    local_read_uint32(fin, &compression);

    local_read_uint32(fin, &dummy32);
    local_read_uint32(fin, &dummy32);
    local_read_uint32(fin, &dummy32);

    // Read colors used and skip
    uint32_t colors_used;
    local_read_uint32(fin, &colors_used);
    local_read_uint32(fin, &dummy32);

    if (type1 != 'B' || type2 != 'M' || bitmap_header_size != 40 || bits_per_pixel != 8
        || compression != 0) {
        fprintf(stderr, "Invalid BMP file format\n");
        fprintf(stderr, "Type: %c%c, Header Size: %u, Bits per Pixel: %u, Compression: %u\n", type1,
            type2, bitmap_header_size, bits_per_pixel, compression);
        free(pbmp);
        return NULL;
    }
    // Determine the number of colors
    uint32_t num_colors = colors_used == 0 ? (1 << bits_per_pixel) : colors_used;
    // Allocate memory for the palette
    pbmp->palette = malloc(num_colors * sizeof(Color));
    // Read the color palette
    pbmp->palette = malloc(num_colors * sizeof(Color));
    if (pbmp->palette == NULL) {
        fprintf(stderr, "Memory allocation failed for color palette\n");
        free(pbmp->a);
        free(pbmp);
        return NULL;
    }

    for (uint32_t i = 0; i < num_colors; i++) {

        local_read_uint8(fin, &pbmp->palette[i].blue);
        local_read_uint8(fin, &pbmp->palette[i].green);
        local_read_uint8(fin, &pbmp->palette[i].red);
        local_read_uint8(fin, &dummy8); // Skip uint8 (palette padding)
    }

    // Allocate pixel array
    uint32_t rounded_width = round_up(pbmp->width, 4);

    pbmp->a = calloc(pbmp->width, sizeof(uint8_t *));

    for (uint32_t x = 0; x < pbmp->width; x++) {

        pbmp->a[x] = calloc(pbmp->height, sizeof(uint8_t));
        if (pbmp->a[x] == NULL) {
            fprintf(stderr, "Memory allocation failed for pixel array\n");

            while (x > 0) {
                free(pbmp->a[--x]);
            }
            free(pbmp->a);
            free(pbmp);
            return NULL;
        }
    }

    // Read pixels
    for (uint32_t y = 0; y < pbmp->height; y++) {
        for (uint32_t x = 0; x < pbmp->width; x++) {
            local_read_uint8(fin, &pbmp->a[x][y]);
        }
        // Skip any extra pixels per row for alignment
        for (uint32_t x = pbmp->width; x < rounded_width; x++) {
            local_read_uint8(fin, &dummy8); // Skip uint8
        }
    }

    return pbmp;
}
// Function to write a BMP struct to a file
void bmp_write(const BMP *pbmp, FILE *fout) {
    if (pbmp == NULL || fout == NULL) {
        fprintf(stderr, "Invalid BMP struct or file pointer\n");
        return;
    }

    // Calculate various sizes and offsets
    uint32_t image_size = pbmp->height * round_up(pbmp->width, 4);
    uint32_t file_header_size = 14;
    uint32_t bitmap_header_size = 40;
    uint32_t palette_size = MAX_COLORS * 4; // 4 bytes per color
    uint32_t bitmap_offset = file_header_size + bitmap_header_size + palette_size;
    uint32_t file_size = bitmap_offset + image_size;

    // Write BMP file header
    write_uint8(fout, 'B');
    write_uint8(fout, 'M');
    write_uint32(fout, file_size);
    write_uint16(fout, 0); // Reserved
    write_uint16(fout, 0); // Reserved
    write_uint32(fout, bitmap_offset);

    // Write DIB header
    write_uint32(fout, bitmap_header_size);
    write_uint32(fout, pbmp->width);
    write_uint32(fout, pbmp->height);
    write_uint16(fout, 1); // Color planes
    write_uint16(fout, 8); // Bits per pixel
    write_uint32(fout, 0); // Compression
    write_uint32(fout, image_size);
    write_uint32(fout, 2835); // Horizontal resolution
    write_uint32(fout, 2835); // Vertical resolution
    write_uint32(fout, MAX_COLORS); // Number of colors in the palette
    write_uint32(fout, MAX_COLORS); // Important colors

    // Write the color palette
    for (uint32_t i = 0; i < MAX_COLORS; i++) {
        write_uint8(fout, pbmp->palette[i].blue);
        write_uint8(fout, pbmp->palette[i].green);
        write_uint8(fout, pbmp->palette[i].red);
        write_uint8(fout, 0); // Reserved
    }

    // Write the pixel data
    uint32_t rounded_width = round_up(pbmp->width, 4);
    for (uint32_t y = 0; y < pbmp->height; y++) {
        for (uint32_t x = 0; x < pbmp->width; x++) {
            write_uint8(fout, pbmp->a[x][y]);
        }
        // Write extra padding bytes if needed
        for (uint32_t x = pbmp->width; x < rounded_width; x++) {
            write_uint8(fout, 0);
        }
    }
}

// Function to free memory of a BMP struct
void bmp_free(BMP **bmp) {
    if (bmp && *bmp) {
        BMP *pbmp = *bmp;

        free(pbmp->palette);

        for (uint32_t i = 0; i < pbmp->width; i++) {
            free(pbmp->a[i]);
        }
        free(pbmp->a);
        free(pbmp);
        *bmp = NULL;
    }
}

// Constrain
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
    for (int i = 0; i < MAX_COLORS; i++) {
        double r = pbmp->palette[i].red;
        double g = pbmp->palette[i].green;
        double b = pbmp->palette[i].blue;

        double SqLe = 0.00999 * r + 0.0664739 * g + 0.7317 * b;
        double SeLq = 0.153384 * r + 0.316624 * g + 0.057134 * b;

        double r_new, g_new, b_new;
        if (SqLe < SeLq) {
            r_new = constrain(0.426331 * r + 0.875102 * g + 0.0801271 * b);
            g_new = constrain(0.281100 * r + 0.571195 * g - 0.0392627 * b);
            b_new = constrain(-0.0177052 * r + 0.0270084 * g + 1.00247 * b);
        } else {
            r_new = constrain(0.758100 * r + 1.45387 * g - 1.48060 * b);
            g_new = constrain(0.118532 * r + 0.287595 * g + 0.725501 * b);
            b_new = constrain(-0.00746579 * r + 0.0448711 * g + 0.954303 * b);
        }

        //printf("Before - Red: %u, Green: %u, Blue: %u\n", pbmp->palette[i].red, pbmp->palette[i].green, pbmp->palette[i].blue);

        pbmp->palette[i].red = (uint8_t) r_new;
        pbmp->palette[i].green = (uint8_t) g_new;
        pbmp->palette[i].blue = (uint8_t) b_new;
    }
}
