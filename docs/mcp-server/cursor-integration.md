# Connecting Cursor to the Infrastructure Sizing MCP Server

The MCP server is built into the web editor backend. Once the backend is running, Cursor can query infrastructure sizing data directly through natural language.

---

## Prerequisites

The backend must be running and reachable at `http://localhost:8000`:

```bash
# Option A — Docker (recommended)
docker compose up backend

# Option B — Local
cd src/web-editor/backend
pip install -r requirements.txt
REPO_ROOT=$(pwd)/../../.. uvicorn main:app --reload --port 8000
```

Verify the MCP endpoint is live:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/mcp/sse
# Expected: 200
```

---

## Option 1: Project-level config via `.cursor/mcp.json` (Recommended)

This file is version-controlled in the repository. Team members who clone the repo get instant Cursor integration with no manual setup.

The file already exists at `.cursor/mcp.json` in this repository. If you cloned the repo, no action is needed.

Contents:

```json
{
  "mcpServers": {
    "infra-sizing": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

After starting the backend, open or restart Cursor. The `infra-sizing` server appears automatically under **Settings → MCP**.

---

## Option 2: Cursor Settings UI

If you prefer to configure MCP through Cursor's UI:

1. Open **Settings** (`Ctrl+,` / `Cmd+,`) → **MCP**
2. Click **Add Server**
3. Fill in:
   - **Name**: `infra-sizing`
   - **URL**: `http://localhost:8000/mcp/sse`
4. Click **Save**
5. Restart Cursor

---

## Verification

Once connected, open a Cursor chat and ask:

> What products are available?

Cursor should call `list_products` and return the available products (e.g. `acme-crm`, `acme-erp`).

Try the full hierarchy:

```
What size tiers does acme-crm have?
What flavours are in acme-crm small?
What are the server specs for acme-crm small appserver?
```

---

## Troubleshooting

### Server not appearing in Cursor MCP settings

- Verify the backend is running: `curl http://localhost:8000/mcp/sse`
- Check that `.cursor/mcp.json` exists at the **repository root** (not in a subdirectory)
- Restart Cursor fully (quit and reopen)

### Connection refused

- The backend is not running or is on a different port
- Start the backend: `docker compose up backend`
- Confirm the port: `curl http://localhost:8000/docs` should return the FastAPI docs

### Empty results or "no products found"

- The `REPO_ROOT` environment variable is not pointing to the repository root
- For local dev: `REPO_ROOT=$(pwd)/../../.. uvicorn main:app --reload --port 8000` from `src/web-editor/backend/`
- For Docker: `REPO_ROOT=/repo` is set in `docker-compose.yml` automatically

### MCP tools return error strings

Each tool returns a plain error string (not an exception) when data is not found:
- `"Product 'X' not found"` — the product shortname does not exist in `infra/products.json`
- `"Size 'Y' not found for product 'X'"` — the size does not exist for that product
- `"Flavour 'Z' not found for product 'X' size 'Y'"` — the flavour does not exist for that combination

Check the `infra/` directory to confirm the expected data exists.
