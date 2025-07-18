CC = gcc
CFLAGS = -Werror -Wall -Wextra -Wconversion -Wdouble-promotion -Wstrict-prototypes -pedantic

all: xd bad_xd

xd: xd.o
	$(CC) $(CFLAGS) -o xd xd.o

xd.o: xd.c
	$(CC) $(CFLAGS) -c xd.c

bad_xd: bad_xd.o
	$(CC) $(CFLAGS) -o bad_xd bad_xd.o

bad_xd.o: bad_xd.c
	$(CC) $(CFLAGS) -c bad_xd.c

clean:
	rm -f xd xd.o bad_xd bad_xd.o

format:
	clang-format -i xd.c bad_xd.c

.PHONY: all clean format

