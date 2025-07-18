#include "bitwriter.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct BitWriter {
    FILE *underlying_stream;
    uint8_t byte;
    uint8_t bit_position;

} BitWriter;

/*typedef struct BitWriter {
    FILE *underlying_stream;
    uint8_t byte;
    uint8_t bit_position;
} BitWriter;*/

//bitwrite open
BitWriter *bit_write_open(const char *filename) {
    BitWriter *bw = malloc(sizeof(BitWriter));
    if (!bw) {
        return NULL;
    }

    bw->underlying_stream = fopen(filename, "wb");
    if (!bw->underlying_stream) {
        free(bw);
        return NULL;
    }

    bw->byte = 0;
    bw->bit_position = 0;

    return bw;
}

//bitwriteclose
void bit_write_close(BitWriter **pbuf) {
    if (pbuf && *pbuf) {
        if ((*pbuf)->bit_position > 0) {
            fputc((*pbuf)->byte, (*pbuf)->underlying_stream);
        }

        fclose((*pbuf)->underlying_stream);
        free(*pbuf);
        *pbuf = NULL;
    }
}

//bitwrite bit
void bit_write_bit(BitWriter *buf, uint8_t x) {
    if (!buf) {
        return;
    }

    if (buf->bit_position > 7) {
        fputc(buf->byte, buf->underlying_stream);
        buf->byte = 0;
        buf->bit_position = 0;
    }

    buf->byte |= (x << buf->bit_position);
    buf->bit_position++;
}

//bit write uint8
void bit_write_uint8(BitWriter *buf, uint8_t x) {
    for (int i = 0; i < 8; i++) {
        bit_write_bit(buf, (x >> i) & 1);
    }
}

//bit write uint16
void bit_write_uint16(BitWriter *buf, uint16_t x) {
    for (int i = 0; i < 16; i++) {
        bit_write_bit(buf, (x >> i) & 1);
    }
}

//bit write uint32
void bit_write_uint32(BitWriter *buf, uint32_t x) {
    for (int i = 0; i < 32; i++) {
        bit_write_bit(buf, (x >> i) & 1);
    }
}
