"""Exercise the shipped session middleware with synthetic sessions and ASGI requests."""
from __future__ import annotations

import ast
import asyncio
import copy
import hashlib
import hmac
import json
import time
import re
import secrets
import unittest
from http.cookies import CookieError, SimpleCookie
from pathlib import Path


def load_middleware():
    source = (Path(__file__).resolve().parents[1] / "assets/native-subsystem-template/app.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.ClassDef) and n.name == "ServerSideSessionMiddleware")
    namespace = dict(hashlib=hashlib, hmac=hmac, re=re, secrets=secrets,
                     SimpleCookie=SimpleCookie, CookieError=CookieError, json=json, time=time,
                     SESSION_SECRET="synthetic-session-test-secret-no-real-credential")
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<session-middleware>", "exec"), namespace)
    return namespace["ServerSideSessionMiddleware"]


class SessionCookieCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sessions = {}
        self.middleware = load_middleware()(self.application)
        self.middleware._load = lambda sid: copy.deepcopy(self.sessions.get(sid, {}))
        self.middleware._save = lambda sid, value: self.sessions.update({sid: copy.deepcopy(value)})
        self.middleware._delete = lambda sid: self.sessions.pop(sid, None)

    async def application(self, scope, receive, send):
        status = 200
        if scope["path"] == "/login":
            scope["session"].clear()
            scope["session"].update(sub="synthetic-current-user", pageKeys=["allowed"])
            scope["rotate_session"] = True
            status = 302
        elif scope["path"] == "/logout":
            scope["session"].clear()
        elif not scope["session"].get("sub"):
            status = 401
        await send(dict(type="http.response.start", status=status, headers=[]))
        await send(dict(type="http.response.body", body=b""))

    async def request(self, path, headers=()):
        messages = []
        async def send(message):
            messages.append(message)
        async def receive():
            return dict(type="http.request", body=b"")
        await self.middleware(dict(type="http", path=path, headers=list(headers)), receive, send)
        return messages[0]

    @staticmethod
    def cookies(response):
        return [value.decode() for name, value in response["headers"] if name == b"set-cookie"]

    async def test_same_site_webview_can_discard_none_partitioned_cookie(self):
        response = await self.request("/login")
        kept = [c.split(";", 1)[0] for c in self.cookies(response) if "SameSite=None" not in c]
        self.assertEqual(len(kept), 1)
        page = await self.request("/page", [(b"cookie", kept[0].encode())])
        self.assertEqual(page["status"], 200)

    async def test_original_partitioned_cookie_still_authenticates(self):
        response = await self.request("/login")
        original = next(c.split(";", 1)[0] for c in self.cookies(response) if "; Partitioned" in c)
        page = await self.request("/page", [(b"cookie", original.encode())])
        self.assertEqual(page["status"], 200)

    async def test_cookie_attributes_and_session_identity_are_preserved(self):
        cookies = self.cookies(await self.request("/login"))
        self.assertEqual(len(cookies), 2)
        self.assertEqual(cookies[0].split(";", 1)[0].split("=", 1)[1],
                         cookies[1].split(";", 1)[0].split("=", 1)[1])
        for cookie in cookies:
            self.assertIn("HttpOnly", cookie)
            self.assertIn("Secure", cookie)
            self.assertIn("Path=/", cookie)
            self.assertIn("Max-Age=28800", cookie)
            self.assertNotIn("Domain=", cookie)
            self.assertNotIn("synthetic-current-user", cookie)
        self.assertIn("SameSite=None; Partitioned", cookies[0])
        self.assertIn("SameSite=Lax", cookies[1])
        self.assertNotIn("Partitioned", cookies[1])

    async def test_stale_compatibility_cookie_does_not_mask_active_primary(self):
        stale = "S" * 43
        primary = "P" * 43
        self.sessions[primary] = dict(sub="synthetic-user")
        raw = ("zjsid_same_site=" + self.middleware._signed_value(stale) +
               "; zjsid=" + self.middleware._signed_value(primary))
        self.assertEqual((await self.request("/page", [(b"cookie", raw.encode())]))["status"], 200)

    async def test_forged_or_expired_compatibility_cookie_is_rejected(self):
        for value in ("unsigned", "F" * 43 + "." + "0" * 64,
                      self.middleware._signed_value("E" * 43)):
            response = await self.request("/page", [(b"cookie", ("zjsid_same_site=" + value).encode())])
            self.assertEqual(response["status"], 401)

    async def test_missing_cookie_still_requires_authentication(self):
        self.assertEqual((await self.request("/page"))["status"], 401)

    async def test_logout_revokes_session_without_erasing_newer_browser_cookies(self):
        cookies = self.cookies(await self.request("/login"))
        raw = "; ".join(c.split(";", 1)[0] for c in cookies)
        response = await self.request("/logout", [(b"cookie", raw.encode())])
        self.assertEqual(self.cookies(response), [])
        self.assertEqual(self.sessions, {})
        self.assertEqual((await self.request("/page", [(b"cookie", raw.encode())]))["status"], 401)

    async def test_sso_rotation_revokes_all_old_cookie_candidates(self):
        ids = ["A" * 43, "B" * 43]
        for sid in ids:
            self.sessions[sid] = dict(sub="synthetic-previous-user")
        raw = ("zjsid_same_site=" + self.middleware._signed_value(ids[0]) +
               "; zjsid=" + self.middleware._signed_value(ids[1]))
        response = await self.request("/login", [(b"cookie", raw.encode())])
        self.assertTrue(all(sid not in self.sessions for sid in ids))
        self.assertEqual(len(self.sessions), 1)
        self.assertEqual(next(iter(self.sessions.values()))["sub"], "synthetic-current-user")
        self.assertEqual(len(self.cookies(response)), 2)

    async def test_separate_cookie_fields_do_not_drop_session(self):
        sid = "H" * 43
        self.sessions[sid] = dict(sub="synthetic-user")
        headers = [(b"cookie", ("zjsid=" + self.middleware._signed_value(sid)).encode()),
                   (b"cookie", b"other=value")]
        self.assertEqual((await self.request("/page", headers))["status"], 200)


if __name__ == "__main__":
    unittest.main()

