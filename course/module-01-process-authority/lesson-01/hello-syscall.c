#include <stdio.h>
#include <unistd.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("userspace: about to write");
    const char message[] = "kernel-visible write\n";
    if (write(STDOUT_FILENO, message, sizeof(message) - 1) < 0) {
        perror("write");
        return 1;
    }
    return 0;
}
