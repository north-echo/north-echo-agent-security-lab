#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s PATH\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY); /* Intentional mistake: no O_CLOEXEC. */
    if (fd < 0) {
        perror("open");
        return 1;
    }
    char *child[] = {"python3", "fd-child.py", NULL};
    execvp(child[0], child);
    perror("execvp");
    return 1;
}
