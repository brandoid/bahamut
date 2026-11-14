# CHECKCONN isolated-network validation plan

This plan is for the current read-only prototype, not a production-ready link
preflight. **Do not deploy the branch to DALnet production servers.**

## Lab topology

Create three disposable Bahamut daemons A, B and C with distinct server
names, ports, data directories and test-only passwords. Link them in a
stable topology so that A and B are both visible from C. Use loopback or
an isolated virtual network. Do not reuse production connect blocks.

Run the operator client on C with the same global routing privilege that
permits remote CONNECT. Capture all server notices and logs. Record the
commit SHA, configuration and exact command/output for every test.

## Read-only prototype cases

| Case | Command / condition | Expected |
| --- | --- | --- |
| Two parameters | CHECKCONN A B | Each endpoint reports its outbound connect-block status for the other |
| Explicit port | CHECKCONN A 7325 B | Both endpoint reports use 7325 |
| Operator on endpoint | Connect operator to A, run CHECKCONN A B | No duplicate reverse request; both endpoints inspected |
| Reverse order | CHECKCONN B A | Both endpoint inspections still occur |
| Missing block | Remove B->A connect block in lab | B reports missing local block; no network link attempt |
| No global route privilege | Run as local-only oper | Rejected |
| Ordinary client | Run without oper | Rejected |
| Invalid port | 0, 65536, -1, 1x, very long digits | Rejected |
| Wildcard | CHECKCONN A* B | Rejected |
| Same endpoint | CHECKCONN A A | Rejected |
| Unknown endpoint | CHECKCONN A missing.example | Rejected |
| Split during request | Disconnect a lab server while routing | No daemon crash; no production-style link attempt |

Check that the network topology and existing links are unchanged before
and after each test. The current prototype must always say connectivity
and authentication are NOT VERIFIED.

## Gates before a live TCP preflight is enabled

1. Implement a bounded, correlated interserver request/result exchange with
   an unpredictable ID, authorization at origin, replay resistance and
   cancellation on splits/quits.
2. Define an explicit diagnostic handshake and capability negotiation. Never
   send normal PASS/SERVER registration on a test socket.
3. Review the password verification design for credential disclosure,
   offline guessing and replay. A TCP success alone must never be reported
   as authentication success.
4. Add nonblocking socket lifecycle, source bind, DNS/TLS handling, timeouts,
   limits and cleanup; run under sanitizers in a disposable test network.
5. Verify compatibility with unmodified Bahamut nodes and reject unsupported
   peers without attempting a real link.
6. Test concurrent requests and simulated firewall asymmetry.
7. Obtain maintainer review before considering a PR.

## Known limitation

The current CHECKCONN command sends two read-only inspection requests, not
a correlated transaction. Results may arrive in either order and do not have
a shared request ID. This is not a substitute for the final orchestration
protocol.
