from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from northecho.grading import Check, run_bounded


PROBE_SOURCE = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>
static int emit(const char *text, size_t length) { return write(1, text, length) == (ssize_t)length ? 0 : 1; }
static int result(long value) { char line[96]; int n = snprintf(line, sizeof(line), "result=%ld errno=%d\n", value, errno); return emit(line, (size_t)n); }
int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (!strcmp(argv[1], "status")) {
        char b[4096] = {0}; int fd = open("/proc/self/status", O_RDONLY); ssize_t n = read(fd, b, sizeof(b)-1); close(fd);
        if (n < 0) return 1; char *a = strstr(b, "NoNewPrivs:"); char *s = strstr(b, "Seccomp:");
        char line[96]; int size = snprintf(line, sizeof(line), "%.13s\n%.10s\n", a, s); return emit(line, (size_t)size);
    }
    if (!strcmp(argv[1], "file") && argc == 3) {
        int fd = open(argv[2], O_RDONLY); char b[256]; ssize_t n = read(fd, b, sizeof(b)); close(fd);
        return n > 0 ? emit(b, (size_t)n) : 1;
    }
    errno = 0;
    if (!strcmp(argv[1], "socket")) return result(socket(AF_UNIX, SOCK_STREAM, 0));
    if (!strcmp(argv[1], "socketpair")) { int p[2]; return result(socketpair(AF_UNIX, SOCK_STREAM, 0, p)); }
    if (!strcmp(argv[1], "ptrace")) return result(ptrace(PTRACE_TRACEME, 0, 0, 0));
    return result(syscall(SYS_getppid));
}
'''


def _run(argv: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return run_bounded(argv, text=True, capture_output=True, timeout=8)
    except subprocess.TimeoutExpired:
        return None


def _output(run: subprocess.CompletedProcess[str] | None) -> str:
    return "" if run is None else run.stdout + run.stderr


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "seccomp_guard.c"
    if not source.is_file():
        return [Check("A seccomp launcher source file is present", False, "Module 06 lab: interface contract")]
    with tempfile.TemporaryDirectory(prefix="north-echo-grade-06-") as raw:
        evaluation = Path(raw)
        submission = evaluation / "submission"
        submission.mkdir()
        copied = submission / "seccomp_guard.c"
        shutil.copy2(source, copied)
        copied.chmod(0o444)
        launcher = submission / "seccomp-guard"
        compiled = run_bounded(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", str(copied), "-o", str(launcher), "-lseccomp"],
            text=True, capture_output=True,
        )
        if compiled.returncode != 0:
            return [Check("The seccomp launcher builds", False, "Module 06 lab: compile with libseccomp")]
        probe_source = evaluation / "probe.c"
        probe = evaluation / "probe"
        probe_source.write_text(PROBE_SOURCE, encoding="utf-8")
        probe_build = run_bounded(["cc", "-std=c11", "-Wall", "-Wextra", "-O2", "-static", str(probe_source), "-o", str(probe)], text=True, capture_output=True)
        if probe_build.returncode != 0:
            return [Check("The grader's static probe builds", False, "Use the documented disposable VM toolchain")]
        data = f"allowed-{fixture['hostname']}\n"
        note = evaluation / "note.txt"
        note.write_text(data, encoding="utf-8")
        status = _run([str(launcher), str(probe), "status"])
        file_run = _run([str(launcher), str(probe), "file", str(note)])
        socket_run = _run([str(launcher), str(probe), "socket"])
        pair_run = _run([str(launcher), str(probe), "socketpair"])
        ptrace_run = _run([str(launcher), str(probe), "ptrace"])
        unexpected = _run([str(launcher), str(probe), "unexpected"])
        malformed = _run([str(launcher)])
    denied = "result=-1 errno=1"
    return [
        Check("The seccomp launcher builds", True, "Module 06 lab interface"),
        Check("Filter mode is active inside the executed child", status is not None and status.returncode == 0 and "Seccomp:\t2" in status.stdout, "Module 06 lesson 03"),
        Check("no_new_privs is active inside the child", status is not None and "NoNewPrivs:\t1" in status.stdout, "Module 06 lesson 03"),
        Check("The stated file-read workload still succeeds", file_run is not None and file_run.returncode == 0 and file_run.stdout == data, "Module 06 lessons 01 and 03"),
        Check("Direct socket creation returns EPERM", denied in _output(socket_run), "Module 06 lessons 02-03"),
        Check("Alternate socket-pair creation returns EPERM", denied in _output(pair_run), "Module 06 lessons 02-03"),
        Check("ptrace returns EPERM", denied in _output(ptrace_run), "Module 06 lesson 03"),
        Check("An unlisted harmless syscall returns EPERM", denied in _output(unexpected), "Module 06 lesson 03: default deny"),
        Check("Malformed invocation fails closed", malformed is not None and malformed.returncode != 0, "Module 06 lab interface"),
    ]
