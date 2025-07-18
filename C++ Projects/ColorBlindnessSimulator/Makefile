CC = clang
CFLAGS = -Werror -Wall -Wextra -Wconversion -Wdouble-promotion -Wstrict-prototypes -pedantic
LDFLAGS = -lm


OBJS = colorb.o bmp.o io.o iotest.o


all: colorb iotest


colorb: colorb.o bmp.o io.o
	$(CC) $(LDFLAGS) -o $@ $^


iotest: iotest.o io.o
	$(CC) $(LDFLAGS) -o $@ $^


%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@


format:
	clang-format -i *.c *.h


clean:
	rm -f $(OBJS) colorb iotest


.PHONY: all format clean
