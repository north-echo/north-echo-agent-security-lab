#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROOT RELATIVE_PATH\n", argv[0]);
        return 2;
    }
    int root_fd = open(argv[1], O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd == -1) {
        perror("open root");
        return 1;
    }
    struct open_how how = {
        .flags = O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC,
        .mode = 0600,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS,
    };
    int fd = syscall(SYS_openat2, root_fd, argv[2], &how, sizeof(how));
    if (fd == -1) {
        perror("openat2");
        close(root_fd);
        return 1;
    }
    close(root_fd);
    const char content[] = "created through an anchored descriptor\n";
    int failed = write(fd, content, sizeof(content) - 1) != (ssize_t)(sizeof(content) - 1);
    if (failed)
        fprintf(stderr, "write did not complete\n");
    if (close(fd) == -1) {
        perror("close output");
        failed = 1;
    }
    return failed;
}
