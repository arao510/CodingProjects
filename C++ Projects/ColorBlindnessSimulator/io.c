#include "io.h"

#include <stdint.h>
#include <stdio.h>

// Read a single byte (uint8_t) from a file
void read_uint8(FILE *fp, uint8_t *value) {
    fread(value, sizeof(uint8_t), 1, fp);
}

// Read a 2-byte word (uint16_t) from a file

void read_uint16(FILE *fp, uint16_t *value) {
    uint8_t bytes[2];
    fread(bytes, sizeof(uint8_t), 2, fp);
    *value = (uint16_t) bytes[0] | ((uint16_t) (bytes[1] << 8));
}

// Read a 4-byte dword (uint32_t) from a file
void read_uint32(FILE *fp, uint32_t *value) {
    uint8_t bytes[4];
    fread(bytes, sizeof(uint8_t), 4, fp);
    *value = (uint32_t) bytes[0] | ((uint32_t) bytes[1] << 8) | ((uint32_t) bytes[2] << 16)
             | ((uint32_t) bytes[3] << 24);
}

// Write a single byte (uint8_t) to a file
void write_uint8(FILE *fp, uint8_t value) {
    fwrite(&value, sizeof(uint8_t), 1, fp);
}

// Write a 2-byte word (uint16_t) to a file
void write_uint16(FILE *fp, uint16_t value) {
    uint8_t bytes[2] = { value & 0xFF, (value >> 8) & 0xFF };
    fwrite(bytes, sizeof(uint8_t), 2, fp);
}

// Write a 4-byte dword (uint32_t) to a file
void write_uint32(FILE *fp, uint32_t value) {
    uint8_t bytes[4]
        = { value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF };
    fwrite(bytes, sizeof(uint8_t), 4, fp);
}

// Skip a given number of bytes in a file
void skip_bytes(FILE *fp, size_t num_bytes) {
    fseek(fp, (long) num_bytes, SEEK_CUR);
}
