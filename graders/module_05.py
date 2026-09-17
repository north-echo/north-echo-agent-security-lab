from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from northecho.grading import Check


PROBE_SOURCE = r'''
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    int fd = strcmp(argv[1], "path") == 0 ? open(argv[2], O_RDONLY) : atoi(argv[2]);
    char buffer[512];
    ssize_t count = read(fd, buffer, sizeof(buffer));
    if (count < 0) { fprintf(stderr, "DENIED:%s\n", strerror(errno)); return 1; }
    return write(STDOUT_FILENO, buffer, (size_t)count) == count ? 0 : 1;
}
'''


def _run(argv: list[str], *, pass_fds: tuple[int, ...] = ()) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(argv, text=True, capture_output=True, timeout=8, pass_fds=pass_fds)
    except subprocess.TimeoutExpired:
        return None


def _ok(run: subprocess.CompletedProcess[str] | None) -> bool:
    return run is not None and run.returncode == 0


def _denied(run: subprocess.CompletedProcess[str] | None, canary: str) -> bool:
    return run is not None and run.returncode != 0 and canary not in run.stdout and canary not in run.stderr


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "fs_guard.c"
    if not source.is_file():
        return [Check("A filesystem guard source file is present", False, "Module 05 lab: interface contract")]

    with tempfile.TemporaryDirectory(prefix="north-echo-grade-05-") as raw:
        evaluation = Path(raw)
        submission = evaluation / "submission"
        allowed = evaluation / f"allowed-{fixture['hostname']}"
        protected = evaluation / f"protected-{fixture['hostname']}"
        submission.mkdir()
        allowed.mkdir()
        protected.mkdir()
        copied = submission / "fs_guard.c"
        shutil.copy2(source, copied)
        copied.chmod(0o444)
        binary = submission / "fs-guard"
        compiled = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-O2", str(copied), "-o", str(binary)],
            text=True,
            capture_output=True,
        )
        if compiled.returncode != 0:
            return [Check("The filesystem guard builds", False, "Module 05 lab: compile the required interface")]

        allowed_text = f"allowed-{fixture['hostname']}\n"
        canary = fixture["canary"]
        (allowed / "input.txt").write_text(allowed_text, encoding="utf-8")
        secret = protected / "secret.txt"
        secret.write_text(canary + "\n", encoding="utf-8")
        (allowed / "escape-link").symlink_to(secret)

        read = _run([str(binary), "read", str(allowed), "input.txt"])
        write_text = f"written-{fixture['hostname']}"
        write = _run([str(binary), "write", str(allowed), "output.txt", write_text])
        write_ok = _ok(write) and (allowed / "output.txt").is_file() and (allowed / "output.txt").read_text() == write_text
        traversal = _run([str(binary), "read", str(allowed), f"../{protected.name}/secret.txt"])
        symlink = _run([str(binary), "read", str(allowed), "escape-link"])
        absolute = _run([str(binary), "read", str(allowed), str(secret)])

        probe_source = allowed / "probe.c"
        probe = allowed / "probe"
        probe_source.write_text(PROBE_SOURCE, encoding="utf-8")
        probe_build = subprocess.run(["cc", "-static", "-O2", str(probe_source), "-o", str(probe)], text=True, capture_output=True)
        child_allowed = None
        child_denied = None
        inherited = None
        if probe_build.returncode == 0:
            child_allowed = _run([str(binary), "run", str(allowed), str(probe), "path", str(allowed / "input.txt")])
            child_denied = _run([str(binary), "run", str(allowed), str(probe), "path", str(secret)])
            fd = os.open(secret, os.O_RDONLY)
            try:
                inherited = _run([str(binary), "run", str(allowed), str(probe), "fd", str(fd)], pass_fds=(fd,))
            finally:
                os.close(fd)

        unknown = _run([str(binary), "unknown", str(allowed), "input.txt"])

    return [
        Check("The filesystem guard builds", True, "Module 05 lab interface"),
        Check("Descriptor-relative read preserves allowed access", _ok(read) and read.stdout == allowed_text, "Module 05 lesson 02"),
        Check("Descriptor-relative write preserves exact content", bool(write_ok), "Module 05 lesson 02"),
        Check("Traversal and absolute-path escapes are denied", _denied(traversal, canary) and _denied(absolute, canary), "Module 05 lessons 01-02"),
        Check("Symlink escape is denied", _denied(symlink, canary), "Module 05 lessons 01-02"),
        Check("A static child inside the allowed tree executes", probe_build.returncode == 0 and _ok(child_allowed) and child_allowed.stdout == allowed_text, "Module 05 lesson 03"),
        Check("Landlock denies the child a new outside open", _denied(child_denied, canary), "Module 05 lesson 03"),
        Check("Pre-opened protected descriptors are closed on exec", _denied(inherited, canary), "Module 05 lesson 03 and Module 01 lesson 03"),
        Check("Unknown operations fail closed", unknown is not None and unknown.returncode != 0, "Module 05 lab interface"),
    ]
