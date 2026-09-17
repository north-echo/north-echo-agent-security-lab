#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s read ROOT PATH | write ROOT PATH CONTENT | run ROOT COMMAND [ARG...]\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "run") == 0) {
        execv(argv[3], &argv[3]);
        perror("execv");
        return 1;
    }
    char path[4096];
    snprintf(path, sizeof(path), "%s/%s", argv[2], argv[3]);
    if (strcmp(argv[1], "read") == 0) {
        FILE *stream = fopen(path, "r");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        char buffer[4096];
        size_t count = fread(buffer, 1, sizeof(buffer), stream);
        fwrite(buffer, 1, count, stdout);
        return ferror(stream) != 0;
    }
    if (strcmp(argv[1], "write") == 0 && argc == 5) {
        FILE *stream = fopen(path, "w");
        if (!stream) {
            perror("fopen");
            return 1;
        }
        fputs(argv[4], stream);
        return fclose(stream) == EOF;
    }
    fprintf(stderr, "unknown mode\n");
    return 2;
}
