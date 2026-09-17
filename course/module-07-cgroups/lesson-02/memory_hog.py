#!/usr/bin/env python3
import sys, time

megabytes = int(sys.argv[1])
blocks = []
for index in range(megabytes):
    blocks.append(bytearray(1024 * 1024))
    if index % 8 == 0:
        print(f"allocated_mb={index + 1}", flush=True)
time.sleep(1)
