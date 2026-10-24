#!/usr/bin/env python3
"""Use a Runtime-bound integration plan without exposing its registration key.

The helper never approves a plan, changes roles, or performs business test writes.
All HTTP endpoints and domain fields are supplied by the published SaaS contract.
"""

from __future__ import annotations

import argparse
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
EDGE_FIELDS = {
    "key", "source_application_id", "source_module_key", "target_application_id",
    "target_module_key", "event_type", "kind",
}
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
    if not isinstance(proposal, dict) or set(proposal) != PROPOSAL_FIELDS:
        raise IntegrationPlanError("Plan must contain only the published proposal fields")
    proposal = json.loads(canonical_json(proposal))
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
        if not isinstance(edge, dict) or set(edge) != EDGE_FIELDS:
            raise IntegrationPlanError("Edge must contain only the published edge fields")
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
    return value


def proposal_from_plan(plan: dict) -> dict:
    result = {field: plan.get(field) for field in PROPOSAL_FIELDS - {"edges"}}
    if not isinstance(plan.get("edges"), list):
        raise IntegrationPlanError("Platform plan lacks exact edges")
    if not all(isinstance(edge, dict) for edge in plan["edges"]):
        raise IntegrationPlanError("Platform plan contains an invalid edge")
    result["edges"] = [{key: edge.get(key) for key in EDGE_FIELDS} for edge in plan["edges"]]
    return validate_proposal(result)


def require_unchanged(before: dict, after: dict) -> dict:
    require_plan(after, before["id"])
    if after["spec_digest"] != before["spec_digest"]:
        raise IntegrationPlanError("Platform plan specification changed")
    return after


def safe_plan_summary(plan: dict) -> dict:
    """Print only contract metadata, references and bounded gap explanations."""
    require_plan(plan)
    summary = {key: plan.get(key) for key in (
        "id", "request_id", "version", "spec_digest", "authorization_status",
        "configuration_status", "configuration_lease_expired", "transport_status",
        "business_status", "apply_expires_at",
    )}
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


def apply(client: PlatformClient, plan_id: str, expected_version: str | None = None) -> dict:
    plan = get_plan(client, plan_id)
    if expected_version is not None and expected_version != plan["version"]:
        raise IntegrationPlanError("Plan version changed; read and review the current plan")
    if plan["authorization_status"] != "approved":
        return {"status": "not_approved", **safe_plan_summary(plan), "next_action": "Use the normal approval URL; continue authorized subsystem implementation and hand off exact gaps"}
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
    args = parser.parse_args(argv)
    client = PlatformClient.from_runtime(args.runtime_profile)
    client.require_integration_plans()
    if args.command == "catalog":
        result = safe_catalog(client.request("GET", API_ROOT + "/catalog"))
    elif args.command == "propose":
        result = propose(client, load_object(args.plan, "integration plan"))
    elif args.command == "status":
        plan = get_plan(client, args.plan_id) if args.plan_id else find_request(client, require_text(args.request_id, "request_id", 120))
        result = {"status": "found", **safe_plan_summary(plan)} if plan else {"status": "not_found", "request_id": args.request_id}
    elif args.command == "apply":
        result = apply(client, args.plan_id, args.version)
    else:
        result = verify(client, args.plan_id, args.delivery_id, args.version)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if isinstance(result, dict) and result.get("status") in {"unknown", "not_ready", "not_approved", "not_acknowledged", "partially_acknowledged", "not_found"} else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IntegrationPlanError as exc:
        result = {"status": "blocked", "error": str(exc)}
        if isinstance(exc, RequestRejected):
            result.update({"http_status": exc.status, "code": exc.code, "next_action": "read_status"})
        elif isinstance(exc, UnsupportedPlatform):
            result.update({"status": "unsupported", "gap": {"owner": "SaaS", "code": "integration_plans_not_supported"}, "next_action": "continue authorized subsystem preparation; hand off the target environment capability gap"})
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(2)
