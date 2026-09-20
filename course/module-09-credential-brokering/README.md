# Module 09 - Broker credentials with operation capabilities

Remove fake credentials from workload environments, then place their use behind a local operation broker. HMAC-authenticated, short-lived capabilities bind the exact operation, resource, arguments, audience, run, and nonce without containing the underlying credential. Nonce consumption is remembered for one broker-process lifetime.

Play in order: `09.01`, `09.02`, `09.03`, then `module-09`.

Outcomes:

- observe that an environment credential is ambient authority inherited across `exec`;
- remove that authority with an explicit minimal environment;
- distinguish a signed capability from an encrypted secret;
- bind operation, resource, canonical input, audience, run identity, issue time, expiry, and nonce;
- deny tampering, expiry, excessive lifetime, replay, and confused-deputy substitutions before upstream contact;
- prove a broker used a fake credential upstream without returning it to the client.

Every credential, signing key, capability, resource, and upstream service is synthetic and lesson-local. Communication uses filesystem Unix sockets only; no DNS, LAN, public, cloud, employer, or production service is involved. Prerequisites are Modules 01, 04, and 08.

## Learning route and limits

First observe what an inherited environment makes available. Next authenticate
readable claims and compare them with a requested operation. Finally add policy
checks, an upstream service, and remembered consumption. Distinguish each step:
encoding is not encryption, HMAC is not an asymmetric signature, a valid token
is not permission for a different request, and a nonce alone does not stop replay.

The issuer, broker, client, and upstream are teaching roles running under one
VM account. A private file mode does not separate same-account processes. The
lessons demonstrate the intended request interface, not a complete secret-storage
boundary. Earlier filesystem/process controls are still required for confinement.

The replay cache is in memory and is lost on restart; consumption before contact
also means an upstream failure can spend a token. There is no exactly-once or
durable replay guarantee. All tests and observations use fake material only.
