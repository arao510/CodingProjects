CC = clang
CFLAGS = -g3 -Werror -Wall -Wextra -Wconversion -Wdouble-promotion -Wstrict-prototypes -pedantic
LDLIBS = -lm

all: colorb iotest

iotest: iotest.c io.c io.h
	$(CC) $(CFLAGS) iotest.c io.c -o $@ $(LDLIBS)
colorb: io.o bmp.o colorb.o
	$(CC) $^ -o $@ $(LDLIBS)
io.o: io.c io.h
	$(CC) $(CFLAGS) -c $< -o $@
bmp.o: bmp.c bmp.h io.h
	$(CC) $(CFLAGS) -c $< -o $@
colorb.o: colorb.c bmp.h io.h
	$(CC) $(CFLAGS) -c $< -o $@
format:
	clang-format -i *.c *.h
clean:
	rm -f *.o colorb iotest
