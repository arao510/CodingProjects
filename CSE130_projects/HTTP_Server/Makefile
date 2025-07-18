CC = clang
CFLAGS = -Wall -Wextra -Werror -pedantic
LIBS = asgn2_helper_funcs.a

all: format httpserver

format:
	clang-format -i httpserver.c

httpserver: httpserver.o
	$(CC) $(CFLAGS) -o httpserver httpserver.o $(LIBS)

httpserver.o: httpserver.c
	$(CC) $(CFLAGS) -c httpserver.c

clean:
	rm -f httpserver httpserver.o
