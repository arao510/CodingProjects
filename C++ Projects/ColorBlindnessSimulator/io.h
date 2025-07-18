// Header file for CSE 13S-01, Fall 2023, asgn6
// io.h
// Made by Dr. Kerry Veenstra
// DO NOT modify this file.

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>

void read_uint8(FILE *fin, uint8_t *px);
void read_uint16(FILE *fin, uint16_t *px);
void read_uint32(FILE *fin, uint32_t *px);

void write_uint8(FILE *fout, uint8_t x);
void write_uint16(FILE *fout, uint16_t x);
void write_uint32(FILE *fout, uint32_t x);
