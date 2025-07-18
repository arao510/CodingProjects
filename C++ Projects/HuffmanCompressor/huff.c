#include "bitreader.h"
#include "bitwriter.h"
#include "node.h"
#include "pq.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define HISTOGRAM_SIZE 256
//stores Huffman Code
typedef struct Code {
    uint64_t code;
    uint8_t code_length;
} Code;

void huff_write_tree(BitWriter *outbuf, Node *node);

//function that fills histogram with frequency of each byte of input file
uint32_t fill_histogram(FILE *fin, uint32_t *histogram) {
    uint32_t filesize = 0;
    int byte;

    //initialiation of histogram array
    for (int i = 0; i < HISTOGRAM_SIZE; i++) {
        histogram[i] = 0;
    }
    //hack
    histogram[0x00]++;
    histogram[0xff]++;

    //frequency of each byte recorded with loop
    while ((byte = fgetc(fin)) != EOF) {
        histogram[byte]++;
        filesize++;
    }

    return filesize;
}

//create function
Node *create_tree(uint32_t *histogram, uint16_t *num_leaves) {
    PriorityQueue *pq = pq_create();
    *num_leaves = 0;

    for (int i = 0; i < HISTOGRAM_SIZE; i++) {
        if (histogram[i] > 0) {
            enqueue(pq, node_create((uint8_t) i, histogram[i]));
            (*num_leaves)++;
        }
    }

    while (pq_size_is_1(pq) == false) {
        Node *left = dequeue(pq);
        Node *right = dequeue(pq);
        Node *parent = node_create(0, left->weight + right->weight);
        parent->left = left;
        parent->right = right;

        enqueue(pq, parent);
    }

    Node *tree = dequeue(pq);
    pq_free(&pq);
    return tree;
}
//fill code table function
void fill_code_table(Code *code_table, Node *node, uint64_t code, uint8_t code_length) {
    if (node->left == NULL && node->right == NULL) { // Leaf node
        code_table[node->symbol].code = code;
        code_table[node->symbol].code_length = code_length;
    } else {
        if (node->left) {
            fill_code_table(code_table, node->left, code, code_length + 1);
        }
        if (node->right) {
            code |= (uint64_t) 1 << code_length;
            fill_code_table(code_table, node->right, code, code_length + 1);
        }
    }
}

//compression function with Huffman coding
void huff_compress_file(BitWriter *outbuf, FILE *fin, uint32_t filesize, uint16_t num_leaves,
    Node *code_tree, Code *code_table) {
    bit_write_uint8(outbuf, 'H');
    bit_write_uint8(outbuf, 'C');
    bit_write_uint32(outbuf, filesize);
    bit_write_uint16(outbuf, num_leaves);
    //huffman tree written to output
    huff_write_tree(outbuf, code_tree);

    //file reset to pointer
    fseek(fin, 0, SEEK_SET);

    for (uint32_t i = 0; i < filesize; i++) {
        int b = fgetc(fin);
        if (b == EOF)
            break;

        uint64_t code = code_table[b].code;
        uint8_t code_length = code_table[b].code_length;

        for (int j = 0; j < code_length; j++) {
            bit_write_bit(outbuf, code & 1);
            code >>= 1;
        }
    }
}

//write tree function that produces huffman tree to output
void huff_write_tree(BitWriter *outbuf, Node *node) {
    if (node->left == NULL && node->right == NULL) {
        bit_write_bit(outbuf, 1);
        bit_write_uint8(outbuf, node->symbol);
    } else {
        huff_write_tree(outbuf, node->left);
        huff_write_tree(outbuf, node->right);
        bit_write_bit(outbuf, 0);
    }
}

int main(int argc, char *argv[]) {
    char *inputFileName = NULL;
    char *outputFileName = NULL;

    // command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            inputFileName = argv[++i];
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            outputFileName = argv[++i];
        }
    }

    // checking if both input and output files are provided
    if (inputFileName == NULL || outputFileName == NULL) {
        fprintf(stderr, "Usage: %s -i <input file> -o <output file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    // open input file
    FILE *inputFile = fopen(inputFileName, "rb");
    if (!inputFile) {
        perror("Error opening input file");
        return EXIT_FAILURE;
    }

    // open output file for BitWriter
    BitWriter *bitWriter = bit_write_open(outputFileName);
    if (!bitWriter) {
        perror("Error creating BitWriter");
        fclose(inputFile);
        return EXIT_FAILURE;
    }

    // filling histogram and creating Huffman tree
    uint32_t histogram[HISTOGRAM_SIZE] = { 0 };
    uint32_t filesize = fill_histogram(inputFile, histogram);
    uint16_t num_leaves;
    Node *root = create_tree(histogram, &num_leaves);

    // checking if tree creation is successful
    if (root == NULL) {
        fprintf(stderr, "Error creating Huffman tree\n");
        fclose(inputFile);
        bit_write_close(&bitWriter);
        return EXIT_FAILURE;
    }

    // filling code table
    Code code_table[HISTOGRAM_SIZE];
    fill_code_table(code_table, root, 0, 0);

    // resetting input file pointer, compressing the file
    fseek(inputFile, 0, SEEK_SET);
    huff_compress_file(bitWriter, inputFile, filesize, num_leaves, root, code_table);

    bit_write_close(&bitWriter);
    fclose(inputFile);
    node_free(&root);

    return EXIT_SUCCESS;
}
