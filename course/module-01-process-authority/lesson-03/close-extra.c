#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int descriptor = open("/dev/null", O_RDONLY);
    if (descriptor < 0) {
        perror("open");
        return 1;
    }
    printf("Opened descriptor: %d\n", descriptor);
    if (close_range(3, ~0U, 0) != 0) {
        perror("close_range");
        return 1;
    }
    errno = 0;
    int flags = fcntl(descriptor, F_GETFD);
    if (flags != -1 || errno != EBADF) {
        fprintf(stderr, "Expected the descriptor to be closed\n");
        return 1;
    }
    puts("Extra descriptor closed; stdout still works.");
    return 0;
}
