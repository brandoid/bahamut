# CHECKCONN lab (Ubuntu 24.04 x86-64)

**Disposable test only.** No production servers, passwords, DNS names or ports.
The generator creates three independent loopback-only configurations. Review
them before launching. The prototype currently tests connect-block presence,
not TCP reachability or link authentication.

## Build

From a clean checkout of `feature/checkconn`:

```sh
sudo apt-get update
sudo apt-get install -y git build-essential autoconf automake libtool libssl-dev zlib1g-dev shtool
libtoolize --force
aclocal
autoheader
automake --force-missing --add-missing || true
autoreconf -vfi
./configure
make
python3 tests/lab/generate.py
```

Read `tests/lab/generated/lab-credentials.txt` locally. Never commit or
paste the generated credentials. All generated configuration files are
private to the local machine (mode 0600).

## Layout

| Server | IRC clients | Server links |
| --- | --- | --- |
| alpha.test.invalid | 16667 | 17325 |
| bravo.test.invalid | 16668 | 17326 |
| charlie.test.invalid | 16669 | 17327 |

Every listener and outbound bind is `127.0.0.1`. Configurations deliberately
set `maxlinks 0` to avoid automatic connection attempts. The three servers
must be linked manually, one link at a time, after checking that each daemon
started correctly. For initial topology use A-B and B-C, not a three-link
cycle. Do not run as root.

Bahamut's `INSTALL` file documents the `./ircd -f /absolute/path/ircd.conf`
option. The generated directories are intended to be independent working
directories; confirm pidfile/logfile paths and runtime file requirements
for the build before starting three daemons.

## Validation

Connect a test IRC client to Charlie on `127.0.0.1:16669`. Oper using the
generated lab credentials. After confirming all three servers appear in
`/LINKS`, run:

```
/CHECKCONN alpha.test.invalid bravo.test.invalid
/CHECKCONN alpha.test.invalid 17326 bravo.test.invalid
/CHECKCONN bravo.test.invalid alpha.test.invalid
```

Capture replies and server logs. The current implementation reports local
connect-block inspection only. It MUST report authentication and connectivity
as NOT VERIFIED. See `doc/CHECKCONN-testing.md` for the full test matrix.

**Do not connect these lab servers to DALnet or any other real IRC network.**
