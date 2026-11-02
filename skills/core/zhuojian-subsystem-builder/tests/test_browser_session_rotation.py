"""Exercise the actual template middleware across delayed ASGI responses."""
import ast
import asyncio
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import tempfile
import time
import unittest
from contextlib import contextmanager
from http.cookies import CookieError, SimpleCookie
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'assets/native-subsystem-template/app.py'


class BrowserSessionRotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'sessions.sqlite'

        @contextmanager
        def db():
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
                connection.commit()
            finally:
                connection.close()

        with db() as connection:
            connection.execute('CREATE TABLE browser_sessions(session_hash TEXT PRIMARY KEY,data TEXT NOT NULL,expires_at INTEGER NOT NULL)')
        namespace = {name: globals()[name] for name in ('hashlib', 'hmac', 'json', 're', 'secrets', 'sqlite3', 'time', 'CookieError', 'SimpleCookie')}
        namespace.update(db=db, SESSION_SECRET='isolated-test-session-key')
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ServerSideSessionMiddleware')
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
        self.middleware = namespace['ServerSideSessionMiddleware']

    def tearDown(self):
        self.temp.cleanup()

    def test_late_old_response_never_sets_cookie_or_resurrects_rotated_session(self):
        for mode in ('unchanged', 'changed', 'cleared'):
            with self.subTest(mode=mode):
                async def scenario():
                    started, finish = asyncio.Event(), asyncio.Event()
                    messages = []

                    async def app(scope, receive, send):
                        started.set()
                        await finish.wait()
                        if mode == 'changed':
                            scope['session']['displayName'] = 'late update'
                        elif mode == 'cleared':
                            scope['session'].clear()
                        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
                        await send({'type': 'http.response.body', 'body': b'ok'})

                    middleware = self.middleware(app)
                    old, new = secrets.token_urlsafe(36), secrets.token_urlsafe(36)
                    middleware._save(old, {'sub': 'employee', 'moduleKey': 'old'})
                    cookie = ('zjsid=' + middleware._signed_value(old)).encode()
                    scope = {'type': 'http', 'method': 'GET', 'path': '/slow', 'headers': [(b'cookie', cookie)]}

                    async def receive():
                        return {'type': 'http.request', 'body': b''}

                    async def send(message):
                        messages.append(message)

                    task = asyncio.create_task(middleware(scope, receive, send))
                    await started.wait()
                    middleware._delete(old)
                    middleware._save(new, {'sub': 'employee', 'moduleKey': 'new'})
                    finish.set()
                    await task
                    self.assertFalse(any(k.lower() == b'set-cookie' for msg in messages for k, _ in msg.get('headers', [])))
                    self.assertEqual(middleware._load(old), {})
                    self.assertEqual(middleware._load(new)['moduleKey'], 'new')

                asyncio.run(scenario())

    def test_fresh_session_keeps_opaque_partitioned_secure_cookie(self):
        async def scenario():
            messages = []

            async def app(scope, receive, send):
                scope['session'].update(sub='private-employee', moduleKey='new-module')
                scope['rotate_session'] = True
                await send({'type': 'http.response.start', 'status': 302, 'headers': []})

            middleware = self.middleware(app)

            async def send(message):
                messages.append(message)

            await middleware({'type': 'http', 'headers': []}, None, send)
            cookie = next(v.decode() for msg in messages for k, v in msg['headers'] if k == b'set-cookie')
            for flag in ('HttpOnly', 'Secure', 'SameSite=None', 'Partitioned'):
                self.assertIn(flag, cookie)
            self.assertNotIn('private-employee', cookie)
            self.assertNotIn('new-module', cookie)
            self.assertLess(len(cookie), 300)

        asyncio.run(scenario())


if __name__ == '__main__':
    unittest.main()
