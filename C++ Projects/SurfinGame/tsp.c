#include "graph.h"
#include "path.h"
#include "stack.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define START_VERTEX 0

struct path {
    Stack *vertices;
    uint32_t total_weight;
};
static bool foundHamiltonianCycle = false;

Path *solve_tsp(const Graph *g);
Graph *read_graph(FILE *infile);

Graph *read_graph(FILE *infile) {
    char line[256];
    uint32_t num_vertices;
    bool directed;

    if (fgets(line, sizeof(line), infile) == NULL) {
        fprintf(stderr, "Error: Failed to read the first line.\n");
        exit(EXIT_FAILURE);
    }

    if (sscanf(line, "%u", &num_vertices) != 1) {
        fprintf(stderr, "Error: Failed to read the number of vertices. Line content: %s\n", line);
        exit(EXIT_FAILURE);
    }

    directed = false;
    int second_value;
    if (sscanf(line, "%*u %d", &second_value) == 1) {
        directed = (bool) second_value;
    }

    Graph *g = graph_create(num_vertices, directed);
    ///
    if (g == NULL) {
        fprintf(stderr, "Error: Failed to create graph\n");
        exit(EXIT_FAILURE);
    }
    ///
    for (uint32_t i = 0; i < num_vertices; ++i) {
        char vertex_name[100];
        fgets(line, sizeof(line), infile);
        sscanf(line, "%99[^\n]", vertex_name);
        graph_add_vertex(g, vertex_name, i);
    }

    uint32_t num_edges;

    if (fgets(line, sizeof(line), infile) == NULL) {
        fprintf(stderr, "Error: Failed to read the number of edges.\n");
        exit(EXIT_FAILURE);
    }

    if (sscanf(line, "%u", &num_edges) != 1) {
        fprintf(stderr, "Error: Failed to read the number of edges. Line content: %s\n", line);
        exit(EXIT_FAILURE);
    }

    for (uint32_t i = 0; i < num_edges; ++i) {
        if (fgets(line, sizeof(line), infile) == NULL) {
            fprintf(stderr, "Error: Failed to read edge %u.\n", i + 1);
            exit(EXIT_FAILURE);
        }

        uint32_t start, end, weight;
        if (sscanf(line, "%u %u %u", &start, &end, &weight) != 3) {
            fprintf(stderr, "Error: Failed to read edge %u. Line content: %s\n", i + 1, line);
            exit(EXIT_FAILURE);
        }

        //fprintf(stderr, "Debug: Read edge %u: %u %u %u\n", i + 1, start, end, weight); // Debug statement
        graph_add_edge(g, start, end, weight);
    }
    return g;
}

void dfs(const Graph *g, uint32_t current_vertex, Path *current_path, Path *best_path,
    uint32_t num_vertices) {
    //visited[current_vertex] = true; // asgn5
    graph_visit_vertex((Graph *) g, current_vertex);
    path_add(current_path, current_vertex, g);

    if (path_vertices(current_path) == num_vertices) {
        uint32_t start_vertex_weight = graph_get_weight(g, current_vertex, START_VERTEX);
        //printf("Debug: Checking edge back to start vertex. Weight: %u\n", start_vertex_weight);

        if (start_vertex_weight > 0) {
            uint32_t total_distance = path_distance(current_path) + start_vertex_weight;
            if (path_distance(best_path) == 0 || total_distance < path_distance(best_path)) {
                path_add(current_path, START_VERTEX, g);
                path_copy(best_path, current_path);
                path_remove(current_path, g);
                // printf("Debug: vertex. Visited and set to True %u\n", current_vertex);
            }
        }
    } else {
        for (uint32_t neighbor = 0; neighbor < graph_vertices(g); ++neighbor) {
            if (!graph_visited(g, neighbor) && graph_get_weight(g, current_vertex, neighbor) > 0) {
                //printf("Debug: in Else vertex. Not Visited and set to False %u\n", current_vertex);
                //visited[current_vertex] = false;
                dfs(g, neighbor, current_path, best_path, num_vertices);
            }
        }
    }

    if (path_vertices(current_path) > 1) {
        uint32_t prev_vertex;
        stack_peek(current_path->vertices, &prev_vertex);
        uint32_t weight = graph_get_weight(g, prev_vertex, current_vertex);
        current_path->total_weight += weight;
    }
    path_remove(current_path, g);
    graph_unvisit_vertex((Graph *) g, current_vertex);
}
Path *solve_tsp(const Graph *g) {
    uint32_t num_vertices = graph_vertices(g);
    Path *current_path = path_create(num_vertices);
    Path *best_path = path_create(num_vertices);

    for (uint32_t start_vertex = 0; start_vertex < num_vertices; ++start_vertex) {
        dfs(g, start_vertex, current_path, best_path, num_vertices);
        if (path_vertices(best_path) == num_vertices) {
            // Hamiltonian cycle found, return the best path
            path_free(&current_path);
            return best_path;
        }
        path_clear(current_path);
    }

    // No Hamiltonian cycle found
    path_free(&current_path);
    path_free(&best_path);
    return NULL;
}

/*Path *solve_tsp(const Graph *g) {
    uint32_t num_vertices = graph_vertices(g);
    Path *current_path = path_create(num_vertices);
    Path *best_path = path_create(num_vertices);

    dfs(g, START_VERTEX, current_path, best_path, num_vertices);
    path_free(&current_path);
    return best_path;
}*/

int main(int argc, char *argv[]) {
    const char *input_filename = NULL;
    const char *output_filename = NULL;
    FILE *infile = stdin;
    FILE *outfile = stdout;

    for (int i = 1; i < argc; ++i) {
        if (argv[i][0] == '-') {
            switch (argv[i][1]) {
            case 'i':
                if (++i < argc) {
                    input_filename = argv[i];
                } else {
                    fprintf(stderr, "Error: -i option requires a filename argument.\n");
                    return EXIT_FAILURE;
                }
                break;
            case 'o':
                if (++i < argc) {
                    output_filename = argv[i];
                } else {
                    fprintf(stderr, "Error: -o option requires a filename argument.\n");
                    return EXIT_FAILURE;
                }
                break;
            case 'd': break;
            case 'h': return EXIT_SUCCESS;
            default: fprintf(stderr, "Error: Unknown option '%s'\n", argv[i]); return EXIT_FAILURE;
            }
        } else {
            fprintf(stderr, "Error: Unknown argument '%s'\n", argv[i]);
            return EXIT_FAILURE;
        }
    }

    if (input_filename != NULL) {
        infile = fopen(input_filename, "r");
        if (infile == NULL) {
            fprintf(stderr, "Error: Unable to open input file '%s'\n", input_filename);
            return EXIT_FAILURE;
        }
    }

    if (output_filename != NULL) {
        outfile = fopen(output_filename, "w");
        if (outfile == NULL) {
            fprintf(stderr, "Error: Unable to open output file '%s'\n", output_filename);
            if (input_filename != NULL) {
                fclose(infile);
            }
            return EXIT_FAILURE;
        }
    }

    Graph *g = read_graph(infile);
    if (g == NULL) {
        fprintf(stderr, "Error: Failed to read graph\n");
        return EXIT_FAILURE;
    }

    Path *best_path = solve_tsp(g);
    if (best_path == NULL) {
        printf("No path found! Alissa is lost!\n");
    } else {
        graph_print(g);
        printf("Total Distance: %u\n", path_distance(best_path));
        path_free(&best_path);
    }

    /* Path *best_path = solve_tsp(g);
    foundHamiltonianCycle = true;
    if (!foundHamiltonianCycle) {
        printf("No path found! Alissa is lost!\n");
    } else {
        graph_print(g);
        printf("Total Distance: %u\n", path_distance(best_path));
    }*/
    // moving to solve_tsp() - asn5
    graph_free(&g);
    path_free(&best_path);
    // end of asn5
    if (input_filename != NULL) {
        fclose(infile);
    }
    if (output_filename != NULL) {
        fclose(outfile);
    }

    return EXIT_SUCCESS;
}
