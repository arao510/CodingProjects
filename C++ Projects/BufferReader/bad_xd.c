#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#define B 16

int main(int c, char **v) {
    unsigned char b[B];
    size_t o = 0, t = 0;
    ssize_t r;
    int f = c == 2 ? open(v[1], O_RDONLY) : 0;
    if (f < 0)
        return 1;

    while ((r = read(f, b + t, B - t)) > 0 || t) {
        if (r > 0)
            t += (size_t) r;
        if (t == B || (r <= 0 && t)) {
            printf("%08lx: ", o);
            for (size_t i = 0; i < B; i++)
                printf(i < t ? "%02x" : "  ", b[i]), printf(i % 2 ? " " : "");
            printf(" ");
            for (size_t i = 0; i < t; i++)
                printf("%c", b[i] > 31 && b[i] < 127 ? (int) b[i] : '.');
            printf("\n"), o += t, t = 0;
        }
    }

    return f ? close(f) : 0;
}
