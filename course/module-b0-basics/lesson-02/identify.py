import os
import sys

print("This is one running copy of identify.py.")
print("Process ID:", os.getpid())
print("Parent process ID:", os.getppid())
if "fail" in sys.argv[1:]:
    print("I printed a message, but I am reporting failure.")
    raise SystemExit(7)
print("Finished successfully.")
