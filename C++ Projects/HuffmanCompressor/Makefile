CC = clang
CFLAGS = -Werror -Wall -Wextra -Wconversion -Wdouble-promotion -Wstrict-prototypes -pedantic
LDFLAGS = 

OBJS = bitwriter.o bitreader.o node.o pq.o huff.o dehuff.o
TEST_OBJS = pqtest.o nodetest.o bwtest.o brtest.o

all: huff dehuff pqtest nodetest bwtest brtest

huff: huff.o bitwriter.o node.o pq.o
	$(CC) $(LDFLAGS) -o $@ $^

dehuff: dehuff.o bitreader.o node.o pq.o
	$(CC) $(LDFLAGS) -o $@ $^

pqtest: pqtest.o pq.o node.o
	$(CC) $(LDFLAGS) -o $@ $^

nodetest: nodetest.o node.o
	$(CC) $(LDFLAGS) -o $@ $^

bwtest: bwtest.o bitwriter.o
	$(CC) $(LDFLAGS) -o $@ $^

brtest: brtest.o bitreader.o
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

format:
	clang-format -i *.c *.h

clean:
	rm -f $(OBJS) $(TEST_OBJS) huff dehuff pqtest nodetest bwtest brtest

.PHONY: all format clean
