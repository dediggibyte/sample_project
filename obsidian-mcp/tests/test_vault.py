from pathlib import Path

import pytest

from obsidian_mcp.vault import FilesystemVault, VaultError


@pytest.fixture
def vault(tmp_path: Path) -> FilesystemVault:
    (tmp_path / "Daily").mkdir()
    (tmp_path / "Daily" / "2026-07-14.md").write_text("# Today\nhello phone\n", encoding="utf-8")
    (tmp_path / "Inbox.md").write_text("capture from mobile\n", encoding="utf-8")
    return FilesystemVault(tmp_path)


def test_list_notes(vault: FilesystemVault) -> None:
    notes = vault.list_notes()
    paths = {n.path for n in notes}
    assert "Inbox.md" in paths
    assert "Daily/2026-07-14.md" in paths


def test_read_and_search(vault: FilesystemVault) -> None:
    assert "hello phone" in vault.read_note("Daily/2026-07-14")
    hits = vault.search_notes("phone")
    assert hits
    assert hits[0]["path"] == "Daily/2026-07-14.md"


def test_write_append_delete(vault: FilesystemVault) -> None:
    path = vault.write_note("Projects/Idea.md", "# Idea\n")
    assert path == "Projects/Idea.md"
    vault.append_note("Projects/Idea.md", "more\n")
    assert "more" in vault.read_note("Projects/Idea")
    deleted = vault.delete_note("Projects/Idea.md")
    assert deleted == "Projects/Idea.md"
    with pytest.raises(VaultError):
        vault.read_note("Projects/Idea.md")


def test_path_traversal_blocked(vault: FilesystemVault) -> None:
    with pytest.raises(VaultError):
        vault.read_note("../outside.md")


def test_list_folders(vault: FilesystemVault) -> None:
    assert "Daily" in vault.list_folders()
