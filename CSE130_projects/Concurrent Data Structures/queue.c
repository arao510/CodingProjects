#include "queue.h"
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

//structure for thread-safe queue
typedef struct queue {
    void **buffer; // circular buffer for storing elements
    int capacity; // maximum number of elements in the queue
    int front; // index of the front element
    int rear; // index of the last element
    int count; // current number of elements in the queue
    pthread_mutex_t lock; // thread safety
    pthread_cond_t not_empty; // condition variable for non-empty queue
    pthread_cond_t not_full; // condition variable for non-full queue
} queue_t;

// creating a new queue with a given size
queue_t *queue_new(int size) {
    if (size <= 0)
        return NULL;

    queue_t *q = (queue_t *) malloc(sizeof(queue_t));
    if (!q)
        return NULL;

    q->buffer = (void **) malloc(size * sizeof(void *));
    if (!q->buffer) {
        free(q);
        return NULL;
    }

    q->capacity = size;
    q->front = 0;
    q->rear = 0;
    q->count = 0;
    pthread_mutex_init(&q->lock, NULL);
    pthread_cond_init(&q->not_empty, NULL);
    pthread_cond_init(&q->not_full, NULL);

    return q;
}

// deleting a queue and freeing all its memory
void queue_delete(queue_t **q) {
    if (!q || !(*q))
        return;

    pthread_mutex_lock(&(*q)->lock);
    free((*q)->buffer);
    pthread_mutex_unlock(&(*q)->lock);

    pthread_mutex_destroy(&(*q)->lock);
    pthread_cond_destroy(&(*q)->not_empty);
    pthread_cond_destroy(&(*q)->not_full);

    free(*q);
    *q = NULL;
}

// pushing an element into the queue and blocks if its full
bool queue_push(queue_t *q, void *elem) {
    if (!q)
        return false;

    pthread_mutex_lock(&q->lock);

    while (q->count == q->capacity) {
        pthread_cond_wait(&q->not_full, &q->lock); // waits if the queue is full
    }

    //simply stores the pointer directly
    q->buffer[q->rear] = elem;
    q->rear = (q->rear + 1) % q->capacity;
    q->count++;

    pthread_cond_signal(&q->not_empty); // notifies consumers
    pthread_mutex_unlock(&q->lock);

    return true;
}

// pops an element from the queue and blocks if empty
bool queue_pop(queue_t *q, void **elem) {
    if (!q || !elem)
        return false;

    pthread_mutex_lock(&q->lock);

    while (q->count == 0) {
        pthread_cond_wait(&q->not_empty, &q->lock); // waits if the queue is empty
    }

    // returns the pointer directly.
    *elem = q->buffer[q->front];
    q->front = (q->front + 1) % q->capacity;
    q->count--;

    pthread_cond_signal(&q->not_full); // notifies producer that queue is not full
    pthread_mutex_unlock(&q->lock); //unlocks the queue

    return true; //succsesfully pops the element
}
