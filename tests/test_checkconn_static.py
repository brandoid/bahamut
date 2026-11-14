#!/usr/bin/env python3
"""Static guardrails for the incomplete CHECKCONN command.

Run from repository root: python3 tests/test_checkconn_static.py
These are NOT functional or network tests.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CheckconnStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serv = (ROOT / "src/s_serv.c").read_text()
        cls.msg = (ROOT / "include/msg.h").read_text()
        match = re.search(r"\bint\s+m_checkconn\s*\([^)]*\)\s*\{", cls.serv)
        if not match:
            raise AssertionError("m_checkconn handler not found")
        start = match.end()
        depth = 1
        i = start
        while depth and i < len(cls.serv):
            if cls.serv[i] == "{":
                depth += 1
            elif cls.serv[i] == "}":
                depth -= 1
            i += 1
        cls.handler = cls.serv[start:i - 1]

    def test_command_registered(self):
        self.assertIn("#define MSG_CHECKCONN", self.msg)
        self.assertRegex(self.msg, r"\{MSG_CHECKCONN,\s*m_checkconn,")

    def test_permission_gate(self):
        self.assertIn("IsAnOper(sptr)", self.handler)
        self.assertNotIn("IsPrivileged(sptr)", self.handler)
        self.assertIn("OPCanGRoute(sptr)", self.handler)

    def test_no_real_link_registration(self):
        for forbidden in ("connect_server(", "do_server_estab(", "m_server_estab(",
                          "sendto_serv_butone("):
            self.assertNotIn(forbidden, self.handler, forbidden)

    def test_routes_only_via_existing_server_routing(self):
        self.assertIn("hunt_server(cptr, sptr", self.handler)
        self.assertIn("HUNTED_ISME", self.handler)

    def test_remote_routing_is_nonrecursive(self):
        self.assertIn("if (mycmp(me.name, server1))", self.handler)
        self.assertIn("if (hunted != HUNTED_ISME)", self.handler)
        self.assertIn("return 0;", self.handler)

    def test_exact_server_targets_only(self):
        self.assertIn('strpbrk(server1, "*?")', self.handler)
        self.assertIn('strpbrk(server2, "*?")', self.handler)

    def test_local_second_endpoint_not_dispatched_twice(self):
        self.assertIn("if (MyClient(sptr) && mycmp(me.name, server2))", self.handler)
        self.assertNotIn("reverse_conn", self.handler)

    def test_no_network_probe_or_secrets(self):
        for forbidden in ("socket(", "connect(", "PASS %s", "cpasswd",
                          "apasswd", "do_server_estab("):
            self.assertNotIn(forbidden, self.handler, forbidden)

    def test_does_not_claim_authentication_success(self):
        self.assertIn("NOT VERIFIED", self.handler)
        self.assertIn("no connections attempted", self.handler)


if __name__ == "__main__":
    unittest.main()
