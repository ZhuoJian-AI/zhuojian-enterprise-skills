"""Local release fixtures only; no stable publication or runtime acceptance."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = "zhuojian-shared-runtime-handover"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "skills/core/zhuojian-subsystem-builder/scripts"))
import build_release
import update_managed_skills as updater


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.temporary.name)
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        releases = {}
        for name in ("zhuojian-subsystem-builder", NAME):
            entry, _ = build_release.package_skill(ROOT, cls.root, name=name,
                source=catalog["skills"][name], tag="local-test-only")
            entry["archiveUrl"] = (cls.root / (name + "-" + entry["skillVersion"] + ".zip")).as_uri()
            releases[name] = entry
        cls.catalog = cls.root / "catalog.json"
        cls.catalog.write_text(json.dumps({"schemaVersion": 1, "channel": "stable",
            "repository": updater.REPOSITORY, "skills": releases}), encoding="utf-8")

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def resolve(self, label, arguments, expected):
        target = self.root / label
        result = updater.main(["--catalog-url", self.catalog.as_uri(), "--allow-test-url",
            "--skills-dir", str(target), "resolve", *arguments])
        self.assertEqual(result, 0)
        installed = target / NAME
        self.assertEqual(installed.is_dir(), expected)
        if expected:
            original = ROOT / "skills/companies/zhuojian" / NAME
            for source in original.rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    self.assertEqual(source.read_bytes(), (installed / source.relative_to(original)).read_bytes())

    def test_exact_runtime_fresh_install(self):
        self.resolve("runtime", ["--runtime-id", "zhuojian-hz-shared-01"], True)

    def test_exact_host_fresh_install(self):
        self.resolve("host", ["--host", "47.114.61.74"], True)

    def test_company_name_and_other_runtime_do_not_select_server_handoff(self):
        self.resolve("company-only", ["--enterprise-key", "zhuojian"], False)
        self.resolve("other-runtime", ["--enterprise-key", "zhuojian", "--runtime-id", "other"], False)

    def test_handoff_does_not_claim_completed_initialization(self):
        text = (ROOT / "skills/companies/zhuojian" / NAME / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("initialization.ready=false", text)
        self.assertIn("不得伪造 doctor 通过", text)


if __name__ == "__main__": unittest.main(verbosity=2)
