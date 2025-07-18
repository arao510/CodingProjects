#include "stack.h"

#include "graph.h"

#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

// Remove the redefinition of 'Stack' here
// typedef struct stack {
//     uint32_t capacity;
//     uint32_t top;
//     uint32_t *items;
// } Stack;

// Use the typedef from stack.h
struct stack {
    uint32_t capacity;
    uint32_t top;
    uint32_t *items;
};

Stack *stack_create(uint32_t capacity) {
    Stack *s = (Stack *) malloc(sizeof(Stack));
    s->capacity = capacity;
    s->top = 0;
    s->items = calloc(s->capacity, sizeof(uint32_t));
    return s;
}

void stack_free(Stack **sp) {
    if (sp != NULL && *sp != NULL) {
        if ((*sp)->items) {
            free((*sp)->items);
            (*sp)->items = NULL;
        }
        free(*sp);
    }
    if (sp != NULL) {
        *sp = NULL;
    }
}

bool stack_push(Stack *s, uint32_t val) {
    if (s == NULL || stack_full(s)) {
        return false;
    }
    s->items[s->top] = val;
    s->top++;
    return true;
}

bool stack_pop(Stack *s, uint32_t *val) {
    if (s == NULL || stack_empty(s)) {
        return false;
    }
    s->top--;
    *val = s->items[s->top];
    return true;
}

bool stack_peek(const Stack *s, uint32_t *val) {
    if (s == NULL || stack_empty(s)) {
        return false;
    }
    *val = s->items[s->top - 1];
    return true;
}

bool stack_empty(const Stack *s) {
    return s == NULL || s->top == 0;
}

bool stack_full(const Stack *s) {
    return s == NULL || s->top == s->capacity;
}

uint32_t stack_size(const Stack *s) {
    return s == NULL ? 0 : s->top;
}

void stack_copy(Stack *dst, const Stack *src) {
    if (dst == NULL || src == NULL) {
        return;
    }
    assert(dst->capacity >= src->top);
    for (uint32_t i = 0; i < src->top; ++i) {
        dst->items[i] = src->items[i];
    }
    dst->top = src->top;
}

void stack_print(const Stack *s, FILE *outfile, char *cities[]) {
    if (s == NULL || outfile == NULL || cities == NULL) {
        return;
    }

    for (uint32_t i = 0; i < s->top; ++i) {
        fprintf(outfile, "%s\n", cities[s->items[i]]);
    }
}
