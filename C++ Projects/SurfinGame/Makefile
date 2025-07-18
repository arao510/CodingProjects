CC = clang
CFLAGS = -Werror -Wall -Wextra -Wconversion -Wdouble-promotion -Wstrict-prototypes -pedantic -gdwarf-4

SRC_FILES = tsp.c graph.c stack.c path.c
OBJ_FILES = $(SRC_FILES:.c=.o)

EXECUTABLE = tsp

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJ_FILES)
	$(CC) $(CFLAGS) $^ -o $@

tsp.o: tsp.c
	$(CC) -Wno-unused-parameter $(CFLAGS) -c $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ_FILES) $(EXECUTABLE)

format:
	clang-format -i $(SRC_FILES) $(wildcard *.h)

.PHONY: all clean format
