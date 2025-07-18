#include "pq.h"

#include <stdio.h>
#include <stdlib.h>

typedef struct ListElement {
    Node *tree;
    struct ListElement *next;
} ListElement;

struct PriorityQueue {
    ListElement *list;
};

PriorityQueue *pq_create(void) {
    PriorityQueue *q = malloc(sizeof(PriorityQueue));
    if (!q) {
        return NULL;
    }
    q->list = NULL;
    return q;
}

void pq_free(PriorityQueue **q) {
    if (q && *q) {
        ListElement *current = (*q)->list;
        while (current) {
            ListElement *temp = current;
            current = current->next;
            free(temp);
        }
        free(*q);
        *q = NULL;
    }
}

bool pq_is_empty(PriorityQueue *q) {
    return q->list == NULL;
}

bool pq_size_is_1(PriorityQueue *q) {
    return q->list != NULL && q->list->next == NULL;
}

bool pq_less_than(ListElement *e1, ListElement *e2) {
    if (e1->tree->weight < e2->tree->weight) {
        return true;
    } else if (e1->tree->weight == e2->tree->weight) {
        return e1->tree->symbol < e2->tree->symbol;
    }
    return false;
}

void enqueue(PriorityQueue *q, Node *tree) {
    ListElement *new_element = malloc(sizeof(ListElement));
    if (!new_element) {
        return;
    }
    new_element->tree = tree;
    new_element->next = NULL;

    if (pq_is_empty(q) || pq_less_than(new_element, q->list)) {
        new_element->next = q->list;
        q->list = new_element;
    } else {
        ListElement *current = q->list;
        while (current->next && !pq_less_than(new_element, current->next)) {
            current = current->next;
        }
        new_element->next = current->next;
        current->next = new_element;
    }
}

Node *dequeue(PriorityQueue *q) {
    if (pq_is_empty(q)) {

        fprintf(stderr, "Error: Attempt to dequeue from an empty priority queue.\n");
        exit(EXIT_FAILURE);
    }
    ListElement *element = q->list;
    q->list = q->list->next;
    Node *tree = element->tree;
    free(element);
    return tree;
}

void pq_print(PriorityQueue *q) {
    assert(q != NULL);
    ListElement *e = q->list;
    int position = 1;
    while (e != NULL) {
        if (position++ == 1) {
            printf("=============================================\n");
        } else {
            printf("---------------------------------------------\n");
        }
        //node_print_tree(e->tree, '<', 2);
        node_print_tree(e->tree);

        e = e->next;
    }
    printf("=============================================\n");
}
