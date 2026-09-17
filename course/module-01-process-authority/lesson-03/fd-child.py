#!/usr/bin/env python3
import os

for fd in range(0, 32):
    try:
        target = os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        continue
    print(f"fd={fd} target={target}")
    if fd >= 3:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            print(os.read(fd, 4096).decode(errors="replace"))
        except OSError:
            pass
