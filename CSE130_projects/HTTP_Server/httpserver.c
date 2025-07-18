#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <regex.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/stat.h>
#include <limits.h>
#include <sys/sendfile.h>
//#include <ctype.h> // Include this for isalpha()

//define buffer size for request processing
#define BUFFER_SIZE 2048

//function prototypes
void send_response(int client_sock, int status_code, const char *status_phrase, const char *body);
void handle_get_request(int client_sock, const char *uri);
void handle_put_request(int client_sock, const char *uri, const char *body, int content_length);
void handle_client(int client_sock);

//sends http response to the client
void send_response(int client_sock, int status_code, const char *status_phrase, const char *body) {
    char header[BUFFER_SIZE];
    int body_length = body ? strlen(body) : 0;

    snprintf(header, sizeof(header), "HTTP/1.1 %d %s\r\nContent-Length: %d\r\n\r\n", status_code,
        status_phrase, body_length);

    write(client_sock, header, strlen(header));
    if (body_length > 0) {
        write(client_sock, body, body_length);
    }
}

//handles the http GET requests
void handle_get_request(int client_sock, const char *uri) {
    char file_path[PATH_MAX];
    //constructs file path
    if (snprintf(file_path, sizeof(file_path), ".%s", uri) >= (int) sizeof(file_path)) {
        send_response(client_sock, 400, "Bad Request", "Bad Request\n");
        return;
    }

    struct stat file_stat;
    if (stat(file_path, &file_stat) == -1) {
        if (errno == EACCES) {
            send_response(client_sock, 403, "Forbidden", "Forbidden\n");
        } else {
            send_response(client_sock, 404, "Not Found", "Not Found\n");
        }
        return;
    }

    //makes sure the requested resource is not a directory
    if (S_ISDIR(file_stat.st_mode)) {
        send_response(client_sock, 403, "Forbidden", "Forbidden\n");
        return;
    }

    int fd = open(file_path, O_RDONLY);
    if (fd == -1) {
        if (errno == EACCES) {
            send_response(client_sock, 403, "Forbidden", "Forbidden\n");
        } else {
            send_response(client_sock, 500, "Internal Server Error", "Internal Server Error\n");
        }
        return;
    }
    //sends HTTP headers with the file size
    char header[BUFFER_SIZE];
    snprintf(header, sizeof(header), "HTTP/1.1 200 OK\r\nContent-Length: %ld\r\n\r\n",
        file_stat.st_size);
    write(client_sock, header, strlen(header));

    //sends file content
    char buffer[BUFFER_SIZE];
    ssize_t bytes_read;
    while ((bytes_read = read(fd, buffer, sizeof(buffer))) > 0) {
        if (write(client_sock, buffer, bytes_read) <= 0) {
            perror("Error writing to client");
            break;
        }
    }

    close(fd);
}
//handles HTTP PUT requests
void handle_put_request(int client_sock, const char *uri, const char *body, int content_length) {
    char file_path[PATH_MAX];
    //constructs file path
    if (snprintf(file_path, sizeof(file_path), ".%s", uri) >= (int) sizeof(file_path)) {
        send_response(client_sock, 400, "Bad Request", "Bad Request\n");
        return;
    }

    struct stat file_stat;
    //checks if its a directory
    if (stat(file_path, &file_stat) == 0 && S_ISDIR(file_stat.st_mode)) {
        send_response(client_sock, 403, "Forbidden", "Forbidden\n");
        return;
    }

    int is_new_file = access(file_path, F_OK) != 0;

    int fd = open(file_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        if (errno == EACCES) {
            send_response(client_sock, 403, "Forbidden", "Forbidden\n");
        } else {
            send_response(client_sock, 500, "Internal Server Error", "Internal Server Error\n");
        }
        return;
    }

    //writes content into file
    ssize_t total_written = 0;
    while (total_written < content_length) {
        ssize_t written = write(fd, body + total_written, content_length - total_written);
        if (written <= 0) {
            close(fd);
            send_response(client_sock, 500, "Internal Server Error", "Internal Server Error\n");
            return;
        }
        total_written += written;
    }

    close(fd);
    //responds with correct status codes
    if (is_new_file) {
        send_response(client_sock, 201, "Created", "Created\n");
    } else {
        send_response(client_sock, 200, "OK", "OK\n");
    }
}

//main function that handles processing client requests
void handle_client(int client_sock) {
    char buffer[BUFFER_SIZE];
    ssize_t total_read = 0;

    // reads the HTTP request
    while (1) {
        ssize_t bytes = read(client_sock, buffer + total_read, sizeof(buffer) - total_read - 1);
        if (bytes <= 0) {
            send_response(client_sock, 400, "Bad Request", "Bad Request\n");
            close(client_sock);
            return;
        }
        total_read += bytes;
        buffer[total_read] = '\0';

        if (strstr(buffer, "\r\n\r\n")) // end of headers detected
            break;

        if (total_read >= BUFFER_SIZE - 1) {
            send_response(client_sock, 400, "Bad Request", "Bad Request\n");
            close(client_sock);
            return;
        }
    }

    // parses HTTP request
    char *headers_end = strstr(buffer, "\r\n\r\n");
    if (!headers_end) {
        send_response(client_sock, 400, "Bad Request", "Bad Request\n");
        close(client_sock);
        return;
    }
    headers_end += 4; // moves past "\r\n\r\n"

    char method[16], uri[128], version[16];
    if (sscanf(buffer, "%15s %127s %15s", method, uri, version) != 3) {
        send_response(client_sock, 400, "Bad Request", "Bad Request\n");
        close(client_sock);
        return;
    }

    // validates HTTP method
    if (strcmp(method, "GET") != 0 && strcmp(method, "PUT") != 0) {
        send_response(client_sock, 501, "Not Implemented", "Not Implemented\n");
        close(client_sock);
        return;
    }

    // validates HTTP version
    if (strncmp(version, "HTTP/1.1", 8) != 0) {
        send_response(client_sock, 505, "Version Not Supported", "Version Not Supported\n");
        close(client_sock);
        return;
    }

    // handling GET Request - validate headers
    if (strcmp(method, "GET") == 0) {
        int has_host_header = 0;
        char *header_line = buffer;
        char *line_end;

        while ((line_end = strstr(header_line, "\r\n")) && header_line < headers_end) {
            *line_end = '\0'; // temporarily null-terminate the header line

            if (strncasecmp(header_line, "Host:", 5) == 0) {
                has_host_header = 1;
                char *host_value = header_line + 5;
                while (*host_value == ' ' || *host_value == '\t')
                    host_value++; // skip spaces
                if (*host_value == '\0') { // empty host header
                    send_response(client_sock, 400, "Bad Request", "Invalid Host header\n");
                    close(client_sock);
                    return;
                }
            }
            header_line = line_end + 2; // move to the next header line
        }

        if (!has_host_header) {
            send_response(client_sock, 400, "Bad Request", "Bad Request\n");
            close(client_sock);
            return;
        }

        handle_get_request(client_sock, uri);
        close(client_sock);
        return;
    }

    // handling PUT Request - allow missing content-Length**
    char *content_length_str = strcasestr(buffer, "Content-Length:");
    int content_length = 0;

    if (content_length_str) {
        content_length_str += strlen("Content-Length:");
        while (*content_length_str == ' ' || *content_length_str == '\t')
            content_length_str++;

        char *endptr;
        content_length = strtol(content_length_str, &endptr, 10);
        if (endptr == content_length_str || content_length < 0) {
            send_response(client_sock, 400, "Bad Request", "Invalid Content-Length\n");
            close(client_sock);
            return;
        }
    }

    // if content-length is missing, assuming 0
    char *body = malloc(content_length + 1);
    if (!body) {
        send_response(client_sock, 500, "Internal Server Error", "Memory allocation failed\n");
        close(client_sock);
        return;
    }
    memset(body, 0, content_length + 1);

    // read request body
    ssize_t body_length = total_read - (headers_end - buffer);
    memcpy(body, headers_end, body_length);

    while (body_length < content_length) {
        ssize_t bytes = read(client_sock, body + body_length, content_length - body_length);
        if (bytes <= 0) {
            free(body);
            send_response(client_sock, 400, "Bad Request", "Incomplete body\n");
            close(client_sock);
            return;
        }
        body_length += bytes;
    }

    // process the PUT request
    handle_put_request(client_sock, uri, body, content_length);
    free(body);
    close(client_sock);
}

// main function that starts the server
int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <port>\n", argv[0]);
        exit(1);
    }

    int port = atoi(argv[1]);
    if (port < 1 || port > 65535) {
        fprintf(stderr, "Invalid Port\n");
        exit(1);
    }

    //creates a socket
    int server_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sock < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    int opt = 1;
    setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    int buf_size = 65536; // 64KB
    setsockopt(server_sock, SOL_SOCKET, SO_RCVBUF, &buf_size, sizeof(buf_size));
    setsockopt(server_sock, SOL_SOCKET, SO_SNDBUF, &buf_size, sizeof(buf_size));

    //binds socket to the port
    struct sockaddr_in server_addr = { 0 };
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    if (bind(server_sock, (struct sockaddr *) &server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        close(server_sock);
        exit(1);
    }
    //starts listening for client connections
    if (listen(server_sock, 10) < 0) {
        perror("Listen failed");
        close(server_sock);
        exit(1);
    }

    printf("Server running on port %d\n", port);
    //accepts incoming client connections
    while (1) {
        int client_sock = accept(server_sock, NULL, NULL);
        if (client_sock < 0) {
            perror("Accept failed");
            continue;
        }
        handle_client(client_sock);
    }

    close(server_sock);
    return 0;
}
