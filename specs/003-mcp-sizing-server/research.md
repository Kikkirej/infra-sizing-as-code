# Research: MCP Sizing Server

## MCP Python SDK — Library Choice

**Decision**: Use the official `mcp` package from `modelcontextprotocol/python-sdk` (`mcp>=1.0.0`), specifically its `FastMCP` high-level API.

**Rationale**: `FastMCP` provides a decorator-based tool registration API and returns a standard ASGI app via `.sse_app()` that mounts directly into the existing FastAPI instance with `app.mount()`. No additional ASGI framework is needed.

**Alternatives considered**:
- `fastmcp` (community package): overlapping API, now merged into the official SDK — use official.
- Raw `mcp.server.Server` low-level API: more boilerplate, no benefit for this scope.

---

## SSE Transport Mounting Pattern

**Decision**: Mount MCP at `/mcp` using `FastMCP.sse_app()`.

```python
# main.py addition
from mcp_server.server import mcp
app.mount("/mcp", mcp.sse_app())
```

This exposes two sub-paths automatically:
- `GET /mcp/sse` — SSE stream (clients connect here)
- `POST /mcp/messages` — message endpoint (used by the SSE transport internally)

The Cursor connection URL is therefore: `http://localhost:8000/mcp/sse`

**Rationale**: `sse_app()` returns a Starlette ASGI sub-application; FastAPI's `mount()` integrates it cleanly without conflicting with existing `/api` routes.

---

## Data Reading Strategy — Bypass state_store

**Decision**: MCP tools read directly from the `infra/` directory using thin wrappers around the existing `services/loader.py` functions. They do NOT read from `state_store`.

**Rationale**:
- `state_store` holds the in-memory editor state, which may contain unsaved changes (ChangeState.MODIFIED / ADDED / DELETED) that haven't been persisted to disk yet. MCP tools must reflect the committed on-disk truth.
- Reading from disk on every request is consistent with FR-006 (no caching) and keeps the MCP layer stateless.
- The existing `_load_product`, `_load_size`, `_load_flavour` functions in `loader.py` already handle the full hierarchy — the MCP reader wraps them with explicit not-found checks.

---

## Startup Validation

**Decision**: Add an explicit `infra/` presence check in the FastAPI lifespan before `state_store.load_state()`. If `infra/products.json` is missing or empty, raise `RuntimeError` with a clear message including the expected path.

**Rationale**: Fail-fast at startup (FR-010) prevents the server from running in a silently broken state. The error surfaces immediately in Docker/uvicorn logs.

---

## Clean MCP Response Models

**Decision**: Define lightweight response dataclasses in `mcp_server/reader.py` that strip editor-specific fields (`ChangeState`, `prefix_content`, `suffix_content`, `image_type`, `image_value`). These are serialized to plain dicts before being returned from MCP tools.

**Rationale**: MCP tool return values are text/JSON consumed by AI assistants. Including `ChangeState` or content blobs would add noise. The clean models expose only what is useful for infrastructure planning queries.

---

## Cursor Configuration Format

**Decision**: Document the `.cursor/mcp.json` project-level configuration file as the primary setup method, with the Cursor Settings UI as the secondary method.

```json
{
  "mcpServers": {
    "infra-sizing": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

**Rationale**: The `.cursor/mcp.json` file is version-controllable and can be checked into the repository, making team onboarding instant — clone the repo, start the backend, open Cursor. The UI method is documented as an alternative for users who prefer it.

---

## CI/CD Impact

**Decision**: Add `mcp>=1.0.0` to `src/web-editor/backend/requirements.txt`. No changes to `.gitlab-ci.yml` or `.github/workflows/build.yml` are required — both pipelines install from `requirements.txt` already.

**Rationale**: The new dependency is pulled in automatically by both existing CI pipelines via the existing pip install step.
