#include "bitreader.h"
#include "node.h"

#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_STACK_SIZE 64

//stack that manages the nodes in Huffman tree
typedef struct {
    Node *stack[MAX_STACK_SIZE];
    int top;
} NodeStack;

//initializes the stack
void stack_init(NodeStack *s) {
    s->top = -1;
}

//function that checks if stack is empty
bool stack_is_empty(NodeStack *s) {
    return s->top == -1;
}

//function that pushes node onto stack
bool stack_push(NodeStack *s, Node *node) {
    if (s->top < MAX_STACK_SIZE - 1) {
        s->stack[++s->top] = node;
        return true;
    }
    return false;
}

//function that pops a node from stack
Node *stack_pop(NodeStack *s) {
    if (!stack_is_empty(s)) {
        return s->stack[s->top--];
    }
    return NULL;
}

//decompression function for file
void dehuff_decompress_file(FILE *fout, BitReader *inbuf) {
    uint8_t type1 = bit_read_uint8(inbuf);
    uint8_t type2 = bit_read_uint8(inbuf);
    uint32_t filesize = bit_read_uint32(inbuf);
    uint16_t num_leaves = bit_read_uint16(inbuf);

    assert(type1 == 'H' && type2 == 'C');

    int num_nodes = 2 * num_leaves - 1;
    NodeStack stack;
    stack_init(&stack);
    Node *node, *left, *right;

    for (int i = 0; i < num_nodes; i++) {
        uint8_t bit = bit_read_bit(inbuf);
        if (bit == 1) {
            uint8_t symbol = bit_read_uint8(inbuf);
            node = node_create(symbol, 0);
            stack_push(&stack, node);
        } else {
            right = stack_pop(&stack);
            left = stack_pop(&stack);
            node = node_create(0, 0);
            node->left = left;
            node->right = right;
            stack_push(&stack, node);
        }
    }

    Node *code_tree = stack_pop(&stack);

    //decompresses the file
    for (uint32_t i = 0; i < filesize; i++) {
        node = code_tree;
        while (node->left != NULL || node->right != NULL) {
            uint8_t bit = bit_read_bit(inbuf);
            node = (bit == 0) ? node->left : node->right;
        }
        fputc(node->symbol, fout);
    }

    node_free(&code_tree);
}

int main(int argc, char *argv[]) {
    char *inputFileName = NULL;
    char *outputFileName = NULL;

    //command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            inputFileName = argv[++i];
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            outputFileName = argv[++i];
        }
    }

    //check if both input and output files are provided
    if (inputFileName == NULL || outputFileName == NULL) {
        fprintf(stderr, "Usage: %s -i <input file> -o <output file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    //opening input file
    FILE *inputFile = fopen(inputFileName, "rb");
    if (!inputFile) {
        perror("Error opening input file");
        return EXIT_FAILURE;
    }

    //creating bitreader
    BitReader *bitReader = bit_read_open(inputFileName);
    if (!bitReader) {
        perror("Error creating BitReader");
        fclose(inputFile);
        return EXIT_FAILURE;
    }

    // opening output file
    FILE *outputFile = fopen(outputFileName, "wb");
    if (!outputFile) {
        perror("Error opening output file");
        bit_read_close(&bitReader);
        fclose(inputFile);
        return EXIT_FAILURE;
    }

    // decompression
    dehuff_decompress_file(outputFile, bitReader);

    // closing file
    bit_read_close(&bitReader);
    fclose(inputFile);
    fclose(outputFile);

    return EXIT_SUCCESS;
}
