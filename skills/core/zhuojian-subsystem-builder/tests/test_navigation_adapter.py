"""Run the shipped JavaScript adapter, not a reimplementation of its rules."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_navigation_adapter_behaviour():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the navigation adapter runtime tests")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, str(root / "tests/navigation_adapter.mjs"),
         str(root / "assets/native-subsystem-template/static/zhuojian-navigation.js")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_assistant_presence_adapter_behaviour():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the assistant presence adapter runtime tests")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, str(root / "tests/assistant_presence_adapter.mjs"),
         str(root / "assets/native-subsystem-template/static/zhuojian-assistant-presence.js")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_assistant_handoff_adapter_behaviour():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the assistant handoff adapter runtime tests")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, str(root / "tests/assistant_adapter.mjs"),
         str(root / "assets/native-subsystem-template/static/zhuojian-assistant.js")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
