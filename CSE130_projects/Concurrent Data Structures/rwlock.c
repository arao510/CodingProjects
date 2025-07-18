#include "rwlock.h"
#include <pthread.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

// structure representing a reader-writer lock
typedef struct rwlock {
    pthread_mutex_t lock; // mutex for mutual exclusion
    pthread_cond_t readers_ok; // condition variable for readers
    pthread_cond_t writers_ok; // condition variable for writers
    int active_readers; // count of active readers
    int active_writers; // count of active writers
    int waiting_readers; // count of waiting readers
    int waiting_writers; // count of waiting writers
    PRIORITY priority; // priority type (READERS, WRITERS, or N_WAY)
    int n_way; // value for N_WAY priority
    int n_way_counter; // counter for enforcing N_WAY priority
    int readers_since_last_writer; // readers since last writer, needed for N_WAY
    int readers_during_writer_wait; // readers allowed while a writer is waiting
} rwlock_t;

// creates and initializes a new reader-writer lock with the given priority
rwlock_t *rwlock_new(PRIORITY p, uint32_t n) {
    rwlock_t *rw = malloc(sizeof(rwlock_t));
    if (!rw) {
        return NULL; // memory allocation failed
    }

    //initialize mutex and condition variables
    pthread_mutex_init(&rw->lock, NULL);
    pthread_cond_init(&rw->readers_ok, NULL);
    pthread_cond_init(&rw->writers_ok, NULL);

    rw->active_readers = 0;
    rw->active_writers = 0;
    rw->waiting_readers = 0;
    rw->waiting_writers = 0;
    rw->priority = p;
    rw->n_way = (p == N_WAY) ? n : 0; // only set n_way if priority is N_WAY
    rw->n_way_counter = 0;
    rw->readers_since_last_writer = 0;
    rw->readers_during_writer_wait = 0;

    return rw;
}

//deletes the reader-writer lock and frees all associated memory
void rwlock_delete(rwlock_t **l) {
    if (!l || !*l) {
        return; // ensures valid pointer before deallocating
    }

    //destorys mutex and condition variables
    pthread_mutex_destroy(&(*l)->lock);
    pthread_cond_destroy(&(*l)->readers_ok);
    pthread_cond_destroy(&(*l)->writers_ok);
    free(*l);
    *l = NULL;
}

// gets the lock for reading
void reader_lock(rwlock_t *rw) {
    pthread_mutex_lock(&rw->lock);
    rw->waiting_readers++;

    while (rw->active_writers > 0 || (rw->priority == WRITERS && rw->waiting_writers > 0)
           || (rw->priority == N_WAY && rw->waiting_writers > 0
               && rw->readers_during_writer_wait >= rw->n_way)) {
        pthread_cond_wait(&rw->readers_ok, &rw->lock);
    }

    rw->waiting_readers--;
    rw->active_readers++;
    rw->readers_since_last_writer++;

    //if N_WAY policy is in effect and writers are waiting, track allowed readers
    if (rw->waiting_writers > 0 && rw->priority == N_WAY) {
        rw->readers_during_writer_wait++;
    }

    pthread_mutex_unlock(&rw->lock);
}

// releases the lock for reading
void reader_unlock(rwlock_t *rw) {
    pthread_mutex_lock(&rw->lock);
    rw->active_readers--;

    if (rw->active_readers == 0) {
        pthread_cond_signal(&rw->writers_ok);
    }

    pthread_mutex_unlock(&rw->lock);
}

// gets the lock for writing
void writer_lock(rwlock_t *rw) {
    pthread_mutex_lock(&rw->lock);
    rw->waiting_writers++;
    rw->readers_during_writer_wait = 0;

    while (rw->active_readers > 0 || rw->active_writers > 0) {
        pthread_cond_wait(&rw->writers_ok, &rw->lock);
    }

    rw->waiting_writers--;
    rw->active_writers++;
    rw->readers_since_last_writer = 0;

    pthread_mutex_unlock(&rw->lock);
}

// releases the lock for writing
void writer_unlock(rwlock_t *rw) {
    pthread_mutex_lock(&rw->lock);
    rw->active_writers--;

    //determine which group should be signaled based on priority policy
    switch (rw->priority) {
    case READERS:
        pthread_cond_broadcast(&rw->readers_ok); // wake all waiting readers
        pthread_cond_signal(&rw->writers_ok); // wake one writer
        break;
    case WRITERS:
        if (rw->waiting_writers > 0) {
            pthread_cond_signal(&rw->writers_ok); // // give priority to a waiting writer
        } else {
            pthread_cond_broadcast(&rw->readers_ok); // otherwise, wake all readers
        }
        break;
    case N_WAY:
        if (rw->waiting_readers > 0) {
            pthread_cond_broadcast(&rw->readers_ok); // allow waiting readers
        }
        pthread_cond_signal(&rw->writers_ok); // signal one writer
        break;
    }

    pthread_mutex_unlock(&rw->lock);
}
