"""Optional Local REST API client for desktop Obsidian.

Requires the "Local REST API" community plugin. On phones this usually is
not available; use FilesystemVault with a synced vault folder instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .vault import VaultError


class RestApiVault:
    """Talk to Obsidian via Local REST API (desktop)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:27123",
        verify_ssl: bool = False,
        timeout: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise VaultError("OBSIDIAN_API_KEY is required for restapi mode")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            verify=verify_ssl,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise VaultError(
                f"Cannot reach Obsidian Local REST API at {self.base_url}: {exc}. "
                "On phone, use filesystem mode with a synced vault instead."
            ) from exc
        if response.status_code >= 400:
            detail = response.text[:500]
            raise VaultError(f"Obsidian API {response.status_code}: {detail}")
        return response

    def list_notes(self, folder: str = "", limit: int = 200) -> list[dict[str, str | int]]:
        # Local REST API does not have a single "list all notes" that is
        # universal across versions; use vault directory listing.
        prefix = folder.strip().strip("/")
        path = f"/vault/{prefix}" if prefix else "/vault/"
        response = self._request("GET", path)
        data = response.json()
        files = data.get("files", []) if isinstance(data, dict) else []
        notes: list[dict[str, str | int]] = []
        for name in files:
            if not isinstance(name, str):
                continue
            if name.endswith("/"):
                continue
            if not name.endswith(".md"):
                continue
            rel = f"{prefix}/{name}".strip("/") if prefix else name
            notes.append({"path": rel, "name": Path(name).stem, "size": -1})
            if len(notes) >= limit:
                break
        return notes

    def list_folders(self, folder: str = "") -> list[str]:
        prefix = folder.strip().strip("/")
        path = f"/vault/{prefix}" if prefix else "/vault/"
        response = self._request("GET", path)
        data = response.json()
        files = data.get("files", []) if isinstance(data, dict) else []
        folders: list[str] = []
        for name in files:
            if isinstance(name, str) and name.endswith("/"):
                rel = f"{prefix}/{name.rstrip('/')}".strip("/")
                folders.append(rel)
        return folders

    def read_note(self, note_path: str) -> str:
        path = self._vault_path(note_path)
        response = self._request("GET", path, headers={"Accept": "text/markdown"})
        return response.text

    def write_note(self, note_path: str, content: str, overwrite: bool = True) -> str:
        path = self._vault_path(note_path)
        if not overwrite:
            try:
                self.read_note(note_path)
            except VaultError:
                pass
            else:
                raise VaultError(f"Note already exists: {note_path}")
        self._request(
            "PUT",
            path,
            content=content.encode("utf-8"),
            headers={"Content-Type": "text/markdown"},
        )
        return self._normalize(note_path)

    def append_note(self, note_path: str, content: str) -> str:
        path = self._vault_path(note_path)
        self._request(
            "POST",
            path,
            content=content.encode("utf-8"),
            headers={"Content-Type": "text/markdown"},
        )
        return self._normalize(note_path)

    def delete_note(self, note_path: str) -> str:
        path = self._vault_path(note_path)
        self._request("DELETE", path)
        return self._normalize(note_path)

    def search_notes(
        self,
        query: str,
        folder: str = "",
        case_sensitive: bool = False,
        limit: int = 50,
    ) -> list[dict[str, str | int]]:
        # Simple search endpoint varies; fall back to reading listed notes
        # is too heavy — use /search/simple/ when available.
        try:
            response = self._request(
                "POST",
                "/search/simple/",
                json={"query": query, "contextLength": 100},
            )
            data = response.json()
        except VaultError:
            return []

        hits: list[dict[str, str | int]] = []
        if not isinstance(data, list):
            return hits
        for item in data:
            if not isinstance(item, dict):
                continue
            filename = str(item.get("filename", ""))
            if folder.strip() and not filename.startswith(folder.strip().strip("/")):
                continue
            matches = item.get("matches") or []
            snippet = ""
            line_no = 0
            if matches and isinstance(matches[0], dict):
                snippet = str(matches[0].get("context", ""))[:240]
            if case_sensitive and query not in snippet and query not in filename:
                # Keep filename hits even if snippet casing differs.
                pass
            hits.append({"path": filename, "line": line_no, "snippet": snippet})
            if len(hits) >= limit:
                break
        return hits

    def vault_stats(self) -> dict[str, int | str]:
        response = self._request("GET", "/")
        payload = response.json() if response.headers.get("content-type", "").startswith(
            "application/json"
        ) else {}
        return {
            "root": self.base_url,
            "note_count": -1,
            "mode": "restapi",
            "status": str(payload.get("status", "ok")),
        }

    @staticmethod
    def _normalize(note_path: str) -> str:
        cleaned = note_path.strip().lstrip("/")
        if not cleaned.endswith(".md"):
            cleaned = f"{cleaned}.md"
        return cleaned

    def _vault_path(self, note_path: str) -> str:
        return f"/vault/{self._normalize(note_path)}"
