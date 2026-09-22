"""Validate a local AI delivery handoff, not runtime configuration or live evidence.

Only checks document structure, declared status consistency and Manifest references.
Never resolves evidenceRefs, contacts services, authorizes actions or changes files.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re


DISCLAIMER = (
    "Structural validation only; evidence contents, live authorization, deployment, "
    "business correctness and end-to-end behavior (including background triggers) "
    "must be independently reviewed. This document does not authorize or execute work."
)
ROOT_FIELDS = {"schemaVersion", "applicationSlug", "scope", "scopeReason", "journeys"}
JOURNEY_FIELDS = {
    "id", "title", "baseline", "target", "ownerDecision", "entryPoint", "delivery",
    "reason", "bindings", "platformChecks", "confirmation", "acceptance", "gaps",
}
DELEGATION_FIELDS = {
    "actorRef", "scope", "expiresAt", "revocation", "limits", "approvalEvidence", "timezone",
}
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")
WRITES = {"create", "update", "delete", "approve"}


class _Checks:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def obj(self, value: object, path: str, fields: set[str], optional: set[str] | None = None) -> dict:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        for field in sorted(fields - value.keys()):
            self.error(f"{path}.{field}", "is required")
        if value.keys() - (fields | (optional or set())):
            self.error(path, "contains unsupported fields")
        return value

    def text(self, value: object, path: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a nonempty string")
            return False
        return True

    def enum(self, value: object, path: str, choices: set[str]) -> bool:
        if not isinstance(value, str) or value not in choices:
            self.error(path, f"must be one of {', '.join(sorted(choices))}")
            return False
        return True

    def array(self, value: object, path: str, *, nonempty: bool = False) -> list:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        if nonempty and not value:
            self.error(path, "must not be empty")
        return value

    def evidence(self, value: object, path: str, *, required: bool = False) -> None:
        for index, item in enumerate(self.array(value, path, nonempty=required)):
            self.text(item, f"{path}[{index}]")


def _index(items: object, key: str, path: str, checks: _Checks) -> dict[str, dict]:
    result = {}
    for index, item in enumerate(checks.array(items, path)):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            checks.error(item_path, "must be an object")
        elif checks.text(item.get(key), f"{item_path}.{key}"):
            identifier = item[key]
            if identifier in result:
                checks.error(f"{item_path}.{key}", "must be unique within its parent")
            else:
                result[identifier] = item
    return result


def _manifest_index(manifest: dict, checks: _Checks) -> dict[str, tuple[dict, dict]]:
    modules = _index(manifest.get("modules"), "moduleKey", "manifest.modules", checks)
    result = {}
    for index, (key, module) in enumerate(modules.items()):
        path = f"manifest.modules[{index}]"
        pages = _index(module.get("pages"), "pageKey", f"{path}.pages", checks)
        actions = _index(module.get("actions"), "actionKey", f"{path}.actions", checks)
        for page_index, page in enumerate(pages.values()):
            action_keys = checks.array(page.get("actionKeys"), f"{path}.pages[{page_index}].actionKeys")
            for action_index, action_key in enumerate(action_keys):
                checks.text(action_key, f"{path}.pages[{page_index}].actionKeys[{action_index}]")
        result[key] = (pages, actions)
    return result


def _bindings(items: list, modules: dict, path: str, checks: _Checks) -> None:
    seen = set()
    for index, value in enumerate(items):
        item_path = f"{path}[{index}]"
        item = checks.obj(value, item_path, {"moduleKey", "pageKey", "actionKey"})
        valid = [checks.text(item.get(key), f"{item_path}.{key}") for key in ("moduleKey", "pageKey", "actionKey")]
        if not all(valid):
            continue
        module_key, page_key, action_key = (item[key] for key in ("moduleKey", "pageKey", "actionKey"))
        identity = (module_key, page_key, action_key)
        if identity in seen:
            checks.error(item_path, "duplicate binding")
        seen.add(identity)
        pages, actions = modules.get(module_key, ({}, {}))
        page, action = pages.get(page_key), actions.get(action_key)
        if page is None or action is None:
            checks.error(item_path, "must reference a real page and Action in the same Manifest module")
            continue
        if not isinstance(page.get("actionKeys"), list) or action_key not in page["actionKeys"]:
            checks.error(item_path, "Action is not registered in this page.actionKeys")
        if action.get("aiEnabled") is not True:
            checks.error(item_path, "Action must have aiEnabled=true")
        operation = action.get("operation")
        if checks.enum(operation, f"{item_path}.manifest.operation", WRITES | {"query", "export"}):
            if operation in WRITES and action.get("requiresConfirmation") is not True:
                checks.error(item_path, "assisted write Action must have requiresConfirmation=true")


def _delegation(value: object, path: str, checks: _Checks) -> None:
    item = checks.obj(value, path, DELEGATION_FIELDS)
    for field in sorted(DELEGATION_FIELDS - {"timezone"}):
        checks.text(item.get(field), f"{path}.{field}")
    checks.enum(item.get("timezone"), f"{path}.timezone", {"Asia/Shanghai"})
    expires = item.get("expiresAt")
    if isinstance(expires, str):
        try:
            if not RFC3339.fullmatch(expires):
                raise ValueError("invalid RFC3339")
            parsed = datetime.fromisoformat(expires.upper().replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError("missing offset")
        except ValueError:
            checks.error(f"{path}.expiresAt", "must be a timezone-aware RFC3339 date-time; expiry is not checked against now")


def _journey(value: object, path: str, modules: dict, checks: _Checks, require_verified: bool) -> str | None:
    item = checks.obj(value, path, JOURNEY_FIELDS, {"delegation"})
    for field in ("id", "title", "baseline", "target", "reason", "confirmation"):
        checks.text(item.get(field), f"{path}.{field}")
    checks.enum(item.get("ownerDecision"), f"{path}.ownerDecision", {"proposed", "confirmed", "declined"})
    checks.enum(item.get("entryPoint"), f"{path}.entryPoint", {"on_demand", "in_page", "background"})
    checks.enum(item.get("delivery"), f"{path}.delivery", {"planned", "blocked", "verified", "not_applicable"})
    verified = item.get("delivery") == "verified"
    if require_verified and item.get("delivery") in ("planned", "blocked"):
        checks.error(f"{path}.delivery", "is not verified")
    if verified and item.get("ownerDecision") != "confirmed":
        checks.error(f"{path}.ownerDecision", "verified delivery requires confirmed requirements, not operational permission")
    bindings = checks.array(item.get("bindings"), f"{path}.bindings", nonempty=verified)
    if item.get("delivery") == "not_applicable":
        if bindings:
            checks.error(path, "not_applicable requires empty bindings")
        if require_verified and item.get("ownerDecision") == "proposed":
            checks.error(f"{path}.ownerDecision", "completed not_applicable outcome requires confirmed design or explicit decline")
    elif item.get("ownerDecision") == "declined":
        checks.error(path, "declined requirements must remain not_applicable")
    _bindings(bindings, modules, f"{path}.bindings", checks)

    platform_checks = checks.array(item.get("platformChecks"), f"{path}.platformChecks", nonempty=verified)
    for index, value in enumerate(platform_checks):
        entry_path = f"{path}.platformChecks[{index}]"
        entry = checks.obj(value, entry_path, {"capability", "contractRef", "deployed", "tenantEnabled", "actorAuthorized", "evidenceRefs"})
        for field in ("capability", "contractRef"):
            checks.text(entry.get(field), f"{entry_path}.{field}")
        for field in ("deployed", "tenantEnabled", "actorAuthorized"):
            checks.enum(entry.get(field), f"{entry_path}.{field}", {"yes", "no", "unknown"})
            if verified and entry.get(field) != "yes":
                checks.error(f"{entry_path}.{field}", "verified delivery requires yes with reviewed evidence")
        checks.evidence(entry.get("evidenceRefs"), f"{entry_path}.evidenceRefs", required=verified)

    cases = checks.array(item.get("acceptance"), f"{path}.acceptance", nonempty=verified)
    for index, value in enumerate(cases):
        entry_path = f"{path}.acceptance[{index}]"
        entry = checks.obj(value, entry_path, {"scenario", "status", "evidenceRefs"})
        checks.text(entry.get("scenario"), f"{entry_path}.scenario")
        checks.enum(entry.get("status"), f"{entry_path}.status", {"pass", "fail", "not_run"})
        if verified and entry.get("status") != "pass":
            checks.error(f"{entry_path}.status", "verified delivery requires pass with reviewed evidence")
        checks.evidence(entry.get("evidenceRefs"), f"{entry_path}.evidenceRefs", required=verified)

    for index, value in enumerate(checks.array(item.get("gaps"), f"{path}.gaps")):
        entry_path = f"{path}.gaps[{index}]"
        entry = checks.obj(value, entry_path, {"owner", "problem", "acceptance", "fallback", "status", "evidenceRefs"})
        for field in ("problem", "acceptance", "fallback"):
            checks.text(entry.get(field), f"{entry_path}.{field}")
        checks.enum(entry.get("owner"), f"{entry_path}.owner", {"SaaS", "Skill", "subsystem"})
        checks.enum(entry.get("status"), f"{entry_path}.status", {"open", "closed"})
        if verified and entry.get("status") != "closed":
            checks.error(f"{entry_path}.status", "verified delivery cannot have open gaps")
        checks.evidence(entry.get("evidenceRefs"), f"{entry_path}.evidenceRefs", required=verified)
    if "delegation" in item or (verified and item.get("entryPoint") == "background"):
        _delegation(item.get("delegation"), f"{path}.delegation", checks)
    return item.get("id") if isinstance(item.get("id"), str) else None


def validate_delivery(
    delivery: object,
    manifest: object,
    require_verified: bool = False,
    journey_ids: list[str] | None = None,
) -> list[str]:
    """Check all structure; optionally require only selected journeys to be verified.

    Selection never suppresses malformed entries or validates evidence contents.
    An empty result does not prove actual delivery or consent.
    """
    checks = _Checks()
    selected = None
    if journey_ids is not None:
        if not require_verified:
            checks.error("journey_ids", "requires require_verified=true")
        selected = set()
        for index, identifier in enumerate(checks.array(journey_ids, "journey_ids", nonempty=True)):
            if checks.text(identifier, f"journey_ids[{index}]"):
                selected.add(identifier)
    document = checks.obj(delivery, "delivery", ROOT_FIELDS)
    if type(document.get("schemaVersion")) is not int or document.get("schemaVersion") != 1:
        checks.error("delivery.schemaVersion", "must be integer 1")
    checks.text(document.get("applicationSlug"), "delivery.applicationSlug")
    checks.text(document.get("scopeReason"), "delivery.scopeReason")
    checks.enum(document.get("scope"), "delivery.scope", {"business_change", "out_of_scope"})
    if not isinstance(manifest, dict):
        checks.error("manifest", "must be an object")
        manifest = {}
    checks.text(manifest.get("applicationSlug"), "manifest.applicationSlug")
    if document.get("applicationSlug") != manifest.get("applicationSlug"):
        checks.error("delivery.applicationSlug", "must match manifest.applicationSlug")
    modules = _manifest_index(manifest, checks)
    journeys = checks.array(document.get("journeys"), "delivery.journeys", nonempty=document.get("scope") == "business_change")
    if document.get("scope") == "out_of_scope" and journeys:
        checks.error("delivery.journeys", "out_of_scope must have no journeys")
    seen = set()
    for index, value in enumerate(journeys):
        path = f"delivery.journeys[{index}]"
        selected_entry = selected is None or (
            isinstance(value, dict)
            and isinstance(value.get("id"), str)
            and value["id"] in selected
        )
        identifier = _journey(value, path, modules, checks, require_verified and selected_entry)
        if identifier in seen:
            checks.error(f"{path}.id", "must be unique")
        seen.add(identifier)
    if selected is not None and selected - seen:
        checks.error("journey_ids", "contains IDs not present in delivery.journeys")
    return checks.errors


def _report(errors: list[str]) -> None:
    print(json.dumps({"valid": not errors, "errors": errors, "disclaimer": DISCLAIMER}, ensure_ascii=True))


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        _report(["arguments: invalid arguments; use --help for usage"])
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description=__doc__)
    parser.add_argument("--delivery", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--require-verified", action="store_true")
    parser.add_argument(
        "--journey", dest="journey_ids", action="append", metavar="ID",
        help="With --require-verified, require completion only for these journey IDs; "
        "repeatable. All document structure is still checked.",
    )
    args = parser.parse_args(argv)
    documents = {}
    for name in ("delivery", "manifest"):
        try:
            documents[name] = json.loads(getattr(args, name).read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, ValueError, RecursionError) as exc:
            _report([f"{name}: cannot read UTF-8 JSON ({type(exc).__name__})"])
            return 2
    errors = validate_delivery(documents["delivery"], documents["manifest"], args.require_verified, args.journey_ids)
    _report(errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
