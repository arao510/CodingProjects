// Header file for CSE 13S-01, Fall 2023, asgn6
// bmp.h
// Made by Dr. Kerry Veenstra
// DO NOT modify this file.

#include "io.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>

#define MAX_COLORS 256

typedef struct bmp BMP;
BMP *bmp_create(FILE *fin);
void bmp_free(BMP **ppbmp);
void bmp_write(const BMP *pbmp, FILE *fout);
void bmp_reduce_palette(BMP *pbmp);
