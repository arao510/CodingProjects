#include "path.h"

#include "graph.h"
#include "stack.h"

#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

// Remove the redefinition of 'Path' here
// typedef struct path {
//     Stack *vertices;
// } Path;

// Use the typedef from path.h
struct path {
    Stack *vertices;
    uint32_t total_weight;
};

Path *path_create(uint32_t capacity) {
    Path *p = (Path *) malloc(sizeof(Path));
    p->total_weight = 0;
    p->vertices = stack_create(capacity);
    return p;
}
/*
#include "graph.h"
#include "path.h"
#include "stack.h"   

#include <assert.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct path {
    uint32_t total_weight;
    Stack *vertices;
} Path;

Path *path_create(uint32_t capacity) {
    Path *p = (Path *)malloc(sizeof(Path));
    p->total_weight = 0;
    p->vertices = stack_create(capacity);
    return p;
}
*/
void path_free(Path **pp) {
    if (pp != NULL && *pp != NULL) {
        stack_free(&(*pp)->vertices);
        free(*pp);
    }
    if (pp != NULL) {
        *pp = NULL;
    }
}

uint32_t path_vertices(const Path *p) {
    return stack_size(p->vertices);
}
/*uint32_t path_distance(const Path *p, const Graph *g) {
    if (p == NULL || g == NULL) {
        fprintf(stderr, "Error: NULL argument provided to path_distance.\n");
        return 0; // Or some error code
    }

    uint32_t total_distance = 0;
    uint32_t prev_vertex, current_vertex;

    // Use a temporary stack to avoid modifying the original path
    Stack *temp_stack = stack_create(stack_size(p->vertices));
    assert(temp_stack != NULL);

    // Reverse the vertices into the temporary stack for correct order processing
    while (stack_pop(p->vertices, &current_vertex)) {
        stack_push(temp_stack, current_vertex);
    }

    // Calculate the total path distance
    if (stack_peek(temp_stack, &current_vertex)) {
        while (stack_pop(temp_stack, &prev_vertex)) {
            uint32_t edge_weight = graph_get_weight(g, prev_vertex, current_vertex);
            total_distance += edge_weight;
            current_vertex = prev_vertex;
        }
    }

    // Restore the vertices back to the original path stack
    while (stack_pop(temp_stack, &current_vertex)) {
        stack_push(p->vertices, current_vertex);
    }

    stack_free(&temp_stack);
    return total_distance;
}
*/

uint32_t path_distance(const Path *p) {
    if (p == NULL) {
        fprintf(stderr, "Error: NULL argument provided to path_distance.\n");
        return 0; // Or some error code
    }
    return p->total_weight;
}

void path_add(Path *p, uint32_t val, const Graph *g) {
    assert(p != NULL && g != NULL);

    if (path_vertices(p) > 0) {
        uint32_t prev_vertex;
        stack_peek(p->vertices, &prev_vertex);
        uint32_t weight = graph_get_weight(g, prev_vertex, val);
        //fprintf(stderr, "Debug: Adding edge from %u to %u with weight: %u\n", prev_vertex, val, weight);
        p->total_weight += weight;
    }
    stack_push(p->vertices, val);
}

uint32_t path_remove(Path *p, const Graph *g) {
    assert(p != NULL && g != NULL);

    if (path_vertices(p) == 0) {
        //fprintf(stderr, "Debug: No vertices to remove from path.\n");
        return UINT32_MAX;
    }

    uint32_t removed_vertex;
    stack_pop(p->vertices, &removed_vertex);
    //fprintf(stderr, "Debug: Removing vertex %u from path.\n", removed_vertex);
    // Consider commenting out or modifying the below logic if it's not needed
    /*
    if (path_vertices(p) > 0) {
       uint32_t new_last_vertex;
       stack_peek(p->vertices, &new_last_vertex);
         uint32_t weight = graph_get_weight(g, new_last_vertex, removed_vertex);
         fprintf(stderr, "Debug: New last vertex: %u, Edge weight from %u to %u: %u\n", new_last_vertex, new_last_vertex, removed_vertex, weight);

        p->total_weight -= weight;
         fprintf(stderr, "Debug: Path total weight after removing: %u\n", p->total_weight);
   } else {
       p->total_weight = 0;
       fprintf(stderr, "Debug: Path is empty, total weight reset to 0.\n");
    }
   */
    //////// Added from asgn5
    if (path_vertices(p) >= 1) { // Change this line
        uint32_t new_last_vertex;
        stack_peek(p->vertices, &new_last_vertex);
        p->total_weight -= graph_get_weight(g, removed_vertex, new_last_vertex);
    } else {
        p->total_weight = 0; // Reset distance to zero
    }
    ////// end of asgn5
    return removed_vertex;
}

void path_copy(Path *dst, const Path *src) {
    assert(dst != NULL && src != NULL);
    stack_copy(dst->vertices, src->vertices);
    dst->total_weight = src->total_weight;
}
void path_print(const Path *p, FILE *outfile, const Graph *g) {
    assert(p != NULL && outfile != NULL && g != NULL);

    uint32_t num_vertices = path_vertices(p);
    uint32_t *vertices = malloc(num_vertices * sizeof(uint32_t));
    assert(vertices != NULL);

    // Pop vertices from the path stack to the array
    for (uint32_t i = 0; i < num_vertices; ++i) {
        stack_pop(p->vertices, &vertices[num_vertices - 1 - i]);
    }

    fprintf(outfile, "Path: ");
    for (uint32_t i = 0; i < num_vertices; ++i) {
        fprintf(outfile, "%s", graph_get_vertex_name(g, vertices[i]));
        if (i < num_vertices - 1) {
            fprintf(outfile, " -> ");
        }
        // Push back to the stack to maintain original state
        stack_push(p->vertices, vertices[i]);
    }
    fprintf(outfile, "\nTotal Distance: %" PRIu32 "\n", p->total_weight);
    free(vertices);
}
