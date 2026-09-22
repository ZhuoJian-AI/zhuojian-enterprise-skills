"""Semantic and tool-contract checks shared by source validation and tests."""

from __future__ import annotations

import json
import re
from typing import Any


STABLE_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SUGGESTION_KEY_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,119}$")
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
MODULE_NAVIGATION_THEME_FIELDS = {
    "accentColor",
    "backgroundColor",
    "selectedBackgroundColor",
    "selectedTextColor",
}
AI_SEMANTICS_FIELDS = {
    "purpose",
    "primaryEntities",
    "fieldSemantics",
    "supportedIntents",
    "relatedPages",
    "businessTerms",
    "defaultQueryActionKey",
    "interactionAnchors",
    "defaultInteractionAnchorKey",
    "workflowGuides",
    "proactiveCheck",
}
EXPORT_RESULT_FIELDS = {
    "snapshotId",
    "snapshotAt",
    "columns",
    "rows",
    "rowCount",
    "nextCursor",
}
PLATFORM_AI_CAPABILITIES = {
    "vision.ocr": "image",
    "vision.compare": "image",
    "vision.classify": "image",
    "speech.transcribe": "audio",
    "text.extract": "text",
    "business.predict": "json",
}
PLATFORM_AI_INPUT_KINDS = {"image", "audio", "text", "json"}


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(left: str, right: str) -> float:
    bright, dark = sorted((_relative_luminance(left), _relative_luminance(right)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def validate_navigation_theme(presentation: object) -> list[str]:
    if presentation is None:
        return ["缺少必填的 presentation.moduleNavigationTheme；发布前须登记与业务页面一致的导航主题"]
    if not isinstance(presentation, dict) or set(presentation) != {"moduleNavigationTheme"}:
        return ["presentation 只能声明 moduleNavigationTheme"]
    theme = presentation.get("moduleNavigationTheme")
    if not isinstance(theme, dict) or set(theme) != MODULE_NAVIGATION_THEME_FIELDS:
        return ["moduleNavigationTheme 必须且只能包含四个受控颜色字段"]
    if any(not isinstance(theme[key], str) or not HEX_COLOR_RE.fullmatch(theme[key]) for key in MODULE_NAVIGATION_THEME_FIELDS):
        return ["moduleNavigationTheme 颜色必须使用 #RRGGBB 格式"]
    failures: list[str] = []
    if _contrast_ratio("#475467", theme["backgroundColor"]) < 4.5:
        failures.append("moduleNavigationTheme 普通文字与背景对比度必须至少为 4.5:1")
    if _contrast_ratio(theme["selectedTextColor"], theme["selectedBackgroundColor"]) < 4.5:
        failures.append("moduleNavigationTheme 选中文字与背景对比度必须至少为 4.5:1")
    if min(
        _contrast_ratio(theme["accentColor"], theme["backgroundColor"]),
        _contrast_ratio(theme["accentColor"], theme["selectedBackgroundColor"]),
    ) < 3:
        failures.append("moduleNavigationTheme 选中标识对比度必须至少为 3:1")
    return failures


def _closed_object_schema(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == "object"
        and value.get("additionalProperties") is False
        and isinstance(value.get("properties"), dict)
        and bool(value["properties"])
    )


def validate_permission_policy(policy: object, operation: object) -> list[str]:
    if policy is None:
        return []
    if not isinstance(policy, dict):
        return ["permissionPolicy 必须是对象"]
    if set(policy) - {"group", "mode", "supportedScopes"}:
        return ["permissionPolicy 含未支持字段"]
    mode = policy.get("mode")
    groups = {"public_read": "public_read", "self": "personal", "configurable": "management"}
    if not isinstance(mode, str) or mode not in groups or policy.get("group") != groups[mode]:
        return ["permissionPolicy 分组与模式不匹配"]
    scopes = policy.get("supportedScopes", [])
    supported = {"self", "department", "department_and_children", "custom_departments", "all"}
    if (not isinstance(scopes, list) or len(scopes) > 5
            or any(not isinstance(s, str) or s not in supported for s in scopes)):
        return ["permissionPolicy supportedScopes 无效"]
    if len(scopes) != len(set(scopes)):
        return ["permissionPolicy supportedScopes 不可重复"]
    if (mode == "configurable") != bool(scopes):
        return ["permissionPolicy 固定模式不得配置范围，管理模式必须声明支持范围"]
    if mode == "public_read" and operation != "query":
        return ["permissionPolicy 企业内公开读取仅允许 query"]
    return []


def _bounded_text(value: object, maximum: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum


def _bounded_key(value: object, maximum: int = 160) -> bool:
    return isinstance(value, str) and len(value) <= maximum and bool(STABLE_KEY_RE.fullmatch(value))


def _workflow_notes(value: object, minimum: int = 0) -> bool:
    return (isinstance(value, list) and minimum <= len(value) <= 5
            and all(_bounded_text(item, 400) for item in value))


def validate_workflow_guides(value: object, page_actions: dict[tuple[str, str], set[str]]) -> list[str]:
    """Validate descriptive workflow knowledge, never an executable workflow DSL."""
    if not isinstance(value, list) or len(value) > 3:
        return ["workflowGuides 必须是最多 3 项的列表"]
    errors: list[str] = []
    guide_keys: set[str] = set()
    for guide in value:
        if not isinstance(guide, dict) or set(guide) != {
            "workflowKey", "name", "goal", "whenToUse", "steps", "exceptions",
        }:
            errors.append("workflowGuides 流程必须且只能包含规定的六个字段")
            continue
        key = guide.get("workflowKey")
        if not _bounded_key(key, 120) or key in guide_keys:
            errors.append("workflowGuides workflowKey 必须是唯一且不超过 120 字符的稳定标识")
        else:
            guide_keys.add(key)
        if not all(_bounded_text(guide.get(field), limit) for field, limit in (
            ("name", 120), ("goal", 600), ("whenToUse", 600),
        )) or not _workflow_notes(guide.get("exceptions")):
            errors.append("workflowGuides 名称、目标、适用情况或异常说明超限或无效")
        steps = guide.get("steps")
        if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
            errors.append("workflowGuides steps 必须包含 1..8 个步骤")
            continue
        step_keys: set[str] = set()
        for step in steps:
            if not isinstance(step, dict) or set(step) != {
                "stepKey", "title", "purpose", "moduleKey", "pageKey", "actionKeys",
                "preconditions", "completionCriteria",
            }:
                errors.append("workflowGuides 步骤必须且只能包含规定的八个字段")
                continue
            step_key = step.get("stepKey")
            if not _bounded_key(step_key, 120) or step_key in step_keys:
                errors.append("workflowGuides stepKey 必须在流程内唯一且不超过 120 字符")
            else:
                step_keys.add(step_key)
            if (not _bounded_text(step.get("title"), 120)
                    or not _bounded_text(step.get("purpose"), 400)
                    or not _workflow_notes(step.get("preconditions"))
                    or not _workflow_notes(step.get("completionCriteria"), 1)):
                errors.append("workflowGuides 步骤说明、前提或完成证据无效")
            module_key, page_key = step.get("moduleKey"), step.get("pageKey")
            if (not _bounded_key(module_key, 120) or not _bounded_key(page_key)
                    or (module_key, page_key) not in page_actions):
                errors.append("workflowGuides 步骤必须指向同一 Manifest 的真实模块与页面")
                continue
            action_keys = step.get("actionKeys")
            if (not isinstance(action_keys, list) or len(action_keys) > 8
                    or any(not _bounded_key(item) for item in action_keys)
                    or len(set(action_keys)) != len(action_keys)
                    or not set(action_keys) <= page_actions[(module_key, page_key)]):
                errors.append("workflowGuides actionKeys 必须唯一且属于步骤目标页面的真实 Action")
    if not errors:
        try:
            if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > 32768:
                errors.append("workflowGuides JSON UTF-8 总量不得超过 32 KiB")
        except (TypeError, ValueError, UnicodeError):
            errors.append("workflowGuides 必须是有效 UTF-8 JSON")
    return errors


def validate_proactive_check(value: object, page_action_keys: list, actions: dict) -> list[str]:
    """An explicitly opted-in current-page check is a regular authorized read."""
    if (not isinstance(value, dict) or set(value) - {"actionKey", "intervalSeconds"}
            or not _bounded_key(value.get("actionKey"))):
        return ["proactiveCheck 只能声明 actionKey 和可选 intervalSeconds"]
    interval = value.get("intervalSeconds", 90)
    if type(interval) is not int or not 60 <= interval <= 600:
        return ["proactiveCheck intervalSeconds 必须为 60..600 的整数，省略时为 90"]
    key = value["actionKey"]
    action = actions.get(key)
    if (key not in page_action_keys or not isinstance(action, dict)
            or action.get("operation") != "query" or action.get("aiEnabled") is not True
            or action.get("requiresConfirmation") is not False
            or action.get("platformAiCapability") is not None):
        return ["proactiveCheck 必须绑定本页 AI 可用、无确认、无 platformAiCapability 的只读 query"]
    schema = action.get("inputSchema")
    if (not isinstance(schema, dict) or schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
            or not isinstance(schema.get("properties"), dict)
            or set(schema["properties"]) != {"context"}
            or schema.get("required") != ["context"]):
        return ["proactiveCheck inputSchema 必须是仅含必填 context 的封闭对象"]
    context = schema["properties"]["context"]
    if (not isinstance(context, dict) or context.get("type") != "object"
            or not isinstance(context.get("properties", {}), dict)
            or set(context.get("properties", {})) - {
                "route", "entity_type", "entity_id", "filters", "selection", "data_version",
            }):
        return ["proactiveCheck context 必须是当前业务上下文对象，不得声明身份、URL 或自由参数"]
    return []


def validate_assistant_check_result(value: object) -> list[str]:
    """Check an actual result.assistantCheck in local business contract tests.

    Manifest/source validation never executes a business query to obtain it.
    Runtime SaaS validation remains authoritative and must recheck permissions.
    """
    if not isinstance(value, dict) or set(value) != {"version", "dataVersion", "summary", "suggestions"}:
        return ["assistantCheck 必须且只能包含 version/dataVersion/summary/suggestions"]
    if (type(value["version"]) is not int or value["version"] != 1
            or not _bounded_text(value["dataVersion"], 160)
            or not _bounded_text(value["summary"], 400)):
        return ["assistantCheck 版本、数据版本或摘要无效"]
    suggestions = value["suggestions"]
    if not isinstance(suggestions, list) or len(suggestions) > 3:
        return ["assistantCheck suggestions 必须为 0..3 条"]
    seen: set[str] = set()
    for item in suggestions:
        if not isinstance(item, dict) or set(item) != {"id", "revision", "title", "summary", "goal"}:
            return ["assistantCheck 建议只允许规定的五个字段"]
        if (any(not isinstance(item[key], str) or not SUGGESTION_KEY_RE.fullmatch(item[key])
                for key in ("id", "revision"))
                or item["id"] in seen
                or not all(_bounded_text(item[key], limit)
                           for key, limit in (("title", 80), ("summary", 400), ("goal", 2000)))):
            return ["assistantCheck 建议 ID、版本或文本无效，ID 不得重复"]
        seen.add(item["id"])
    try:
        if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > 16384:
            return ["assistantCheck JSON UTF-8 总量不得超过 16 KiB"]
    except (TypeError, ValueError, UnicodeError):
        return ["assistantCheck 必须是有效 UTF-8 JSON"]
    return []


def validate_manifest_semantics(manifest: object, *, require_semantics: bool) -> list[str]:
    if not isinstance(manifest, dict):
        return ["subsystem.json 根节点必须是对象"]
    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        return ["v2.5 subsystem.json 必须声明非空 modules"] if require_semantics else []

    failures: list[str] = validate_navigation_theme(manifest.get("presentation"))
    page_index: set[tuple[str, str]] = set()
    page_actions: dict[tuple[str, str], set[str]] = {}
    for module in modules:
        if not isinstance(module, dict):
            continue
        module_key = str(module.get("moduleKey") or "")
        actual_actions = {action.get("actionKey") for action in module.get("actions") or []
                          if isinstance(action, dict) and isinstance(action.get("actionKey"), str)}
        for page in module.get("pages") or []:
            if isinstance(page, dict):
                target = (module_key, str(page.get("pageKey") or ""))
                page_index.add(target)
                page_actions[target] = {key for key in page.get("actionKeys") or []
                                        if isinstance(key, str) and key in actual_actions}

    for module in modules:
        if not isinstance(module, dict):
            failures.append("modules 只能包含对象")
            continue
        module_key = str(module.get("moduleKey") or "")
        actions = {
            str(action.get("actionKey") or ""): action
            for action in module.get("actions") or []
            if isinstance(action, dict)
        }
        proactive_action_keys: set[str] = set()
        if require_semantics:
            action_meanings: dict[tuple[str, str], str] = {}
            for action_key, action in actions.items():
                if not action.get("aiEnabled"):
                    continue
                operation = str(action.get("operation") or "")
                meaning = re.sub(
                    r"\s+",
                    " ",
                    str(action.get("description") or action.get("name") or "").strip().casefold(),
                )
                if not meaning:
                    failures.append(f"Action {action_key} 缺少可区分的 name 或 description")
                    continue
                fingerprint = (operation, meaning)
                if fingerprint in action_meanings:
                    failures.append(
                        f"Action {action_key} 与 {action_meanings[fingerprint]} 的操作语义重复，"
                        "请合并或明确区分"
                    )
                else:
                    action_meanings[fingerprint] = action_key
        pages = [page for page in module.get("pages") or [] if isinstance(page, dict)]
        for page in pages:
            page_key = str(page.get("pageKey") or "")
            label = f"页面 {module_key}/{page_key}"
            semantics = page.get("aiSemantics")
            if semantics is None and require_semantics:
                failures.append(f"{label} 缺少 aiSemantics")
                continue
            if semantics is None:
                continue
            if not isinstance(semantics, dict):
                failures.append(f"{label} aiSemantics 必须是对象")
                continue
            unknown = sorted(set(semantics) - AI_SEMANTICS_FIELDS)
            if unknown:
                failures.append(f"{label} aiSemantics 含未支持字段：{', '.join(unknown)}")
            if "workflowGuides" in semantics:
                failures.extend(f"{label} {error}" for error in validate_workflow_guides(
                    semantics["workflowGuides"], page_actions,
                ))
            if "proactiveCheck" in semantics:
                check_errors = validate_proactive_check(
                    semantics["proactiveCheck"], page.get("actionKeys") or [], actions,
                )
                failures.extend(f"{label} {error}" for error in check_errors)
                if not check_errors:
                    proactive_action_keys.add(semantics["proactiveCheck"]["actionKey"])
            purpose = semantics.get("purpose")
            if not isinstance(purpose, str) or not purpose.strip():
                failures.append(f"{label} aiSemantics.purpose 不能为空")
            entities = semantics.get("primaryEntities")
            if (
                not isinstance(entities, list)
                or not entities
                or any(not isinstance(item, str) or not STABLE_KEY_RE.fullmatch(item) for item in entities)
                or len(set(entities)) != len(entities)
            ):
                failures.append(f"{label} aiSemantics.primaryEntities 必须是非空且唯一的稳定标识")
            supported = semantics.get("supportedIntents")
            if (
                not isinstance(supported, list)
                or not supported
                or any(not isinstance(item, str) or not item.strip() for item in supported)
            ):
                failures.append(f"{label} aiSemantics.supportedIntents 必须列出可回答的问题")
            for collection, key_name, meaning_name in (
                (semantics.get("fieldSemantics", []), "field", "meaning"),
                (semantics.get("businessTerms", []), "term", "meaning"),
            ):
                if not isinstance(collection, list) or any(
                    not isinstance(item, dict)
                    or set(item) != {key_name, meaning_name}
                    or not str(item.get(key_name) or "").strip()
                    or not str(item.get(meaning_name) or "").strip()
                    for item in collection
                ):
                    failures.append(f"{label} 的 {key_name} 语义声明格式无效")
            related = semantics.get("relatedPages", [])
            if not isinstance(related, list):
                failures.append(f"{label} aiSemantics.relatedPages 必须是列表")
            else:
                seen_related: set[tuple[str, str]] = set()
                for item in related:
                    if not isinstance(item, dict) or set(item) != {"moduleKey", "pageKey", "relationship"}:
                        failures.append(f"{label} 包含格式无效的关联页面")
                        continue
                    target = (str(item.get("moduleKey") or ""), str(item.get("pageKey") or ""))
                    if target == (module_key, page_key) or target in seen_related or target not in page_index:
                        failures.append(f"{label} 关联了自身、重复或不存在的页面 {target[0]}/{target[1]}")
                    if not str(item.get("relationship") or "").strip():
                        failures.append(f"{label} 的关联页面缺少 relationship")
                    seen_related.add(target)
            default_query = str(semantics.get("defaultQueryActionKey") or "")
            page_action_keys = page.get("actionKeys") or []
            if not default_query:
                failures.append(f"{label} 缺少 aiSemantics.defaultQueryActionKey")
            elif (
                default_query not in page_action_keys
                or default_query not in actions
                or actions[default_query].get("operation") != "query"
            ):
                failures.append(f"{label} defaultQueryActionKey 未指向本页 query Action")

            anchors = semantics.get("interactionAnchors")
            anchor_keys: set[str] = set()
            mapped_actions: set[str] = set()
            if not isinstance(anchors, list) or not anchors or len(anchors) > 100:
                failures.append(f"{label} 缺少非空且有界的 aiSemantics.interactionAnchors")
            else:
                for anchor in anchors:
                    if not isinstance(anchor, dict) or set(anchor) != {
                        "anchorKey", "name", "description", "actionKeys",
                    }:
                        failures.append(f"{label} 包含格式无效的交互锚点")
                        continue
                    anchor_key = str(anchor.get("anchorKey") or "")
                    anchor_name = str(anchor.get("name") or "")
                    description = str(anchor.get("description") or "")
                    anchor_actions = anchor.get("actionKeys")
                    if (
                        not STABLE_KEY_RE.fullmatch(anchor_key)
                        or anchor_key in anchor_keys
                        or not anchor_name.strip()
                        or not description.strip()
                        or not isinstance(anchor_actions, list)
                        or not anchor_actions
                        or len(anchor_actions) > 30
                        or any(
                            not isinstance(action_key, str) or not STABLE_KEY_RE.fullmatch(action_key)
                            for action_key in anchor_actions
                        )
                        or len(set(anchor_actions)) != len(anchor_actions)
                    ):
                        failures.append(f"{label} 包含无效或重复的交互锚点 {anchor_key or '<empty>'}")
                        continue
                    anchor_keys.add(anchor_key)
                    for action_key in anchor_actions:
                        if (
                            not isinstance(action_key, str)
                            or action_key not in page_action_keys
                            or action_key not in actions
                            or not actions[action_key].get("aiEnabled")
                            or action_key in mapped_actions
                        ):
                            failures.append(
                                f"{label} 交互锚点 {anchor_key} 必须唯一绑定本页 AI Action"
                            )
                            continue
                        mapped_actions.add(action_key)
            default_anchor = str(semantics.get("defaultInteractionAnchorKey") or "")
            if not default_anchor or default_anchor not in anchor_keys:
                failures.append(f"{label} defaultInteractionAnchorKey 未指向本页交互锚点")
            required_anchor_actions = {
                action_key
                for action_key in page_action_keys
                if action_key in actions and actions[action_key].get("aiEnabled")
            }
            missing_anchor_actions = sorted(required_anchor_actions - mapped_actions)
            if missing_anchor_actions:
                failures.append(
                    f"{label} 的 AI Action 未登记交互锚点：{', '.join(missing_anchor_actions)}"
                )

        for action_key, action in actions.items():
            failures.extend(
                f"Action {action_key} {error}"
                for error in validate_permission_policy(action.get("permissionPolicy"), action.get("operation"))
            )
            platform_ai = action.get("platformAiCapability")
            if platform_ai is not None:
                if not require_semantics:
                    failures.append(
                        f"Action {action_key} 的 platformAiCapability 只能用于 v2.5"
                    )
                elif not isinstance(platform_ai, dict):
                    failures.append(f"Action {action_key} platformAiCapability 必须是对象")
                else:
                    unknown = set(platform_ai) - {
                        "type", "inputKinds", "humanConfirmation",
                    }
                    capability = platform_ai.get("type")
                    input_kinds = platform_ai.get("inputKinds")
                    if unknown:
                        failures.append(
                            f"Action {action_key} platformAiCapability 含未支持字段"
                        )
                    if capability not in PLATFORM_AI_CAPABILITIES:
                        failures.append(f"Action {action_key} 声明了不支持的平台 AI 能力")
                    if (
                        not isinstance(input_kinds, list)
                        or not input_kinds
                        or len(input_kinds) > 4
                        or any(
                            not isinstance(kind, str)
                            or kind not in PLATFORM_AI_INPUT_KINDS
                            for kind in input_kinds
                        )
                        or len(set(input_kinds)) != len(input_kinds)
                    ):
                        failures.append(f"Action {action_key} 的平台 AI inputKinds 无效")
                    elif (
                        capability in PLATFORM_AI_CAPABILITIES
                        and PLATFORM_AI_CAPABILITIES[capability] not in input_kinds
                    ):
                        failures.append(
                            f"Action {action_key} 的 inputKinds 缺少 "
                            f"{PLATFORM_AI_CAPABILITIES[capability]}"
                        )
                    if platform_ai.get("humanConfirmation") != "required":
                        failures.append(f"Action {action_key} 的平台 AI 结果必须人工确认")
                    if action.get("operation") != "query" or not action.get("aiEnabled"):
                        failures.append(
                            f"Action {action_key} 的平台 AI 能力必须是 AI 可用的 query"
                        )
            if not action.get("aiEnabled"):
                continue
            # v2.4 remains a maintained compatibility contract.  The closed
            # schemas, bounded queries and dataset export shape are new v2.5
            # requirements and must not silently turn a Skill update into a
            # contract migration for an existing v2.4 subsystem.
            if not require_semantics:
                continue
            input_schema = action.get("inputSchema")
            result_schema = action.get("resultSchema")
            if not _closed_object_schema(input_schema):
                failures.append(f"Action {action_key} inputSchema 必须是非空封闭对象 Schema")
            if not _closed_object_schema(result_schema):
                failures.append(f"Action {action_key} resultSchema 必须是非空封闭对象 Schema")
            operation = action.get("operation")
            if (
                operation in {"query", "export"}
                and platform_ai is None
                and action_key not in proactive_action_keys
                and isinstance(input_schema, dict)
            ):
                limit = (input_schema.get("properties") or {}).get("limit")
                if (
                    not isinstance(limit, dict)
                    or limit.get("type") != "integer"
                    or not isinstance(limit.get("maximum"), int)
                    or limit["maximum"] > 500
                ):
                    failures.append(f"Action {action_key} 必须提供 maximum 不超过 500 的 limit")
            if operation == "export" and isinstance(result_schema, dict):
                properties = result_schema.get("properties") or {}
                required = set(result_schema.get("required") or [])
                if set(properties) != EXPORT_RESULT_FIELDS or required != EXPORT_RESULT_FIELDS:
                    failures.append(f"Action {action_key} 必须返回标准分页数据集字段")
    return failures
