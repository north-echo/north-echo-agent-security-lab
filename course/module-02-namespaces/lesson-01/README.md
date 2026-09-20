# 02.01 - Read namespace identity

## Goals

- Record baseline namespace handles.
- Create a mapped user namespace as an ordinary user.
- Interpret namespace-local UID 0 without confusing it with host root.
- Read the UID mapping that connects inside and outside identities.

## Before you start

Complete Module 01 first. Work as your ordinary user inside the disposable Linux VM. In this chapter, **parent** means the surrounding VM environment, not your Mac. None of these commands belong in the Mac terminal.

A namespace is a kernel object that gives member processes a particular view of one category of state. Joining a UTS namespace changes hostname state; joining a PID namespace changes process-number visibility. A user namespace also defines how user and group IDs map to the parent. Creating one kind does not create all the others.

`/proc` is a kernel-provided filesystem, not a collection of saved reports. `/proc/self` refers to the process accessing it. Thus the `readlink` child below inspects its own membership, inherited from your shell. A namespace handle such as `user:[4026531837]` identifies an object; it is not a user ID and its exact number is not a learning target.

From the course root:

```bash
./lab-start 02.01
cd .student/02.01
pwd
ls -l
```

`lab-start` prepares the editable workspace. `cd` enters it, `pwd` confirms where you are, and `ls -l` shows its contents. This lesson uses shell commands; there is no hidden program you need to find or compile.

## Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

## What each line does

- The first `printf` emits headings. `%-8s` left-aligns a string in an eight-character field.
- `for ns in ...; do` begins a loop and assigns each listed namespace name to `ns` in turn.
- `readlink /proc/self/ns/$ns` asks procfs for this process's handle for the current type.
- `$(...)` substitutes that handle into `printf`.
- Quotes around both expansions preserve one argument per value.
- `done` ends the loop.

Expected shape:

```text
TYPE     HANDLE
user     user:[4026531837]
uts      uts:[4026531838]
pid      pid:[4026531836]
mnt      mnt:[4026531841]
net      net:[4026531992]
ipc      ipc:[4026531839]
cgroup   cgroup:[4026531835]
```

Exact numbers vary. Equal handles mean two processes refer to the same namespace object for that type; unequal handles mean different membership.

## Exercise 2 - Create a mapped user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

## What each line does

- `unshare` creates requested namespaces for the command that follows.
- `--user` requests a new user namespace.
- `--map-root-user` maps the invoking ordinary identity to UID and GID 0 inside it.
- `sh -c` starts a shell whose program is the following quoted string.
- Single quotes keep the outer shell from expanding `$(id -u)` or interpreting inner newlines.
- Inside, `id -u` prints the namespace-visible effective UID.
- `readlink` records the new user namespace handle.
- `uid_map` describes how ranges of inside UIDs translate to parent-namespace UIDs.

Typical mapping shape:

```text
inside uid=0
user:[4026532777]
         0       1000          1
```

The mapping line means one ID beginning at inside UID 0 maps to parent UID 1000. The parent value will match your ordinary VM account, not necessarily 1000.

## Exercise 3 - Disprove “UID 0 means global root”

```bash
unshare --user --map-root-user sh -c 'id; ls /root'
```

## What each part does

- The namespace flags reproduce the mapped identity.
- `;` runs the second inner command whether or not `id` succeeds.
- `id` reports namespace-relative UID 0.
- `ls /root` attempts a read-only directory listing through the existing VM filesystem.
- On the course image, `/root` is not readable by your ordinary account. The expected permission denial shows that namespace-local UID 0 did not grant that access. If an administrator made `/root` world-readable, this particular test would not demonstrate a denial; inspect permissions instead of changing them.

User namespaces can grant a process capabilities over resources owned by the new namespace. They do not grant corresponding power over parent-owned resources. A complete identity statement therefore includes the numeric IDs, the user namespace handle, and the ID mappings.

## Troubleshooting and checkpoint

- `Operation not permitted` usually means unprivileged user namespaces are disabled by VM policy.
- An empty or surprising map means the mapping helper failed; inspect stderr instead of assuming root was created.
- Never interpret `id -u` alone as a privilege proof.
- You should be able to compare two namespace handles and explain the three columns in `uid_map`.

Before continuing, predict whether creating only a user namespace also changes the UTS handle. Repeat the baseline loop inside the quoted child command to test your prediction. The repair to the mistaken "root everywhere" interpretation is to record the mapping and namespace, not to add `sudo`.

The child namespace is released when its last process/reference disappears. No global setting needs undoing. To discard lesson work, return to the course root with `cd ../..` and run `./lab-reset 02.01`; that reset deliberately removes this lesson's workspace.

## Source truth

The identity and mapping model is documented in [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html); the command flags are documented in [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html). These explain the mechanism, while the observations above establish what your VM actually allowed.
