#include "names.h"

#include <stdio.h>
#include <stdlib.h>
#define SEED 2023

int main(void) {

    typedef enum { SIDE, RAZORBACK, TROTTER, SNOUTER, JOWLER } Position;

    const Position pig[7] = { SIDE, SIDE, RAZORBACK, TROTTER, SNOUTER, JOWLER, JOWLER };

    int num_players = 2;
    printf("Number of players (2 to 10)? ");
    int scanf_result = scanf("%d", &num_players);

    if (scanf_result < 1 || num_players < 2 || num_players > 10) {
        fprintf(stderr, "Invalid number of players. Using 2 instead.\n");
        num_players = 2;
    }

    unsigned seed = 2023;
    printf("Random-number seed? ");
    scanf_result = scanf("%u", &seed);

    if (scanf_result < 1) {
        fprintf(stderr, "Invalid seed. Using 2023 instead.\n");
    }

    srandom(seed);
    int player_scores[num_players];
    for (int i = 0; i < num_players; i++) {
        player_scores[i] = 0;
    }
    int curr_player = 0;

    int roll = 0;
    printf("%s\n", player_name[curr_player]);

    while (1) {
        roll = rand() % 7;
        int points_earned = 0;
        switch (pig[roll]) {
        case SIDE: points_earned = 0; break;
        case RAZORBACK: points_earned = 10; break;
        case TROTTER: points_earned = 10; break;
        case SNOUTER: points_earned = 15; break;
        case JOWLER: points_earned = 5; break;
        default: break;
        }
        player_scores[curr_player] += points_earned;

        printf(" rolls %d, has %d\n", points_earned, player_scores[curr_player]);

        if (player_scores[curr_player] >= 100) {
            printf("%s won!\n", player_name[curr_player]);
            break;
        }

        if (roll == 0 || roll == 1) {
            curr_player = (curr_player + 1) % num_players;
            printf("%s\n", player_name[curr_player]);
            // break;
        }
    }

    return 0;
}
