#include "io.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void read_uint8(FILE *fin, uint8_t *px) {
    int result = fgetc(fin);
    if (result == EOF) {
        fprintf(stderr, "Unexpected end of file.\n");
        exit(EXIT_FAILURE);
    }
    *px = (uint8_t) result;
}

void read_uint16(FILE *fin, uint16_t *px) {
    uint8_t low, high;
    read_uint8(fin, &low);
    read_uint8(fin, &high);
    *px = (uint16_t) (low | (high << 8));
}

void read_uint32(FILE *fin, uint32_t *px) {
    uint16_t low, high;
    read_uint16(fin, &low);
    read_uint16(fin, &high);
    *px = (uint32_t) (low | (high << 16));
}

void write_uint8(FILE *fout, uint8_t x) {
    int result = fputc(x, fout);
    if (result == EOF) {
        fprintf(stderr, "Unable to write to file.\n");
        exit(EXIT_FAILURE);
    }
}

void write_uint16(FILE *fout, uint16_t x) {
    write_uint8(fout, (uint8_t) x);
    write_uint8(fout, (uint8_t) (x >> 8));
}

void write_uint32(FILE *fout, uint32_t x) {
    write_uint16(fout, (uint16_t) x);
    write_uint16(fout, (uint16_t) (x >> 16));
}
