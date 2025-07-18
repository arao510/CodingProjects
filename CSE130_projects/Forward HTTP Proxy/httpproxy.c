#include "client_socket.h"
#include "iowrapper.h"
#include "listener_socket.h"
#include "prequest.h"
#include "a5protocol.h"

#include <assert.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

//cache data structures

//struct for individual cache entry
typedef struct cache_entry {
    char *host, *uri, *response;
    int port;
    size_t response_size;
    struct cache_entry *next, *prev;
} cache_entry_t;

//struct for cache
typedef struct cache {
    cache_entry_t *head, *tail;
    int size, capacity;
    char *mode;
} cache_t;

//global variables
Listener_Socket_t *sock = NULL;
cache_t *cache = NULL;

//initialize a new cache with a given capacity and mode
cache_t *cache_new(int capacity, char *mode) {
    cache_t *c = malloc(sizeof(cache_t));
    if (!c) return NULL;
    c->head = c->tail = NULL; c->size = 0; c->capacity = capacity;
    if (!(c->mode = strdup(mode))) { free(c); return NULL; }
    return c;
}
//free all cache entries
void cache_delete(cache_t **c) {
    if (!c || !*c) return;
    for (cache_entry_t *cur = (*c)->head; cur;) {
        cache_entry_t *next = cur->next;
        free(cur->host); free(cur->uri); free(cur->response); free(cur);
        cur = next;
    }
    free((*c)->mode); free(*c); *c = NULL;
}

cache_entry_t *cache_lookup(cache_t *c, char *host, int port, char *uri) {
    if (!c || c->capacity == 0) return NULL;
    for (cache_entry_t *cur = c->head; cur; cur = cur->next)
        if (!strcmp(cur->host, host) && cur->port == port && !strcmp(cur->uri, uri))
            return cur;
    return NULL;
}
//look up an entry in the cache based on host, port, and URI
void cache_remove(cache_t *c, cache_entry_t *entry) {
    if (!c || !entry) return;
    if (entry->prev) entry->prev->next = entry->next;
    else c->head = entry->next;
    if (entry->next) entry->next->prev = entry->prev;
    else c->tail = entry->prev;
    free(entry->host); free(entry->uri); free(entry->response); free(entry);
    c->size--;
}
//move a cache entry to the front (used for LRU)
void cache_move_to_front(cache_t *c, cache_entry_t *entry) {
    if (!c || !entry || c->head == entry) return;
    if (entry->prev) entry->prev->next = entry->next;
    if (entry->next) entry->next->prev = entry->prev;
    else c->tail = entry->prev;
    entry->prev = NULL;
    entry->next = c->head;
    c->head->prev = entry;
    c->head = entry;
}
//add repsonse to cache
void cache_add(cache_t *c, char *host, int port, char *uri, char *response, size_t size) {
    if (!c || c->capacity == 0 || size > MAX_CACHE_ENTRY) { free(response); return; }
    cache_entry_t *entry = cache_lookup(c, host, port, uri);
    if (entry) {
        free(entry->response);
        entry->response = response; entry->response_size = size;
        if (!strcmp(c->mode, "LRU")) cache_move_to_front(c, entry);
        return;
    }
    entry = malloc(sizeof(cache_entry_t));
    if (!entry || !(entry->host = strdup(host)) || !(entry->uri = strdup(uri))) {
        free(entry ? entry->host : NULL); free(entry); free(response); return;
    }
    entry->port = port; entry->response = response; entry->response_size = size;
    entry->next = entry->prev = NULL;
    if (c->size >= c->capacity && c->tail) {
        cache_remove(c, c->tail);
    }
    if (!c->head) { c->head = c->tail = entry; }
    else { entry->next = c->head; c->head->prev = entry; c->head = entry; }
    c->size++;
}
//add response to cache
char *add_cached_header(char *resp, size_t *size) {
    if (!resp || *size == 0) return NULL;
    const char *end = strstr(resp, "\r\n\r\n");
    if (!end) return NULL;
    size_t hdr_len = end - resp, add_len = strlen(CACHED_HEADER);
    char *new_resp = malloc(*size + add_len + 2);
    if (!new_resp) return NULL;
    memcpy(new_resp, resp, hdr_len);
    memcpy(new_resp + hdr_len, "\r\n", 2);
    memcpy(new_resp + hdr_len + 2, CACHED_HEADER, add_len);
    memcpy(new_resp + hdr_len + 2 + add_len, end, *size - hdr_len);
    *size += add_len + 2;
    return new_resp;
}

static char *read_full_response(int fd, size_t *total) {
    size_t buf_size = 8192, tot = 0;
    char *buf = malloc(buf_size);
    if (!buf) return NULL;
    while (1) {
        ssize_t n = read_n_bytes(fd, buf + tot, buf_size - tot);
        if (n <= 0) break;
        tot += n;
        if (tot >= buf_size - 1024) {
            buf_size *= 2;
            char *new_buf = realloc(buf, buf_size);
            if (!new_buf) { free(buf); return NULL; }
            buf = new_buf;
        }
    }
    *total = tot;
    return buf;
}
//handle incoming connection requests
void handle_connection(uintptr_t connfd) {
    Prequest_t *preq = prequest_new(connfd);
    if (!preq) { close(connfd); return; }
    char *uri_orig = prequest_get_uri(preq);
    if (!uri_orig) { prequest_delete(&preq); close(connfd); return; }
    char *uri = strdup(uri_orig);
    if (!uri) { prequest_delete(&preq); close(connfd); return; }
    if (uri[0] != '/') {
        char *temp = malloc(strlen(uri) + 2);
        if (!temp) { free(uri); prequest_delete(&preq); close(connfd); return; }
        sprintf(temp, "/%s", uri); free(uri); uri = temp;
    }
    char *host = prequest_get_host(preq);
    int port = prequest_get_port(preq);
    if (!host) { free(uri); prequest_delete(&preq); close(connfd); return; }
    fprintf(stderr, "Request for http://%s:%d%s\n", host, port, uri);

    cache_entry_t *entry = cache_lookup(cache, host, port, uri);
    if (entry) {
        fprintf(stderr, "Cache hit for http://%s:%d%s\n", host, port, uri);
        size_t cs = entry->response_size;
        char *cached = add_cached_header(entry->response, &cs);
        if (cached) { write_n_bytes(connfd, cached, cs); free(cached); }
        else { write_n_bytes(connfd, entry->response, entry->response_size); }
        if (!strcmp(cache->mode, "LRU"))
            cache_move_to_front(cache, entry);
    } else {
        fprintf(stderr, "Cache miss for http://%s:%d%s\n", host, port, uri);
        int serverfd = cs_new(host, port);
        if (serverfd < 0) { free(uri); prequest_delete(&preq); close(connfd); return; }
        char request[MAX_HEADER_LEN];
        if (port == 80)
            snprintf(request, MAX_HEADER_LEN, "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n", uri, host);
        else
            snprintf(request, MAX_HEADER_LEN, "GET %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\n\r\n", uri, host, port);
        write_n_bytes(serverfd, request, strlen(request));
        size_t resp_size = 0;
        char *response = read_full_response(serverfd, &resp_size);
        close(serverfd);
        if (response && resp_size > 0) {
            write_n_bytes(connfd, response, resp_size);
            if (cache->capacity > 0 && resp_size <= MAX_CACHE_ENTRY) {
                char *copy = malloc(resp_size);
                if (copy) { memcpy(copy, response, resp_size); cache_add(cache, host, port, uri, copy, resp_size); }
            }
        }
        free(response);
    }
    prequest_delete(&preq);
    free(uri);
    close(connfd);
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s <port> <mode> <n>\n", argv[0]);
        return EXIT_FAILURE;
    }
    char *endptr;
    int port = (int)strtoull(argv[1], &endptr, 10);
    char *mode = argv[2];
    int capacity = (int)strtoull(argv[3], &endptr, 10);
    if ((endptr && *endptr != '\0') || port < 1 || port > 65535 ||
        (strcmp(mode, "FIFO") && strcmp(mode, "LRU")) ||
        (endptr && *endptr != '\0') || capacity < 0 || capacity > 1024) {
        fprintf(stderr, "Invalid Argument\n");
        return EXIT_FAILURE;
    }
    if (!(cache = cache_new(capacity, mode)) || !(sock = ls_new(port))) {
        cache_delete(&cache);
        return EXIT_FAILURE;
    }
    while (1) {
        uintptr_t connfd = ls_accept(sock);
        assert(connfd > 0);
        handle_connection(connfd);
    }
    cache_delete(&cache);
    ls_delete(&sock);
    return EXIT_SUCCESS;
}
