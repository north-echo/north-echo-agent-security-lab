# Module 09 - Broker credentials with operation capabilities

Remove fake credentials from workload environments, then place them behind a local operation broker. Signed, short-lived capabilities bind the exact operation, resource, arguments, audience, run, and one-use nonce without containing the underlying credential.

Play in order: `09.01`, `09.02`, `09.03`, then `module-09`.

Outcomes:

- observe that an environment credential is ambient authority inherited across `exec`;
- remove that authority with an explicit minimal environment;
- distinguish a signed capability from an encrypted secret;
- bind operation, resource, canonical input, audience, run identity, issue time, expiry, and nonce;
- deny tampering, expiry, excessive lifetime, replay, and confused-deputy substitutions before upstream contact;
- prove a broker used a fake credential upstream without returning it to the client.

Every credential, signing key, capability, resource, and upstream service is synthetic and lesson-local. Communication uses filesystem Unix sockets only; no DNS, LAN, public, cloud, employer, or production service is involved. Prerequisites are Modules 01, 04, and 08.
