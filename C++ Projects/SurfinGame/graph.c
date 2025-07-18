// graph.c
int dummy_declaration_for_translation_unit;
//#ifdef GRAPH_C
#include "stack.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#define _XOPEN_SOURCE 500
#include <string.h>
char *strdup(const char *s);

// Use a different name for typedef internally in graph.c
typedef struct graph {
    uint32_t vertices;
    bool directed;
    bool *visited;
    char **names;
    uint32_t **weights;
} GraphStruct;
typedef GraphStruct Graph;

Graph *graph_create(uint32_t vertices, bool directed) {
    Graph *g = calloc(1, sizeof(Graph));
    if (g == NULL) {
        perror("Failed to allocate memory for graph");
        exit(EXIT_FAILURE);
    }

    g->vertices = vertices;
    g->directed = directed;

    // Allocate memory for visited array
    g->visited = calloc(vertices, sizeof(bool));
    if (g->visited == NULL) {
        perror("Failed to allocate memory for visited array");
        exit(EXIT_FAILURE);
    }

    // Allocate memory for names array
    g->names = calloc(vertices, sizeof(char *));
    if (g->names == NULL) {
        perror("Failed to allocate memory for names array");
        exit(EXIT_FAILURE);
    }

    // Allocate memory for weights matrix
    g->weights = calloc(vertices, sizeof(g->weights[0]));
    if (g->weights == NULL) {
        perror("Failed to allocate memory for weights matrix");
        exit(EXIT_FAILURE);
    }

    // Allocate each row in the adjacency matrix
    for (uint32_t i = 0; i < vertices; ++i) {
        g->weights[i] = calloc(vertices, sizeof(g->weights[0][0]));
        if (g->weights[i] == NULL) {
            perror("Failed to allocate memory for weights matrix row");
            exit(EXIT_FAILURE);
        }
    }
    return g;
}
void graph_free(Graph **gp) {
    Graph *g = *gp;
    if (g == NULL)
        return;
    // Free visited array
    free(g->visited);
    // Free names array
    for (uint32_t i = 0; i < g->vertices; ++i) {
        if (g->names[i]) {
            free(g->names[i]);
        }
    }
    free(g->names);
    // Free weights matrix
    for (uint32_t i = 0; i < g->vertices; ++i) {
        free(g->weights[i]);
    }
    free(g->weights);
    // Free graph struct
    free(g);
    *gp = NULL;
}

uint32_t graph_vertices(const Graph *g) {
    return g->vertices;
}

void graph_add_vertex(Graph *g, const char *name, uint32_t v) {
    if (v >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        ///exit(EXIT_FAILURE);
        return;
    }
    // Free existing name if it exists
    if (g->names[v]) {
        free(g->names[v]);
    }
    // Make a copy of the name and store it in the graph
    g->names[v] = strdup(name);
    if (g->names[v] == NULL) {
        perror("Failed to allocate memory for vertex name");
        exit(EXIT_FAILURE);
    }
}
const char *graph_get_vertex_name(const Graph *g, uint32_t v) {
    if (v >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        exit(EXIT_FAILURE);
    }
    return g->names[v];
}
char **graph_get_names(const Graph *g) {
    return g->names;
}

void graph_add_edge(Graph *g, uint32_t start, uint32_t end, uint32_t weight) {
    if (start >= g->vertices || end >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        exit(EXIT_FAILURE);
    }

    if (g->weights[start][end] != 0 && g->weights[start][end] != weight) {
        // printf("Warning: Edge %u -> %u already exists with a different weight. Updating the weight.\n", start, end);
        //printf("Existing Weight: %u, New Weight: %u\n", g->weights[start][end], weight);
    }
    g->weights[start][end] = weight;

    if (!g->directed && (g->weights[end][start] == 0 || g->weights[end][start] == weight)) {
        g->weights[end][start] = weight;
    }
}

uint32_t graph_get_weight(const Graph *g, uint32_t start, uint32_t end) {
    if (start >= g->vertices || end >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        exit(EXIT_FAILURE);
    }
    return g->weights[start][end];
}

void graph_visit_vertex(Graph *g, uint32_t v) {
    if (v >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        exit(EXIT_FAILURE);
    }
    g->visited[v] = true;
}

void graph_unvisit_vertex(Graph *g, uint32_t vertex) {
    if (g != NULL && vertex < g->vertices) {
        g->visited[vertex] = false; // Set the visited status to false during unvisit
    }
}
bool graph_visited(const Graph *g, uint32_t v) {
    if (v >= g->vertices) {
        fprintf(stderr, "Error: Invalid vertex index\n");
        exit(EXIT_FAILURE);
    }
    return g->visited[v];
}
void graph_print(const Graph *g) {
    printf("Alissa starts at:\n");
    for (uint32_t i = 0; i < g->vertices; ++i) {
        printf("%s\n", g->names[i]);
    }
    printf("Home\n"); // Assuming the path ends at the starting point (Home)
}
//#endif // GRAPH_C
