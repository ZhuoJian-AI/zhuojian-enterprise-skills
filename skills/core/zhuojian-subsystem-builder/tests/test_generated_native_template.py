from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_checked(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_scaffold_uses_the_runtime_enterprise_identity(tmp_path: Path):
    project = tmp_path / "default-identity"
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "scaffold_subsystem.py"),
            "--output",
            str(project),
            "--company-slug",
            "zhipu",
            "--company-name",
            "质谱科技",
            "--application-slug",
            "identity-probe",
            "--application-name",
            "Identity probe",
            "--module-key",
            "identity.main",
            "--module-name",
            "Identity",
            "--department",
            "ops:Operations:owner",
        ],
        cwd=ROOT,
    )

    manifest = json.loads((project / "subsystem.json").read_text(encoding="utf-8"))
    page_html = (project / "static" / "index.html").read_text(encoding="utf-8")
    app = (project / "app.py").read_text(encoding="utf-8")
    assert manifest["enterprise"] == {"key": "zhipu", "name": "质谱科技"}
    assert manifest["contractRevision"] == "2.5"
    assert manifest["presentation"]["moduleNavigationTheme"] == {
        "accentColor": "#5148D8",
        "backgroundColor": "#FFFFFF",
        "selectedBackgroundColor": "#EEECFF",
        "selectedTextColor": "#5148D8",
    }
    assert "background:#eeecff" in page_html
    assert "color:#5148d8" in page_html
    assert all(action.get("permissionPolicy", {}).get("mode") == "configurable"
               for module in manifest["modules"] for action in module["actions"])
    manifest_page = manifest["modules"][0]["pages"][0]
    assert manifest_page["aiSemantics"]["defaultQueryActionKey"] == f"{manifest_page['pageKey'].rsplit('.', 1)[0]}.query"
    assert manifest_page["aiSemantics"]["primaryEntities"]
    assert all(
        action["inputSchema"].get("additionalProperties") is False
        and action["resultSchema"].get("additionalProperties") is False
        for action in manifest["modules"][0]["actions"]
    )
    assert "enterprise_key:'zhipu'" in page_html
    assert "质谱科技 业务模块" in page_html
    assert "__COMPANY_NAME__" not in page_html
    assert "data-zhuojian-embedded" in page_html
    assert page_html.index("data-zhuojian-embedded") < page_html.index("<style>")
    assert "100dvh" in page_html
    assert "viewport-fit=cover" in page_html
    assert "safe-area-inset-bottom" in page_html
    assert 'html[data-zhuojian-embedded="true"] .bar' in page_html
    assert 'html[data-zhuojian-embedded="true"] .module-nav' in page_html
    assert "display:none!important" in page_html
    assert ".table-scroll" in page_html
    assert "@media(max-width:768px)" in page_html
    assert "@media(prefers-reduced-motion:reduce)" in page_html
    assert "frame-ancestors 'self' " in app


def test_scaffolded_native_system_runs_its_security_and_recovery_suite(tmp_path: Path):
    project = tmp_path / "generated-native-system"
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "scaffold_subsystem.py"),
            "--output",
            str(project),
            "--company-slug",
            "alphabet",
            "--company-name",
            "Alphabet",
            "--application-slug",
            "ci-contract-probe",
            "--application-name",
            "CI contract probe",
            "--module-key",
            "probe.main",
            "--module-name",
            "Probe",
            "--department",
            "ops:Operations:owner",
        ],
        cwd=ROOT,
    )
    run_checked([sys.executable, "-m", "pytest", "-q"], cwd=project)
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_source.py"),
            "--path",
            str(project),
            "--requires-file-storage",
            "--requires-object-storage",
        ],
        cwd=ROOT,
    )


def test_scaffold_can_add_reviewable_saas_specialist_ai(tmp_path: Path):
    project = tmp_path / "specialist-ai"
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "scaffold_subsystem.py"),
            "--output",
            str(project),
            "--company-slug",
            "alphabet",
            "--company-name",
            "Alphabet",
            "--application-slug",
            "specialist-probe",
            "--application-name",
            "Specialist probe",
            "--module-key",
            "inspection",
            "--module-name",
            "查货报告",
            "--department",
            "quality:品质部:owner",
            "--platform-ai-capability",
            "vision.ocr",
            "--platform-ai-capability",
            "speech.transcribe",
        ],
        cwd=ROOT,
    )

    manifest = json.loads((project / "subsystem.json").read_text(encoding="utf-8"))
    actions = manifest["modules"][0]["actions"]
    declarations = {
        action["platformAiCapability"]["type"]: action
        for action in actions
        if "platformAiCapability" in action
    }
    assert set(declarations) == {"vision.ocr", "speech.transcribe"}
    assert all(action["operation"] == "query" for action in declarations.values())
    assert all(
        action["resultSchema"]["additionalProperties"] is False
        for action in declarations.values()
    )
    page_html = (project / "static" / "index.html").read_text(encoding="utf-8")
    assert "zhuojian:ai-run" in page_html
    assert "zhuojian:ai-result" in page_html
    assert "请核对 AI 草稿" in page_html
    assert "/api/ui/actions/" in page_html
    run_checked(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_source.py"),
            "--path",
            str(project),
        ],
        cwd=ROOT,
    )
