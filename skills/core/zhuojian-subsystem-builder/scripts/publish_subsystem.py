#!/usr/bin/env python3
"""Publish a healthy local-Git subsystem release into ZhuoJian SaaS."""

from __future__ import annotations

import argparse
import contextlib
import functools
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener
from urllib.request import HTTPRedirectHandler
from uuid import UUID

try:
    from contract_versions import require_supported_contract_revision
except ModuleNotFoundError:  # imported as scripts.publish_subsystem in tests
    from scripts.contract_versions import require_supported_contract_revision
try:
    from manifest_semantics import checkbox_permission_report, validate_navigation_theme
except ModuleNotFoundError:  # imported as scripts.publish_subsystem in tests
    from scripts.manifest_semantics import checkbox_permission_report, validate_navigation_theme

try:  # Linux production dependency; Windows remains usable for --help/tests.
    import fcntl
except ImportError:  # pragma: no cover - Windows development host
    fcntl = None


RUNTIME_LOCK_FILE = Path("/run/lock/zhuojian-runtime-admin.lock")
CANONICAL_ENTERPRISE_KEY = "alphabet"
ORIGIN_ADOPTION_CONTRACT = "registered-application-origin-adoption-v1"
ORIGIN_REGISTRATION_CAPABILITY = {
    "supported": True, "version": 1, "scope": "exact-existing-managed-application-origin",
    "lookupEndpoint": "/api/v1/ecs-publisher/modules/{application_slug}",
    "crossRuntime": "inactive-same-organization-environment-healthy-replay", "preservesApplicationIdentity": True,
}


class OriginNoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical_enterprise_key(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return CANONICAL_ENTERPRISE_KEY if normalized == "aifabei" else normalized


def require_publishable_navigation_theme(manifest: dict) -> None:
    failures = validate_navigation_theme(manifest.get("presentation"))
    if failures:
        raise SystemExit("模块导航主题未通过发布校验：\n- " + "\n- ".join(failures))


@contextlib.contextmanager
def runtime_locked(path: Path = RUNTIME_LOCK_FILE) -> Iterator[None]:
    """Serialize publication with every Runtime deploy/rollback command."""

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise SystemExit(f"无法获取 Runtime 发布锁: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit("Runtime 发布锁必须是普通文件")
        if os.name != "nt" and (info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600):
            raise SystemExit("Runtime 发布锁必须由 root 持有且权限为 0600")
        if fcntl is None:
            raise SystemExit("发布只能在支持文件锁的 Linux Runtime 上执行")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def with_runtime_lock(function):
    """Keep --help portable while locking every real publication end to end."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if any(value in {"-h", "--help"} for value in sys.argv[1:]):
            return function(*args, **kwargs)
        with runtime_locked():
            return function(*args, **kwargs)

    return wrapper


def call_json(
    url: str,
    token: str,
    method: str = "GET",
    body: dict | None = None,
    *, no_redirect: bool = False,
) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "ZhuoJian-ECS-Publisher/1.0",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    try:
        opener = build_opener(ProxyHandler({}), *([OriginNoRedirect()] if no_redirect else []))
        with opener.open(
            Request(url, data=data, method=method, headers=headers), timeout=30
        ) as response:
            payload = response.read(4 * 1024 * 1024 + 1)
            if len(payload) > 4 * 1024 * 1024:
                raise SystemExit("接口响应超过 4 MiB，已拒绝处理")
            return json.loads(payload)
    except HTTPError as exc:
        # This helper sends bearer tokens and, during registration, all four
        # project credentials. Never relay an untrusted upstream error body:
        # debug proxies sometimes echo request headers or JSON fields.
        raise SystemExit(f"接口返回 HTTP {exc.code}；响应正文已隐藏以保护凭证") from exc
    except URLError as exc:
        raise SystemExit(f"接口连接失败: {exc.reason}") from exc


def git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "本地 Git 命令失败")
    return result.stdout.strip()


def require_running_source_commit(project: Path, commit: str) -> None:
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SystemExit("Runtime 当前源码提交无效")
    if git(project, "rev-parse", "--verify", commit + "^{commit}").lower() != commit:
        raise SystemExit("项目 Git 缺少当前运行提交，先恢复准确源码再登记")


def load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取{label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label}必须是 JSON 对象: {path}")
    return value


def load_runtime_release(path: Path, application_slug: str) -> dict:
    try:
        info = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise SystemExit("Runtime 发布记录必须是普通文件且不能是符号链接")
        if os.name != "nt" and (info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o640):
            raise SystemExit("Runtime 发布记录必须由 root 持有且权限为 0640")
        release = load_object(path, "Runtime 发布记录")
    except OSError as exc:
        raise SystemExit(f"无法读取 Runtime 发布记录 {path}: {exc}") from exc
    if (
        release.get("managedBy") != "zhuojian-runtime-admin/v1"
        or release.get("applicationSlug") != application_slug
    ):
        raise SystemExit("Runtime 发布记录与当前应用不匹配")
    current = release.get("current")
    if not isinstance(current, dict):
        raise SystemExit("Runtime 发布记录没有当前运行版本")
    commit = current.get("commit")
    image = current.get("image")
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(char not in "0123456789abcdef" for char in commit)
        or not isinstance(image, str)
        or not image.endswith(":" + commit)
    ):
        raise SystemExit("Runtime 当前版本不是可核对的 commit SHA 镜像")
    return release


def update_runtime_release_status(
    path: Path,
    release: dict,
    *,
    status: str,
    platform_release: dict,
    contract_revision: str,
    manifest_digest: str,
) -> None:
    current = release.get("current")
    if not isinstance(current, dict):
        raise SystemExit("Runtime 发布记录没有当前运行版本")
    current["contractRevision"] = contract_revision
    current["manifestDigest"] = manifest_digest
    release["current"] = current
    release["status"] = status
    release["platformRelease"] = {
        "id": platform_release.get("id"),
        "status": status,
        "requestedCommit": platform_release.get("requested_commit"),
        "lastSuccessCommit": platform_release.get("last_success_commit"),
    }
    payload = (json.dumps(release, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def require_initial_backup(profile, slug, commit, runtime_profile):
    if not profile.get('platformStorageBinding', {}).get('enabled'):
        return
    candidates = [Path('/usr/local/lib/zhuojian/runtime_backup_plan.py'),
                  Path(__file__).parent.parent / 'assets/admin-runtime/host/runtime_backup_plan.py']
    source = next((p for p in candidates if p.is_file() and not p.is_symlink()), None)
    if source is None:
        raise SystemExit('首次备份验收工具尚未安装，不能将新系统报告为已保护')
    spec = importlib.util.spec_from_file_location('zhuojian_publish_backup_plan', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = module.protection_status(profile, slug, commit, plan_path=Path(runtime_profile).parent / 'backup-online-plan.json')
    if state.get('required') is True and state.get('status') != 'verified':
        raise SystemExit('新系统当前提交的首次机外备份、完整回读和隔离恢复尚未通过；线上旧系统继续服务，由开发AI补齐适配并重试登记')


def verify_running_container(release: dict, enterprise_key: str, application_slug: str) -> None:
    """Bind publisher metadata to the exact healthy Runtime-managed container."""

    current = release.get("current")
    if not isinstance(current, dict):
        raise SystemExit("Runtime 发布记录没有当前运行版本")
    container_name = release.get("containerName")
    expected_name = f"zhuojian-{enterprise_key}-{application_slug}"
    if container_name != expected_name:
        raise SystemExit("Runtime 容器名称与当前企业应用不匹配")
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            (
                "{{.State.Running}}|{{.Config.Image}}|"
                '{{ index .Config.Labels "com.zhuojian.managed-by" }}|'
                '{{ index .Config.Labels "com.zhuojian.application" }}|'
                '{{ index .Config.Labels "com.zhuojian.enterprise" }}|'
                '{{ index .Config.Labels "com.zhuojian.commit" }}'
            ),
            container_name,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise SystemExit("无法核对 Runtime 当前运行容器")
    fields = result.stdout.strip().split("|")
    expected = [
        "true",
        str(current.get("image") or ""),
        "zhuojian-runtime-admin/v1",
        application_slug,
        enterprise_key,
        str(current.get("commit") or ""),
    ]
    if fields != expected:
        raise SystemExit("运行容器与 Runtime 发布记录不一致，已拒绝登记")


def reload_verified_runtime_release(
    path: Path,
    application_slug: str,
    enterprise_key: str,
    expected_current: dict,
) -> dict:
    """Re-attest immutable state before writing the platform result."""

    latest_release = load_runtime_release(path, application_slug)
    if (
        latest_release.get("releaseSwitch") is not None
        or latest_release.get("current") != expected_current
    ):
        raise SystemExit("平台登记期间 Runtime 发布状态发生变化，已拒绝覆盖；请重新执行")
    verify_running_container(latest_release, enterprise_key, application_slug)
    return latest_release


def load_app_environment(path: Path) -> dict[str, str]:
    """Read one Runtime-managed env file without printing its contents."""

    try:
        info = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise SystemExit("应用凭证文件必须是普通文件且不能是符号链接")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise SystemExit("应用凭证文件权限必须是 0600")
        if hasattr(info, "st_uid") and info.st_uid != 0:
            raise SystemExit("应用凭证文件必须由 root 持有")
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"无法安全读取 Runtime 管理的应用凭证文件: {path}") from exc
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SystemExit("应用凭证文件格式无效")
        key, value = line.split("=", 1)
        if key in values:
            raise SystemExit("应用凭证文件包含重复字段")
        values[key] = value
    return values


def require_v25_credentials(values: dict[str, str]) -> dict[str, str]:
    expected = {
        "manifest_access_token": ("ZHUOJIAN_MANIFEST_ACCESS_TOKEN", "zjmf_"),
        "sso_exchange_token": ("ZHUOJIAN_SSO_EXCHANGE_TOKEN", "zjss_"),
        "action_signing_secret": ("ZHUOJIAN_ACTION_SIGNING_SECRET", "zjac_"),
        "event_signing_secret": ("ZHUOJIAN_EVENT_SIGNING_SECRET", "zjev_"),
    }
    credentials: dict[str, str] = {}
    for field, (key, prefix) in expected.items():
        value = values.get(key, "")
        if len(value) < 40 or not value.startswith(prefix):
            raise SystemExit(f"Runtime 管理的应用凭证缺少或类型错误: {key}")
        credentials[field] = value
    if len(set(credentials.values())) != len(credentials):
        raise SystemExit("四类应用凭证不得复用")
    return credentials


def load_app_credentials(path: Path) -> dict[str, str]:
    """Backward-compatible helper for callers that explicitly need v2.5."""

    return require_v25_credentials(load_app_environment(path))


def select_manifest_credential(values: dict[str, str]) -> tuple[str, str]:
    """Select the only configured manifest credential without guessing a migration."""

    modern = values.get("ZHUOJIAN_MANIFEST_ACCESS_TOKEN", "").strip()
    legacy = values.get("ZHUOJIAN_INTEGRATION_SECRET", "").strip()
    if modern and legacy:
        raise SystemExit(
            "应用凭证文件同时包含 2.4 和 2.5 凭证；"
            "请完成明确的契约迁移后再发布"
        )
    if modern:
        return modern, "2.5"
    if len(legacy) >= 32:
        return legacy, "2.4"
    raise SystemExit(
        "Runtime 管理的应用凭证缺少 Manifest 访问凭证："
        "需要 ZHUOJIAN_MANIFEST_ACCESS_TOKEN 或 ZHUOJIAN_INTEGRATION_SECRET"
    )


def registration_auth_payload(
    values: dict[str, str], contract_revision: str
) -> dict[str, object]:
    """Build exactly one SaaS registration credential shape for the manifest revision."""

    try:
        revision = require_supported_contract_revision(contract_revision)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    _manifest_token, credential_revision = select_manifest_credential(values)
    if credential_revision != revision:
        raise SystemExit(
            f"contractRevision={revision} 与 Runtime 凭证类型 {credential_revision} 不一致；"
            "普通发布不得自动迁移契约"
        )
    if revision == "2.5":
        return {"credentials": require_v25_credentials(values)}
    return {"integration_secret": values["ZHUOJIAN_INTEGRATION_SECRET"].strip()}


def require_publishable_checkbox_permissions(manifest: dict, baseline: dict | None = None) -> None:
    report = checkbox_permission_report(manifest, baseline)
    if report["errors"]:
        raise SystemExit("业务能力勾选授权未通过登记校验：\n- " + "\n- ".join(report["errors"]))
    for upgrade in report["legacyUpgradeRequired"]:
        print("PERMISSION UPGRADE REQUIRED: " + upgrade)


def initial_access_payload(platform_url: str, token: str, policy: str) -> dict:
    """Refuse closed registration when an older server would ignore the field."""
    if policy == "runtime_developer":
        return {}
    if policy != "disabled":
        raise SystemExit("Unsupported initial access policy")
    capabilities = call_json(platform_url + "/api/v1/ecs-publisher/platform-capabilities", token)
    feature = (capabilities.get("features") or {}).get("initialApplicationAccess") or {}
    if not (
        capabilities.get("protocol") == "zhuojian-platform-capabilities"
        and feature.get("supported") is True
        and feature.get("version") == 1
        and "disabled" in feature.get("policies", [])
        and feature.get("scope") == "new-application-only"
        and feature.get("disabledSuppressesAutomaticGrants") is True
    ):
        raise SystemExit("平台未确认关闭权限登记能力，已拒绝登记；请先发布匹配的平台版本")
    return {"initial_access_policy": "disabled"}


def assert_registered_origin_path(path: Path) -> None:
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or (os.name != "nt" and (info.st_uid != 0 or info.st_mode & 0o022)):
            raise SystemExit("旧入口采用记录必须位于 root 持有的无符号链接路径")
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_size > 65536
            or (os.name != "nt" and stat.S_IMODE(info.st_mode) != 0o600)):
        raise SystemExit("旧入口采用记录必须是 root0600 JSON")


def registered_https_origin(value: object) -> str:
    if not isinstance(value, str):
        raise SystemExit("既有应用入口必须是精确 HTTPS 根入口")
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.port is not None or parsed.netloc != parsed.hostname
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError
    except ValueError:
        raise SystemExit("既有应用入口必须是精确 HTTPS 根入口") from None
    return "https://" + parsed.hostname


def load_registered_origin(profile_path: Path, profile: dict, slug: str, base_url: str) -> dict:
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", slug):
        raise SystemExit("旧入口采用必须明确有效的 application-slug")
    path = profile_path.parent / "origin-adoptions" / f"{slug}.json"
    try:
        assert_registered_origin_path(path)
        def unique(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError("duplicate adoption field")
                result[key] = value
            return result
        record = json.loads(path.read_bytes(), object_pairs_hook=unique)
        fields = {"schema", "contract", "application_slug", "application_id", "organization_id", "environment",
                  "enterprise_key", "target_runtime_alias", "target_runtime_id", "source_runtime_id", "base_url",
                  "first_healthy_commit", "attestation", "created_at", "record_sha256"}
        body = {k: v for k, v in record.items() if k != "record_sha256"}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        parsed = urlsplit(record["base_url"])
        if (set(record) != fields or type(record["schema"]) is not int or record["schema"] != 1
                or record["contract"] != ORIGIN_ADOPTION_CONTRACT or record["record_sha256"] != digest
                or record["application_slug"] != slug or record["base_url"] != base_url
                or record["organization_id"] != profile.get("organizationId")
                or record["environment"] != profile.get("environment") or not record["environment"]
                or record["enterprise_key"] != profile.get("enterpriseKey")
                or record["target_runtime_alias"] != profile.get("runtimeId") or not record["target_runtime_alias"]
                or parsed.scheme != "https" or not parsed.hostname or parsed.netloc != parsed.hostname
                or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password
                or not re.fullmatch(r"[a-f0-9]{40}", record["first_healthy_commit"])):
            raise ValueError("adoption identity differs")
        for key in ("application_id", "organization_id", "source_runtime_id", "target_runtime_id"):
            if str(UUID(record[key])) != record[key]:
                raise ValueError("adoption UUID differs")
        expected = {"application_id": record["application_id"], "organization_id": record["organization_id"],
                    "application_slug": slug, "runtime_id": record["source_runtime_id"],
                    "requester_runtime_id": record["target_runtime_id"], "base_url": base_url,
                    "status": "healthy", "last_success_commit": record["first_healthy_commit"]}
        if record["attestation"] != expected:
            raise ValueError("adoption attestation differs")
        return record
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        raise SystemExit("旧入口没有与当前 Runtime/企业/应用一致的受控采用记录；拒绝登记") from None


def require_registered_origin(profile: dict, token: str, record: dict, commit: str) -> str:
    platform = str(profile["platform"]["baseUrl"]).rstrip("/")
    capabilities = call_json(platform + "/api/v1/ecs-publisher/platform-capabilities", token, no_redirect=True)
    features = capabilities.get("features") if isinstance(capabilities, dict) else None
    feature = features.get("registeredApplicationOriginRegistration") if isinstance(features, dict) else None
    if (not isinstance(capabilities, dict) or capabilities.get("protocol") != "zhuojian-platform-capabilities"
            or not isinstance(feature, dict)
            or any(type(feature.get(k)) is not type(v) or feature[k] != v for k, v in ORIGIN_REGISTRATION_CAPABILITY.items())):
        raise SystemExit("SaaS 尚未证明支持既有应用旧入口采用；拒绝登记")
    module = call_json(platform + "/api/v1/ecs-publisher/modules/" + record["application_slug"], token, no_redirect=True)
    if not isinstance(module, dict):
        raise SystemExit("SaaS 现有应用响应无效；拒绝登记")
    module = {**module, "base_url": registered_https_origin(module.get("base_url"))}
    expected = {"application_id": record["application_id"], "organization_id": record["organization_id"],
                "application_slug": record["application_slug"], "base_url": record["base_url"],
                "requester_runtime_id": record["target_runtime_id"]}
    if not isinstance(module, dict) or any(str(module.get(k)) != v for k, v in expected.items()):
        raise SystemExit("SaaS 现有应用身份或旧入口与采用记录不符；拒绝登记")
    if module.get("runtime_id") == record["target_runtime_id"] and module.get("owned_by_requester") is True:
        return "target"
    if (module.get("runtime_id") == record["source_runtime_id"] and module.get("owned_by_requester") is False
            and module.get("status") == "healthy" and module.get("last_success_commit") == commit == record["first_healthy_commit"]):
        return "source"
    raise SystemExit("首次采用必须登记原健康版本，且来源必须是同企业/环境的已停用 Runtime")


@with_runtime_lock
def main() -> int:
    parser = argparse.ArgumentParser(
        description="业务 AI 将当前本地 Git 版本登记并同步到灼见"
    )
    parser.add_argument("--project-path", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--runtime-profile",
        type=Path,
        default=Path("/etc/zhuojian/runtime.json"),
    )
    parser.add_argument("--runtime-credential-file", type=Path)
    parser.add_argument("--app-env-file", type=Path)
    parser.add_argument("--application-slug", help="受控旧入口采用时明确原 applicationSlug")
    parser.add_argument("--release-metadata", type=Path)
    parser.add_argument("--permission-baseline", type=Path, help="已部署且已核对业务勾选界面的旧 Manifest；不修改角色或放宽边界")
    parser.add_argument(
        "--use-running-release",
        action="store_true",
        help="按 Runtime 已核实的当前运行镜像登记，支持任务worktree发布与回滚，不使用 Git HEAD",
    )
    parser.add_argument("--runtime-release-file", type=Path)
    parser.add_argument(
        "--initial-access-policy", choices=("runtime_developer", "disabled"),
        default="runtime_developer",
        help="新应用使用 disabled 时停用应用与助手，并禁止自动授权；不撤销既有应用权限",
    )
    args = parser.parse_args()

    project = args.project_path.resolve()
    if not project.is_dir():
        raise SystemExit(f"项目目录不存在: {project}")
    if not args.use_running_release and git(project, "status", "--porcelain"):
        raise SystemExit("发布被拒绝：本地 Git 工作树不干净，请先审查并提交本次修改")
    git_commit = git(project, "rev-parse", "HEAD").lower() if not args.use_running_release else None

    profile = load_object(args.runtime_profile, "Runtime 环境档案")
    platform_url = str((profile.get("platform") or {}).get("baseUrl") or "").rstrip("/")
    if urlsplit(platform_url).scheme != "https":
        raise SystemExit("Runtime 环境档案中的 platform.baseUrl 必须是 HTTPS")
    credential_value = str(
        (profile.get("deployment") or {}).get("registrationCredentialRef") or ""
    ).strip()
    if args.runtime_credential_file is None and not credential_value:
        raise SystemExit("Runtime 环境档案缺少登记凭证引用")
    credential_ref = args.runtime_credential_file or Path(credential_value)
    try:
        runtime_credential = credential_ref.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"无法读取 Runtime 登记凭证: {credential_ref}") from exc
    if not runtime_credential:
        raise SystemExit("Runtime 登记凭证为空")

    base_url = args.base_url.rstrip("/")
    parsed = urlsplit(base_url)
    domain_suffix = str((profile.get("domains") or {}).get("suffix") or "").lower()
    if parsed.scheme != "https" or not parsed.hostname:
        raise SystemExit("模块入口必须是公网 HTTPS URL")
    registered_origin = None
    if domain_suffix and parsed.hostname.endswith("." + domain_suffix):
        inferred_slug = parsed.hostname[: -(len(domain_suffix) + 1)]
        if not inferred_slug or "." in inferred_slug or (args.application_slug and args.application_slug != inferred_slug):
            raise SystemExit("无法从模块域名确定 applicationSlug")
    else:
        inferred_slug = args.application_slug or ""
        registered_origin = load_registered_origin(args.runtime_profile, profile, inferred_slug, base_url)
    app_env_file = args.app_env_file or Path("/etc/zhuojian/apps") / f"{inferred_slug}.env"
    app_environment = load_app_environment(app_env_file)
    manifest_token, credential_revision = select_manifest_credential(app_environment)
    release_file = args.runtime_release_file or (
        Path("/srv/zhuojian/deployments") / inferred_slug / "release.json"
    )
    release = load_runtime_release(release_file, inferred_slug)
    running = release["current"]
    verify_running_container(release, str(profile.get("enterpriseKey") or ""), inferred_slug)
    require_initial_backup(profile, inferred_slug, str(running['commit']), args.runtime_profile)
    if args.use_running_release:
        commit = str(running["commit"])
        # The public Manifest and managed container above are the registration
        # source. Other developers' working files are neither read nor published.
        require_running_source_commit(project, commit)
    else:
        commit = git_commit
        if running.get("commit") != commit:
            raise SystemExit("Git HEAD 与 Runtime 当前运行版本不一致；登记已运行的任务版本或回滚版本请使用 --use-running-release")
    image_ref = str(running["image"])
    if registered_origin:
        require_registered_origin(profile, runtime_credential, registered_origin, commit)

    manifest = call_json(base_url + "/api/integration/manifest", manifest_token,
                         **({"no_redirect": True} if registered_origin else {}))
    require_publishable_navigation_theme(manifest)
    permission_baseline = load_object(args.permission_baseline, "已核对权限基线") if args.permission_baseline else None
    require_publishable_checkbox_permissions(manifest, permission_baseline)
    application_slug = str(manifest.get("applicationSlug") or "")
    application_name = str(manifest.get("applicationName") or "")
    enterprise_key = str((manifest.get("enterprise") or {}).get("key") or "")
    if not application_slug or not application_name:
        raise SystemExit("Manifest 缺少 applicationSlug/applicationName")
    if (application_slug != inferred_slug
            or (not registered_origin and parsed.hostname != f"{application_slug}.{domain_suffix}")):
        raise SystemExit("Manifest applicationSlug 与模块域名不一致")
    if canonical_enterprise_key(enterprise_key) != canonical_enterprise_key(
        profile.get("enterpriseKey")
    ):
        raise SystemExit("Manifest enterprise.key 与 Runtime 企业不一致")
    try:
        contract_revision = require_supported_contract_revision(
            manifest.get("contractRevision")
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if contract_revision != credential_revision:
        raise SystemExit(
            f"contractRevision={contract_revision} 与 Runtime 凭证类型 "
            f"{credential_revision} 不一致；普通发布不得自动迁移契约"
        )
    registration_auth = registration_auth_payload(app_environment, contract_revision)

    metadata = load_object(args.release_metadata, "发布元数据") if args.release_metadata else {}
    access_payload = initial_access_payload(platform_url, runtime_credential, args.initial_access_policy)
    result = call_json(
        platform_url + "/api/v1/ecs-publisher/modules/register",
        runtime_credential,
        "POST",
        {
            "application_slug": application_slug,
            "application_name": application_name,
            "base_url": base_url,
            **registration_auth,
            "source_commit": commit,
            "image_ref": image_ref,
            "release_metadata": metadata,
            **access_payload,
        },
        **({"no_redirect": True} if registered_origin else {}),
    )
    if registered_origin and (str(result.get("application_id")) != registered_origin["application_id"]
            or str(result.get("runtime_id")) != registered_origin["target_runtime_id"]
            or str(result.get("requester_runtime_id")) != registered_origin["target_runtime_id"]
            or result.get("owned_by_requester") is not True):
        raise SystemExit("登记返回的应用或 Runtime 归属不符；先只读核对原应用，不自动重试")
    summary = {
        "status": result.get("status"),
        "applicationSlug": result.get("application_slug"),
        "applicationId": result.get("application_id"),
        "contractRevision": result.get("contract_revision"),
        "sourceCommit": result.get("last_success_commit"),
        "requestedInitialAccessPolicy": args.initial_access_policy,
        "authorization": (
            "disabled registration requested; verify persisted flags and zero grants"
            if args.initial_access_policy == "disabled"
            else "existing persisted policy or runtime developer managed; verify grants"
        ),
    }
    manifest_digest = hashlib.sha256(
        json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    # The official Runtime commands share the lock above. Re-read and attest a
    # second time before persisting so publication never overwrites a newer
    # release record with the stale object loaded before the network request.
    latest_release = reload_verified_runtime_release(
        release_file,
        inferred_slug,
        str(profile.get("enterpriseKey") or ""),
        running,
    )
    update_runtime_release_status(
        release_file,
        latest_release,
        status=str(result.get("status") or "failed"),
        platform_release=result,
        contract_revision=contract_revision,
        manifest_digest=manifest_digest,
    )
    if result.get("status") != "healthy":
        summary["error"] = result.get("last_error") or "contract verification failed"
        print(json.dumps(summary, ensure_ascii=False))
        return 2
    if profile.get('platformStorageBinding', {}).get('enabled'):
        reporter = Path('/usr/local/sbin/zhuojian-storage-bootstrap')
        if reporter.is_file() and not reporter.is_symlink():
            report_result = subprocess.run([str(reporter), 'report'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            summary['storageReport'] = 'reported' if report_result.returncode == 0 else 'pending_retry'
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
