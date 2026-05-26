# Quickstart: MCP Sizing Server

## What's being built

An MCP (Model Context Protocol) server mounted into the existing web editor backend. It exposes 4 tools that let AI assistants (Cursor, Claude, etc.) query infrastructure sizing data directly from the `infra/` repository.

## New files

```text
src/web-editor/backend/
├── mcp_server/
│   ├── __init__.py          # Empty
│   ├── server.py            # FastMCP instance + 4 tool definitions
│   └── reader.py            # Disk reader: bypasses state_store, reads infra/ fresh
├── requirements.txt         # Add: mcp>=1.0.0
├── main.py                  # Add: app.mount("/mcp", mcp.sse_app())
                             #       + startup infra/ validation

docs/mcp-server/
└── cursor-integration.md    # Cursor setup guide + troubleshooting
```

## Key design decisions (from research.md)

- **No state_store**: MCP tools read from disk on every call. The `state_store` holds unsaved editor changes — MCP must reflect committed on-disk truth only.
- **Bypass loader caching**: Call `_load_product` / `_load_size` / `_load_flavour` from `services/loader.py` directly in `reader.py`, wrapped with explicit not-found checks.
- **Same process, same port**: Mounted at `/mcp` within the existing FastAPI app. No new ports or processes.
- **Fail-fast**: Check `infra/products.json` exists and is non-empty before starting. Raise `RuntimeError` with the expected path if missing.
- **Clean response shapes**: Strip `ChangeState`, prefix/suffix content, and image data before returning from MCP tools (see data-model.md).

## Running locally

```bash
# Start the backend (MCP is automatically available)
docker compose up backend

# Or without Docker:
cd src/web-editor/backend
pip install -r requirements.txt
REPO_ROOT=$(pwd)/../../.. uvicorn main:app --reload --port 8000
```

MCP SSE endpoint: `http://localhost:8000/mcp/sse`

## Connecting Cursor

See `docs/mcp-server/cursor-integration.md` for step-by-step setup.

Short version: create `.cursor/mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "infra-sizing": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

Then restart Cursor. The `infra-sizing` server will appear under Settings → MCP.

## Testing the tools

Use the MCP inspector or `curl` to verify:

```bash
# List products
curl -s -N -H "Accept: text/event-stream" http://localhost:8000/mcp/sse
# (Then send tool calls via POST /mcp/messages)
```

Or run the backend tests:
```bash
cd src/web-editor/backend
pytest tests/
```

New tests to add (see tasks.md):
- `tests/test_mcp_tools.py` — covers all 4 tools, not-found errors, and startup validation
