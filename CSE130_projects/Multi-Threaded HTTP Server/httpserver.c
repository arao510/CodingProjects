#include "listener_socket.h"
#include "connection.h"
#include "response.h"
#include "request.h"
#include "rwlock.h"
#include "queue.h"
#include <sys/socket.h>
#include <limits.h>

#include <err.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

//default number of worker threads
#define DEFAULT_THREAD_COUNT 4
//size of the request queue
#define QUEUE_SIZE 128

// global variables
queue_t *request_queue; // queue for storing client connections
pthread_t *worker_threads;
int thread_count = DEFAULT_THREAD_COUNT; // number of worker threads

//  function prototypes
void handle_connection(int connfd);
void handle_get(conn_t *conn);
void handle_put(conn_t *conn);
void handle_unsupported(conn_t *conn);
void log_request(const char *operation, const char *uri, int status, const char *request_id);
void *worker_thread(void *arg);

pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;

void log_request(const char *operation, const char *uri, int status, const char *request_id) {
    pthread_mutex_lock(&log_mutex);
    fprintf(stderr, "%s,%s,%d,%s\n", operation, uri, status, request_id ? request_id : "0");
    fflush(stderr);
    pthread_mutex_unlock(&log_mutex);
}

// handle unsupported requests
void handle_unsupported(conn_t *conn) {
    const char *request_id = conn_get_header(conn, "Request-Id");
    log_request("UNSUPPORTED", conn_get_uri(conn), 501, request_id);
    conn_send_response(conn, &RESPONSE_NOT_IMPLEMENTED);
}

// rwlock helper functions
typedef struct file_lock {
    char *uri;
    rwlock_t *lock;
    struct file_lock *next;
} file_lock_t;

file_lock_t *file_lock_table = NULL;
pthread_mutex_t file_lock_table_mutex = PTHREAD_MUTEX_INITIALIZER;

rwlock_t *get_file_lock(const char *uri) {
    pthread_mutex_lock(&file_lock_table_mutex);

    file_lock_t *fl = file_lock_table;
    while (fl) {
        if (strcmp(fl->uri, uri) == 0) {
            pthread_mutex_unlock(&file_lock_table_mutex);
            return fl->lock;
        }
        fl = fl->next;
    }

    // allocate lock dynamically to prevent memory issues
    file_lock_t *new_fl = calloc(1, sizeof(file_lock_t));
    new_fl->uri = strdup(uri);
    new_fl->lock = rwlock_new(READERS, 0); // uses dynamic allocation

    new_fl->next = file_lock_table;
    file_lock_table = new_fl;

    pthread_mutex_unlock(&file_lock_table_mutex);
    return new_fl->lock;
}

//  handle http connections
void handle_connection(int connfd) {
    conn_t *conn = conn_new(connfd);
    const Response_t *res = conn_parse(conn);
    if (res) {
        conn_send_response(conn, res);
    } else {
        const Request_t *req = conn_get_request(conn);
        if (req == &REQUEST_GET) {
            handle_get(conn);
        } else if (req == &REQUEST_PUT) {
            handle_put(conn);
        } else {
            handle_unsupported(conn);
        }
    }
    conn_delete(&conn);
}

void handle_get(conn_t *conn) {
    char *uri = conn_get_uri(conn);
    rwlock_t *lock = get_file_lock(uri);

    reader_lock(lock);

    int fd = open(uri, O_RDONLY);
    if (fd >= 0) {
        struct stat file_stat;
        if (fstat(fd, &file_stat) == 0) {
            conn_send_file(conn, fd, file_stat.st_size);
            close(fd);
            // log after sending response but before releasing the lock
            log_request("GET", uri, 200, conn_get_header(conn, "Request-Id"));
            reader_unlock(lock);
            return;
        }
        close(fd);
    }

    log_request("GET", uri, 404, conn_get_header(conn, "Request-Id"));
    conn_send_response(conn, &RESPONSE_NOT_FOUND);
    reader_unlock(lock);
}

void *worker_thread(__attribute__((unused)) void *arg) {
    while (1) {
        void *data;
        if (queue_pop(request_queue, &data)) { // check return value properly
            int connfd = (intptr_t) data;
            if (connfd >= 0) {
                handle_connection(connfd);
                close(connfd);
            }
        }
    }
    return NULL;
}

void handle_put(conn_t *conn) {
    char *uri = conn_get_uri(conn);
    rwlock_t *lock = get_file_lock(uri);

    // creates a temporary file for receiving data
    char template[256];
    snprintf(template, sizeof(template), "/tmp/httpserver_XXXXXX");
    int temp_fd = mkstemp(template);

    if (temp_fd < 0) {
        // failed to create temp file
        conn_send_response(conn, &RESPONSE_INTERNAL_SERVER_ERROR);
        log_request("PUT", uri, 500, conn_get_header(conn, "Request-Id"));
        return;
    }

    // receive file contents to temporary file (outside the lock)
    // conn_recv_file returns 0 on success
    int recv_success = (conn_recv_file(conn, temp_fd) == 0);
    if (!recv_success) {
        // failed to receive file
        close(temp_fd);
        unlink(template); // deletes the temp file
        conn_send_response(conn, &RESPONSE_INTERNAL_SERVER_ERROR);
        log_request("PUT", uri, 500, conn_get_header(conn, "Request-Id"));
        return;
    }

    // now acquire the writer lock to update the actual file
    writer_lock(lock);

    // check if the file already exists
    int is_new_file = (access(uri, F_OK) != 0);

    // open the destination file
    int dest_fd = open(uri, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (dest_fd < 0) {
        writer_unlock(lock);
        close(temp_fd);
        unlink(template);
        conn_send_response(conn, &RESPONSE_INTERNAL_SERVER_ERROR);
        log_request("PUT", uri, 500, conn_get_header(conn, "Request-Id"));
        return;
    }

    // copies data from temp file to destination file
    lseek(temp_fd, 0, SEEK_SET); // rewinds temp file to beginning
    char buffer[4096];
    ssize_t bytes_read;

    while ((bytes_read = read(temp_fd, buffer, sizeof(buffer))) > 0) {
        if (write(dest_fd, buffer, bytes_read) != bytes_read) {
            // writes error
            close(temp_fd);
            close(dest_fd);
            unlink(template);
            writer_unlock(lock);
            conn_send_response(conn, &RESPONSE_INTERNAL_SERVER_ERROR);
            log_request("PUT", uri, 500, conn_get_header(conn, "Request-Id"));
            return;
        }
    }

    // cleans up
    close(temp_fd);
    close(dest_fd);
    unlink(template); // deletes temp file

    // sends responses
    if (is_new_file) {
        conn_send_response(conn, &RESPONSE_CREATED);
        log_request("PUT", uri, 201, conn_get_header(conn, "Request-Id"));
    } else {
        conn_send_response(conn, &RESPONSE_OK);
        log_request("PUT", uri, 200, conn_get_header(conn, "Request-Id"));
    }

    writer_unlock(lock);
}

//main function
int main(int argc, char **argv) {
    int opt;
    while ((opt = getopt(argc, argv, "t:")) != -1) {
        if (opt == 't') {
            thread_count = atoi(optarg);
        }
    }
    if (optind >= argc) {
        fprintf(stderr, "Usage: %s [-t threads] <port>\n", argv[0]);
        return EXIT_FAILURE;
    }

    size_t port = strtoull(argv[optind], NULL, 10);
    signal(SIGPIPE, SIG_IGN);
    Listener_Socket_t *sock = ls_new(port);
    if (!sock) {
        errx(EXIT_FAILURE, "Failed to open socket");
    }

    request_queue = queue_new(QUEUE_SIZE);
    if (!request_queue) {
        errx(EXIT_FAILURE, "Failed to initialize queue");
    }

    if (thread_count < 8) {
        thread_count = 8;
    }

    worker_threads = malloc(thread_count * sizeof(pthread_t));
    for (int i = 0; i < thread_count; i++) {
        pthread_create(&worker_threads[i], NULL, worker_thread, NULL);
    }

    while (1) {
        int connfd = ls_accept(sock);
        if (connfd >= 0) {
            // sets a more aggressive timeout for socket operations
            struct timeval tv;
            tv.tv_sec = 0; // 0 seconds
            tv.tv_usec = 500000; // 500 milliseconds
            setsockopt(connfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

            queue_push(request_queue, (void *) (intptr_t) connfd);
        }
    }

    ls_delete(&sock);
    return EXIT_SUCCESS;
}
