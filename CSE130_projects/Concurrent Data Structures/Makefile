SOURCES  = queue.c rwlock.c
OBJECTS  = $(SOURCES:%.c=%.o)
FORMATS  = $(SOURCES:%.c=%.fmt)

CC       = clang
FORMAT   = clang-format
CFLAGS   = -Wall -Wpedantic -Werror -Wextra

.PHONY: all clean format

all: $(OBJECTS)


queue.o: queue.c queue.h
	$(CC) $(CFLAGS) -c queue.c -o queue.o


rwlock.o: rwlock.c rwlock.h
	$(CC) $(CFLAGS) -c rwlock.c -o rwlock.o



clean:
	rm -f $(EXECBIN) $(OBJECTS) $(FORMAT)

format: $(FORMATS)

%.fmt: %.c
	$(FORMAT) -i $<
	touch $@