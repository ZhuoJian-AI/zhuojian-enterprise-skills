#!/usr/bin/env python3
"""Build deterministic Release assets for every Skill in the catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY = "ZhuoJian-AI/zhuojian-enterprise-skills"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "Git 命令失败")
    return result.stdout.strip()


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{label} 不是有效 UTF-8 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label} 顶层必须是对象")
    return value


def validate_name(value: object) -> str:
    if not isinstance(value, str) or len(value) > 63 or not SKILL_NAME_RE.fullmatch(value):
        raise SystemExit("catalog.json 包含无效 Skill 名称")
    return value


def validate_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise SystemExit(f"{label} 必须是不重复的非空字符串数组")
    if len(value) != len(set(value)):
        raise SystemExit(f"{label} 不能重复")
    return value


def validate_changelog(text: str, version: str, name: str) -> None:
    heading = re.compile(
        rf"(?m)^##[ \t]+\[?{re.escape(version)}\]?"
        r"(?:[ \t]+-[ \t]+\d{4}-\d{2}-\d{2})?[ \t]*$"
    )
    match = heading.search(text)
    if match is None:
        raise SystemExit(f"{name}/CHANGELOG.md 缺少 {version} 的更新记录")
    remainder = text[match.end():]
    next_heading = re.search(r"(?m)^##[ \t]+", remainder)
    section = remainder[:next_heading.start()] if next_heading else remainder
    if re.search(r"(?m)^[ \t]*[-*][ \t]+\S", section) is None:
        raise SystemExit(f"{name}/CHANGELOG.md 中 {version} 的更新记录为空")


def tracked_files(root: Path, skill_path: Path) -> list[tuple[Path, int]]:
    relative_skill = skill_path.relative_to(root)
    raw = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", relative_skill.as_posix()],
        cwd=root,
        capture_output=True,
        check=True,
    ).stdout
    files: list[tuple[Path, int]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode = int(metadata.split(b" ", 1)[0], 8)
        if stat.S_IFMT(mode) != stat.S_IFREG:
            raise SystemExit(f"{relative_skill.as_posix()} 包含不允许的链接或特殊文件")
        repository_relative = Path(encoded_path.decode("utf-8"))
        full_path = root / repository_relative
        if full_path.is_file():
            files.append((repository_relative.relative_to(relative_skill), mode))
    return sorted(files, key=lambda item: item[0].as_posix())


def package_skill(
    root: Path,
    output: Path,
    *,
    name: str,
    source: dict,
    tag: str,
) -> tuple[dict, dict]:
    path_value = source.get("path")
    kind = source.get("kind")
    if not isinstance(path_value, str) or not path_value:
        raise SystemExit(f"{name} 缺少 path")
    if kind not in {"core", "handoff"}:
        raise SystemExit(f"{name} 的 kind 无效")
    skill_path = (root / path_value).resolve()
    try:
        skill_path.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"{name} 的 path 越出仓库") from exc
    if skill_path.name != name or not skill_path.is_dir():
        raise SystemExit(f"{name} 的 path 与目录名不匹配")

    metadata = load_json(skill_path / "skill-version.json", f"{name}/skill-version.json")
    version = metadata.get("skillVersion")
    if (
        metadata.get("schemaVersion") != 1
        or metadata.get("skillName") != name
        or metadata.get("managedBy") != REPOSITORY
        or not isinstance(version, str)
        or not SEMVER_RE.fullmatch(version)
    ):
        raise SystemExit(f"{name} 的版本元数据无效")
    skill_entry = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    if re.search(rf"(?m)^name:\s*[\"']?{re.escape(name)}[\"']?\s*$", skill_entry) is None:
        raise SystemExit(f"{name}/SKILL.md 的名称不匹配")
    changelog = (skill_path / "CHANGELOG.md").read_text(encoding="utf-8")
    validate_changelog(changelog, version, name)

    files = tracked_files(root, skill_path)
    required = {Path("SKILL.md"), Path("skill-version.json"), Path("CHANGELOG.md")}
    if not required.issubset({relative for relative, _ in files}):
        raise SystemExit(f"{name} 缺少已跟踪的必要文件")
    archive_name = f"{name}-{version}.zip"
    archive_path = output / archive_name
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, mode in files:
            info = zipfile.ZipInfo(
                f"{name}/{relative.as_posix()}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            permissions = 0o755 if mode & 0o111 else 0o644
            info.external_attr = ((0o100000 | permissions) << 16)
            archive.writestr(info, (skill_path / relative).read_bytes())
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    release = {
        "skillName": name,
        "skillVersion": version,
        "archiveUrl": f"https://github.com/{REPOSITORY}/releases/download/{tag}/{archive_name}",
        "archiveSha256": digest,
        "kind": kind,
        "enterpriseKeys": validate_string_list(source.get("enterpriseKeys", []), f"{name} enterpriseKeys"),
        "runtimeIds": validate_string_list(source.get("runtimeIds", []), f"{name} runtimeIds"),
        "hosts": validate_string_list(source.get("hosts", []), f"{name} hosts"),
    }
    return release, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="构建企业 Skills 总仓库稳定版资产")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    if not TAG_RE.fullmatch(args.tag):
        raise SystemExit("--tag 格式无效")
    root = args.source_dir.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise SystemExit("--source-dir 必须是总仓库根目录")
    if git(root, "status", "--porcelain"):
        raise SystemExit("发布构建要求干净工作树")

    source_catalog = load_json(root / "catalog.json", "catalog.json")
    if source_catalog.get("schemaVersion") != 1 or source_catalog.get("repository") != REPOSITORY:
        raise SystemExit("catalog.json 的仓库身份无效")
    raw_skills = source_catalog.get("skills")
    if not isinstance(raw_skills, dict) or not raw_skills:
        raise SystemExit("catalog.json 没有 Skill")

    output.mkdir(parents=True, exist_ok=True)
    source_commit = git(root, "rev-parse", "HEAD")
    releases: dict[str, dict] = {}
    metadata_by_name: dict[str, dict] = {}
    for raw_name, source in sorted(raw_skills.items()):
        name = validate_name(raw_name)
        if not isinstance(source, dict):
            raise SystemExit(f"{name} 的目录记录无效")
        release, metadata = package_skill(root, output, name=name, source=source, tag=args.tag)
        releases[name] = release
        metadata_by_name[name] = metadata

    core_name = "aifabei-subsystem-builder"
    core = releases.get(core_name)
    if core is None or core["kind"] != "core":
        raise SystemExit("目录缺少 aifabei-subsystem-builder 总 Skill")
    released_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    release_catalog = {
        "schemaVersion": 1,
        "channel": "stable",
        "repository": REPOSITORY,
        "bundleTag": args.tag,
        "sourceCommit": source_commit,
        "releasedAt": released_at,
        "skills": releases,
    }
    (output / "catalog.json").write_text(
        json.dumps(release_catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    core_metadata = metadata_by_name[core_name]
    update_manifest = {
        "schemaVersion": 1,
        "skillName": core_name,
        "skillVersion": core["skillVersion"],
        "channel": "stable",
        "archiveUrl": core["archiveUrl"],
        "archiveSha256": core["archiveSha256"],
        "sourceCommit": source_commit,
        "releasedAt": released_at,
        "defaultContractRevision": core_metadata["defaultContractRevision"],
        "supportedContractRevisions": core_metadata["supportedContractRevisions"],
    }
    (output / "update-manifest.json").write_text(
        json.dumps(update_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    core_path = root / raw_skills[core_name]["path"]
    shutil.copy2(core_path / "scripts" / "update_skill.py", output / "update_skill.py")
    print(json.dumps({
        "tag": args.tag,
        "sourceCommit": source_commit,
        "skills": {name: release["skillVersion"] for name, release in releases.items()},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
