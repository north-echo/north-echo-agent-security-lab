#define _GNU_SOURCE
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    char *end;
    long status = strtol(argv[1], &end, 10);
    if (!*argv[1] || *end || status < 0 || status > 125)
        return 2;
    FILE *membership = fopen("/proc/self/cgroup", "r");
    char line[PATH_MAX], relative[PATH_MAX], path[PATH_MAX];
    int found = 0;
    while (membership && fgets(line, sizeof(line), membership)) {
        if (sscanf(line, "0::%4095[^\n]", relative) == 1) {
            found = 1;
            break;
        }
    }
    if (membership)
        fclose(membership);
    if (!found || snprintf(path, sizeof(path), "/sys/fs/cgroup%s/memory.max", relative)
            >= (int)sizeof(path))
        return 2;
    FILE *limit = fopen(path, "r");
    unsigned long long memory;
    int observed = limit && fscanf(limit, "%llu", &memory) == 1;
    if (limit)
        fclose(limit);
    if (!observed)
        return 2;
    printf("{\"requested_status\":%ld,\"memory\":%llu}\n", status, memory);
    return (int)status;
}
