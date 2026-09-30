from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    (PROJECT_ROOT / "subsystem.json").is_file(),
    "action integration tests run in a project produced by scaffold_subsystem.py",
)
class ActionRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import jwt
            from fastapi.testclient import TestClient
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("install requirements-dev.txt to run route tests") from exc

        cls.jwt = jwt
        cls.TestClient = TestClient
        cls.temporary = tempfile.TemporaryDirectory()
        temporary_root = Path(cls.temporary.name)
        cls.previous_environment = {
            key: os.environ.get(key)
            for key in (
                "ZHUOJIAN_MANIFEST_ACCESS_TOKEN",
                "ZHUOJIAN_SSO_EXCHANGE_TOKEN",
                "ZHUOJIAN_ACTION_SIGNING_SECRET",
                "ZHUOJIAN_EVENT_SIGNING_SECRET",
                "SESSION_SECRET",
                "ZHUOJIAN_ORGANIZATION_ID",
                "ZHUOJIAN_PUBLIC_ORIGIN",
                "ZHUOJIAN_SAAS_ORIGIN",
                "DATABASE_PATH",
                "FILE_STORAGE_DRIVER",
                "FILE_STORAGE_ROOT",
            )
        }
        cls.manifest_token = "zjmf_manifest-token-used-only-by-action-tests-123456789"
        cls.sso_token = "zjss_exchange-token-used-only-by-action-tests-123456789"
        cls.action_secret = "zjac_action-secret-used-only-by-action-tests-123456789"
        cls.event_secret = "zjev_event-secret-used-only-by-action-tests-123456789"
        cls.organization_id = "11111111-1111-4111-8111-111111111111"
        cls.department_id = "ops"
        cls.role_ids = ["ops-owner"]
        cls.effective_data_scope = {
            "unrestricted": False,
            "include_self": False,
            "own_only": False,
            "department_ids": [cls.department_id],
        }
        os.environ.update({
            "ZHUOJIAN_MANIFEST_ACCESS_TOKEN": cls.manifest_token,
            "ZHUOJIAN_SSO_EXCHANGE_TOKEN": cls.sso_token,
            "ZHUOJIAN_ACTION_SIGNING_SECRET": cls.action_secret,
            "ZHUOJIAN_EVENT_SIGNING_SECRET": cls.event_secret,
            "SESSION_SECRET": "session-secret-used-only-by-action-tests-123",
            "ZHUOJIAN_ORGANIZATION_ID": cls.organization_id,
            "ZHUOJIAN_PUBLIC_ORIGIN": "https://testserver",
            "ZHUOJIAN_SAAS_ORIGIN": "https://saas.test.example.com",
            "DATABASE_PATH": str(temporary_root / "subsystem.db"),
            "FILE_STORAGE_DRIVER": "local",
            "FILE_STORAGE_ROOT": str(temporary_root / "files"),
        })
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.modules.pop("app", None)
        cls.application = importlib.import_module("app")
        cls.real_validate_live_session = staticmethod(cls.application.validate_live_session)
        cls.client_context = TestClient(
            cls.application.app,
            base_url="https://testserver",
            headers={"Origin": "https://testserver"},
        )
        cls.client = cls.client_context.__enter__()

        module = next(iter(cls.application.MODULES.values()))
        cls.module_key = module["moduleKey"]
        page = module["pages"][0]
        cls.page_key = page["pageKey"]
        cls.actions = {
            action["operation"]: cls.application.ACTIONS[action["actionKey"]]
            for action in module["actions"]
        }
        action_keys = [action["actionKey"] for action in module["actions"]]
        now = datetime.now(timezone.utc)
        launch_nonce = "launch_nonce_used_by_action_tests"
        code = "zjsc_" + "a" * 48
        claims = {
            "iss": "zhuojian-saas",
            "typ": "zhuojian-sso-code",
            "aud": cls.application.APP_SLUG,
            "sub": "page-action-test-user",
            "organizationId": cls.organization_id,
            "departmentId": cls.department_id,
            "departmentIds": [cls.department_id],
            "roleIds": cls.role_ids,
            "effectiveDataScope": cls.effective_data_scope,
            "moduleKey": cls.module_key,
            "pageKeys": [cls.page_key],
            "actionKeys": action_keys,
            "pageAccess": {
                cls.page_key: {
                    "actionKeys": action_keys,
                    "permissions": [
                        "view", "ai_query", "ai_create", "ai_update",
                        "ai_delete", "ai_approve", "export",
                    ],
                    "dataScopes": {
                        permission: cls.effective_data_scope
                        for permission in [
                            "view", "ai_query", "ai_create", "ai_update",
                            "ai_delete", "ai_approve", "export",
                        ]
                    },
                    "actionDataScopes": {
                        action_key: cls.effective_data_scope for action_key in action_keys
                    },
                }
            },
            "jti": uuid4().hex,
            "launchNonce": launch_nonce,
            "sessionBindingHash": "a" * 64,
            "authEpoch": 0,
            "permissions": [
                "view", "ai_query", "ai_create", "ai_update",
                "ai_delete", "ai_approve", "export",
            ],
            "iat": now.isoformat(),
            "exp": (now + timedelta(seconds=120)).isoformat(),
        }
        exchange_response = mock.Mock(
            status_code=200,
            content=b"{}",
            headers={"content-type": "application/json"},
        )
        cls.sso_claims = claims
        cls.sso_exchange_payload = {
            "application_id": "22222222-2222-4222-8222-222222222222",
            "application_slug": cls.application.APP_SLUG,
            "organization_id": cls.organization_id,
            "module_key": cls.module_key,
            "redirect": page["routePattern"],
            "launch_nonce": launch_nonce,
            "claims": claims,
        }
        exchange_response.json.return_value = cls.sso_exchange_payload
        with mock.patch.object(cls.application.httpx, "post", return_value=exchange_response):
            response = cls.client.get(
                "/api/integration/sso",
                params={
                    "code": code,
                    "redirect": page["routePattern"],
                    "launch_nonce": launch_nonce,
                },
                headers={
                    "Referer": cls.application.SAAS_ORIGIN + "/terminal",
                    "Sec-Fetch-Dest": "iframe",
                },
                follow_redirects=False,
            )
        if response.status_code != 302:
            raise AssertionError(response.text)
        if response.headers.get("location") != page["routePattern"]:
            raise AssertionError("SSO code was not removed from the redirect URL")
        cls.sso_set_cookie = response.headers.get("set-cookie", "")
        cls.live_session_patcher = mock.patch.object(
            cls.application,
            "validate_live_session",
            side_effect=lambda session, module_key, page_key, action_key=None: (
                cls.application.action_scoped_actor(session, page_key, action_key)
                if action_key
                else {
                    **session,
                    "effectiveDataScope": session["pageAccess"][page_key]["dataScopes"]["view"],
                }
            ),
        )
        cls.live_session_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.live_session_patcher.stop()
        cls.client_context.__exit__(None, None, None)
        sys.modules.pop("app", None)
        if sys.path and sys.path[0] == str(PROJECT_ROOT):
            sys.path.pop(0)
        for key, value in cls.previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        cls.temporary.cleanup()

    def action_body(
        self,
        operation: str,
        request_id: str,
        params: dict,
        expected_version: int | None = None,
    ) -> dict:
        return {
            "requestId": request_id,
            "moduleKey": self.module_key,
            "pageKey": self.page_key,
            "operation": operation,
            "expectedVersion": expected_version,
            "params": params,
        }

    def action_token(
        self,
        operation: str,
        request_id: str,
        params: dict,
        *,
        confirmed_at: datetime | None = None,
        confirmation_id: str | None = None,
    ) -> str:
        action = self.actions[operation]
        now = int(time.time())
        claims = {
            "iss": "zhuojian-saas",
            "typ": "zhuojian-action",
            "aud": self.application.APP_SLUG,
            "sub": "integration-action-test-user",
            "organizationId": self.organization_id,
            "departmentId": self.department_id,
            "departmentIds": [self.department_id],
            "roleIds": self.role_ids,
            "effectiveDataScope": self.effective_data_scope,
            "moduleKey": self.module_key,
            "pageKey": self.page_key,
            "actionKey": action["actionKey"],
            "operation": operation,
            "requestId": request_id,
            "permissions": ["view", self.application.required_permission(operation)],
            "iat": now,
            "exp": now + 60,
        }
        if action.get("requiresConfirmation"):
            claims.update({
                "confirmed": True,
                "confirmationId": confirmation_id or str(uuid4()),
                "confirmedBy": claims["sub"],
                "confirmedAt": (confirmed_at or datetime.now(timezone.utc)).isoformat(),
                "paramsHash": self.application.canonical_hash(params),
            })
        return self.jwt.encode(claims, self.action_secret, algorithm="HS256")

    def event_body(self, *, event_type: str = "inventory.changed.v1") -> dict:
        return {
            "deliveryId": "delivery-" + uuid4().hex,
            "sourceApplicationSlug": "inventory-source",
            "event": {
                "eventId": "event-" + uuid4().hex,
                "eventType": event_type,
                "enterpriseKey": self.application.MANIFEST["enterprise"]["key"],
                "moduleKey": "inventory",
                "entityType": "stock_item",
                "entityId": "STOCK-001",
                "occurredAt": datetime.now(timezone.utc).isoformat(),
                "payload": {"available": 3},
            },
        }

    def event_token(self, body: dict, **overrides) -> str:
        now = int(time.time())
        event = body["event"]
        claims = {
            "iss": "zhuojian-saas",
            "typ": "zhuojian-event",
            "aud": self.application.APP_SLUG,
            "organizationId": self.organization_id,
            "deliveryId": body["deliveryId"],
            "eventId": event["eventId"],
            "eventType": event["eventType"],
            "targetModuleKey": self.module_key,
            "iat": now,
            "exp": now + 60,
            **overrides,
        }
        return self.jwt.encode(claims, self.event_secret, algorithm="HS256")

    def post_event(self, body: dict, *, token: str | None = None):
        return self.client.post(
            "/api/integration/event-deliveries",
            headers={"Authorization": f"Bearer {token or self.event_token(body)}"},
            json=body,
        )

    def post_integration(
        self,
        operation: str,
        body: dict,
        *,
        token: str | None = None,
    ):
        request_id = body.get("requestId")
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        token = token or self.action_token(operation, request_id, params)
        return self.client.post(
            f"/api/integration/actions/{self.actions[operation]['actionKey']}",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )

    def test_manifest_and_event_polling_accept_only_the_manifest_token(self):
        for path in ("/api/integration/manifest", "/api/integration/events"):
            accepted = self.client.get(
                path,
                headers={"Authorization": f"Bearer {self.manifest_token}"},
            )
            rejected = self.client.get(
                path,
                headers={"Authorization": f"Bearer {self.action_secret}"},
            )
            self.assertEqual(accepted.status_code, 200, accepted.text)
            self.assertEqual(rejected.status_code, 401, rejected.text)

    def test_export_returns_one_frozen_opaque_dataset_without_creating_files(self):
        batch = "export-" + uuid4().hex
        for index in range(3):
            request_id = uuid4().hex
            created = self.post_integration(
                "create",
                self.action_body(
                    "create",
                    request_id,
                    {
                        "id": uuid4().hex,
                        "data": {"name": f"记录 {index}", "batch": batch},
                    },
                ),
            )
            self.assertEqual(created.status_code, 200, created.text)

        storage_root = Path(os.environ["FILE_STORAGE_ROOT"])
        before_files = sorted(
            str(path.relative_to(storage_root))
            for path in storage_root.rglob("*")
            if path.is_file()
        ) if storage_root.exists() else []
        first_id = uuid4().hex
        first = self.post_integration(
            "export",
            self.action_body(
                "export",
                first_id,
                {"filters": {"batch": batch}, "limit": 2},
            ),
        )
        self.assertEqual(first.status_code, 200, first.text)
        first_page = first.json()
        self.assertEqual(first_page["rowCount"], 3)
        self.assertEqual(len(first_page["rows"]), 2)
        self.assertTrue(first_page["snapshotId"])
        self.assertTrue(first_page["nextCursor"])
        self.assertNotIn("/", first_page["nextCursor"])

        second_params = {
            "filters": {"batch": batch},
            "limit": 2,
            "snapshotId": first_page["snapshotId"],
            "nextCursor": first_page["nextCursor"],
        }
        second_id = uuid4().hex
        second = self.post_integration(
            "export",
            self.action_body("export", second_id, second_params),
        )
        self.assertEqual(second.status_code, 200, second.text)
        second_page = second.json()
        self.assertEqual(second_page["snapshotId"], first_page["snapshotId"])
        self.assertEqual(second_page["snapshotAt"], first_page["snapshotAt"])
        self.assertEqual(len(second_page["rows"]), 1)
        self.assertIsNone(second_page["nextCursor"])
        self.assertEqual(
            {row["name"] for row in [*first_page["rows"], *second_page["rows"]]},
            {"记录 0", "记录 1", "记录 2"},
        )
        after_files = sorted(
            str(path.relative_to(storage_root))
            for path in storage_root.rglob("*")
            if path.is_file()
        ) if storage_root.exists() else []
        self.assertEqual(after_files, before_files)

    def test_sso_exchange_uses_fixed_url_and_dedicated_bearer(self):
        payload = json.loads(json.dumps(self.sso_exchange_payload))
        nonce = "different_launch_nonce_for_binding_test"
        payload["launch_nonce"] = "attacker_nonce_that_must_not_be_accepted"
        response_from_saas = mock.Mock(
            status_code=200,
            content=b"{}",
            headers={"content-type": "application/json"},
        )
        response_from_saas.json.return_value = payload

        with mock.patch.object(
            self.application.httpx, "post", return_value=response_from_saas
        ) as post:
            response = self.client.get(
                "/api/integration/sso",
                params={
                    "code": "zjsc_" + "c" * 48,
                    "redirect": payload["redirect"],
                    "launch_nonce": nonce,
                },
                headers={
                    "Referer": self.application.SAAS_ORIGIN + "/terminal",
                    "Sec-Fetch-Dest": "iframe",
                },
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(post.call_args.args[0], self.application.SSO_EXCHANGE_URL)
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"],
            f"Bearer {self.sso_token}",
        )
        self.assertEqual(post.call_args.kwargs["json"]["launch_nonce"], nonce)
        self.assertFalse(post.call_args.kwargs["follow_redirects"])
        self.assertFalse(post.call_args.kwargs["trust_env"])

    def test_sso_uses_small_partitioned_server_side_cookie_and_requires_saas_navigation(self):
        self.assertIn("SameSite=None", self.sso_set_cookie)
        self.assertIn("Partitioned", self.sso_set_cookie)
        self.assertIn("HttpOnly", self.sso_set_cookie)
        self.assertLess(len(self.sso_set_cookie), 1024)
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            stored = connection.execute("SELECT data FROM browser_sessions").fetchone()
        self.assertIsNotNone(stored)
        self.assertIn("pageAccess", json.loads(stored[0]))

        response = self.client.get(
            "/api/integration/sso",
            params={
                "code": "zjsc_" + "n" * 48,
                "redirect": self.sso_exchange_payload["redirect"],
                "launch_nonce": self.sso_exchange_payload["launch_nonce"],
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_sso_exchange_rejects_claims_over_120_seconds(self):
        payload = json.loads(json.dumps(self.sso_exchange_payload))
        now = datetime.now(timezone.utc)
        payload["claims"]["iat"] = now.isoformat()
        payload["claims"]["exp"] = (now + timedelta(seconds=121)).isoformat()
        response_from_saas = mock.Mock(
            status_code=200,
            content=b"{}",
            headers={"content-type": "application/json"},
        )
        response_from_saas.json.return_value = payload
        with mock.patch.object(
            self.application.httpx, "post", return_value=response_from_saas
        ):
            response = self.client.get(
                "/api/integration/sso",
                params={
                    "code": "zjsc_" + "d" * 48,
                    "redirect": payload["redirect"],
                    "launch_nonce": payload["launch_nonce"],
                },
                headers={
                    "Referer": self.application.SAAS_ORIGIN + "/terminal",
                    "Sec-Fetch-Dest": "iframe",
                },
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 401, response.text)

    def test_request_id_schema_and_payload_binding_are_enforced(self):
        bad_body = self.action_body(
            "create", "bad/id", {"id": uuid4().hex, "data": {}}
        )
        bad = self.post_integration("create", bad_body)
        self.assertEqual(bad.status_code, 422, bad.text)

        request_id = uuid4().hex
        record_id = uuid4().hex
        body = self.action_body(
            "create", request_id, {"id": record_id, "data": {"name": "first"}}
        )
        created = self.post_integration("create", body)
        self.assertEqual(created.status_code, 200, created.text)

        changed = self.action_body(
            "create", request_id, {"id": record_id, "data": {"name": "changed"}}
        )
        rebound = self.post_integration("create", changed)
        self.assertEqual(rebound.status_code, 409, rebound.text)

    def test_ai_disabled_action_is_enforced_by_the_module(self):
        action = self.actions["query"]
        previous = action.get("aiEnabled")
        action["aiEnabled"] = False
        try:
            body = self.action_body("query", uuid4().hex, {})
            response = self.post_integration("query", body)
        finally:
            action["aiEnabled"] = previous

        self.assertEqual(response.status_code, 404, response.text)

    def test_role_scope_and_dynamic_action_parameter_shapes_are_enforced(self):
        denied = self.post_integration(
            "create",
            self.action_body(
                "create",
                uuid4().hex,
                {"data": {"name": "outside", "departmentId": "finance"}},
            ),
        )
        self.assertEqual(denied.status_code, 403, denied.text)

        record_id = uuid4().hex
        created = self.post_integration(
            "create",
            self.action_body(
                "create",
                uuid4().hex,
                {"id": record_id, "data": {"name": "inside"}},
            ),
        )
        self.assertEqual(created.status_code, 200, created.text)

        changed = self.post_integration(
            "update",
            self.action_body(
                "update",
                uuid4().hex,
                {"id": record_id, "changes": {"name": "updated"}},
                expected_version=1,
            ),
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["version"], 2)

        malformed = self.post_integration(
            "update",
            self.action_body(
                "update",
                uuid4().hex,
                {"id": record_id, "name": "flat-shape-is-not-v2.4"},
                expected_version=2,
            ),
        )
        self.assertEqual(malformed.status_code, 422, malformed.text)

        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            row = connection.execute(
                "SELECT data,department_id,created_by,version FROM records WHERE id=?",
                (record_id,),
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(json.loads(row[0])["name"], "updated")
        self.assertEqual(row[1], self.department_id)
        self.assertEqual(row[2], "integration-action-test-user")
        self.assertEqual(row[3], 2)

    def test_page_action_uses_its_own_scope_not_the_broader_view_scope(self):
        session = json.loads(json.dumps(self.sso_claims))
        session["effectiveDataScope"] = {
            "unrestricted": True,
            "include_self": False,
            "own_only": False,
            "department_ids": [],
        }
        delete_key = self.actions["delete"]["actionKey"]
        session["pageAccess"][self.page_key]["actionDataScopes"][delete_key] = {
            "unrestricted": False,
            "include_self": True,
            "own_only": True,
            "department_ids": [],
        }

        actor = self.application.action_scoped_actor(session, self.page_key, delete_key)
        with self.assertRaises(self.application.HTTPException) as raised:
            self.application.require_record_scope(actor, "finance", "another-user")
        self.assertEqual(raised.exception.status_code, 403)

    def directory_actor(self):
        return {**self.sso_claims, "sub": "33333333-3333-4333-8333-333333333333",
                "applicationId": self.sso_exchange_payload["application_id"]}

    def directory_response(self, *, resolve=False):
        payload = {
            "organization_id": self.organization_id,
            "application_id": self.sso_exchange_payload["application_id"],
            "module_key": self.module_key, "page_key": self.page_key,
            "action_key": self.actions["create"]["actionKey"],
            "employees": [{"user_id": "44444444-4444-4444-8444-444444444444",
                           "username": "member", "display_name": None}],
        }
        if not resolve:
            payload.update(has_more=False, next_offset=None)
        return payload

    def call_directory(self, payload, *, status=200, actor=None, **parameters):
        response = mock.Mock(status_code=status, content=b"{}", headers={"content-type": "application/json"})
        response.json.return_value = payload
        action = self.actions["create"]
        with mock.patch.dict(action, {"employeeDirectory": True}), mock.patch.object(
            self.application.httpx, "post", return_value=response,
        ) as transport:
            result = self.application.platform_employee_directory(
                actor if actor is not None else self.directory_actor(),
                self.module_key, self.page_key, action["actionKey"], **parameters,
            )
        return result, transport

    def test_directory_search_and_resolve_use_trusted_context_and_fixed_transport(self):
        payload = self.directory_response()
        result, transport = self.call_directory(payload, query="member", offset=0, limit=20)
        self.assertEqual(result, payload)
        request = transport.call_args
        self.assertEqual(request.args, (self.application.SAAS_ORIGIN + "/api/v1/subsystem-sso/employees/search",))
        self.assertEqual(request.kwargs["headers"]["Authorization"], "Bearer " + self.sso_token)
        self.assertFalse(request.kwargs["follow_redirects"])
        self.assertFalse(request.kwargs["trust_env"])
        self.assertEqual(request.kwargs["json"], {
            "user_id": self.directory_actor()["sub"], "auth_epoch": 0,
            "module_key": self.module_key, "page_key": self.page_key,
            "action_key": self.actions["create"]["actionKey"], "query": "member", "offset": 0, "limit": 20,
        })
        employee_id = payload["employees"][0]["user_id"]
        resolved, transport = self.call_directory(self.directory_response(resolve=True), user_ids=[employee_id])
        self.assertEqual(resolved["employees"][0]["user_id"], employee_id)
        self.assertTrue(transport.call_args.args[0].endswith("/resolve"))
        self.assertEqual(transport.call_args.kwargs["json"]["user_ids"], [employee_id])

    def test_directory_ui_search_uses_its_own_sso_session_and_rechecks_revocation(self):
        from fastapi.testclient import TestClient

        payload = json.loads(json.dumps(self.sso_exchange_payload))
        payload["claims"]["sub"] = self.directory_actor()["sub"]
        response = mock.Mock(status_code=200, content=b"{}", headers={"content-type": "application/json"})
        action = self.actions["create"]
        with TestClient(self.application.app, base_url="https://testserver", headers={"Origin": "https://testserver"}) as client:
            response.json.return_value = payload
            with mock.patch.object(self.application.httpx, "post", return_value=response):
                opened = client.get("/api/integration/sso", params={
                    "code": "zjsc_" + "e" * 48, "redirect": payload["redirect"], "launch_nonce": payload["launch_nonce"],
                }, headers={"Referer": self.application.SAAS_ORIGIN + "/terminal", "Sec-Fetch-Dest": "iframe"}, follow_redirects=False)
            self.assertEqual(opened.status_code, 302, opened.text)
            response.json.return_value = self.directory_response()
            with mock.patch.dict(action, {"employeeDirectory": True}), mock.patch.object(
                self.application.httpx, "post", return_value=response,
            ) as transport:
                body = {"moduleKey": self.module_key, "pageKey": self.page_key, "actionKey": action["actionKey"]}
                found = client.post("/api/ui/employees/search", json=body)
                self.assertEqual(found.status_code, 200, found.text)
                self.assertEqual(transport.call_args.kwargs["json"]["user_id"], payload["claims"]["sub"])
                response.status_code = 403
                denied = client.post("/api/ui/employees/search", json=body)
                self.assertEqual(denied.status_code, 403, denied.text)

    def test_directory_rejects_unbound_identity_invalid_parameters_and_disabled_action(self):
        actor = self.directory_actor()
        for field in ("applicationId", "authEpoch", "sub"):
            missing = {key: value for key, value in actor.items() if key != field}
            with self.subTest(field=field), self.assertRaises(self.application.HTTPException) as caught:
                self.call_directory({}, actor=missing)
            self.assertEqual(caught.exception.status_code, 401)
        for parameters in ({"user_ids": []}, {"user_ids": ["not-a-uuid"]},
                           {"user_ids": [actor["sub"], actor["sub"]]}, {"limit": True},
                           {"limit": 51}, {"offset": -1}, {"query": "x" * 101}):
            with self.subTest(parameters=parameters), self.assertRaises(self.application.HTTPException) as caught:
                self.call_directory({}, **parameters)
            self.assertEqual(caught.exception.status_code, 422)
        with mock.patch.object(self.application.httpx, "post") as transport:
            with self.assertRaises(self.application.HTTPException) as caught:
                self.application.platform_employee_directory(
                    actor, self.module_key, self.page_key, self.actions["create"]["actionKey"],
                )
            self.assertEqual(caught.exception.status_code, 403)
            transport.assert_not_called()
        response = self.client.post("/api/ui/employees/search", json={
            "moduleKey": self.module_key, "pageKey": self.page_key,
            "actionKey": self.actions["create"]["actionKey"], "user_id": actor["sub"],
        })
        self.assertEqual(response.status_code, 422)

    def test_directory_rejects_cross_context_partial_duplicate_and_extra_resolutions(self):
        original = self.directory_response(resolve=True)
        employee_id = original["employees"][0]["user_id"]
        cases = []
        for field in ("organization_id", "application_id", "module_key", "page_key", "action_key"):
            cases.append({**original, field: "another-context"})
        cases.extend([
            {**original, "employees": []},
            {**original, "employees": original["employees"] * 2},
            {**original, "employees": [*original["employees"], {
                "user_id": self.directory_actor()["sub"], "username": "extra", "display_name": "same name",
            }]},
            {**original, "employees": [{**original["employees"][0], "user_id": "legacy-name"}]},
        ])
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(self.application.HTTPException) as caught:
                self.call_directory(payload, user_ids=[employee_id])
            self.assertEqual(caught.exception.status_code, 503)
        for status in (401, 403, 404, 429, 500, 302):
            with self.subTest(status=status), self.assertRaises(self.application.HTTPException) as caught:
                self.call_directory(original, status=status, user_ids=[employee_id])
            self.assertEqual(caught.exception.status_code, status if status in {401, 403, 404} else 503)

    def test_optional_name_never_changes_created_by_or_sso_identity(self):
        for display_name in (None, "", "same name"):
            payload = json.loads(json.dumps(self.sso_exchange_payload))
            payload["claims"]["displayName"] = display_name
            actor = self.application.validate_sso_exchange(
                payload, payload["redirect"], payload["launch_nonce"],
            )
            self.assertEqual(actor["sub"], self.sso_claims["sub"])
            self.assertEqual(actor["applicationId"], payload["application_id"])
            self.assertEqual(actor["displayName"], display_name or None)
        record_id = uuid4().hex
        response = self.client.post(
            "/api/ui/actions/" + self.actions["create"]["actionKey"],
            json=self.action_body("create", uuid4().hex, {"id": record_id, "data": {
                "name": "", "userId": "forged-user", "displayName": "someone else",
            }}),
        )
        self.assertEqual(response.status_code, 200, response.text)
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            owner = connection.execute("SELECT created_by FROM records WHERE id=?", (record_id,)).fetchone()[0]
        self.assertEqual(owner, self.sso_claims["sub"])

    @contextmanager
    def identity_client(self, *, display_name=None, authenticated=True):
        """Use real SSO/session handling; only the remote SaaS transport is simulated."""
        with self.TestClient(
            self.application.app, base_url="https://testserver",
            headers={"Origin": "https://testserver"},
        ) as client:
            claims = json.loads(json.dumps(self.sso_claims))
            claims.update({
                "sub": str(uuid4()), "jti": uuid4().hex,
                "launchNonce": uuid4().hex, "displayName": display_name,
                "iat": datetime.now(timezone.utc).isoformat(),
                "exp": (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat(),
            })
            own_scope = {
                "unrestricted": False, "include_self": True,
                "own_only": True, "department_ids": [],
            }
            claims["effectiveDataScope"] = own_scope
            access = claims["pageAccess"][self.page_key]
            access["dataScopes"] = {key: own_scope for key in access["dataScopes"]}
            access["actionDataScopes"] = {key: own_scope for key in access["actionDataScopes"]}
            if authenticated:
                payload = {
                    **self.sso_exchange_payload, "claims": claims,
                    "launch_nonce": claims["launchNonce"],
                }
                remote = mock.Mock(status_code=200, content=b"{}", headers={
                    "content-type": "application/json",
                })
                remote.json.return_value = payload
                with mock.patch.object(self.application.httpx, "post", return_value=remote):
                    response = client.get("/api/integration/sso", params={
                        "code": "zjsc_" + uuid4().hex + uuid4().hex,
                        "redirect": payload["redirect"],
                        "launch_nonce": payload["launch_nonce"],
                    }, headers={
                        "Referer": self.application.SAAS_ORIGIN + "/terminal",
                        "Sec-Fetch-Dest": "iframe",
                    }, follow_redirects=False)
                self.assertEqual(response.status_code, 302, response.text)
                self.assertTrue(client.cookies.get("zjsid"))
            with mock.patch.object(
                self.application, "validate_live_session", self.real_validate_live_session,
            ):
                yield client, claims

    def identity_business_requests(self, *, include_directory=False):
        context = {"moduleKey": self.module_key, "pageKey": self.page_key}
        requests = [
            ("GET", "/api/ui/bootstrap", {"params": context}),
            ("POST", "/api/ui/actions/" + self.actions["query"]["actionKey"], {
                "json": self.action_body("query", uuid4().hex, {}),
            }),
            ("POST", "/api/ui/actions/" + self.actions["create"]["actionKey"], {
                "json": self.action_body("create", uuid4().hex, {"data": {"name": "test"}}),
            }),
            ("POST", "/api/ui/confirmations", {"json": {
                **self.action_body("delete", uuid4().hex, {"id": "test-record"}, 1),
                "actionKey": self.actions["delete"]["actionKey"], "confirmed": True,
            }}),
            ("GET", "/api/ui/files", {"params": {
                **context, "actionKey": self.actions["query"]["actionKey"],
            }}),
            ("POST", "/api/ui/files", {
                "params": {**context, "actionKey": self.actions["create"]["actionKey"],
                           "filename": "identity-test.txt"},
                "content": b"must not be stored",
            }),
        ]
        if include_directory:
            requests.append(("POST", "/api/ui/employees/search", {"json": {
                **context, "actionKey": self.actions["create"]["actionKey"], "query": "test",
            }}))
        return requests

    def identity_database_state(self):
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            return {
                table: connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                for table in (
                    "records", "request_results", "outbox", "page_confirmations", "stored_files",
                )
            }

    @staticmethod
    def forged_identity_headers():
        return {
            "Authorization": "Basic dGVzdDp0ZXN0",
            "X-User-Id": "forged-owner", "X-Forwarded-User": "forged-owner",
            "X-Display-Name": "forged name",
        }

    def test_identity_http_missing_sso_rejects_basic_and_forged_headers(self):
        before = self.identity_database_state()
        forged = self.forged_identity_headers()
        header_cases = (
            {}, {"Authorization": forged["Authorization"]},
            {key: value for key, value in forged.items() if key != "Authorization"}, forged,
        )
        with self.identity_client(authenticated=False) as (client, _):
            with mock.patch.object(self.application.httpx, "post") as remote:
                for headers in header_cases:
                    for method, path, kwargs in self.identity_business_requests(include_directory=True):
                        with self.subTest(method=method, path=path, headers=tuple(headers)):
                            response = client.request(method, path, headers=headers, **kwargs)
                            self.assertEqual(response.status_code, 401, response.text)
                remote.assert_not_called()
        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_expired_session_cannot_fall_back_to_headers(self):
        before = self.identity_database_state()
        with self.identity_client() as (client, _):
            cookie = client.cookies.get("zjsid")
            middleware = self.application.ServerSideSessionMiddleware
            session_id = middleware._verified_id(cookie)
            with sqlite3.connect(os.environ["DATABASE_PATH"]) as connection:
                changed = connection.execute(
                    "UPDATE browser_sessions SET expires_at=? WHERE session_hash=?",
                    (int(time.time()) - 1, middleware._digest(session_id)),
                )
                self.assertEqual(changed.rowcount, 1)
            with mock.patch.object(self.application.httpx, "post") as remote:
                for method, path, kwargs in self.identity_business_requests(include_directory=True):
                    with self.subTest(method=method, path=path):
                        response = client.request(method, path, headers={
                            **self.forged_identity_headers(), "Cookie": "zjsid=" + cookie,
                        }, **kwargs)
                        self.assertEqual(response.status_code, 401, response.text)
                remote.assert_not_called()
        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_revoked_session_clears_cookie_and_rejects_reuse(self):
        before = self.identity_database_state()
        for status in (401, 403):
            for method, path, kwargs in self.identity_business_requests():
                with self.subTest(status=status, method=method, path=path):
                    with self.identity_client() as (client, claims):
                        cookie = client.cookies.get("zjsid")
                        remote_response = mock.Mock(status_code=status, content=b"{}")
                        with mock.patch.object(
                            self.application.httpx, "post", return_value=remote_response,
                        ) as remote:
                            response = client.request(
                                method, path, headers=self.forged_identity_headers(), **kwargs,
                            )
                            self.assertEqual(response.status_code, status, response.text)
                            self.assertIn("Max-Age=0", response.headers.get("set-cookie", ""))
                            remote.assert_called_once()
                            self.assertEqual(remote.call_args.args, (self.application.SSO_SESSION_CHECK_URL,))
                            self.assertEqual(remote.call_args.kwargs["json"]["user_id"], claims["sub"])
                            retried = client.request(method, path, headers={
                                **self.forged_identity_headers(), "Cookie": "zjsid=" + cookie,
                            }, **kwargs)
                            self.assertEqual(retried.status_code, 401, retried.text)
                            remote.assert_called_once()
        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_authorization_failure_is_closed_and_retryable(self):
        before = self.identity_database_state()
        for failure in ("timeout", "server-error", "invalid-epoch", "invalid-json"):
            for method, path, kwargs in self.identity_business_requests():
                with self.subTest(failure=failure, method=method, path=path):
                    with self.identity_client() as (client, claims):
                        remote_response = mock.Mock(status_code=200, content=b"{}")
                        remote_response.json.return_value = {
                            "valid": True, "auth_epoch": 1,
                            "effective_data_scope": claims["effectiveDataScope"],
                        }
                        options = {"return_value": remote_response}
                        if failure == "timeout":
                            options = {"side_effect": self.application.httpx.TimeoutException("test timeout")}
                        elif failure == "server-error":
                            remote_response.status_code = 500
                        elif failure == "invalid-json":
                            remote_response.json.side_effect = ValueError("test invalid JSON")
                        with mock.patch.object(self.application.httpx, "post", **options) as remote:
                            response = client.request(
                                method, path, headers=self.forged_identity_headers(), **kwargs,
                            )
                            self.assertEqual(response.status_code, 503, response.text)
                            remote.assert_called_once()
                        recovered = mock.Mock(status_code=200, content=b"{}")
                        recovered.json.return_value = {
                            "valid": True, "auth_epoch": 0,
                            "effective_data_scope": claims["effectiveDataScope"],
                        }
                        with mock.patch.object(self.application.httpx, "post", return_value=recovered):
                            response = client.get("/api/ui/bootstrap", params={
                                "moduleKey": self.module_key, "pageKey": self.page_key,
                            })
                            self.assertEqual(response.status_code, 200, response.text)
                            self.assertEqual(response.json()["actor"]["userId"], claims["sub"])
        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_nameless_employee_writes_reads_and_keeps_trusted_owner(self):
        for display_name in (None, "", "same name"):
            with self.subTest(display_name=display_name), self.identity_client(
                display_name=display_name,
            ) as (client, claims):
                remote = mock.Mock(status_code=200, content=b"{}")
                remote.json.return_value = {
                    "valid": True, "auth_epoch": 0, "display_name": display_name,
                    "effective_data_scope": claims["effectiveDataScope"],
                }
                record_id = uuid4().hex
                forged_data = {
                    "name": "", "created_by": "forged-owner", "userId": "forged-owner",
                    "displayName": "forged name", "note": "first",
                }
                with mock.patch.object(self.application.httpx, "post", return_value=remote) as transport:
                    bootstrap = client.get("/api/ui/bootstrap", params={
                        "moduleKey": self.module_key, "pageKey": self.page_key,
                    }, headers=self.forged_identity_headers())
                    self.assertEqual(bootstrap.status_code, 200, bootstrap.text)
                    self.assertEqual(bootstrap.json()["actor"], {
                        "userId": claims["sub"], "displayName": display_name or None,
                    })
                    for operation, params, version in (
                        ("create", {"id": record_id, "data": forged_data}, None),
                        ("update", {"id": record_id, "changes": {**forged_data, "note": "updated"}}, 1),
                    ):
                        response = client.post("/api/ui/actions/" + self.actions[operation]["actionKey"],
                            headers=self.forged_identity_headers(),
                            json=self.action_body(operation, uuid4().hex, params, version))
                        self.assertEqual(response.status_code, 200, response.text)
                    response = client.post("/api/ui/actions/" + self.actions["query"]["actionKey"],
                        json=self.action_body("query", uuid4().hex, {}))
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual([(item["id"], item["note"]) for item in response.json()["items"]],
                                     [(record_id, "updated")])
                    for call in transport.call_args_list:
                        self.assertEqual(call.args, (self.application.SSO_SESSION_CHECK_URL,))
                        self.assertEqual(call.kwargs["json"]["user_id"], claims["sub"])
                        self.assertFalse(call.kwargs["trust_env"])
                with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
                    owner, version = connection.execute(
                        "SELECT created_by,version FROM records WHERE id=?", (record_id,),
                    ).fetchone()
                self.assertEqual((owner, version), (claims["sub"], 2))
                # A same-name employee cannot take ownership through JSON or headers.
                with self.identity_client(display_name=display_name) as (other_client, other_claims):
                    remote.json.return_value["effective_data_scope"] = other_claims["effectiveDataScope"]
                    with mock.patch.object(self.application.httpx, "post", return_value=remote):
                        response = other_client.post(
                            "/api/ui/actions/" + self.actions["query"]["actionKey"],
                            json=self.action_body("query", uuid4().hex, {}))
                        self.assertEqual(response.status_code, 200, response.text)
                        self.assertEqual(response.json()["items"], [])
                        before = self.identity_database_state()
                        response = other_client.post(
                            "/api/ui/actions/" + self.actions["update"]["actionKey"],
                            headers={"X-User-Id": claims["sub"]},
                            json=self.action_body("update", uuid4().hex, {
                                "id": record_id, "changes": {"created_by": other_claims["sub"]},
                            }, 2))
                        self.assertEqual(response.status_code, 403, response.text)
                        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_action_rejects_bad_credentials_despite_valid_browser_session(self):
        before = self.identity_database_state()
        body = self.action_body("create", uuid4().hex, {"data": {"name": "test"}})
        token = self.action_token("create", body["requestId"], body["params"])
        claims = self.jwt.decode(token, self.action_secret, algorithms=["HS256"],
                                 audience=self.application.APP_SLUG)
        expired = {**claims, "iat": int(time.time()) - 120, "exp": int(time.time()) - 60}
        credentials = [
            self.forged_identity_headers(),
            {"Authorization": "Bearer " + self.jwt.encode(expired, self.action_secret, algorithm="HS256")},
            {"Authorization": "Bearer " + self.jwt.encode(claims, "wrong-test-key-" * 4, algorithm="HS256")},
        ]
        with mock.patch.object(self.application.httpx, "post") as remote:
            for headers in credentials:
                with self.subTest(credential=headers["Authorization"].split()[0]):
                    response = self.client.post(
                        "/api/integration/actions/" + self.actions["create"]["actionKey"],
                        headers=headers, json=body,
                    )
                    self.assertEqual(response.status_code, 401, response.text)
            remote.assert_not_called()
        self.assertEqual(self.identity_database_state(), before)

    def test_identity_http_signed_action_owns_records_without_browser_or_display_name(self):
        owner = str(uuid4())
        record_id = uuid4().hex

        def invoke(client, operation, params, *, actor=owner, version=None):
            body = self.action_body(operation, uuid4().hex, params, version)
            original = self.action_token(operation, body["requestId"], params)
            claims = self.jwt.decode(original, self.action_secret, algorithms=["HS256"],
                                     audience=self.application.APP_SLUG)
            claims.update({
                "sub": actor,
                "effectiveDataScope": {
                    "unrestricted": False, "include_self": True,
                    "own_only": True, "department_ids": [],
                },
            })
            self.assertNotIn("displayName", claims)
            return client.post("/api/integration/actions/" + self.actions[operation]["actionKey"],
                headers={**self.forged_identity_headers(), "Authorization": "Bearer " +
                         self.jwt.encode(claims, self.action_secret, algorithm="HS256")},
                json=body)

        with self.identity_client(authenticated=False) as (client, _):
            response = invoke(client, "create", {"id": record_id, "data": {
                "name": "", "created_by": "forged-owner", "userId": "forged-owner",
                "displayName": "forged name",
            }})
            self.assertEqual(response.status_code, 200, response.text)
            response = invoke(client, "query", {})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual([item["id"] for item in response.json()["items"]], [record_id])
            with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
                row = connection.execute("SELECT created_by FROM records WHERE id=?", (record_id,)).fetchone()
            self.assertEqual(row[0], owner)
            before = self.identity_database_state()
            response = invoke(client, "update", {"id": record_id, "changes": {"name": "attempt"}},
                              actor=str(uuid4()), version=1)
            self.assertEqual(response.status_code, 403, response.text)
            self.assertEqual(self.identity_database_state(), before)

    def test_sibling_origin_cannot_use_the_ui_session_with_simple_content_type(self):
        body = self.action_body("delete", uuid4().hex, {"id": "victim"}, expected_version=1)
        response = self.client.post(
            "/api/ui/confirmations",
            headers={
                "Origin": "https://evil-sibling.example.com",
                "Content-Type": "text/plain",
            },
            content=json.dumps({
                **body,
                "actionKey": self.actions["delete"]["actionKey"],
                "confirmed": True,
            }),
        )

        self.assertEqual(response.status_code, 403, response.text)

    def test_event_delivery_is_schema_bound_subscribed_and_conflict_safe(self):
        body = self.event_body()
        module_events = self.application.MODULES[self.module_key].setdefault(
            "events", {"publishes": [], "subscribes": []}
        )
        previous_subscriptions = list(module_events.get("subscribes") or [])
        module_events["subscribes"] = [body["event"]["eventType"]]
        token = self.event_token(body)
        try:
            accepted = self.post_event(body, token=token)
            replay = self.post_event(body, token=token)
            changed = {
                **body,
                "event": {**body["event"], "payload": {"available": 999}},
            }
            conflict = self.post_event(changed, token=token)
        finally:
            module_events["subscribes"] = previous_subscriptions

        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()["status"], "accepted")
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json()["status"], "duplicate")
        self.assertEqual(conflict.status_code, 409, conflict.text)

    def test_event_delivery_rejects_invalid_scope_schema_and_unsubscribed_type(self):
        body = self.event_body()
        module_events = self.application.MODULES[self.module_key].setdefault(
            "events", {"publishes": [], "subscribes": []}
        )
        previous_subscriptions = list(module_events.get("subscribes") or [])
        try:
            module_events["subscribes"] = []
            unsubscribed = self.post_event(body)

            module_events["subscribes"] = [body["event"]["eventType"]]
            invalid_source = self.post_event({**body, "sourceApplicationSlug": "Bad Source"})
            missing_entity = {
                **body,
                "event": {
                    key: value for key, value in body["event"].items() if key != "entityId"
                },
            }
            missing = self.post_event(missing_entity, token=self.event_token(body))
            cross_enterprise = {
                **body,
                "event": {**body["event"], "enterpriseKey": "other-company"},
            }
            cross = self.post_event(cross_enterprise, token=self.event_token(body))
            wrong_claim = self.post_event(
                body,
                token=self.event_token(body, eventType="different.event.v1"),
            )
        finally:
            module_events["subscribes"] = previous_subscriptions

        self.assertEqual(unsubscribed.status_code, 403, unsubscribed.text)
        self.assertEqual(invalid_source.status_code, 422, invalid_source.text)
        self.assertEqual(missing.status_code, 422, missing.text)
        self.assertEqual(cross.status_code, 403, cross.text)
        self.assertEqual(wrong_claim.status_code, 403, wrong_claim.text)

    def test_jwt_requires_exp_and_enforces_contract_lifetime(self):
        now = int(time.time())
        for token_type, maximum_lifetime, signing_secret in (
            ("zhuojian-action", 60, self.action_secret),
            ("zhuojian-event", 60, self.event_secret),
        ):
            base_claims = {
                "iss": "zhuojian-saas",
                "typ": token_type,
                "aud": self.application.APP_SLUG,
                "organizationId": self.organization_id,
                "iat": now,
            }
            missing_exp = self.jwt.encode(
                base_claims,
                signing_secret,
                algorithm="HS256",
            )
            with self.assertRaises(Exception) as missing_context:
                self.application.decode_jwt(missing_exp, token_type)
            self.assertEqual(missing_context.exception.status_code, 401)

            excessive = self.jwt.encode(
                {**base_claims, "exp": now + maximum_lifetime + 1},
                signing_secret,
                algorithm="HS256",
            )
            with self.assertRaises(Exception) as excessive_context:
                self.application.decode_jwt(excessive, token_type)
            self.assertEqual(excessive_context.exception.status_code, 401)

            valid = self.jwt.encode(
                {**base_claims, "exp": now + maximum_lifetime},
                signing_secret,
                algorithm="HS256",
            )
            self.assertEqual(
                self.application.decode_jwt(valid, token_type)["typ"],
                token_type,
            )

    def test_concurrent_same_request_executes_business_change_once(self):
        request_id = uuid4().hex
        record_id = uuid4().hex
        params = {"id": record_id, "data": {"name": "concurrent"}}
        body = self.action_body("create", request_id, params)
        token = self.action_token("create", request_id, params)

        def submit():
            return self.post_integration("create", body, token=token)

        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _index: submit(), range(2)))

        self.assertEqual([response.status_code for response in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM records WHERE id=?", (record_id,)).fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM outbox WHERE entity_id=?", (record_id,)).fetchone()[0],
                1,
            )
            request_row = connection.execute(
                "SELECT state,request_hash FROM request_results WHERE request_id=?",
                (request_id,),
            ).fetchone()
            self.assertEqual(request_row[0], "completed")
            self.assertRegex(request_row[1], r"^[0-9a-f]{64}$")

    def test_business_change_and_idempotency_result_rollback_together(self):
        request_id = uuid4().hex
        record_id = uuid4().hex
        action = self.actions["create"]
        params = {"id": record_id, "data": {"name": "crash-test"}}
        actor_claims = {
            "sub": "integration-action-test-user",
            "departmentId": self.department_id,
            "roleIds": self.role_ids,
            "effectiveDataScope": self.effective_data_scope,
        }
        request_hash = self.application.action_request_hash(
            action["actionKey"],
            self.module_key,
            self.page_key,
            "integration-action-test-user",
            params,
            None,
        )

        def crash_after_business_change(connection):
            self.application.execute_business_action(
                action, params, None, actor_claims, connection
            )
            raise RuntimeError("simulated crash before request result commit")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            self.application.execute_idempotent_action(
                action_key=action["actionKey"],
                action=action,
                request_id=request_id,
                request_hash=request_hash,
                actor="integration-action-test-user",
                params=params,
                confirmation=None,
                require_page_confirmation=False,
                perform=crash_after_business_change,
            )

        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM records WHERE id=?", (record_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM request_results WHERE request_id=?", (request_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM outbox WHERE entity_id=?", (record_id,)).fetchone()[0], 0)

        result = self.application.execute_idempotent_action(
            action_key=action["actionKey"],
            action=action,
            request_id=request_id,
            request_hash=request_hash,
            actor="integration-action-test-user",
            params=params,
            confirmation=None,
            require_page_confirmation=False,
            perform=lambda connection: self.application.execute_business_action(
                action, params, None, actor_claims, connection
            ),
        )
        self.assertEqual(result["id"], record_id)

    def test_high_risk_integration_confirmation_expires_and_is_idempotent(self):
        record_id = uuid4().hex
        create_id = uuid4().hex
        created = self.post_integration(
            "create",
            self.action_body("create", create_id, {"id": record_id, "data": {}}),
        )
        self.assertEqual(created.status_code, 200, created.text)

        params = {"id": record_id}
        expired_id = uuid4().hex
        expired_body = self.action_body("delete", expired_id, params, expected_version=1)
        expired_token = self.action_token(
            "delete",
            expired_id,
            params,
            confirmed_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        expired = self.post_integration("delete", expired_body, token=expired_token)
        self.assertEqual(expired.status_code, 403, expired.text)

        request_id = uuid4().hex
        body = self.action_body("delete", request_id, params, expected_version=1)
        token = self.action_token("delete", request_id, params)
        deleted = self.post_integration("delete", body, token=token)
        repeated = self.post_integration("delete", body, token=token)
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertEqual(deleted.json(), repeated.json())
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM records WHERE id=?", (record_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM consumed_confirmations WHERE request_id=?", (request_id,)).fetchone()[0], 1)

    def test_create_and_update_cannot_bypass_dedicated_status_action(self):
        record_id = uuid4().hex
        forged_create = self.post_integration(
            "create",
            self.action_body(
                "create",
                uuid4().hex,
                {"id": record_id, "data": {"status": "approved"}},
            ),
        )
        self.assertEqual(forged_create.status_code, 422, forged_create.text)

        created = self.post_integration(
            "create",
            self.action_body("create", uuid4().hex, {"id": record_id, "data": {}}),
        )
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["status"], "draft")

        forged_update = self.post_integration(
            "update",
            self.action_body(
                "update",
                uuid4().hex,
                {"id": record_id, "changes": {"status": "approved"}},
                expected_version=1,
            ),
        )
        self.assertEqual(forged_update.status_code, 422, forged_update.text)
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            status, version = connection.execute(
                "SELECT status, version FROM records WHERE id=?",
                (record_id,),
            ).fetchone()
        self.assertEqual((status, version), ("draft", 1))

    def test_page_high_risk_action_requires_issued_matching_confirmation(self):
        record_id = uuid4().hex
        created = self.post_integration(
            "create",
            self.action_body("create", uuid4().hex, {"id": record_id, "data": {}}),
        )
        self.assertEqual(created.status_code, 200, created.text)

        request_id = uuid4().hex
        params = {"id": record_id}
        body = self.action_body("delete", request_id, params, expected_version=1)
        unconfirmed = self.client.post(
            f"/api/ui/actions/{self.actions['delete']['actionKey']}",
            json=body,
        )
        self.assertEqual(unconfirmed.status_code, 403, unconfirmed.text)

        issued = self.client.post(
            "/api/ui/confirmations",
            json={
                **body,
                "actionKey": self.actions["delete"]["actionKey"],
                "confirmed": True,
            },
        )
        self.assertEqual(issued.status_code, 201, issued.text)
        confirmed_body = {**body, "confirmation": issued.json()}
        deleted = self.client.post(
            f"/api/ui/actions/{self.actions['delete']['actionKey']}",
            json=confirmed_body,
        )
        repeated = self.client.post(
            f"/api/ui/actions/{self.actions['delete']['actionKey']}",
            json=confirmed_body,
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(repeated.status_code, 200, repeated.text)
        self.assertEqual(deleted.json(), repeated.json())

    def test_page_confirmation_cannot_refresh_database_issued_time(self):
        record_id = uuid4().hex
        created = self.post_integration(
            "create",
            self.action_body("create", uuid4().hex, {"id": record_id, "data": {}}),
        )
        self.assertEqual(created.status_code, 200, created.text)

        request_id = uuid4().hex
        params = {"id": record_id}
        body = self.action_body("delete", request_id, params, expected_version=1)
        issued = self.client.post(
            "/api/ui/confirmations",
            json={
                **body,
                "actionKey": self.actions["delete"]["actionKey"],
                "confirmed": True,
            },
        )
        self.assertEqual(issued.status_code, 201, issued.text)
        confirmation = issued.json()
        stale_database_time = (
            datetime.now(timezone.utc)
            - timedelta(seconds=self.application.CONFIRMATION_MAX_AGE_SECONDS + 1)
        ).isoformat()
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            connection.execute(
                "UPDATE page_confirmations SET confirmed_at=? WHERE confirmation_id=?",
                (stale_database_time, confirmation["confirmationId"]),
            )
            connection.commit()

        forged_fresh_time = {
            **confirmation,
            "confirmedAt": datetime.now(timezone.utc).isoformat(),
        }
        rejected = self.client.post(
            f"/api/ui/actions/{self.actions['delete']['actionKey']}",
            json={**body, "confirmation": forged_fresh_time},
        )
        self.assertIn(rejected.status_code, {403, 409}, rejected.text)
        with closing(sqlite3.connect(os.environ["DATABASE_PATH"])) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM records WHERE id=?",
                    (record_id,),
                ).fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()
