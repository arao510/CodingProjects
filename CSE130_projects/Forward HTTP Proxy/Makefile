CC = clang
CFLAGS = -Wall -Wpedantic -Werror -Wextra -O3 -g
BUILD_DIR = build
LIB = asgn5_helper_funcs.a

.PHONY: all clean httpproxy

all: httpproxy

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/httpproxy.o: httpproxy.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

httpproxy: $(BUILD_DIR)/httpproxy.o $(LIB)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -rf $(BUILD_DIR) httpproxy *.o
