#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/landlock.h>
#include <linux/openat2.h>
#include <seccomp.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

/* Disposable child only: prove actual kernel enforcement, not header presence. */
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    struct open_how how = {.flags = O_RDONLY};
    int fd = syscall(SYS_openat2, AT_FDCWD, argv[1], &how, sizeof(how));
    if (fd < 0) return 1;
    close(fd);
    int abi = syscall(SYS_landlock_create_ruleset, NULL, 0,
                      LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1) return 1;
    struct landlock_ruleset_attr rules = {.handled_access_fs = LANDLOCK_ACCESS_FS_READ_FILE};
    int policy = syscall(SYS_landlock_create_ruleset, &rules, sizeof(rules), 0);
    int allowed = open(argv[1], O_PATH | O_CLOEXEC);
    if (policy < 0 || allowed < 0) return 1;
    struct landlock_path_beneath_attr rule = {
        .allowed_access = LANDLOCK_ACCESS_FS_READ_FILE, .parent_fd = allowed
    };
    if (syscall(SYS_landlock_add_rule, policy, LANDLOCK_RULE_PATH_BENEATH, &rule, 0) < 0 ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 ||
        syscall(SYS_landlock_restrict_self, policy, 0) < 0) return 1;
    close(policy);
    close(allowed);
    fd = open(argv[1], O_RDONLY);
    if (fd < 0) return 1;
    close(fd);
    errno = 0;
    fd = open(argv[2], O_RDONLY);
    if (fd >= 0 || errno != EACCES) return 1;
    scmp_filter_ctx filter = seccomp_init(SCMP_ACT_ALLOW);
    if (!filter || seccomp_rule_add(filter, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(getppid), 0) < 0 ||
        seccomp_load(filter) < 0) return 1;
    seccomp_release(filter);
    errno = 0;
    if (syscall(SYS_getppid) != -1 || errno != EPERM) return 1;
    printf("openat2 works; Landlock ABI %d enforces read policy; seccomp enforces EPERM\n", abi);
    return 0;
}
