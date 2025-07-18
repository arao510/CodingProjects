#include "set.h"

Set set_empty(void) {
    return 0;
}

Set set_universal(void) {
    return 255;
}

bool set_member(Set s, int x) {
    return (s & (1 << x)) != 0;
}

Set set_insert(Set s, int x) {
    return s | (1 << x);
}

Set set_remove(Set s, int x) {
    return s & ~(1 << x);
}

Set set_union(Set s, Set t) {
    return s | t;
}

Set set_intersect(Set s, Set t) {
    return s & t;
}

Set set_difference(Set s, Set t) {
    return s & ~t;
}

Set set_complement(Set s) {
    return ~s;
}
