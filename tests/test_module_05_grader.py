from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "scripts"))
sys.path.insert(0, str(SOURCE / "graders"))

import module_05  # noqa: E402


REFERENCE_SOURCE = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/close_range.h>
#include <linux/landlock.h>
#include <linux/openat2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

static int ll_create(const struct landlock_ruleset_attr *a, size_t s, __u32 f) { return syscall(SYS_landlock_create_ruleset, a, s, f); }
static int ll_add(int fd, const struct landlock_path_beneath_attr *a) { return syscall(SYS_landlock_add_rule, fd, LANDLOCK_RULE_PATH_BENEATH, a, 0); }
static int ll_restrict(int fd) { return syscall(SYS_landlock_restrict_self, fd, 0); }

static __u64 rights_for(int abi) {
    __u64 r = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |
        LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |
        LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |
        LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |
        LANDLOCK_ACCESS_FS_MAKE_SYM;
    if (abi >= 2) r |= LANDLOCK_ACCESS_FS_REFER;
    if (abi >= 3) r |= LANDLOCK_ACCESS_FS_TRUNCATE;
    return r;
}

static int mark_inherited(void) {
    if (syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC) == 0) return 0;
    if (errno != ENOSYS) return -1;
    long maximum = sysconf(_SC_OPEN_MAX);
    for (int fd = 3; fd < maximum; fd++) {
        int flags = fcntl(fd, F_GETFD);
        if (flags != -1 && fcntl(fd, F_SETFD, flags | FD_CLOEXEC) == -1) return -1;
    }
    return 0;
}

static int open_beneath(const char *root, const char *path, int flags, mode_t mode) {
    int root_fd = open(root, O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd == -1) return -1;
    struct open_how how = {.flags = (unsigned long long)(flags | O_CLOEXEC), .mode = mode,
        .resolve = RESOLVE_BENEATH | RESOLVE_NO_MAGICLINKS | RESOLVE_NO_SYMLINKS};
    int fd = syscall(SYS_openat2, root_fd, path, &how, sizeof(how));
    int saved = errno;
    close(root_fd);
    errno = saved;
    return fd;
}

static int copy_fd(int input, int output) {
    char buffer[4096];
    ssize_t count;
    while ((count = read(input, buffer, sizeof(buffer))) > 0) {
        ssize_t offset = 0;
        while (offset < count) {
            ssize_t wrote = write(output, buffer + offset, (size_t)(count - offset));
            if (wrote < 0) return -1;
            offset += wrote;
        }
    }
    return count < 0 ? -1 : 0;
}

static int run_confined(char **argv) {
    int abi = ll_create(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 1) return -1;
    __u64 rights = rights_for(abi);
    struct landlock_ruleset_attr ruleset = {.handled_access_fs = rights};
    int rs = ll_create(&ruleset, sizeof(ruleset), 0);
    int root = open(argv[2], O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (rs == -1 || root == -1) return -1;
    struct landlock_path_beneath_attr rule = {.allowed_access = rights, .parent_fd = root};
    if (ll_add(rs, &rule) == -1) return -1;
    close(root);
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == -1 || ll_restrict(rs) == -1) return -1;
    close(rs);
    if (mark_inherited() == -1) return -1;
    execv(argv[3], &argv[3]);
    return -1;
}

int main(int argc, char **argv) {
    if (argc < 4) return 2;
    if (strcmp(argv[1], "read") == 0 && argc == 4) {
        int fd = open_beneath(argv[2], argv[3], O_RDONLY, 0);
        if (fd == -1) return 1;
        int result = copy_fd(fd, STDOUT_FILENO);
        close(fd);
        return result != 0;
    }
    if (strcmp(argv[1], "write") == 0 && argc == 5) {
        int fd = open_beneath(argv[2], argv[3], O_WRONLY | O_CREAT | O_TRUNC, 0600);
        if (fd == -1) return 1;
        size_t left = strlen(argv[4]);
        const char *cursor = argv[4];
        while (left) {
            ssize_t count = write(fd, cursor, left);
            if (count < 0) { close(fd); return 1; }
            cursor += count;
            left -= (size_t)count;
        }
        return close(fd) == -1;
    }
    if (strcmp(argv[1], "run") == 0) {
        if (run_confined(argv) == -1) return 1;
    }
    return 2;
}
'''


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class Module05GraderTests(unittest.TestCase):
    def fixture(self) -> dict:
        return {
            "hostname": "ne-testhost",
            "fixture_id": "a1b2c3d4",
            "synthetic_user": "quiet-heron-555",
            "canary": "NECHO-test-only-canary",
        }

    def test_starter_fails_security_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-05-filesystem-landlock/lab/fs_guard.c", workspace / "fs_guard.c")
            checks = module_05.grade(workspace, self.fixture())
        self.assertFalse(all(check.passed for check in checks))
        self.assertFalse(next(check.passed for check in checks if check.name == "Traversal and absolute-path escapes are denied"))

    def test_reference_passes_all_behavioral_checks(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            (workspace / "fs_guard.c").write_text(REFERENCE_SOURCE, encoding="utf-8")
            checks = module_05.grade(workspace, self.fixture())
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))


if __name__ == "__main__":
    unittest.main()
