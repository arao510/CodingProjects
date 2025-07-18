#include "node.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

Node *node_create(uint8_t symbol, uint32_t weight) {
    Node *newNode = malloc(sizeof(Node));
    if (newNode == NULL) {
        return NULL;
    }

    newNode->symbol = symbol;
    newNode->weight = weight;
    newNode->left = NULL;
    newNode->right = NULL;
    newNode->code = 0;
    newNode->code_length = 0;

    return newNode;
}

//revised node_free
void node_free(Node **pnode) {
    if (pnode && *pnode) {
        // Recursively free left and right children
        node_free(&((*pnode)->left));
        node_free(&((*pnode)->right));

        // Free node itself and set the pointer to NULL
        free(*pnode);
        *pnode = NULL;
    }
}

static void node_print_node(Node *tree, char ch, int indentation) {
    if (tree == NULL) {
        return;
    }

    node_print_node(tree->right, '/', indentation + 3);
    printf("%*cweight = %u", indentation + 1, ch, tree->weight);

    if (tree->left == NULL && tree->right == NULL) {
        if (' ' <= tree->symbol && tree->symbol <= '~') {
            printf(", symbol = '%c'", tree->symbol);
        } else {
            printf(", symbol = 0x%02x", tree->symbol);
        }
    }

    printf("\n");
    node_print_node(tree->left, '\\', indentation + 3);
}

void node_print_tree(Node *tree) {
    node_print_node(tree, '<', 2);
}
