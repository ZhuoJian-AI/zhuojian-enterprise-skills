from __future__ import annotations

import sys

import pytest

from scripts import register_subsystem


def test_legacy_registrar_blocks_missing_theme_before_discovery(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_call(url: str, _token: str, method: str, _body: dict | None = None) -> dict:
        calls.append((url, method))
        return {"modules": []}

    monkeypatch.setattr(register_subsystem, "call", fake_call)
    monkeypatch.setenv("ZHUOJIAN_ADMIN_TOKEN", "test-admin")
    monkeypatch.setenv("ZHUOJIAN_SUBSYSTEM_TOKEN", "test-integration")
    monkeypatch.setattr(sys, "argv", [
        "register_subsystem.py", "--organization-id", "org-1",
        "--base-url", "https://business.example", "--apply",
    ])

    with pytest.raises(SystemExit, match="模块导航主题未通过登记校验"):
        register_subsystem.main()

    assert calls == [("https://business.example/api/integration/manifest", "GET")]


def test_legacy_registrar_accepts_valid_theme():
    register_subsystem.require_navigation_theme({
        "presentation": {
            "moduleNavigationTheme": {
                "accentColor": "#176B57",
                "backgroundColor": "#FFFAF1",
                "selectedBackgroundColor": "#E8F4EF",
                "selectedTextColor": "#174F43",
            }
        }
    })
