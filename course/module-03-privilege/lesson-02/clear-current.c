#define _GNU_SOURCE
#include <linux/capability.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(void) {
    struct __user_cap_header_struct header = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0
    };
    struct __user_cap_data_struct data[2] = {0};

    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0) != 0) {
        perror("clear ambient capabilities");
        return 1;
    }
    if (syscall(SYS_capset, &header, data) != 0) {
        perror("capset");
        return 1;
    }
    if (syscall(SYS_capget, &header, data) != 0) {
        perror("capget");
        return 1;
    }
    printf("effective=%08x%08x\n", data[1].effective, data[0].effective);
    printf("permitted=%08x%08x\n", data[1].permitted, data[0].permitted);
    printf("inheritable=%08x%08x\n", data[1].inheritable, data[0].inheritable);
    return 0;
}
