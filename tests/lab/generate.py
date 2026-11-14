#!/usr/bin/env python3
"""Generate isolated, loopback-only Bahamut lab configurations.

Run from the repository root: python3 tests/lab/generate.py
The generated lab/ directory is intentionally gitignored.
"""
from pathlib import Path
import os
import secrets

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "lab" / "generated"
NODES = [
    ("alpha", "alpha.test.invalid", 16667, 17325),
    ("bravo", "bravo.test.invalid", 16668, 17326),
    ("charlie", "charlie.test.invalid", 16669, 17327),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    os.chmod(OUT, 0o700)
    passwords = {name: secrets.token_hex(24) for name, *_ in NODES}
    oper_password = secrets.token_hex(18)
    for name, server, client_port, link_port in NODES:
        directory = OUT / name
        directory.mkdir(exist_ok=True)
        os.chmod(directory, 0o700)
        links = []
        for other, other_server, _, other_port in NODES:
            if other == name:
                continue
            links.append(f"""connect {{
    name {other_server};
    host 127.0.0.1;
    port {other_port};
    bind 127.0.0.1;
    apasswd "{passwords[name]}";
    cpasswd "{passwords[other]}";
    flags H;
    class servers;
}};""")
        conf = f"""# Generated disposable CHECKCONN lab; DO NOT use on production.
global {{
    name {server};
    info "Isolated CHECKCONN lab";
}};
options {{
    network_name checkconn-lab;
    local_kline "lab@localhost";
    servtype hub;
    show_links;
    allow_split_ops;
}};
port {{ port {client_port}; bind 127.0.0.1; }};
port {{ port {link_port}; bind 127.0.0.1; }};
allow {{ host *@127.0.0.1; class users; }};
class {{ name users; maxusers 50; pingfreq 90; maxsendq 100000; }};
class {{ name opers; pingfreq 90; maxsendq 500000; }};
class {{ name servers; pingfreq 120; connfreq 300; maxsendq 1000000; maxlinks 0; }};
oper {{
    name laboper;
    passwd "{oper_password}";
    access OAaRD;
    host *@127.0.0.1;
    class opers;
}};
{chr(10).join(links)}
"""
        target = directory / "ircd.conf"
        target.write_text(conf)
        os.chmod(target, 0o600)
    secret_file = OUT / "lab-credentials.txt"
    secret_file.write_text("LAB OPER USER: laboper\nLAB OPER PASSWORD: " + oper_password + "\n")
    os.chmod(secret_file, 0o600)
    print("Generated configurations under:", OUT)
    print("Credentials saved to:", secret_file)
    print("No daemons were started. Review configs before launching.")

if __name__ == "__main__":
    main()
