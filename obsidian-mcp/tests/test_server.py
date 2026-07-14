import json
import os
from pathlib import Path

import pytest

from obsidian_mcp import server


@pytest.fixture
def vault_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "Note.md").write_text("# Hi from phone\n", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_MODE", "filesystem")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    return tmp_path


def test_tools_roundtrip(vault_env: Path) -> None:
    info = json.loads(server.vault_info())
    assert info["mode"] == "filesystem"
    assert info["note_count"] == 1

    notes = json.loads(server.list_notes())
    assert notes[0]["path"] == "Note.md"

    content = server.read_note("Note.md")
    assert "Hi from phone" in content

    written = json.loads(server.write_note("New.md", "created"))
    assert written["written"] == "New.md"

    search = json.loads(server.search_notes("created"))
    assert search["count"] >= 1


def test_missing_vault_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OBSIDIAN_MODE", "filesystem")
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    payload = json.loads(server.vault_info())
    assert "error" in payload
    assert "OBSIDIAN_VAULT_PATH" in payload["error"]
