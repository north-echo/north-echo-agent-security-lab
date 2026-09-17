#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s COMMAND [ARG ...]\n", argv[0]);
        return 2;
    }

    /* Intentional starter flaw: authority is transferred without hygiene. */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
