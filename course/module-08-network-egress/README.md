# Module 08 - Isolate the network and mediate egress

Remove the workload's inherited IP network, then expose only a narrow HTTP capability through a filesystem Unix socket. The broker uses an explicit synthetic name-to-loopback map, binds requests to a run identity, and authorizes every redirect again.

Play in order: `08.01`, `08.02`, `08.03`, then `module-08`.

Outcomes:

- prove a new network namespace starts with loopback down and cannot reach a service on host loopback;
- distinguish removing direct IP connectivity from authorizing one mediated operation;
- carry a structured request over `AF_UNIX` without restoring an IP route;
- authorize a synthetic hostname, resolved address, port, path shape, and run identity;
- reauthorize redirects before contacting their destinations;
- bound request and response sizes and cleanly remove the broker socket.

All services are synthetic and bind only to `127.0.0.1`. The exercises do not create veth devices, routes, firewall rules, DNS traffic, or public requests. Prerequisites are Modules 01-07 and Linux support for unprivileged user plus network namespaces.

## Learning route and limits

Begin with a working connection before removing the network view. Otherwise a stopped server could look like successful isolation. Next separate direct connectivity from a permitted broker operation. Finally follow a redirect through a fresh authorization decision and compare correct enforcement with an incorrectly broad policy.

The network namespace, Unix-socket pathname, policy file, and broker process are different parts of the design. Be able to point to the decision each controls. A run ID is a context label, not authentication; mode 0600 does not isolate same-account processes; these small HTTP fixtures are not production services.

Each lesson includes exact preparation commands, complete sources, observations, a deliberate mistake and repair, and registered cleanup. Keep the resource limits and runtime backstops from Module 07. Do not disable SELinux to make a demonstration work.

Readiness for the independent lab means you can explain why a parser is not an authorizer, why an allowed first hop does not authorize a redirect, and why absence of a protected body is weaker evidence than measuring that no protected request occurred.
