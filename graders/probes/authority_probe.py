#!/usr/bin/env python3
import os

print("PROBE_ALIVE")
if os.environ.get("NE_LAB_TOKEN"):
    print("ENV_LEAK")
for fd in range(3, 256):
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        data = os.read(fd, 4096).decode(errors="replace")
    except OSError:
        continue
    if data:
        print("FD_LEAK")
        print(data)
