#include <stdio.h>
#include <unistd.h>

int main(void) {
    char *arguments[] = {"env", NULL};
    char *environment[] = {"PATH=/usr/bin:/bin", "LANG=C.UTF-8", NULL};
    execve("/usr/bin/env", arguments, environment);
    perror("execve");
    return 1;
}
