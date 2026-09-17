from __future__ import annotations

CATALOG = {
    "01.01": ("01", "Processes are the boundary you actually launched", True),
    "01.02": ("01", "Environment inheritance is authority", True),
    "01.03": ("01", "File descriptors cross exec", True),
    "01.lab": ("01", "Independent lab: hygienic launcher", True),
    "02.01": ("02", "Read namespace identity", True),
    "02.02": ("02", "Change UTS state without changing the host", True),
    "02.03": ("02", "PID namespaces and the /proc mistake", True),
    "02.lab": ("02", "Independent lab: namespace launcher", True),
    "03.01": ("03", "UIDs are not the whole privilege story", True),
    "03.02": ("03", "Drop capability sets deliberately", True),
    "03.03": ("03", "Make privilege non-gainable", True),
    "03.lab": ("03", "Independent lab: privilege floor", True),
    "04.01": ("04", "Run a deterministic tool loop and record every action", True),
    "04.02": ("04", "Preserve argv boundaries and handle tool failure", True),
    "04.03": ("04", "Inventory and remove ambient launcher authority", True),
    "04.lab": ("04", "Independent lab: auditable local tool runner", True),
    "05.01": ("05", "Break pathname string checks", True),
    "05.02": ("05", "Make lookup descriptor-relative with openat2", True),
    "05.03": ("05", "Restrict a child with Landlock", True),
    "05.lab": ("05", "Independent lab: filesystem guard", True),
    "06.01": ("06", "Measure the workload before filtering", True),
    "06.02": ("06", "Compare errno, kill, and blacklist bypass", True),
    "06.03": ("06", "Launch with a native default-deny filter", True),
    "06.lab": ("06", "Independent lab: default-deny syscall launcher", True),
    "07.01": ("07", "Observe an effective CPU quota", True),
    "07.02": ("07", "Bound memory and observe OOM", True),
    "07.03": ("07", "Bound process-tree growth and collect it", True),
    "07.lab": ("07", "Independent lab: bounded transient runner", True),
    "08.01": ("08", "Remove the inherited IP network", True),
    "08.02": ("08", "Reach one service through a Unix-socket broker", True),
    "08.03": ("08", "Reauthorize names, ports, redirects, and runs", True),
    "08.lab": ("08", "Independent lab: policy-bound egress broker", True),
    "09.01": ("09", "Remove ambient credential authority", True),
    "09.02": ("09", "Bind a signed operation capability", True),
    "09.03": ("09", "Deny replay and confused-deputy substitution", True),
    "09.lab": ("09", "Independent lab: capability-bound credential broker", True),
}

SCAFFOLDS = {
    "10": "Compose a complete agent runtime",
    "11": "Vulnerable variants and break/fix research",
    "12": "Adaptive adversary and Boundary Atlas graduation",
}

MODULE_SLUGS = {
    "01": "process-authority",
    "02": "namespaces",
    "03": "privilege",
    "04": "minimal-agent",
    "05": "filesystem-landlock",
    "06": "seccomp",
    "07": "cgroups",
    "08": "network-egress",
    "09": "credential-brokering",
    "10": "complete-runtime",
    "11": "break-fix-research",
    "12": "adaptive-adversary",
}


def course_dir_name(module: str) -> str:
    return f"module-{module}-{MODULE_SLUGS[module]}"


def target_dir_name(target: str) -> str:
    module, item = target.split(".")
    return "lab" if item == "lab" else f"lesson-{item}"


def normalize_target(raw: str) -> str:
    value = raw.strip().lower()
    if value.startswith("module-"):
        module = value.removeprefix("module-").zfill(2)
        return f"{module}.lab"
    if value.count(".") == 1:
        module, item = value.split(".")
        return f"{module.zfill(2)}.{item.zfill(2) if item.isdigit() else item}"
    raise ValueError(f"invalid target: {raw}")


def targets_for_scope(raw: str) -> list[str]:
    value = raw.strip().lower()
    if value == "--all":
        return sorted(CATALOG)
    if value.startswith("module-"):
        module = value.removeprefix("module-").zfill(2)
        targets = sorted(key for key in CATALOG if key.startswith(module + "."))
        if not targets:
            raise ValueError(f"module is not playable in this release: {raw}")
        return targets
    target = normalize_target(value)
    if target not in CATALOG:
        raise ValueError(f"unknown or not-yet-playable target: {raw}")
    return [target]
