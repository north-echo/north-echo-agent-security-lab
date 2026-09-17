#!/usr/bin/env python3
import json

wanted = {"Uid", "CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb", "NoNewPrivs"}
values = {}
with open("/proc/self/status", encoding="utf-8") as stream:
    for line in stream:
        key, separator, value = line.partition(":")
        if separator and key in wanted:
            values[key] = value.strip()
print("NE_PROBE=" + json.dumps(values, sort_keys=True))
