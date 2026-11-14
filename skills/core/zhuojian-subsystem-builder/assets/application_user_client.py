"""Optional, dependency-free server client for applicationUsers version 1.

Use only after the source authenticates its account. Never expose the source
credential or returned sessions to logs. No login UI, polling or account store
is imposed; callers retain their own transactions, IDs, roles and delivery.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class ApplicationUserError(RuntimeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Application identity service returned HTTP {status}")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ApplicationUserClient:
    def __init__(self, origin: str, source_credential: str, *, application_id: str,
                 timeout: float = 8, allow_http_loopback: bool = False):
        parsed = urlsplit(origin)
        local = allow_http_loopback and parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"}
        if (not (parsed.scheme == "https" or local) or not parsed.hostname or parsed.username
                or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            raise ValueError("A trusted HTTPS platform origin is required")
        if not source_credential.startswith("zjss_") or not application_id:
            raise ValueError("The application's own source credential and ID are required")
        self.origin, self.application_id = origin.rstrip("/"), application_id
        self._credential, self.timeout = source_credential, timeout
        self._opener = build_opener(_NoRedirect())

    def _call(self, operation: str, data: dict) -> dict:
        req = Request(self.origin + "/api/v1/subsystem-users/" + operation,
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self._credential})
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                content = response.read(65537)
                if len(content) > 65536:
                    raise ApplicationUserError(502)
                value = json.loads(content)
                if not isinstance(value, dict):
                    raise ApplicationUserError(502)
                return value
        except HTTPError as exc:
            raise ApplicationUserError(exc.code) from None
        except (URLError, TimeoutError, ValueError):
            raise ApplicationUserError(503) from None

    def register(self, *, external_id: str, source_version: int,
                 display_name: str | None = None, business_roles: list[str] | None = None,
                 relation: str = "customer", source_label: str | None = None,
                 is_active: bool = True, identity_link_token: str | None = None,
                 invitation_token: str | None = None) -> dict:
        payload = dict(external_id=external_id, source_version=source_version,
            display_name=display_name, business_roles=business_roles or [], relation=relation,
            source_label=source_label, is_active=is_active)
        if identity_link_token:
            payload["identity_link_token"] = identity_link_token
        if invitation_token:
            payload["invitation_token"] = invitation_token
        value = self._call("register", payload)
        if value.get("application_id") != self.application_id or value.get("external_id") != external_id:
            raise ApplicationUserError(502)
        return value

    def login(self, external_id: str) -> dict:
        """Caller has just authenticated this exact source account."""
        return self._call("login", {"external_id": external_id})

    def check(self, session_token: str) -> dict:
        """Persist renewed_session_token if present; do not relogin on failure."""
        return self._call("session-check", {"session_token": session_token})

    def logout(self, session_token: str) -> dict:
        return self._call("logout", {"session_token": session_token})

    def resolve_invitation(self, invitation_token: str) -> dict:
        return self._call("invitations/resolve", {"invitation_token": invitation_token})

    def identity_proof(self, session_token: str, target_application_id: str) -> dict:
        return self._call("identity-proof", {"session_token": session_token, "application_id": target_application_id})
