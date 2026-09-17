#!/usr/bin/env python3
import json
import os
import socket

status = {}
with open("/proc/self/status", encoding="utf-8") as stream:
    for line in stream:
        if ":" in line:
            key, value = line.split(":", 1)
            status[key] = value.strip()

payload = {
    "hostname": socket.gethostname(),
    "uts_inode": os.stat("/proc/self/ns/uts").st_ino,
    "pid_inode": os.stat("/proc/self/ns/pid").st_ino,
    "mnt_inode": os.stat("/proc/self/ns/mnt").st_ino,
    "nspid": [int(value) for value in status.get("NSpid", "").split()],
    "proc_one_is_self": os.stat("/proc/1/ns/pid").st_ino == os.stat("/proc/self/ns/pid").st_ino and os.getpid() == 1,
}
print("NE_PROBE=" + json.dumps(payload, sort_keys=True))
