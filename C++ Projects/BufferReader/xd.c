#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#define BUFFER_SIZE 16

void print_hex_ascii_line(const unsigned char *buffer, size_t size, size_t offset) {
    size_t i;
    printf("%08lx: ", (unsigned long) offset);
    for (i = 0; i < size; i++) {
        printf("%02x", buffer[i]);
        if (i % 2 != 0) {
            printf(" ");
        }
    }
    for (; i < BUFFER_SIZE; i++) {
        printf("  ");
        if (i % 2 != 0) {
            printf(" ");
        }
    }
    printf(" ");
    for (i = 0; i < size; i++) {
        if (buffer[i] >= 32 && buffer[i] <= 126) {
            printf("%c", buffer[i]);
        } else {
            printf(".");
        }
    }
    printf("\n");
}

void buffered_reader(int fileDescriptor) {
    unsigned char buffer[BUFFER_SIZE];
    ssize_t bytesRead;
    size_t offset = 0;
    size_t totalBytes = 0;

    while ((bytesRead = read(fileDescriptor, buffer + totalBytes, BUFFER_SIZE - totalBytes)) > 0
           || (bytesRead == -1 && errno == EINTR)) {
        if (bytesRead > 0) {
            totalBytes += (size_t) bytesRead;
            if (totalBytes >= BUFFER_SIZE) {
                // Process full buffer
                print_hex_ascii_line(buffer, BUFFER_SIZE, offset);
                offset += BUFFER_SIZE;
                memmove(buffer, buffer + BUFFER_SIZE, totalBytes - BUFFER_SIZE);
                totalBytes -= BUFFER_SIZE;
            }
        } else if (bytesRead == -1 && errno != EINTR) {
            fprintf(stderr, "Error reading file: %s\n", strerror(errno));
            break;
        }
    }

    if (totalBytes > 0) {
        print_hex_ascii_line(buffer, totalBytes, offset);
    }
}

int main(int argc, char *argv[]) {
    int fileDescriptor;

    if (argc == 2) {
        const char *filename = argv[1];
        fileDescriptor = open(filename, O_RDONLY);
    } else {
        fileDescriptor = STDIN_FILENO;
    }
    if (fileDescriptor == -1) {
        if (errno == ENOENT) {
            return EXIT_FAILURE;
        } else {
            fprintf(stderr, "Error opening file: %s\n", strerror(errno));
            return EXIT_FAILURE;
        }
    }
    buffered_reader(fileDescriptor);
    close(fileDescriptor);
    return EXIT_SUCCESS;
}
