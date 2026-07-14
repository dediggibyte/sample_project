"""Filesystem-backed Obsidian vault access.

Designed for vaults synced from Obsidian mobile (Obsidian Sync, iCloud,
Dropbox, Syncthing, Git, etc.) onto a path this MCP server can read.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {".obsidian", ".trash", ".git", ".smart-env", "node_modules"}


@dataclass(frozen=True)
class NoteInfo:
    path: str
    name: str
    size: int


class VaultError(Exception):
    """User-facing vault operation error."""


class FilesystemVault:
    """Read/write markdown notes under an Obsidian vault root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise VaultError(
                f"Vault path does not exist or is not a directory: {self.root}"
            )

    def resolve_note(self, note_path: str) -> Path:
        """Resolve a vault-relative note path with traversal protection."""
        cleaned = note_path.strip().lstrip("/")
        if not cleaned:
            raise VaultError("Note path is empty")
        if not cleaned.endswith(".md"):
            cleaned = f"{cleaned}.md"

        target = (self.root / cleaned).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise VaultError("Note path escapes the vault root") from exc
        return target

    def list_notes(self, folder: str = "", limit: int = 200) -> list[NoteInfo]:
        base = self.root
        if folder.strip():
            base = self.resolve_folder(folder)

        notes: list[NoteInfo] = []
        for path in sorted(base.rglob("*.md")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            rel = path.relative_to(self.root).as_posix()
            notes.append(NoteInfo(path=rel, name=path.stem, size=path.stat().st_size))
            if len(notes) >= limit:
                break
        return notes

    def resolve_folder(self, folder: str) -> Path:
        cleaned = folder.strip().strip("/")
        target = (self.root / cleaned).resolve() if cleaned else self.root
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise VaultError("Folder path escapes the vault root") from exc
        if not target.is_dir():
            raise VaultError(f"Folder not found: {cleaned}")
        return target

    def list_folders(self, folder: str = "") -> list[str]:
        base = self.resolve_folder(folder) if folder.strip() else self.root
        folders: list[str] = []
        for path in sorted(base.iterdir()):
            if not path.is_dir():
                continue
            if path.name in SKIP_DIRS or path.name.startswith("."):
                continue
            folders.append(path.relative_to(self.root).as_posix())
        return folders

    def read_note(self, note_path: str) -> str:
        target = self.resolve_note(note_path)
        if not target.is_file():
            raise VaultError(f"Note not found: {note_path}")
        return target.read_text(encoding="utf-8")

    def write_note(self, note_path: str, content: str, overwrite: bool = True) -> str:
        target = self.resolve_note(note_path)
        if target.exists() and not overwrite:
            raise VaultError(f"Note already exists: {note_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target.relative_to(self.root).as_posix()

    def append_note(self, note_path: str, content: str) -> str:
        target = self.resolve_note(note_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = ""
        if target.is_file():
            existing = target.read_text(encoding="utf-8")
            if existing and not existing.endswith("\n"):
                existing += "\n"
        target.write_text(existing + content, encoding="utf-8")
        return target.relative_to(self.root).as_posix()

    def delete_note(self, note_path: str) -> str:
        target = self.resolve_note(note_path)
        if not target.is_file():
            raise VaultError(f"Note not found: {note_path}")
        rel = target.relative_to(self.root).as_posix()
        target.unlink()
        return rel

    def search_notes(
        self,
        query: str,
        folder: str = "",
        case_sensitive: bool = False,
        limit: int = 50,
    ) -> list[dict[str, str | int]]:
        if not query.strip():
            raise VaultError("Search query is empty")

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(query), flags)
        base = self.resolve_folder(folder) if folder.strip() else self.root
        hits: list[dict[str, str | int]] = []

        for path in sorted(base.rglob("*.md")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    hits.append(
                        {
                            "path": path.relative_to(self.root).as_posix(),
                            "line": i,
                            "snippet": line.strip()[:240],
                        }
                    )
                    if len(hits) >= limit:
                        return hits
                    break
        return hits

    def vault_stats(self) -> dict[str, int | str]:
        notes = self.list_notes(limit=100_000)
        return {
            "root": str(self.root),
            "note_count": len(notes),
            "mode": "filesystem",
            "pid": os.getpid(),
        }
