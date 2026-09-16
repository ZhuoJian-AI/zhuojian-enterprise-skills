"""Read-only declaration audit. Never migrates grants or business data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from manifest_semantics import validate_permission_policy


def action_index(manifest: dict) -> dict[tuple[str, str], dict]:
    return {
        (module["moduleKey"], action["actionKey"]): action
        for module in manifest.get("modules", [])
        for action in module.get("actions", [])
    }


def audit(current: dict, baseline: dict | None = None) -> dict:
    old = action_index(baseline or {})
    new = action_index(current)
    errors, legacy, changes = [], [], []
    for key, action in sorted(new.items()):
        label = "/".join(key)
        policy = action.get("permissionPolicy")
        if policy is None:
            (legacy if key in old else errors).append(label + ": 范围未声明")
        else:
            errors.extend(label + ": " + message for message in validate_permission_policy(policy, action.get("operation")))
        if key not in old:
            changes.append({"resource": label, "status": "新增，核对授权"})
        elif action != old[key]:
            changes.append({"resource": label, "status": "已改变，人工核对语义与范围"})
    changes.extend({"resource": "/".join(key), "status": "移除，核对旧入口"} for key in sorted(old.keys() - new.keys()))
    return {"errors": errors, "legacyUpgradeRequired": legacy, "changes": changes,
            "runtimeVerificationRequired": True, "grantsModified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    report = audit(json.loads(args.current.read_text(encoding="utf-8")),
                   json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
