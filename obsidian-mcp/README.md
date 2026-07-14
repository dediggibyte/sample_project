# Obsidian MCP

MCP server that lets Cursor (and other MCP clients) read and write your **Obsidian** vault — including vaults you keep on your **phone**.

## Phone vault (recommended)

Obsidian on iOS/Android cannot expose Local REST API to Cursor Cloud the way desktop can. Sync the vault to a folder on the machine that runs Cursor, then point this MCP at that folder.

1. Sync your phone vault with one of:
   - **Obsidian Sync**
   - **iCloud / Dropbox / Google Drive / OneDrive**
   - **Syncthing**
   - **Git**
2. On the computer that runs Cursor, confirm the vault folder contains your `.md` notes (and usually a `.obsidian` folder).
3. Install and configure this MCP (below).

## Tools

| Tool | Purpose |
|------|---------|
| `vault_info` | Mode, path, note count |
| `list_notes` | List markdown notes |
| `list_folders` | List folders |
| `read_note` | Read a note |
| `write_note` | Create / overwrite a note |
| `append_to_note` | Append to a note |
| `delete_note` | Delete a note |
| `search_notes` | Search note contents |

## Setup (filesystem mode — phone)

```bash
cd obsidian-mcp
uv sync
```

Add to Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/obsidian-mcp",
        "obsidian-mcp"
      ],
      "env": {
        "OBSIDIAN_MODE": "filesystem",
        "OBSIDIAN_VAULT_PATH": "/ABSOLUTE/PATH/TO/your/ObsidianVault"
      }
    }
  }
}
```

Restart Cursor MCP / reload window. Ask: “list my Obsidian notes” or “search my vault for …”.

See `examples/cursor-mcp.json` for a copy-paste template.

## Desktop mode (Local REST API)

If Obsidian is running on the **same machine** as Cursor:

1. Install community plugin **Local REST API**.
2. Enable the HTTP server (port `27123`) or use HTTPS (`27124`).
3. Copy the API key.

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/obsidian-mcp",
        "obsidian-mcp"
      ],
      "env": {
        "OBSIDIAN_MODE": "restapi",
        "OBSIDIAN_API_KEY": "your-api-key",
        "OBSIDIAN_BASE_URL": "http://127.0.0.1:27123",
        "OBSIDIAN_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OBSIDIAN_MODE` | `filesystem` | `filesystem` or `restapi` |
| `OBSIDIAN_VAULT_PATH` | — | Absolute path to vault (filesystem mode) |
| `OBSIDIAN_API_KEY` | — | Local REST API key (restapi mode) |
| `OBSIDIAN_BASE_URL` | `http://127.0.0.1:27123` | Local REST API base URL |
| `OBSIDIAN_VERIFY_SSL` | `false` | Verify TLS (set `true` for trusted certs) |

## Develop / test

```bash
cd obsidian-mcp
uv sync --extra dev
uv run pytest
```

## Notes

- Paths are vault-relative (`Daily/2026-07-14.md`). `.md` is added if omitted.
- `.obsidian`, `.trash`, and `.git` are skipped when listing/searching.
- Path traversal outside the vault root is blocked.
- Writes go to the synced folder; Obsidian on your phone picks them up after sync.
