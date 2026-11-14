# CHECKCONN: bidirectional server-link preflight (design draft)

Status: design only; no daemon behavior has changed.

## Goal

Allow an authorized IRC operator connected to any server to request a non-disruptive
preflight of two existing servers' ability to initiate a server link in either
direction, without changing current topology.

Operator syntax: `CHECKCONN <server1> [port] <server2>`

- Two names: each endpoint uses its own configured outbound port (or existing
  Bahamut default if absent).
- Three arguments: the middle argument must be a decimal TCP port in 1..65535;
  the explicit port applies to both directions.
- Both names must identify currently linked servers. Reject identical names.
- An operator must have global routing privileges. Recheck authorization at
  the originating server, and accept interserver requests only from an existing
  trusted server connection. Never expose configured secrets in replies.

## Proposed orchestration

1. The operator's local server allocates an unpredictable request identifier,
   records the requesting operator and both endpoints, and sends an authenticated
   interserver CHECKCONN request to server1 via the existing network.
2. Server1 validates the request and starts an asynchronous, bounded probe to
   server2, using the configured source address, destination, transport, and
   connect-block policy. Report an explicit stage-by-stage result.
3. After the first response or timeout, the coordinator sends the reverse probe
   request to server2. Never run both probes simultaneously.
4. The coordinator returns the results to the original operator and deletes
   request state. Abort cleanly if the operator quits, a server splits, or a
   timeout expires.

The request and response protocol must prevent spoofed or cross-wired results
and must not be accepted from ordinary client connections. Cap concurrent
requests and bound memory, sockets, DNS work, and timeouts.

## Diagnostic handshake constraints

A plain TCP connect is not enough to verify a server link. However, starting
the normal PASS/SERVER negotiation can trigger duplicate-server, leaf/hub, and
registration side effects. A probe MUST NOT call do_server_estab(), register
a server, emit a network burst, alter existing uplinks, or change connect-block
configuration.

Prefer a dedicated, early, opt-in diagnostic handshake with a separate state
and explicit peer capability/version handling. Reuse existing authorization
checks only after auditing them for side effects. The mechanism must not
disclose plaintext passwords, password equality, or other credential material
to arbitrary clients. A challenge/response design must be reviewed for replay
and offline-guessing risks before implementation. A failure to prove credentials
must be reported as NOT VERIFIED, not PASS.

A successful preflight is not a guarantee that a subsequent real link will
complete; transient network conditions and topology-specific checks may differ.

## Compatibility

- A peer without support reports UNSUPPORTED; never fall back to a normal
  server registration attempt.
- Existing CONNECT, autoconnect, server negotiation, and server routing remain
  unchanged.
- No changes to production configuration are required.

## Implementation areas to investigate

- `src/s_serv.c:m_connect`: routing and privilege model (`hunt_server`,
  `OPCanGRoute`).
- `include/msg.h`: command definitions and command table.
- `src/s_bsd.c:connect_server`, `check_server_init`: socket lifecycle,
  outbound binding and inbound host/IP checks.
- `src/m_server.c:m_server_estab`, `do_server_estab`: authentication,
  duplicate-name and leaf/hub checks, and registration boundary.
- `include/struct.h:Conf_Connect`: source, host, port, flags, passwords.
- Event loop, timeout cleanup, TLS, DNS, and per-client state management
  still require a full audit.

## Acceptance tests

- Both directions pass using real configured ports and source addresses.
- One-way firewall rejection/timeout yields directional failure.
- Wrong/missing connect block and mismatched transport are differentiated.
- Authentication is reported accurately without exposing credentials.
- Existing linked server names and leaf/hub policy do not cause disruption.
- Peer lacking CHECKCONN support yields UNSUPPORTED.
- Operator permission checks and spoofed request/result rejection.
- Concurrent requests, disconnects, timeouts, DNS failures, and TLS failures.
- No server introductions, bursts, topology changes, or misleading link notices.

This document is intentionally a specification rather than an untested
partial implementation. The wire protocol and authentication design must be
reviewed before modifying the daemon's connection state machine.

Build validation: CI workflow is configured to run on pushes to feature/checkconn.

## Source audit: socket and registration boundaries

Inspected on the feature branch after the first successful C/C++ CI build:

- `src/s_bsd.c:accept_connection` accepts inbound sockets and delegates
  registration to `add_connection`.
- `src/s_bsd.c:read_packet` processes received data through the normal
  client input path; diagnostic sockets must not accidentally enter this
  parser as ordinary unknown clients.
- `src/s_bsd.c:completed_connection` handles outbound completion.
- `src/s_bsd.c:connect_server` is the normal outbound server-link entry
  point and MUST NOT be called by the preflight implementation as-is.
- `src/m_server.c:m_server_estab` performs password, duplicate-server,
  leaf/hub, and registration checks; `do_server_estab` is the forbidden
  side-effect boundary for diagnostic traffic.

Implementation gate: before enabling any network probe, define how an
inbound diagnostic session is distinguished *before* ordinary server
registration and how the outbound diagnostic socket is represented in the
existing event loop. Keep this opt-in on both peers; reject unsupported
peers without falling back to PASS/SERVER. Review authentication design
separately to avoid introducing a credential-testing oracle.

The existing CHECKCONN command is currently only a parser plus local
read-only connect-block inspection; it does not implement remote routing
or live connectivity checks. Do not represent its output as a successful
preflight.
