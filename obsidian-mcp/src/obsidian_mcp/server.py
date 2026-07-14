"""Obsidian MCP server entrypoint.

Modes
-----
filesystem (default, best for phone vaults)
    Point OBSIDIAN_VAULT_PATH at a folder synced from your phone
    (Obsidian Sync / iCloud / Dropbox / Syncthing / Git).

restapi (desktop Obsidian)
    Requires Local REST API plugin + OBSIDIAN_API_KEY.
    Phone apps generally cannot expose this to Cursor Cloud.
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .rest_api import RestApiVault
from .vault import FilesystemVault, VaultError

mcp = FastMCP("obsidian")


def _mode() -> str:
    return os.environ.get("OBSIDIAN_MODE", "filesystem").strip().lower()


def _get_fs() -> FilesystemVault:
    path = os.environ.get("OBSIDIAN_VAULT_PATH", "").strip()
    if not path:
        raise VaultError(
            "OBSIDIAN_VAULT_PATH is required in filesystem mode. "
            "Set it to your synced Obsidian vault folder (from your phone)."
        )
    return FilesystemVault(path)


def _get_api() -> RestApiVault:
    return RestApiVault(
        api_key=os.environ.get("OBSIDIAN_API_KEY", ""),
        base_url=os.environ.get("OBSIDIAN_BASE_URL", "http://127.0.0.1:27123"),
        verify_ssl=os.environ.get("OBSIDIAN_VERIFY_SSL", "false").lower()
        in {"1", "true", "yes"},
    )


def _err(exc: Exception) -> str:
    return json.dumps({"error": str(exc)}, indent=2)


def _ok(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


@mcp.tool()
def vault_info() -> str:
    """Show vault connection mode, path/URL, and basic stats."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                return _ok(api.vault_stats())
            finally:
                api.close()
        return _ok(_get_fs().vault_stats())
    except Exception as exc:  # noqa: BLE001 — surface to MCP client
        return _err(exc)


@mcp.tool()
def list_notes(folder: str = "", limit: int = 200) -> str:
    """List markdown notes in the vault (optionally under a folder)."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                return _ok(api.list_notes(folder=folder, limit=limit))
            finally:
                api.close()
        notes = _get_fs().list_notes(folder=folder, limit=limit)
        return _ok([note.__dict__ for note in notes])
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def list_folders(folder: str = "") -> str:
    """List subfolders in the vault (or under a folder)."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                return _ok(api.list_folders(folder=folder))
            finally:
                api.close()
        return _ok(_get_fs().list_folders(folder=folder))
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def read_note(path: str) -> str:
    """Read a note by vault-relative path (e.g. Daily/2026-07-14.md)."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                return api.read_note(path)
            finally:
                api.close()
        return _get_fs().read_note(path)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def write_note(path: str, content: str, overwrite: bool = True) -> str:
    """Create or overwrite a note. Path is vault-relative."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                saved = api.write_note(path, content, overwrite=overwrite)
            finally:
                api.close()
        else:
            saved = _get_fs().write_note(path, content, overwrite=overwrite)
        return _ok({"written": saved})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def append_to_note(path: str, content: str) -> str:
    """Append markdown content to a note (creates the note if missing)."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                saved = api.append_note(path, content)
            finally:
                api.close()
        else:
            saved = _get_fs().append_note(path, content)
        return _ok({"appended": saved})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def delete_note(path: str) -> str:
    """Delete a note by vault-relative path."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                deleted = api.delete_note(path)
            finally:
                api.close()
        else:
            deleted = _get_fs().delete_note(path)
        return _ok({"deleted": deleted})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


@mcp.tool()
def search_notes(
    query: str,
    folder: str = "",
    case_sensitive: bool = False,
    limit: int = 50,
) -> str:
    """Search note contents for a query string."""
    try:
        if _mode() == "restapi":
            api = _get_api()
            try:
                hits = api.search_notes(
                    query,
                    folder=folder,
                    case_sensitive=case_sensitive,
                    limit=limit,
                )
            finally:
                api.close()
        else:
            hits = _get_fs().search_notes(
                query,
                folder=folder,
                case_sensitive=case_sensitive,
                limit=limit,
            )
        return _ok({"query": query, "count": len(hits), "hits": hits})
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
