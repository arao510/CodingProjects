#include "bitreader.h"

#include <stdio.h>
#include <stdlib.h>

struct BitReader {
    FILE *underlying_stream;
    uint8_t byte;
    uint8_t bit_position;
};

BitReader *bit_read_open(const char *filename) {
    BitReader *br = malloc(sizeof(BitReader));
    if (!br) {
        return NULL;
    }

    br->underlying_stream = fopen(filename, "rb");
    if (!br->underlying_stream) {
        free(br);
        return NULL;
    }

    br->byte = 0;
    br->bit_position = 8;

    return br;
}

void bit_read_close(BitReader **pbuf) {
    if (pbuf && *pbuf) {
        fclose((*pbuf)->underlying_stream);
        free(*pbuf);
        *pbuf = NULL;
    }
}

uint8_t bit_read_bit(BitReader *buf) {
    if (!buf) {
        // Handle error: invalid buffer
        exit(EXIT_FAILURE);
    }

    if (buf->bit_position > 7) {
        int c = fgetc(buf->underlying_stream);
        if (c == EOF) {

            exit(EXIT_FAILURE);
        }
        buf->byte = (uint8_t) c;
        buf->bit_position = 0;
    }

    uint8_t bit = (buf->byte >> buf->bit_position) & 1;
    buf->bit_position++;
    return bit;
}

uint8_t bit_read_uint8(BitReader *buf) {
    uint8_t value = 0;
    for (int i = 0; i < 8; i++) {
        uint8_t bit = bit_read_bit(buf);
        value |= (bit << i);
    }
    return value;
}

uint16_t bit_read_uint16(BitReader *buf) {
    uint16_t value = 0;
    for (int i = 0; i < 16; i++) {
        uint16_t bit = bit_read_bit(buf);
        value |= (bit << i);
    }
    return value;
}

uint32_t bit_read_uint32(BitReader *buf) {
    uint32_t value = 0;
    for (int i = 0; i < 32; i++) {
        uint32_t bit = bit_read_bit(buf);
        value |= (bit << i);
    }
    return value;
}
