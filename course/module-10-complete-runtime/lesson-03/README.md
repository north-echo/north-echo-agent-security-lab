# 10.03 - Launch, observe, and collect the composed runtime

## Outcomes and prerequisites

Complete 10.01-10.02 and Modules 01-09. You will compare an incomplete inner-only launch with the outer composition, interpret each effective-state field, and verify exact service collection. The final exercise bridges single-job execution to the independent batch capstone.

## Concepts before commands

The composition has several jobs: constrain resources before descendants start, create private user/network views, reduce privilege, clear the workload environment, install filesystem/syscall policy, permit one intended broker exchange, then collect owned runtime objects.

A **trusted computing base (TCB)** is the code and configuration whose correctness the design relies on. Here it includes the VM kernel, user service manager, launcher, guard, and broker. A valid filename does not establish that a guard's contents are trustworthy; the exercise supplies trusted code.

The word **attestation** in this small program means a local structured observation. It is not a hardware-signed report or proof that arbitrary malicious workload code tells the truth. The grader compiles its own known observer to check behavior independently.

Keep the baseline limits visible. This composition creates user/network namespaces, not private mount/PID namespaces. Its Landlock policy permits selected read-only observation paths. On the validated Fedora ABI 7 baseline, Landlock does not enforce the newer ABI 9 pathname Unix-socket-resolution right. Successful access to the intended broker is therefore **not proof that no other pathname Unix socket is reachable**. The minimal static workload and finite checks are not a production general-purpose agent sandbox.

## Prepare and locate the sources

From the course root:

```bash
./lab-start 10.03
cd .student/10.03
pwd
ls -l complete_runtime.py runtime_probe.c demo_broker.py batch_worker.c
cat complete_runtime.py
cat runtime_probe.c
cat demo_broker.py
cat batch_worker.c
```

The guard source from 10.02 remains available under the course tree for compilation. You read it in that lesson; do not edit it there. Every new local source is reproduced below.

### The outer launcher

<!-- source: course/module-10-complete-runtime/lesson-03/complete_runtime.py format=code -->
```python
#!/usr/bin/env python3
"""Launch one synthetic workload through the North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    fields = {"guard", "allowed_root", "command", "memory_max", "tasks_max", "cpu_percent"}
    if not isinstance(spec, dict) or set(spec) != fields:
        raise ValueError("spec must be an object with exactly the documented fields")
    if not all(isinstance(spec[name], str) for name in ("guard", "allowed_root")):
        raise ValueError("guard and allowed_root must be path strings")
    guard, root = Path(spec["guard"]), Path(spec["allowed_root"])
    command = spec["command"]
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(
            not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    if not Path(command[0]).is_absolute():
        raise ValueError("command executable must be absolute")
    root = root.resolve(strict=True)
    if root == Path("/"):
        raise ValueError("the whole filesystem cannot be the workload root")
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    return (
        guard.resolve(strict=True), root, [str(executable), *command[1:]],
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def register_owner(client_env: dict) -> dict:
    workspace = Path(__file__).resolve().parent
    prepared = workspace.parent.name == ".student"
    target = workspace.name if prepared else "10.lab"
    if target not in {"10.03", "10.lab"}:
        raise ValueError("unsupported prepared runtime workspace")
    unit = f"north-echo-{os.getuid()}-{target.replace('.', '-')}-{secrets.token_hex(6)}.service"
    owner = {"unit": unit, "uid": os.getuid(),
             "description": f"North Echo {target} workspace={workspace}", "record": None}
    if prepared:
        control = workspace.parent.parent / "scripts/labctl.py"
        subprocess.run([sys.executable, str(control), "register-unit", target, unit],
                       check=True, capture_output=True, text=True, timeout=5, env=client_env)
    else:
        # The external grader copies this file into a separate owned directory.
        runtime = workspace / ".runtime"
        if runtime.is_symlink():
            raise ValueError("refusing a symlinked ownership directory")
        runtime.mkdir(mode=0o700, exist_ok=True)
        record = runtime / (unit + ".json")
        with record.open("x", encoding="utf-8") as stream:
            json.dump(owner, stream, sort_keys=True)
        owner["record"] = record
    return owner


def inspect_unit(owner: dict, client_env: dict) -> dict | None:
    run = subprocess.run(
        ["systemctl", "--user", "show", owner["unit"], "--property=LoadState",
         "--property=Description", "--property=ControlGroup"],
        text=True, capture_output=True, timeout=5, env=client_env,
    )
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    if properties.get("LoadState") == "not-found":
        return None
    if run.returncode or not properties.get("LoadState"):
        raise RuntimeError("unit state could not be established; ownership record retained")
    return properties


def collect_owned(owner: dict, client_env: dict) -> None:
    properties = inspect_unit(owner, client_env)
    if properties is not None:
        group = properties.get("ControlGroup", "")
        prefix = f"/user.slice/user-{owner['uid']}.slice/user@{owner['uid']}.service/"
        if (properties.get("Description") != owner["description"]
                or not group.startswith(prefix) or not group.endswith("/" + owner["unit"])):
            raise RuntimeError("unit ownership mismatch; refusing stop and retaining record")
        subprocess.run(["systemctl", "--user", "stop", owner["unit"]],
                       check=True, capture_output=True, timeout=5, env=client_env)
        for _ in range(20):
            if inspect_unit(owner, client_env) is None:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("unit remains after stop; ownership record retained")
        if Path("/sys/fs/cgroup" + group).exists():
            raise RuntimeError("owned cgroup remains; ownership record retained")
    if owner["record"] is not None:
        owner["record"].unlink()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} SPEC.json RESULT.json", file=sys.stderr)
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, TypeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        owner = register_owner(client_env)
        unit = owner["unit"]
        argv = [
            "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
            "--expand-environment=no", f"--unit={unit}", f"--description={owner['description']}",
            "--property=KillMode=control-group", "--property=TimeoutStopSec=2s",
            "--property=RuntimeMaxSec=15s", "--property=CPUQuotaPeriodSec=100ms",
            f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
            "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
            "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
            "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
            "--", "/usr/bin/unshare", "--user", "--map-root-user", "--net", "--",
            "/usr/bin/setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
            "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
            "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
        ]
        try:
            run = subprocess.run(argv, text=True, capture_output=True, check=False,
                                 timeout=20, env=client_env)
        finally:
            collect_owned(owner, client_env)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"runtime launch or collection failed: {error}", file=sys.stderr)
        return 1

    attestation = None
    try:
        attestation = json.loads(run.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        pass
    result_path.write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": unit,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": attestation,
    }, sort_keys=True) + "\n", encoding="utf-8")
    return int(run.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- `integer` enforces bounds and rejects Boolean values. `validated` requires the exact spec fields before creating a unit or result.
- Guard/root fields must be absolute paths of the expected kind. The guard is trusted setup input, not an executable chosen by an untrusted tool request.
- Command arguments must be separate strings without NUL characters. Its executable must be absolute and resolve beneath the allowed root; the whole filesystem is refused as a root.
- `commonpath` compares path components, not textual prefixes. These checks assume operator-controlled setup paths; they are not race-free validation against a concurrent directory writer.
- `register_owner` records exact name, UID, and workspace description before launch. In prepared 10.03/10.lab workspaces it uses the course runtime registry; `module-10` is a CLI alias, not the directory name.
- The external grader copies the file into its own directory without the course launcher. That case writes an exclusive ownership record in a local `.runtime` directory.
- `inspect_unit` asks the user manager for exact-unit properties. Explicit `LoadState=not-found` means absent; a manager error is not absence.
- `collect_owned` verifies description and delegated cgroup path before stopping a remaining unit. It waits for observed absence and checks the recorded cgroup is gone. Unknown ownership keeps evidence and refuses mutation.
- `client_env` preserves only fixed locale/path plus the IPC variables needed to reach the user manager. These are for the trusted systemd client, not the final workload.
- The argv list uses `--expand-environment=no`. A Python list alone would not prevent systemd's own environment-reference expansion.
- `--wait --pipe --collect` waits for completion and captures output. CPU period is explicitly 100 ms; CPU/memory/swap/tasks and runtime/stop limits are set before descendants start.
- `unshare` establishes the private user/network views. `setpriv` then clears bounding, inheritable, and ambient sets and sets no-new-privileges. The observer checks all five capability sets after execution.
- `env -i` constructs the final fixed workload environment. The native guard then marks extra descriptors close-on-exec, applies Landlock, applies seccomp, and executes exact workload argv.
- The `finally` around execution runs owned collection on normal return, failure, or client timeout. A result is not published as a completed run if launch/collection raises an error.
- The last stdout line is parsed as an observation when possible. The result separately retains status, full stdout/stderr, and unit identity; the launcher does not infer every security property from status alone.

This teaching launcher captures output in memory. Its time and workload-resource limits are not a separate strict byte quota on the outer launcher's capture buffer. Use the supplied small observers; a production runner needs bounded streaming, stronger setup-file trust, and additional threat-model work.

### The confined observer

<!-- source: course/module-10-complete-runtime/lesson-03/runtime_probe.c format=code -->
```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

static int read_text(const char *path, char *buffer, size_t size) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd == -1)
        return -1;
    ssize_t count = read(fd, buffer, size - 1);
    close(fd);
    if (count < 0)
        return -1;
    buffer[count] = '\0';
    return 0;
}

static int status_value(const char *status, const char *name, unsigned long long *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%llx", value) == 1 ? 0 : -1;
}

static int status_decimal(const char *status, const char *name, int *value) {
    const char *line = strstr(status, name);
    if (!line)
        return -1;
    return sscanf(line + strlen(name), "%d", value) == 1 ? 0 : -1;
}

static int read_cgroup_value(const char *name, char *value, size_t size) {
    char membership[4096], relative[PATH_MAX], path[PATH_MAX];
    if (read_text("/proc/self/cgroup", membership, sizeof(membership)) == -1)
        return -1;
    char *line = strstr(membership, "0::");
    if (!line || sscanf(line, "0::%4095[^\n]", relative) != 1)
        return -1;
    if (snprintf(path, sizeof(path), "/sys/fs/cgroup%s/%s", relative, name) >= (int)sizeof(path))
        return -1;
    if (read_text(path, value, size) == -1)
        return -1;
    value[strcspn(value, "\n")] = '\0';
    return 0;
}

static int broker_request(const char *socket_path, const char *request_path,
                          const char *forbidden_marker, char *response, size_t size) {
    char request[16384];
    if (read_text(request_path, request, sizeof(request)) == -1)
        return 0;
    size_t length = strlen(request);
    if (length == 0 || request[length - 1] != '\n')
        return 0;
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd == -1)
        return 0;
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    if (strlen(socket_path) >= sizeof(address.sun_path)) {
        close(fd);
        return 0;
    }
    strcpy(address.sun_path, socket_path);
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) == -1 ||
        write(fd, request, length) != (ssize_t)length) {
        close(fd);
        return 0;
    }
    shutdown(fd, SHUT_WR);
    size_t used = 0;
    while (used < size - 1) {
        ssize_t count = read(fd, response + used, size - 1 - used);
        if (count == -1 && errno == EINTR)
            continue;
        if (count < 0) {
            close(fd);
            return 0;
        }
        if (count == 0)
            break;
        used += (size_t)count;
        if (memchr(response, '\n', used))
            break;
    }
    close(fd);
    if (used == 0 || used == size - 1)
        return 0;
    response[used] = '\0';
    return strcmp(response, "{\"ok\":true,\"result\":{\"value\":\"synthetic-result\"}}\n") == 0
           && strstr(response, forbidden_marker) == NULL;
}

int main(int argc, char **argv) {
    if (argc != 8) {
        fprintf(stderr, "usage: %s ALLOWED PROTECTED BROKER REQUEST HOST_NET_INODE HOST_USER_INODE FORBIDDEN_MARKER\n", argv[0]);
        return 2;
    }
    char byte[8], status[16384], cpu[128] = "?", memory[128] = "?";
    char swap[128] = "?", pids[128] = "?", broker_response[65536];
    int allowed_read = read_text(argv[1], byte, sizeof(byte)) == 0;
    errno = 0;
    int protected_fd = open(argv[2], O_RDONLY | O_CLOEXEC);
    int protected_denied = protected_fd == -1 && (errno == EACCES || errno == EPERM);
    if (protected_fd != -1)
        close(protected_fd);

    int inet_fd = socket(AF_INET, SOCK_STREAM, 0);
    int inet_denied = inet_fd == -1 && errno == EPERM;
    if (inet_fd != -1)
        close(inet_fd);

    struct stat net_stat, user_stat;
    unsigned long long host_net = strtoull(argv[5], NULL, 10);
    int private_net = stat("/proc/self/ns/net", &net_stat) == 0 &&
                      (unsigned long long)net_stat.st_ino != host_net;
    unsigned long long host_user = strtoull(argv[6], NULL, 10);
    int private_user = stat("/proc/self/ns/user", &user_stat) == 0 &&
                       (unsigned long long)user_stat.st_ino != host_user;

    unsigned long long cap_eff = 1, cap_bnd = 1, cap_amb = 1, cap_prm = 1, cap_inh = 1;
    int no_new_privs = 0, seccomp = 0;
    int status_ok = read_text("/proc/self/status", status, sizeof(status)) == 0 &&
                    status_value(status, "CapEff:\t", &cap_eff) == 0 &&
                    status_value(status, "CapBnd:\t", &cap_bnd) == 0 &&
                    status_value(status, "CapAmb:\t", &cap_amb) == 0 &&
                    status_value(status, "CapPrm:\t", &cap_prm) == 0 &&
                    status_value(status, "CapInh:\t", &cap_inh) == 0 &&
                    status_decimal(status, "NoNewPrivs:\t", &no_new_privs) == 0 &&
                    status_decimal(status, "Seccomp:\t", &seccomp) == 0;
    read_cgroup_value("cpu.max", cpu, sizeof(cpu));
    read_cgroup_value("memory.max", memory, sizeof(memory));
    read_cgroup_value("memory.swap.max", swap, sizeof(swap));
    read_cgroup_value("pids.max", pids, sizeof(pids));
    int broker_ok = broker_request(argv[3], argv[4], argv[7], broker_response, sizeof(broker_response));
    int credential_absent = getenv("NORTH_ECHO_FAKE_CREDENTIAL") == NULL;

    printf("{\"allowed_read\":%s,\"protected_denied\":%s,\"inet_denied\":%s,"
           "\"private_net\":%s,\"private_user\":%s,\"caps_zero\":%s,\"no_new_privs\":%d,"
           "\"seccomp\":%d,\"cpu\":\"%s\",\"memory\":\"%s\","
           "\"swap\":\"%s\",\"pids\":\"%s\",\"broker_ok\":%s,"
           "\"credential_absent\":%s}\n",
           allowed_read ? "true" : "false", protected_denied ? "true" : "false",
           inet_denied ? "true" : "false", private_net ? "true" : "false",
           private_user ? "true" : "false",
           status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
           cap_prm == 0 && cap_inh == 0 ? "true" : "false",
           no_new_privs, seccomp, cpu, memory, swap, pids,
           broker_ok ? "true" : "false", credential_absent ? "true" : "false");
    return !(allowed_read && protected_denied && inet_denied && private_net && private_user &&
             status_ok && cap_eff == 0 && cap_bnd == 0 && cap_amb == 0 &&
             cap_prm == 0 && cap_inh == 0 &&
             no_new_privs == 1 && seccomp == 2 && broker_ok && credential_absent);
}
```
<!-- /source -->

### Source, block by block

- `read_text` opens a path, reads a bounded buffer, closes the descriptor, and terminates the C string.
- Status helpers locate hexadecimal capability fields and decimal policy fields in this process's status text.
- `read_cgroup_value` derives the process's own unified cgroup path from `0::...`, then reads controller files. It does not infer effective values from the launch spec.
- `broker_request` reads a small prebuilt request, requires its newline, checks pathname length, and creates an AF_UNIX socket.
- The response read loops over a byte stream rather than assuming one read is a whole message. Its final comparison expects the exact compact synthetic response from this fixture; it is not a general JSON parser.
- The main observer performs allowed/protected reads and an AF_INET socket attempt. It records actual denials, not just the existence of policy APIs.
- Namespace inode numbers are compared with saved parent observations. Different numbers establish different namespace objects, not every desired property of their contents.
- Effective, permitted, inheritable, bounding, and ambient capabilities are checked along with no-new-privileges and seccomp mode.
- CPU, memory, swap, and task values are printed for an external checkpoint to compare against the requested profile.
- A successful intended broker exchange and absence of the named fake environment variable are separate fields.
- The exit status aggregates the fixed Boolean checks. Resource-profile equality still requires comparing the printed values with the spec.

### The outside synthetic broker

<!-- source: course/module-10-complete-runtime/lesson-03/demo_broker.py format=code -->
```python
#!/usr/bin/env python3
"""One-shot synthetic operation broker for the composition lesson."""

import hashlib
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


def main() -> int:
    if len(sys.argv) != 5:
        return 2
    socket_path, token_path, credential_path, event_path = map(Path, sys.argv[1:])
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    token = token_path.read_text(encoding="utf-8").strip()
    credential = credential_path.read_text(encoding="utf-8").strip()
    if socket_path.exists() or socket_path.is_symlink():
        raise SystemExit("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        listener.listen(1)
        listener.settimeout(300)
        peer, _ = listener.accept()
        with peer:
            peer.settimeout(2)
            with peer.makefile("rb") as incoming:
                line = incoming.readline(16385)
            if len(line) > 16384 or not line.endswith(b"\n"):
                raise ValueError("request must be one bounded line")
            request = json.loads(line)
            expected = {"operation": "read", "resource": "synthetic:record", "token": token}
            if request != expected:
                response = {"ok": False, "error": "capability denied"}
            else:
                proof = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
                event_path.write_text(json.dumps({"credential_used": True, "proof": proof}) + "\n",
                                      encoding="utf-8")
                response = {"ok": True, "result": {"value": "synthetic-result"}}
            peer.sendall(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, line by line

- The broker reads a random opaque token and a fake credential from files outside the workload root.
- It creates a mode-0600 pathname socket below the workload root, where the intended caller can reach it.
- It accepts one bounded request with a peer timeout, requiring the exact token, operation, and resource.
- Success hashes the fake credential plus fixed operation context into a separate event and returns only the harmless synthetic value.
- This event demonstrates use of the fake value by trusted teaching code. There is no separate credential-protected upstream in this smaller composition fixture; 09.03 supplied that fuller example.
- The token is an opaque one-operation teaching grant, **not** the full HMAC/expiry/replay protocol from Module 09. Do not claim this fixture reimplements that protocol.
- The listener is one-shot, and normal SIGTERM/SIGINT cleanup removes its socket. The runtime backstop limits an abandoned instance.

### A small worker for later batch practice

<!-- source: course/module-10-complete-runtime/lesson-03/batch_worker.c format=code -->
```c
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
```
<!-- /source -->

### Source, line by line

- `strtol` parses a requested ordinary exit code from 0 through 125 and rejects trailing text.
- The membership loop finds this process's unified cgroup path and closes its file.
- Bounded `snprintf` constructs the memory-controller filename, refusing truncation.
- Reading an integer from `memory.max` requires a finite numeric limit; `max` would not be accepted as a number.
- The final JSON reports the requested status and the **observed** memory ceiling, then exits with that status. This worker does not need a broker.

## Exercise 1 - Build local synthetic fixtures

```bash
NE_DEMO=$(mktemp -d "$PWD/d.XXXXXX")
mkdir "$NE_DEMO/allowed"
gcc -O2 -Wall -Wextra -static \
  ../../course/module-10-complete-runtime/lesson-02/runtime_guard.c \
  -o "$NE_DEMO/runtime_guard" -lseccomp
gcc -O2 -Wall -Wextra -static runtime_probe.c -o "$NE_DEMO/allowed/runtime_probe"
gcc -O2 -Wall -Wextra -static batch_worker.c -o "$NE_DEMO/allowed/batch_worker"
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import secrets
import sys

root = Path(sys.argv[1])
token = "CAP-" + secrets.token_hex(16)
credential = "FAKE-CREDENTIAL-" + secrets.token_hex(16)
(root / "allowed/allowed.txt").write_text("allowed\n")
(root / "protected.txt").write_text("synthetic-protected\n")
for name, value in (("token.txt", token), ("credential.txt", credential)):
    with (root / name).open("x") as stream:
        stream.write(value + "\n")
    (root / name).chmod(0o600)
(root / "allowed/request.json").write_text(json.dumps({
    "operation": "read", "resource": "synthetic:record", "token": token
}, sort_keys=True, separators=(",", ":")) + "\n")
PY
NE_HOST_NET=$(stat -Lc '%i' /proc/self/ns/net)
NE_HOST_USER=$(stat -Lc '%i' /proc/self/ns/user)
```

The new directory is inside this prepared workspace. Static binaries avoid dynamic-loader exceptions. Random token/credential values stay synthetic; only the narrow request goes below the workload root. `stat -L` follows the namespace link to obtain the parent namespace object's inode for comparison.

Define a registered helper for the outside broker:

```bash
start_demo_broker() {
  NE_BROKER_UNIT="north-echo-$(id -u)-10-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 10.03 "$NE_BROKER_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_BROKER_UNIT" --description="North Echo 10.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- \
    /usr/bin/python3 "$PWD/demo_broker.py" "$NE_DEMO/allowed/broker.sock" \
    "$NE_DEMO/token.txt" "$NE_DEMO/credential.txt" "$1"
  for attempt in {1..50}; do test -S "$NE_DEMO/allowed/broker.sock" && break; sleep 0.1; done
  test -S "$NE_DEMO/allowed/broker.sock"
}
```

This uses the owned lifecycle from Modules 07-09. Its argument selects the exact event filename. A failed readiness check is setup failure; inspect `journalctl --user -u "$NE_BROKER_UNIT" --no-pager`, then clean up before continuing.

## Exercise 2 - Observe an incomplete inner-only launch

```bash
start_demo_broker "$NE_DEMO/direct-event.json"
NE_DIRECT_STATUS=0
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  timeout 5s "$NE_DEMO/runtime_guard" "$NE_DEMO/allowed" "$NE_DEMO/allowed/runtime_probe" \
  "$NE_DEMO/allowed/allowed.txt" "$NE_DEMO/protected.txt" "$NE_DEMO/allowed/broker.sock" \
  "$NE_DEMO/allowed/request.json" "$NE_HOST_NET" "$NE_HOST_USER" 'FAKE-CREDENTIAL-' \
  > "$NE_DEMO/direct.json" || NE_DIRECT_STATUS=$?
python3 -m json.tool "$NE_DEMO/direct.json"
test "$NE_DIRECT_STATUS" -eq 1
../../lab-cleanup 10.03
test ! -e "$NE_DEMO/allowed/broker.sock"
```

The temporary assignment deliberately gives this one launch the **fake** ambient credential. The guard enforces its filesystem/syscall controls and the intended broker operation works, but `private_net`, `private_user`, and `credential_absent` are false. Resource values come from the parent rather than this lesson's desired profile.

Expected status is 1 from the observer's failed conjunction, not timeout status 124 or a missing executable. Partial success is not complete composition. The broker is one-shot, so the repair needs a fresh instance.

## Exercise 3 - Generate the spec and run the composition

```bash
python3 - "$NE_DEMO" "$NE_HOST_NET" "$NE_HOST_USER" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
spec = {
    "guard": str(root / "runtime_guard"), "allowed_root": str(root / "allowed"),
    "command": [str(root / "allowed/runtime_probe"),
                str(root / "allowed/allowed.txt"), str(root / "protected.txt"),
                str(root / "allowed/broker.sock"), str(root / "allowed/request.json"),
                sys.argv[2], sys.argv[3], "FAKE-CREDENTIAL-"],
    "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50
}
(root / "spec.json").write_text(json.dumps(spec) + "\n")
PY
start_demo_broker "$NE_DEMO/event.json"
NORTH_ECHO_FAKE_CREDENTIAL="$(head -n 1 "$NE_DEMO/credential.txt")" \
  python3 complete_runtime.py "$NE_DEMO/spec.json" "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/result.json"
python3 -m json.tool "$NE_DEMO/event.json"
../../lab-cleanup 10.03
```

Python serializes structured values instead of building JSON by shell string concatenation. The fake credential is still present in the launcher's environment, so observed absence in the final workload tests the actual handoff repair.

The result should retain status 0 and a final observation in which every intended Boolean is true. Expected resource strings are CPU `50000 100000`, memory `50331648`, swap `0`, and tasks `16`. Cleanup checks both the already-collected workload and the separate outside broker through their registered ownership.

## Checkpoint - Compare effects and verify the exact unit

```bash
python3 - "$NE_DEMO" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
direct = json.loads((root / "direct.json").read_text())
assert direct["private_net"] is False and direct["private_user"] is False
assert direct["credential_absent"] is False
assert direct["allowed_read"] is True and direct["protected_denied"] is True
result = json.loads((root / "result.json").read_text())
observed = result["attestation"]
assert result["status"] == 0
for field in ("allowed_read", "protected_denied", "inet_denied", "private_net",
              "private_user", "caps_zero", "broker_ok", "credential_absent"):
    assert observed[field] is True, field
assert observed["no_new_privs"] == 1 and observed["seccomp"] == 2
assert (observed["cpu"], observed["memory"], observed["swap"], observed["pids"]) == (
    "50000 100000", "50331648", "0", "16")
credential = (root / "credential.txt").read_text().strip()
event = json.loads((root / "event.json").read_text())
expected = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
assert event == {"credential_used": True, "proof": expected}
assert credential not in (root / "result.json").read_text()
unit = subprocess.run(["systemctl", "--user", "show", result["unit"],
                       "--property=LoadState"], capture_output=True, text=True, check=False)
assert unit.stdout.strip() == "LoadState=not-found", unit.stdout + unit.stderr
assert not (root / "allowed/broker.sock").exists()
print("COMPOSED EFFECTS AND EXACT COLLECTION: PASS")
PY
```

The checker compares effective state, recomputes the synthetic broker event, and asks about the **exact** returned unit. An empty wildcard listing or a failed manager command cannot substitute for that observed absence.

This evidence concerns the supplied code and fixtures. It does not certify arbitrary workload output, every possible secret channel, future Landlock rights, or exclusive access to one Unix socket on older ABIs.

## Faded practice - One job, then three

The batch worker is already compiled. Create three single-job specs from the known-good outer spec, with desired exit statuses 0, 7, and 0:

```bash
python3 - "$NE_DEMO" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
base = json.loads((root / "spec.json").read_text())
for index, status in enumerate((0, 7, 0), start=1):
    spec = dict(base)
    spec["command"] = [str(root / "allowed/batch_worker"), str(status)]
    spec["memory_max"] = 33554432 if index == 2 else 50331648
    (root / f"job-{index}.json").write_text(json.dumps(spec) + "\n")
PY
python3 complete_runtime.py "$NE_DEMO/job-1.json" "$NE_DEMO/job-1-result.json"
NE_JOB_TWO_STATUS=0
python3 complete_runtime.py "$NE_DEMO/job-2.json" "$NE_DEMO/job-2-result.json" || NE_JOB_TWO_STATUS=$?
test "$NE_JOB_TWO_STATUS" -ne 0
python3 complete_runtime.py "$NE_DEMO/job-3.json" "$NE_DEMO/job-3-result.json"
```

No broker is needed for this worker. The outer launcher reports nonzero for the middle workload, while its saved `status` is 7. The third valid job still runs. Inspect each result's observed memory value; the middle one must report 33554432, not merely inherit the input filename.

Now write `batch-notes.md` and design your own ordered batch interface using Module 04's list/trace skills. Give jobs unique IDs, validate **all** specs before any launch, preserve IDs and statuses in input order, and verify each exact unit is absent.

Deliberate mistake to reason about: a later job has `tasks_max: 0`, but the first job was already launched before validating it. Explain why malformed input should reject the batch before side effects, while a valid job returning 7 need not prevent later valid jobs. Use `validated` from this local source to review each spec without launching; it is separate from `main`.

Checkpoint for this faded practice: show ordered 0/7/0 results, observed per-job memory, exact unit absence, and a malformed later spec rejected before any worker runs. The capstone withholds a batch implementation and uses fresh profiles.

## Troubleshooting and replay

A missing result can mean validation, setup, timeout, or collection failure; read the specific launcher diagnostic. A valid result with status 7 means an ordinary workload failure was preserved. A remaining owner record is evidence to inspect, not permission to kill a name-matched process.

If cgroups fail, run `../../scripts/linux-preflight`. If a socket path is too long, keep the VM course path short and use a fresh prepared workspace. If static execution fails, verify the workload is beneath its allowed root. Keep SELinux enabled; do not add IP routes, host firewall changes, or public services.

Preview `../../lab-cleanup 10.03 --dry-run`, then run `../../lab-cleanup 10.03`. Save your notes, return with `cd ../..`, and use `./lab-reset 10.03` to discard this lesson's generated artifacts after verified cleanup.

## Source truth

[setpriv(1)](https://man7.org/linux/man-pages/man1/setpriv.1.html) explains privilege settings across execution; [proc_pid_status(5)](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html) defines observed capability/policy fields. Use the installed `man systemd-run` and `man systemd.resource-control` for the VM's manager version. The [Landlock documentation](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html) defines the ABI-specific limits that a passing local observation must not overstate.
