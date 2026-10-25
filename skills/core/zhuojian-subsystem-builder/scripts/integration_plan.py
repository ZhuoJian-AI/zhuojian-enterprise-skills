#!/usr/bin/env python3
"""Use a Runtime-bound integration plan without exposing its registration key.

Runtime endpoint owners may confirm an exact event-configuration plan after local
business-intent confirmation. This is machine delegation, not an administrator
session or business-role grant. The helper never performs business test writes.
"""

from __future__ import annotations

import argparse
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import stat
import sys
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
API_ROOT = "/api/v1/ecs-publisher/integration-plans"
PROPOSAL_FIELDS = {
    "request_id", "title", "purpose", "data_description", "ownership_description", "edges",
}
PROPOSAL_OPTIONS = {"authorization_mode", "configuration_ttl_hours"}
RUNTIME_MODE = "runtime_endpoints"
EDGE_FIELDS = {
    "key", "source_application_id", "source_module_key", "target_application_id",
    "target_module_key", "event_type", "kind",
}
EDGE_OPTIONS = {"adopt_route_id"}
VERSION_RE = re.compile(r"[0-9a-f]{64}")
KEY_RE = re.compile(r"[a-z][a-z0-9_-]{0,59}")
EVENT_RE = re.compile(r"[a-z0-9][a-z0-9._-]*\.v[1-9][0-9]*")
ERROR_CODES = {
    "plan_version_conflict", "runtime_unavailable", "administrator_revoked",
    "organization_unavailable", "plan_not_found", "application_pair_required",
    "runtime_binding_missing", "requester_not_endpoint", "integration_boundary_mismatch",
    "application_binding_invalid", "module_not_registered", "request_id_reused",
    "plan_not_pending", "invalid_configuration_lease", "plan_not_approved",
    "configuration_lease_expired", "integration_not_ready", "configured_route_changed",
    "existing_route_conflict", "duplicate_delivery_reference", "delivery_reference_not_found",
    "runtime_authority_not_enabled", "authorization_digest_conflict", "runtime_not_participant",
    "runtime_authorization_changed", "runtime_confirmation_changed", "invalid_runtime_decision",
    "participant_confirmations_required",
    "plan_not_configured", "recovery_edge_not_found", "recovery_cursor_invalid",
    "recovery_request_not_found", "recovery_request_reused", "recovery_not_ready",
    "recovery_event_outside_grant", "recovery_route_unavailable", "recovery_delivery_busy",
    "recovery_delivery_unknown", "discovery_cursor_invalid",
    "route_deleted", "route_disabled", "route_not_exact", "route_scope_not_organization",
    "route_already_managed", "route_has_unsettled_deliveries", "route_endpoint_mismatch",
}


class IntegrationPlanError(RuntimeError):
    """A safe, non-secret error suitable for a JSON command result."""


class RequestRejected(IntegrationPlanError):
    def __init__(self, status: int, code: str | None = None) -> None:
        self.status = status
        self.code = code if code in ERROR_CODES else None
        suffix = f": {self.code}" if self.code else ""
        super().__init__(f"Platform rejected request (HTTP {status}){suffix}; read current plan status and readiness gaps")


class RequestOutcomeUnknown(IntegrationPlanError):
    """A mutating request needs a GET reconciliation before further action."""


class UnsupportedPlatform(IntegrationPlanError):
    """The target SaaS has not declared the matching plan API capability."""


class UnsupportedRuntimeAuthorization(UnsupportedPlatform):
    """Legacy plan support does not imply Runtime endpoint confirmation."""


class UnsupportedSelfService(UnsupportedPlatform):
    """Plan support alone does not imply discovery or original-window recovery."""


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IntegrationPlanError("Input must be finite JSON") from exc


def load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrationPlanError(f"Unable to read {label} JSON") from exc
    if not isinstance(value, dict):
        raise IntegrationPlanError(f"{label} must be an object")
    return value


def require_text(value: object, label: str, maximum: int = 2000) -> str:
    if (
        not isinstance(value, str) or not value.strip() or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\r\t" for character in value)
    ):
        raise IntegrationPlanError(f"Invalid {label}")
    return value


def require_uuid(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise IntegrationPlanError(f"Invalid {label}")
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise IntegrationPlanError(f"Invalid {label}") from exc


def validate_proposal(proposal: dict) -> dict:
    """Reject local mistakes; SaaS still authorizes every resource and operation."""
    if not isinstance(proposal, dict) or not PROPOSAL_FIELDS <= set(proposal) or set(proposal) - PROPOSAL_FIELDS - PROPOSAL_OPTIONS:
        raise IntegrationPlanError("Plan must contain only the published proposal fields")
    proposal = json.loads(canonical_json(proposal))
    mode = proposal.get("authorization_mode", "administrator")
    if mode == RUNTIME_MODE:
        ttl = proposal.get("configuration_ttl_hours", 72)
        if type(ttl) is not int or not 1 <= ttl <= 168:
            raise IntegrationPlanError("configuration_ttl_hours must be an integer from 1 to 168")
        proposal["configuration_ttl_hours"] = ttl
    elif mode == "administrator":
        if "configuration_ttl_hours" in proposal:
            raise IntegrationPlanError("Legacy administrator plans do not accept configuration_ttl_hours")
        # Preserve the legacy proposal comparison and specification exactly.
        proposal.pop("authorization_mode", None)
    else:
        raise IntegrationPlanError("Unknown authorization_mode")
    require_text(proposal["request_id"], "request_id", 120)
    require_text(proposal["title"], "title", 160)
    for field in ("purpose", "data_description", "ownership_description"):
        require_text(proposal[field], field)
    edges = proposal["edges"]
    if not isinstance(edges, list) or not 1 <= len(edges) <= 8:
        raise IntegrationPlanError("Plan requires 1 to 8 explicit edges")
    seen = set()
    identities = set()
    applications = set()
    for edge in edges:
        if not isinstance(edge, dict) or not EDGE_FIELDS <= set(edge) or set(edge) - EDGE_FIELDS - EDGE_OPTIONS:
            raise IntegrationPlanError("Edge must contain only the published edge fields")
        if "adopt_route_id" in edge:
            edge["adopt_route_id"] = require_uuid(edge["adopt_route_id"], "adopt_route_id")
        if not isinstance(edge["key"], str) or KEY_RE.fullmatch(edge["key"]) is None:
            raise IntegrationPlanError("Invalid edge key")
        for field in ("source_module_key", "target_module_key"):
            value = require_text(edge[field], "edge " + field, 120)
            if any(character.isspace() or character in "*?[]" for character in value):
                raise IntegrationPlanError(f"Invalid edge {field}")
        if edge["key"] in seen:
            raise IntegrationPlanError("Edge keys must be unique")
        seen.add(edge["key"])
        source = require_uuid(edge["source_application_id"], "source_application_id")
        target = require_uuid(edge["target_application_id"], "target_application_id")
        edge["source_application_id"] = source
        edge["target_application_id"] = target
        applications.update((source, target))
        if source == target and edge["source_module_key"] == edge["target_module_key"]:
            raise IntegrationPlanError("An edge must connect distinct application/modules")
        if not isinstance(edge["event_type"], str) or len(edge["event_type"]) > 160 or EVENT_RE.fullmatch(edge["event_type"]) is None:
            raise IntegrationPlanError("Edge requires an explicit versioned event_type")
        if edge["kind"] not in {"forward", "result"}:
            raise IntegrationPlanError("Edge kind must be forward or result")
        identity = (source, edge["source_module_key"], edge["event_type"], target, edge["target_module_key"])
        if identity in identities:
            raise IntegrationPlanError("Exact edges must be unique")
        identities.add(identity)
    if len(applications) > 2:
        raise IntegrationPlanError("One integration plan may involve at most two applications")
    connected = {(edges[0]["source_application_id"], edges[0]["source_module_key"])}
    remaining = list(edges)
    while remaining:
        previous = len(remaining)
        for edge in list(remaining):
            source = (edge["source_application_id"], edge["source_module_key"])
            target = (edge["target_application_id"], edge["target_module_key"])
            if source in connected or target in connected:
                connected.update((source, target))
                remaining.remove(edge)
        if len(remaining) == previous:
            raise IntegrationPlanError("Plan edges must form a connected module graph")
    # Edge order does not define execution order. SaaS projects plans by key,
    # and stable request reconciliation must compare the same keyed graph.
    proposal["edges"].sort(key=lambda edge: edge["key"])
    return proposal


def read_runtime_key(path: Path) -> str:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "r", encoding="utf-8") as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise IntegrationPlanError("Runtime credential must be a regular file")
            if os.name != "nt" and (
                info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise IntegrationPlanError("Runtime credential must be root-owned mode 0600")
            value = source.read(8193)
    except (OSError, UnicodeError) as exc:
        raise IntegrationPlanError("Unable to read protected Runtime credential") from exc
    value = value.strip()
    if not value or len(value) > 8192 or any(character.isspace() for character in value):
        raise IntegrationPlanError("Runtime credential is invalid")
    return value


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


class PlatformClient:
    """Fixed-origin, no-redirect JSON transport with sanitized failures."""

    def __init__(self, base_url: str, credential: str, *, opener=None) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}
        ):
            raise IntegrationPlanError("Runtime platform.baseUrl must be an HTTPS origin")
        self.base_url = base_url.rstrip("/")
        self._credential = credential
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())
        self._integration_capability_checked = False
        self._features = {}

    @classmethod
    def from_runtime(cls, profile_path: Path) -> PlatformClient:
        profile = load_object(profile_path, "Runtime profile")
        platform = profile.get("platform")
        deployment = profile.get("deployment")
        if not isinstance(platform, dict) or not isinstance(deployment, dict):
            raise IntegrationPlanError("Runtime profile lacks platform/deployment settings")
        reference = deployment.get("registrationCredentialRef")
        if not isinstance(reference, str) or not reference or not Path(reference).is_absolute():
            raise IntegrationPlanError("Runtime profile lacks an absolute credential reference")
        # Reject a malformed origin before opening any credential file.
        client = cls(str(platform.get("baseUrl") or ""), "")
        client._credential = read_runtime_key(Path(reference))
        return client

    def require_integration_plans(self) -> None:
        if self._integration_capability_checked:
            return
        try:
            capabilities = self.request("GET", "/api/v1/ecs-publisher/platform-capabilities")
        except RequestRejected as exc:
            if exc.status == 404:
                raise UnsupportedPlatform("Target SaaS does not declare integrationPlans v1; configuration remains unenabled") from exc
            raise
        features = capabilities.get("features") if isinstance(capabilities, dict) else None
        feature = features.get("integrationPlans") if isinstance(features, dict) else None
        if not isinstance(feature, dict) or feature.get("supported") is not True or type(feature.get("version")) is not int or feature["version"] != 1:
            raise UnsupportedPlatform("Target SaaS does not declare integrationPlans v1; configuration remains unenabled")
        self._integration_capability_checked = True
        self._features = features

    def require_runtime_authorization(self) -> None:
        self.require_integration_plans()
        feature = self._features.get("integrationPlanRuntimeAuthorization")
        if (
            not isinstance(feature, dict) or feature.get("supported") is not True
            or type(feature.get("version")) is not int or feature["version"] != 1
            or feature.get("authorizationMode") != RUNTIME_MODE
            or feature.get("authority") != "runtime-owned-app-configuration"
            or feature.get("allParticipantRuntimesRequired") is not True
            or feature.get("requiresAdministratorSession") is not False
        ):
            raise UnsupportedRuntimeAuthorization("Target SaaS lacks Runtime endpoint confirmation; continue authorized preparation and report the exact capability gap")

    def require_self_service(self) -> None:
        self.require_integration_plans()
        feature = self._features.get("integrationPlanSelfService")
        if (
            not isinstance(feature, dict) or feature.get("supported") is not True
            or type(feature.get("version")) is not int or feature["version"] != 1
            or type(feature.get("contractProjectionRevision")) is not int
            or feature["contractProjectionRevision"] != 2
            or feature.get("recoveryScope") != "original-plan-event-window"
            or feature.get("requiresAdministratorSession") is not False
        ):
            raise UnsupportedSelfService("Target SaaS lacks integrationPlanSelfService v1; do not assume the legacy plan list is complete or replay historical events")

    def require_route_adoption(self) -> None:
        self.require_self_service()
        if self._features["integrationPlanSelfService"].get("exactActiveRouteAdoption") is not True:
            raise UnsupportedSelfService("Target SaaS lacks exact active route adoption; do not replace an existing route")

    def request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        if method not in {"GET", "POST"}:
            raise IntegrationPlanError("Unsupported integration method")
        if not path.startswith("/api/v1/") or path.startswith("//") or "#" in path:
            raise IntegrationPlanError("Integration path must stay within the platform API")
        if "\\" in path or "://" in path or any(ord(character) < 32 for character in path):
            raise IntegrationPlanError("Invalid integration API path")
        data = canonical_json(payload) if payload is not None else None
        request = Request(
            self.base_url + path, data=data, method=method,
            headers={
                "Authorization": "Bearer " + self._credential,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ZhuoJian-Integration-Plan/1",
            },
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("oversized JSON response")
                value = json.loads(raw)
                if not isinstance(value, (dict, list)):
                    raise ValueError("non-container JSON response")
                return value
        except HTTPError as exc:
            # Do not print response bodies; upstream errors can contain secrets.
            if method == "POST" and (exc.code == 408 or exc.code >= 500):
                raise RequestOutcomeUnknown("Write outcome unknown; reconcile with GET") from exc
            code = None
            try:
                failure = json.loads(exc.read(8193))
                detail = failure.get("detail") if isinstance(failure, dict) else None
                if isinstance(detail, dict) and detail.get("code") in ERROR_CODES:
                    code = detail["code"]
            except (OSError, HTTPException, TypeError, ValueError):
                pass
            raise RequestRejected(exc.code, code) from exc
        except (URLError, OSError, HTTPException, UnicodeError, ValueError) as exc:
            if method == "POST":
                raise RequestOutcomeUnknown("Write outcome unknown; reconcile with GET") from exc
            raise IntegrationPlanError("Platform read failed; no write was performed") from exc


def require_plan(value: object, plan_id: str | None = None) -> dict:
    if not isinstance(value, dict):
        raise IntegrationPlanError("Platform plan response must be an object")
    require_uuid(value.get("id"), "plan id")
    if plan_id is not None and value["id"] != plan_id:
        raise IntegrationPlanError("Platform returned a different plan")
    for field in ("version", "spec_digest"):
        if not isinstance(value.get(field), str) or VERSION_RE.fullmatch(value[field]) is None:
            raise IntegrationPlanError(f"Platform plan lacks a valid {field}")
    if value.get("authorization_status") not in {"pending", "approved", "rejected", "revoked"}:
        raise IntegrationPlanError("Unknown platform plan authorization status")
    if value.get("authorization_mode", "administrator") not in {"administrator", RUNTIME_MODE}:
        raise IntegrationPlanError("Unknown platform plan authorization mode")
    return value


def proposal_from_plan(plan: dict) -> dict:
    result = {field: plan.get(field) for field in PROPOSAL_FIELDS - {"edges"}}
    if not isinstance(plan.get("edges"), list):
        raise IntegrationPlanError("Platform plan lacks exact edges")
    if not all(isinstance(edge, dict) for edge in plan["edges"]):
        raise IntegrationPlanError("Platform plan contains an invalid edge")
    result["edges"] = [
        {**{key: edge.get(key) for key in EDGE_FIELDS},
         **{key: edge[key] for key in EDGE_OPTIONS if edge.get(key) is not None}}
        for edge in plan["edges"]
    ]
    if plan.get("authorization_mode") == RUNTIME_MODE:
        result.update(authorization_mode=RUNTIME_MODE, configuration_ttl_hours=plan.get("configuration_ttl_hours"))
    return validate_proposal(result)


def require_unchanged(before: dict, after: dict) -> dict:
    require_plan(after, before["id"])
    if after["spec_digest"] != before["spec_digest"]:
        raise IntegrationPlanError("Platform plan specification changed")
    if before.get("authorization_mode", "administrator") != after.get("authorization_mode", "administrator"):
        raise IntegrationPlanError("Platform plan authorization mode changed")
    if before.get("authorization_mode") == RUNTIME_MODE and before.get("authorization_digest") != after.get("authorization_digest"):
        raise IntegrationPlanError("Platform plan authorization digest changed")
    if before.get("authorization_mode") == RUNTIME_MODE and before.get("apply_expires_at") != after.get("apply_expires_at"):
        raise IntegrationPlanError("Platform plan common configuration deadline changed")
    return after


def safe_plan_summary(plan: dict) -> dict:
    """Print only contract metadata, references and bounded gap explanations."""
    require_plan(plan)
    summary = {key: plan.get(key) for key in (
        "id", "request_id", "version", "spec_digest", "authorization_status",
        "configuration_status", "configuration_lease_expired", "transport_status",
        "business_status", "apply_expires_at",
    )}
    summary["authorization_mode"] = plan.get("authorization_mode", "administrator")
    summary["business_scope"] = {
        key: str(plan.get(key) or "")[:2000]
        for key in ("title", "purpose", "data_description", "ownership_description")
    }
    summary["edges"] = [
        {key: edge.get(key) for key in EDGE_FIELDS | EDGE_OPTIONS}
        for edge in plan.get("edges") or [] if isinstance(edge, dict)
    ]
    if plan.get("authorization_mode") == RUNTIME_MODE:
        summary.update({key: plan.get(key) for key in (
            "authorization_digest", "authorization_authority", "configuration_ttl_hours",
            "requires_administrator_session", "current_runtime_id", "requester_runtime_id",
            "current_runtime_application_ids", "current_runtime_can_confirm",
        )})
        summary["runtime_confirmations"] = [
            {key: item.get(key) for key in ("runtime_id", "application_ids", "confirmed", "valid", "confirmed_at")}
            for item in plan.get("runtime_confirmations") or [] if isinstance(item, dict)
        ]
    readiness = plan.get("readiness")
    summary["readiness"] = {"ready": False, "gaps": []}
    if isinstance(readiness, dict):
        summary["readiness"]["ready"] = readiness.get("ready") is True
        for gap in readiness.get("gaps") or []:
            if isinstance(gap, dict):
                summary["readiness"]["gaps"].append({
                    key: str(gap.get(key) or "")[:1000] for key in ("code", "edge_key", "message")
                })
    approval_url = plan.get("approval_url")
    if isinstance(approval_url, str):
        parsed = urlsplit(approval_url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        safe_query = not query or any(
            query == {"integration_plan": [str(plan["id"])], key: ["integration"]}
            for key in ("tab", "section")
        )
        if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password and safe_query and not parsed.fragment:
            summary["approval_url"] = approval_url
    summary["end_to_end_verified"] = False
    summary["remaining_business_checks"] = [
        "target authorized readback and object/version mapping",
        "source obtains and displays the real final result",
        "file/content hash comparison when applicable",
    ]
    return summary


def find_request(client: PlatformClient, request_id: str) -> dict | None:
    values = client.request("GET", API_ROOT + "?" + urlencode({"request_id": request_id}))
    if not isinstance(values, list):
        raise IntegrationPlanError("Platform plan list response must be an array")
    matches = [require_plan(value) for value in values if isinstance(value, dict) and value.get("request_id") == request_id]
    if len(matches) > 1:
        raise IntegrationPlanError("Platform returned multiple plans for one request_id")
    return matches[0] if matches else None


def get_plan(client: PlatformClient, plan_id: str) -> dict:
    plan_id = require_uuid(plan_id, "plan id")
    return require_plan(client.request("GET", API_ROOT + "/" + quote(plan_id, safe="")), plan_id)


def post_plan(client: PlatformClient, path: str, payload: dict) -> dict:
    value = client.request("POST", path, payload)
    try:
        return require_plan(value)
    except IntegrationPlanError as exc:
        raise RequestOutcomeUnknown("Write returned an incomplete plan; reconcile with GET") from exc


def propose(client: PlatformClient, proposal: dict) -> dict:
    proposal = validate_proposal(proposal)
    if any(edge.get("adopt_route_id") for edge in proposal["edges"]):
        client.require_route_adoption()
    if proposal.get("authorization_mode") == RUNTIME_MODE:
        client.require_runtime_authorization()
    existing = find_request(client, proposal["request_id"])
    if existing is not None:
        if canonical_json(proposal_from_plan(existing)) != canonical_json(proposal):
            raise IntegrationPlanError("request_id already belongs to a different plan")
        return {"status": "existing", **safe_plan_summary(existing)}
    try:
        plan = post_plan(client, API_ROOT, proposal)
    except RequestOutcomeUnknown:
        try:
            plan = find_request(client, proposal["request_id"])
        except IntegrationPlanError:
            plan = None
        if plan is None:
            return {"status": "unknown", "operation": "propose", "request_id": proposal["request_id"], "next_action": "status by the same request_id; do not create a new request or automatically POST again"}
        if canonical_json(proposal_from_plan(plan)) != canonical_json(proposal):
            raise IntegrationPlanError("Reconciled request_id belongs to a different plan")
        return {"status": "reconciled", **safe_plan_summary(plan)}
    if canonical_json(proposal_from_plan(plan)) != canonical_json(proposal):
        raise IntegrationPlanError("Platform returned a different proposal")
    return {"status": "proposed", **safe_plan_summary(plan)}


def runtime_participant(plan: dict, authorization_digest: str, *, require_snapshot_membership: bool = True) -> dict:
    """Validate public scope metadata; only the SaaS authorizes the caller."""
    if plan.get("authorization_mode") != RUNTIME_MODE:
        raise IntegrationPlanError("Legacy administrator plan has no Runtime confirmation; create a new explicit runtime_endpoints proposal when supported")
    if not isinstance(authorization_digest, str) or VERSION_RE.fullmatch(authorization_digest) is None:
        raise IntegrationPlanError("Platform plan lacks a valid public authorization_digest")
    if (
        plan.get("authorization_digest") != authorization_digest
        or plan.get("authorization_authority") not in ({"runtime_app_owners"} if require_snapshot_membership else {"runtime_app_owners", "enterprise_administrator"})
        or plan.get("requires_administrator_session") is not False
    ):
        raise IntegrationPlanError("Authorization scope changed or Runtime authority is missing; read and review the current plan")
    runtime_id = require_uuid(plan.get("current_runtime_id"), "current Runtime id")
    owned = plan.get("current_runtime_application_ids")
    if not isinstance(owned, list) or not owned:
        raise IntegrationPlanError("Current Runtime owns no exact participant application scope")
    for app_id in owned:
        require_uuid(app_id, "current Runtime application id")
    endpoints = {
        require_uuid(edge.get(key), "edge application id")
        for edge in plan.get("edges") or [] if isinstance(edge, dict)
        for key in ("source_application_id", "target_application_id")
    }
    if len(set(owned)) != len(owned) or not set(owned) <= endpoints:
        raise IntegrationPlanError("Current Runtime application scope differs from plan endpoints")
    confirmations = plan.get("runtime_confirmations")
    if not isinstance(confirmations, list) or not 1 <= len(confirmations) <= 2:
        raise IntegrationPlanError("Platform plan lacks Runtime confirmations")
    runtime_ids, covered = set(), set()
    for row in confirmations:
        if not isinstance(row, dict):
            raise IntegrationPlanError("Invalid Runtime confirmation")
        row_id = require_uuid(row.get("runtime_id"), "participant Runtime id")
        apps = row.get("application_ids")
        if row_id in runtime_ids or not isinstance(apps, list) or not apps:
            raise IntegrationPlanError("Invalid participant Runtime application scope")
        runtime_ids.add(row_id)
        for app_id in apps:
            require_uuid(app_id, "participant application id")
        if len(set(apps)) != len(apps) or covered.intersection(apps):
            raise IntegrationPlanError("Overlapping participant application scope")
        covered.update(apps)
        if any(type(row.get(key)) is not bool for key in ("confirmed", "valid")):
            raise IntegrationPlanError("Invalid Runtime confirmation state")
    if covered != endpoints:
        raise IntegrationPlanError("Runtime confirmations do not cover the exact plan endpoints")
    matches = [row for row in confirmations if isinstance(row, dict) and row.get("runtime_id") == runtime_id]
    # A current new owner may withdraw a stale relation after ownership drift.
    # It cannot sign the old snapshot, but requiring that signature to revoke
    # would contradict the backend's current-owner withdrawal authority.
    if not require_snapshot_membership:
        return matches[0] if len(matches) == 1 else {}
    if len(matches) != 1 or not isinstance(matches[0].get("application_ids"), list):
        raise IntegrationPlanError("Current Runtime confirmation does not match its owned applications")
    for app_id in matches[0]["application_ids"]:
        require_uuid(app_id, "confirmed application id")
    if set(matches[0]["application_ids"]) != set(owned) or any(type(matches[0].get(key)) is not bool for key in ("confirmed", "valid")):
        raise IntegrationPlanError("Current Runtime confirmation does not match its owned applications")
    return matches[0]


def runtime_decision(client: PlatformClient, plan_id: str, authorization_digest: str,
                     *, operation: str, business_intent_confirmed: bool, reason: str | None = None) -> dict:
    # This flag only prevents accidental local invocation. It is not evidence of
    # a human identity and is deliberately absent from the authenticated body.
    if business_intent_confirmed is not True:
        raise IntegrationPlanError("Explicit local business-intent confirmation is required")
    if operation not in {"confirm", "reject", "revoke"}:
        raise IntegrationPlanError("Unsupported Runtime decision")
    if not isinstance(authorization_digest, str) or VERSION_RE.fullmatch(authorization_digest) is None:
        raise IntegrationPlanError("Use the exact public authorization_digest from the reviewed plan")
    if reason is not None:
        require_text(reason, "decision reason", 1000)
        if operation == "confirm":
            raise IntegrationPlanError("confirm does not accept a reason")
    client.require_runtime_authorization()
    plan = get_plan(client, plan_id)
    if operation == "confirm" and plan["authorization_status"] == "approved" and plan.get("authorization_authority") == "enterprise_administrator":
        runtime_participant(plan, authorization_digest, require_snapshot_membership=False)
        return {"status": "already_authorized_by_administrator", **safe_plan_summary(plan)}
    own = runtime_participant(plan, authorization_digest, require_snapshot_membership=operation == "confirm")
    desired = {"reject": "rejected", "revoke": "revoked"}.get(operation)
    if operation == "confirm":
        if plan["authorization_status"] not in {"pending", "approved"}:
            raise IntegrationPlanError("This plan cannot be confirmed; review its terminal decision")
        if own.get("confirmed") is True and own.get("valid") is True:
            return {"status": "already_confirmed", **safe_plan_summary(plan)}
        if plan.get("current_runtime_can_confirm") is not True or plan.get("configuration_lease_expired") is not False:
            return {"status": "not_ready", **safe_plan_summary(plan)}
    elif plan["authorization_status"] == desired:
        return {"status": "already_" + desired, **safe_plan_summary(plan)}
    before_runtime = plan["current_runtime_id"]
    payload = {"authorization_digest": authorization_digest}
    if reason is not None:
        payload["reason"] = reason
    unknown = False
    try:
        result = post_plan(client, API_ROOT + "/" + quote(plan_id, safe="") + "/" + operation, payload)
        try:
            require_unchanged(plan, result)
            runtime_participant(result, authorization_digest, require_snapshot_membership=operation == "confirm")
            if result["current_runtime_id"] != before_runtime:
                raise IntegrationPlanError("Platform returned another Runtime's confirmation")
        except IntegrationPlanError as exc:
            raise RequestOutcomeUnknown("Decision response incomplete; reconcile with GET") from exc
    except RequestOutcomeUnknown:
        unknown = True
        try:
            result = require_unchanged(plan, get_plan(client, plan_id))
        except IntegrationPlanError:
            result = None
    if result is not None:
        own_result = runtime_participant(result, authorization_digest, require_snapshot_membership=operation == "confirm")
        if result["current_runtime_id"] != before_runtime:
            raise IntegrationPlanError("Platform returned another Runtime's confirmation")
        complete = (
            result["authorization_status"] in {"pending", "approved"}
            and own_result.get("confirmed") is True and own_result.get("valid") is True
        ) if operation == "confirm" else result["authorization_status"] == desired
        if complete:
            return {"status": "reconciled" if unknown else ("confirmed" if operation == "confirm" else desired),
                    "operation": operation,
                    **safe_plan_summary(result)}
    return {"status": "unknown" if unknown else "not_ready", "operation": operation, "id": plan_id,
            "next_action": "GET the same plan and inspect this Runtime's exact confirmation; do not automatically POST again"}


def apply(client: PlatformClient, plan_id: str, expected_version: str | None = None) -> dict:
    plan = get_plan(client, plan_id)
    if plan.get("authorization_mode") == RUNTIME_MODE:
        client.require_runtime_authorization()
        administrator_approved = plan["authorization_status"] == "approved" and plan.get("authorization_authority") == "enterprise_administrator"
        runtime_participant(plan, plan.get("authorization_digest"), require_snapshot_membership=not administrator_approved)
        require_uuid(plan.get("requester_runtime_id"), "requester Runtime id")
        if plan.get("current_runtime_id") != plan.get("requester_runtime_id"):
            return {"status": "requester_required", **safe_plan_summary(plan), "next_action": "Run apply on the original requester Runtime using its local credential"}
        if plan["authorization_status"] == "approved" and not administrator_approved and not all(row["confirmed"] is True and row["valid"] is True for row in plan["runtime_confirmations"]):
            return {"status": "not_ready", **safe_plan_summary(plan)}
    if expected_version is not None and expected_version != plan["version"]:
        raise IntegrationPlanError("Plan version changed; read and review the current plan")
    if plan["authorization_status"] != "approved":
        return {"status": "not_approved", **safe_plan_summary(plan), "next_action": "Review the exact business scope in Codex and confirm on each participant Runtime" if plan.get("authorization_mode") == RUNTIME_MODE else "Legacy administrator-session plan; Runtime confirmation is unavailable for this plan"}
    if plan.get("configuration_status") == "configured":
        return {"status": "already_configured", **safe_plan_summary(plan)}
    readiness = plan.get("readiness")
    if plan.get("configuration_lease_expired") is not False or not isinstance(readiness, dict) or readiness.get("ready") is not True:
        return {"status": "not_ready", **safe_plan_summary(plan)}
    try:
        result = require_unchanged(plan, post_plan(client, API_ROOT + "/" + quote(plan_id, safe="") + "/apply", {"version": plan["version"]}))
    except RequestOutcomeUnknown:
        try:
            result = require_unchanged(plan, get_plan(client, plan_id))
        except IntegrationPlanError:
            result = None
        if result is None or result.get("configuration_status") != "configured":
            return {"status": "unknown", "operation": "apply", "id": plan_id, "next_action": "GET status and review the same plan; do not automatically POST again"}
        return {"status": "reconciled", **safe_plan_summary(result)}
    return {"status": "configured" if result.get("configuration_status") == "configured" else "not_ready", **safe_plan_summary(result)}


def acknowledged_receipts(plan: dict, delivery_ids: list[str]) -> list[dict]:
    """Require saved target receipts, never an HTTP or accepted-only success."""
    verification = plan.get("verification")
    if not isinstance(verification, dict) or verification.get("end_to_end_verified") is not False or verification.get("scope") != "saved-target-receipts-only":
        raise IntegrationPlanError("Platform verification lacks an explicit end-to-end boundary")
    deliveries = verification.get("deliveries")
    if not isinstance(deliveries, list) or len(deliveries) != len(delivery_ids):
        raise IntegrationPlanError("Verification does not contain the requested saved deliveries")
    if {item.get("delivery_id") for item in deliveries if isinstance(item, dict)} != set(delivery_ids):
        raise IntegrationPlanError("Verification delivery IDs do not match the request")
    edge_keys = {edge.get("key") for edge in plan.get("edges") or [] if isinstance(edge, dict)}
    receipts = []
    for delivery in deliveries:
        if delivery.get("edge_key") not in edge_keys or delivery.get("processed") is not True or delivery.get("business_status") != "business_acknowledged":
            raise IntegrationPlanError("A requested delivery is not business-acknowledged")
        receipt = delivery.get("receipt")
        if not isinstance(receipt, dict) or receipt.get("status") != "completed":
            raise IntegrationPlanError("A requested delivery lacks a completed target receipt")
        for key in ("id", "entityType", "entityId"):
            require_text(receipt.get(key), "receipt " + key, 240)
        version = receipt.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise IntegrationPlanError("Target receipt version must be a positive integer")
        digest = receipt.get("contentSha256")
        if digest is not None and (not isinstance(digest, str) or VERSION_RE.fullmatch(digest) is None):
            raise IntegrationPlanError("Target receipt contentSha256 is invalid")
        receipts.append({"delivery_id": delivery["delivery_id"], "edge_key": delivery["edge_key"], "receipt": {key: receipt[key] for key in ("id", "status", "entityType", "entityId", "version", "contentSha256") if key in receipt}})
    return receipts


def verify(client: PlatformClient, plan_id: str, delivery_ids: list[str], expected_version: str | None = None) -> dict:
    if not 1 <= len(delivery_ids) <= 8 or len(set(delivery_ids)) != len(delivery_ids):
        raise IntegrationPlanError("Use 1 to 8 distinct actual delivery IDs")
    for value in delivery_ids:
        require_text(value, "delivery id", 160)
    plan = get_plan(client, plan_id)
    if plan.get("authorization_mode") == RUNTIME_MODE:
        client.require_runtime_authorization()
        runtime_participant(plan, plan.get("authorization_digest"), require_snapshot_membership=plan.get("authorization_authority") != "enterprise_administrator")
        require_uuid(plan.get("requester_runtime_id"), "requester Runtime id")
        if plan.get("current_runtime_id") != plan.get("requester_runtime_id"):
            return {"status": "requester_required", **safe_plan_summary(plan), "next_action": "Run verification on the original requester Runtime using its local credential"}
    if expected_version is not None and expected_version != plan["version"]:
        raise IntegrationPlanError("Plan version changed; read and review the current plan")
    if plan["authorization_status"] != "approved":
        return {"status": "not_approved", **safe_plan_summary(plan)}
    if plan.get("configuration_status") != "configured":
        return {"status": "not_ready", **safe_plan_summary(plan)}
    unknown = False
    try:
        result = require_unchanged(plan, post_plan(client, API_ROOT + "/" + quote(plan_id, safe="") + "/verification", {"version": plan["version"], "delivery_ids": delivery_ids}))
    except RequestOutcomeUnknown:
        unknown = True
        try:
            result = require_unchanged(plan, get_plan(client, plan_id))
        except IntegrationPlanError:
            return {"status": "unknown", "operation": "verify", "id": plan_id, "next_action": "GET status and inspect saved receipts; do not automatically POST again"}
    try:
        receipts = acknowledged_receipts(result, delivery_ids)
    except IntegrationPlanError as exc:
        return {"status": "unknown" if unknown else "not_acknowledged", **safe_plan_summary(result), "reason": str(exc)}
    if result.get("business_status") != "business_acknowledged":
        return {"status": "partially_acknowledged", **safe_plan_summary(result), "target_receipts": receipts, "reason": "Other plan edges still lack completed business receipts", "reconciled": unknown}
    return {"status": "business_acknowledged", **safe_plan_summary(result), "target_receipts": receipts, "reconciled": unknown}


def page_query(*, limit: int = 50, cursor: str | None = None, **filters) -> str:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise IntegrationPlanError("Page limit must be from 1 to 100")
    values = {"limit": limit, **{k: v for k, v in filters.items() if v is not None}}
    if cursor is not None:
        values["cursor"] = require_uuid(cursor, "page cursor")
    return "?" + urlencode(values)


def require_page(value: object, *, limit: int, cursor: str | None, identity: str) -> dict:
    if (not isinstance(value, dict) or not isinstance(value.get("items"), list)
            or len(value["items"]) > limit or type(value.get("has_more")) is not bool):
        raise IntegrationPlanError("Invalid paged response; inventory is incomplete")
    ids = []
    for item in value["items"]:
        if not isinstance(item, dict):
            raise IntegrationPlanError("Invalid page item")
        ids.append(require_uuid(item.get(identity), "page item id"))
    if len(ids) != len(set(ids)) or cursor in ids:
        raise IntegrationPlanError("Page repeated an item or did not advance")
    if value["has_more"]:
        next_cursor = require_uuid(value.get("next_cursor"), "next cursor")
        if not ids or next_cursor != ids[-1] or next_cursor == cursor:
            raise IntegrationPlanError("Page cursor did not advance")
    elif value.get("next_cursor") is not None:
        raise IntegrationPlanError("Completed page must not advertise another cursor")
    return value


def discover(client: PlatformClient, *, application_id=None, limit=50, cursor=None) -> dict:
    client.require_self_service()
    if application_id is not None:
        application_id = require_uuid(application_id, "application id")
    query = page_query(limit=limit, cursor=cursor, application_id=application_id)
    page = require_page(client.request("GET", API_ROOT + "/discovery" + query),
                        limit=limit, cursor=cursor, identity="id")
    return {"items": [safe_plan_summary(item) for item in page["items"]],
            "has_more": page["has_more"], "next_cursor": page.get("next_cursor"),
            "inventory_complete": not page["has_more"],
            "scope": "current-runtime-participating-plans"}


def recovery_path(plan_id: str) -> str:
    return API_ROOT + "/" + require_uuid(plan_id, "plan id") + "/recovery"


def discover_routes(client: PlatformClient, source_application_id: str, *, target_application_id=None, limit=50, cursor=None) -> dict:
    client.require_route_adoption()
    source = require_uuid(source_application_id, "source application id")
    target = require_uuid(target_application_id, "target application id") if target_application_id is not None else None
    query = page_query(limit=limit, cursor=cursor, source_application_id=source, target_application_id=target)
    page = require_page(client.request("GET", API_ROOT + "/routes" + query),
                        limit=limit, cursor=cursor, identity="route_id")
    items = []
    for row in page["items"]:
        if row.get("source_application_id") != source or (target and row.get("target_application_id") != target):
            raise IntegrationPlanError("Route discovery returned a different application scope")
        require_uuid(row.get("target_application_id"), "route target application id")
        if any(type(row.get(key)) is not bool for key in ("is_active", "deleted", "managed", "adoptable")):
            raise IntegrationPlanError("Route discovery lacks explicit eligibility")
        blockers = row.get("blockers")
        if not isinstance(blockers, list) or any(not isinstance(v, str) for v in blockers):
            raise IntegrationPlanError("Invalid route blockers")
        if row["adoptable"] and (not row["is_active"] or row["deleted"] or row["managed"] or blockers):
            raise IntegrationPlanError("Contradictory route adoption eligibility")
        item = {key: row.get(key) for key in ("route_id", "name", "source_application_id", "source_module_key",
                "event_type", "target_application_id", "target_module_key", "is_active", "deleted", "managed", "adoptable")}
        item["blockers"] = [v[:200] for v in blockers]
        items.append(item)
    return {"items": items, "has_more": page["has_more"], "next_cursor": page.get("next_cursor"),
            "inventory_complete": not page["has_more"], "scope": "current-runtime-owned-endpoints"}


def recovery_list(client: PlatformClient, plan_id: str, edge_key: str, *, limit=50, cursor=None) -> dict:
    client.require_self_service()
    if not isinstance(edge_key, str) or KEY_RE.fullmatch(edge_key) is None:
        raise IntegrationPlanError("Invalid recovery edge key")
    query = page_query(limit=limit, cursor=cursor, edge_key=edge_key)
    page = require_page(client.request("GET", recovery_path(plan_id) + query),
                        limit=limit, cursor=cursor, identity="event_record_id")
    if page.get("plan_id") != plan_id or not VERSION_RE.fullmatch(str(page.get("version") or "")):
        raise IntegrationPlanError("Recovery candidates do not match the plan")
    items = []
    for item in page["items"]:
        require_text(item.get("event_id"), "event id", 200)
        if item.get("edge_key") != edge_key or item.get("status") not in {"not_queued", "pending", "failed", "delivering", "delivered"}:
            raise IntegrationPlanError("Invalid recovery candidate")
        items.append({key: item.get(key) for key in (
            "event_id", "event_record_id", "source_sequence", "occurred_at", "edge_key", "delivery_id", "status")})
    readiness = page.get("readiness")
    if not isinstance(readiness, dict) or type(readiness.get("ready")) is not bool:
        raise IntegrationPlanError("Recovery response lacks current readiness")
    gaps = [{key: str(gap.get(key) or "")[:1000] for key in ("code", "edge_key", "message")}
            for gap in readiness.get("gaps") or [] if isinstance(gap, dict)]
    return {"plan_id": plan_id, "version": page["version"],
            "readiness": {"ready": readiness["ready"], "gaps": gaps}, "items": items,
            "has_more": page["has_more"], "next_cursor": page.get("next_cursor"),
            "business_completed": False, "scope": "original-plan-event-window"}


def recovery_request_id(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}", value) is None:
        raise IntegrationPlanError("Recovery request_id must be a stable identifier using letters, digits, dot, colon, underscore or hyphen")
    return value


def validate_recovery(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"version", "request_id", "reason", "items"}:
        raise IntegrationPlanError("Recovery request requires only version, request_id, reason and exact items")
    value = json.loads(canonical_json(value))
    if not isinstance(value["version"], str) or VERSION_RE.fullmatch(value["version"]) is None:
        raise IntegrationPlanError("Invalid expected recovery plan version")
    recovery_request_id(value["request_id"])
    require_text(value["reason"], "recovery reason", 1000)
    if not isinstance(value["items"], list) or not 1 <= len(value["items"]) <= 100:
        raise IntegrationPlanError("Recovery requires 1 to 100 explicit items")
    seen = set()
    for item in value["items"]:
        if not isinstance(item, dict) or set(item) != {"edge_key", "event_id"}:
            raise IntegrationPlanError("Recovery items require only edge_key and event_id")
        if not isinstance(item["edge_key"], str) or KEY_RE.fullmatch(item["edge_key"]) is None:
            raise IntegrationPlanError("Invalid recovery edge key")
        require_text(item["event_id"], "event id", 200)
        identity = (item["edge_key"], item["event_id"])
        if identity in seen:
            raise IntegrationPlanError("Duplicate recovery item")
        seen.add(identity)
    return value


def recovery_digest(payload: dict) -> str:
    # Match the SaaS service digest, which uses ASCII-escaped canonical JSON.
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def safe_recovery_receipt(value: object, plan_id: str, request_id: str, payload=None) -> dict:
    if (not isinstance(value, dict) or value.get("plan_id") != plan_id
            or value.get("request_id") != request_id or value.get("business_completed") is not False
            or not VERSION_RE.fullmatch(str(value.get("version") or ""))
            or not VERSION_RE.fullmatch(str(value.get("request_digest") or ""))
            or not isinstance(value.get("items"), list) or not 1 <= len(value["items"]) <= 100):
        raise IntegrationPlanError("Invalid or mismatched recovery receipt")
    items = []
    seen = set()
    for item in value["items"]:
        if not isinstance(item, dict) or not KEY_RE.fullmatch(str(item.get("edge_key") or "")):
            raise IntegrationPlanError("Invalid recovery receipt item")
        require_text(item.get("event_id"), "receipt event id", 200)
        require_text(item.get("delivery_id"), "receipt delivery id", 240)
        if item.get("status") not in {"pending", "failed", "delivering", "delivered"}:
            raise IntegrationPlanError("Unknown recovery delivery status")
        identity = (item["edge_key"], item["event_id"])
        if identity in seen:
            raise IntegrationPlanError("Duplicate recovery receipt item")
        seen.add(identity)
        items.append({key: item[key] for key in ("edge_key", "event_id", "delivery_id", "status")})
    if payload is not None and (value["request_digest"] != recovery_digest(payload)
            or value["version"] != payload["version"]
            or seen != {(row["edge_key"], row["event_id"]) for row in payload["items"]}):
        raise IntegrationPlanError("Recovery request_id belongs to different content")
    return {"plan_id": plan_id, "request_id": request_id, "version": value["version"],
            "request_digest": value["request_digest"], "items": items, "business_completed": False}


def recovery_status(client: PlatformClient, plan_id: str, request_id: str, *, payload=None) -> dict:
    client.require_self_service()
    path = recovery_path(plan_id) + "/requests/" + quote(recovery_request_id(request_id), safe="")
    try:
        value = client.request("GET", path)
    except RequestRejected as exc:
        if exc.status == 404 and exc.code == "recovery_request_not_found":
            return {"status": "not_found", "plan_id": plan_id, "request_id": request_id,
                    "business_completed": False}
        raise
    return {"status": "found", **safe_recovery_receipt(value, plan_id, request_id, payload)}


def recover(client: PlatformClient, plan_id: str, payload: dict, *, business_intent_confirmed=False) -> dict:
    if business_intent_confirmed is not True:
        raise IntegrationPlanError("Confirm the business recovery scope before queueing existing events")
    payload = validate_recovery(payload)
    existing = recovery_status(client, plan_id, payload["request_id"], payload=payload)
    if existing["status"] == "found":
        return {**existing, "status": "existing"}
    current = get_plan(client, plan_id)
    if current["version"] != payload["version"]:
        raise IntegrationPlanError("Recovery plan version changed; read current candidates and readiness")
    try:
        value = client.request("POST", recovery_path(plan_id), payload)
        try:
            return {"status": "queued", **safe_recovery_receipt(value, plan_id, payload["request_id"], payload)}
        except IntegrationPlanError as exc:
            raise RequestOutcomeUnknown("Incomplete recovery response; reconcile the same request") from exc
    except RequestOutcomeUnknown:
        try:
            status = recovery_status(client, plan_id, payload["request_id"], payload=payload)
            if status["status"] == "found":
                return {**status, "status": "reconciled"}
        except IntegrationPlanError:
            pass
        return {"status": "unknown", "operation": "recover", "plan_id": plan_id,
                "request_id": payload["request_id"], "business_completed": False,
                "next_action": "GET recovery-status using the same request_id; do not change the ID or automatically POST again"}


def safe_catalog(value: object) -> dict:
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] != 1 or not isinstance(value.get("applications"), list):
        raise IntegrationPlanError("Unsupported integration catalog")
    applications = []
    for application in value["applications"]:
        if not isinstance(application, dict):
            raise IntegrationPlanError("Invalid catalog application")
        item = {key: application.get(key) for key in ("id", "slug", "name", "runtime_id", "owned_by_requester")}
        item["modules"] = []
        for module in application.get("modules") or []:
            if not isinstance(module, dict):
                raise IntegrationPlanError("Invalid catalog module")
            item["modules"].append({key: module.get(key) for key in ("key", "name", "publishes", "subscribes")})
        applications.append(item)
    return {"schema_version": 1, "environment": value.get("environment"), "applications": applications}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-profile", type=Path, default=Path("/etc/zhuojian/runtime.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog", help="Read the current enterprise/environment app/module event catalog")
    discovery_parser = commands.add_parser("discover", help="Page through current Runtime participant plans; continue until has_more is false")
    discovery_parser.add_argument("--application-id")
    discovery_parser.add_argument("--limit", type=int, default=50)
    discovery_parser.add_argument("--cursor")
    routes_parser = commands.add_parser("routes", help="Inspect exact owned-endpoint routes and adoption blockers without changes")
    routes_parser.add_argument("--source-application-id", required=True)
    routes_parser.add_argument("--target-application-id")
    routes_parser.add_argument("--limit", type=int, default=50)
    routes_parser.add_argument("--cursor")
    recovery_list_parser = commands.add_parser("recovery-list", help="Read original-plan event candidates without queueing them")
    recovery_list_parser.add_argument("--plan-id", required=True)
    recovery_list_parser.add_argument("--edge-key", required=True)
    recovery_list_parser.add_argument("--limit", type=int, default=50)
    recovery_list_parser.add_argument("--cursor")
    recovery_parser = commands.add_parser("recover", help="Recover an explicit original-window event list under confirmed business scope")
    recovery_parser.add_argument("--plan-id", required=True)
    recovery_parser.add_argument("--request", type=Path, required=True)
    recovery_parser.add_argument("--confirm-business-intent", action="store_true", required=True)
    recovery_status_parser = commands.add_parser("recovery-status", help="Reconcile the same Runtime recovery request without another write")
    recovery_status_parser.add_argument("--plan-id", required=True)
    recovery_status_parser.add_argument("--request-id", required=True)
    proposal_parser = commands.add_parser("propose", help="Create an exact plan; never approve it")
    proposal_parser.add_argument("--plan", type=Path, required=True)
    status_parser = commands.add_parser("status", help="Read a plan without changing its state")
    selector = status_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--plan-id")
    selector.add_argument("--request-id")
    for command in ("apply", "verify"):
        command_parser = commands.add_parser(command)
        command_parser.add_argument("--plan-id", required=True)
        command_parser.add_argument("--version", help="Optional expected opaque server version")
        if command == "verify":
            command_parser.add_argument("--delivery-id", action="append", required=True)
    for command in ("confirm", "reject", "revoke"):
        command_parser = commands.add_parser(command, help="Decide exact owned-endpoint configuration after local business-intent confirmation")
        command_parser.add_argument("--plan-id", required=True)
        command_parser.add_argument("--authorization-digest", required=True)
        command_parser.add_argument("--confirm-business-intent", action="store_true", required=True,
                                    help="Local UX guard after the owner confirms the displayed scope; not an identity or permission proof")
        if command != "confirm":
            command_parser.add_argument("--reason")
    args = parser.parse_args(argv)
    client = PlatformClient.from_runtime(args.runtime_profile)
    client.require_integration_plans()
    if args.command == "catalog":
        result = safe_catalog(client.request("GET", API_ROOT + "/catalog"))
    elif args.command == "discover":
        result = discover(client, application_id=args.application_id, limit=args.limit, cursor=args.cursor)
    elif args.command == "routes":
        result = discover_routes(client, args.source_application_id, target_application_id=args.target_application_id,
                                 limit=args.limit, cursor=args.cursor)
    elif args.command == "recovery-list":
        result = recovery_list(client, args.plan_id, args.edge_key, limit=args.limit, cursor=args.cursor)
    elif args.command == "recover":
        result = recover(client, args.plan_id, load_object(args.request, "recovery request"),
                         business_intent_confirmed=args.confirm_business_intent)
    elif args.command == "recovery-status":
        result = recovery_status(client, args.plan_id, args.request_id)
    elif args.command == "propose":
        result = propose(client, load_object(args.plan, "integration plan"))
    elif args.command == "status":
        plan = get_plan(client, args.plan_id) if args.plan_id else find_request(client, require_text(args.request_id, "request_id", 120))
        result = {"status": "found", **safe_plan_summary(plan)} if plan else {"status": "not_found", "request_id": args.request_id}
    elif args.command == "apply":
        result = apply(client, args.plan_id, args.version)
    elif args.command in {"confirm", "reject", "revoke"}:
        result = runtime_decision(client, args.plan_id, args.authorization_digest, operation=args.command,
                                  business_intent_confirmed=args.confirm_business_intent, reason=getattr(args, "reason", None))
    else:
        result = verify(client, args.plan_id, args.delivery_id, args.version)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if isinstance(result, dict) and result.get("status") in {"unknown", "not_ready", "not_approved", "not_acknowledged", "partially_acknowledged", "not_found", "requester_required"} else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IntegrationPlanError as exc:
        result = {"status": "blocked", "error": str(exc)}
        if isinstance(exc, RequestRejected):
            result.update({"http_status": exc.status, "code": exc.code, "next_action": "read_status"})
        elif isinstance(exc, UnsupportedPlatform):
            code = ("runtime_endpoint_confirmation_not_supported" if isinstance(exc, UnsupportedRuntimeAuthorization)
                    else "integration_self_service_not_supported" if isinstance(exc, UnsupportedSelfService)
                    else "integration_plans_not_supported")
            result.update({"status": "unsupported", "gap": {"owner": "SaaS", "code": code}, "next_action": "continue authorized subsystem preparation; hand off the target environment capability gap"})
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(2)
