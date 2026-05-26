# Implementation Plan: MCP Sizing Server

**Branch**: `003-mcp-sizing-server` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-mcp-sizing-server/spec.md`

## Summary

Add an MCP (Model Context Protocol) server to the existing FastAPI backend that exposes four tools for querying infrastructure sizing data directly from the `infra/` repository. The server communicates via HTTP/SSE transport, mounts at `/mcp` within the existing backend process (port 8000), and reads data fresh from disk on every request — bypassing the editor's in-memory `state_store`. A Cursor integration guide is delivered in `docs/mcp-server/`.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: FastAPI 0.111, Uvicorn 0.29, Pydantic 2.7, `mcp>=1.0.0` (to be added)

**Storage**: File system — `infra/` directory tree, read at query time (no caching)

**Testing**: pytest + httpx (existing framework)

**Target Platform**: Linux server (Docker) + local dev (both already served by existing backend)

**Project Type**: Web service — MCP endpoint mounted as ASGI sub-application into existing FastAPI backend

**Performance Goals**: Tool responses under 2 seconds (SC-001)

**Constraints**: Read-at-query-time, no caching; same process as web editor backend; fail-fast on missing `infra/`; local/internal use only (no auth)

**Scale/Scope**: Local/internal; no concurrent-user scaling required for v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git as Single Source of Truth | ✅ Pass | MCP tools read from `infra/` files in Git; no side-channel state |
| II. File-First Architecture | ✅ Pass | New code in `src/web-editor/backend/mcp_server/`; docs in `docs/mcp-server/` |
| III. Infrastructure as Code | ✅ Pass | No new infra definitions; reads existing `infra/` structure |
| IV. CI/CD Portability | ✅ Pass | Adding `mcp>=1.0.0` to `requirements.txt` is picked up by both GitLab CI and GitHub Actions automatically |
| V. Documentation-Driven Development | ✅ Pass | `docs/mcp-server/cursor-integration.md` delivered as part of this feature |

No gate violations. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/003-mcp-sizing-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── mcp-tools.md     # Phase 1 output — 4 tool contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/web-editor/backend/
├── main.py                    # Modified: mount MCP sub-app + startup infra/ check
├── mcp_server/
│   ├── __init__.py            # New (empty)
│   ├── server.py              # New: FastMCP instance + 4 tool definitions
│   └── reader.py              # New: disk reader (bypasses state_store)
├── requirements.txt           # Modified: add mcp>=1.0.0
└── tests/
    └── test_mcp_tools.py      # New: tests for all 4 tools + error paths

docs/
└── mcp-server/
    └── cursor-integration.md  # New: Cursor setup guide + troubleshooting
```

**Structure Decision**: MCP logic is isolated in `src/web-editor/backend/mcp_server/` — a new sub-package within the existing backend. This keeps MCP concerns separate from the editor's REST routers while sharing models and the existing loader. The `docs/mcp-server/` directory follows the established pattern of `docs/<feature-name>/`.

## Implementation Notes

### mcp_server/reader.py

- `read_products(repo_root)` → reads `infra/products.json`, returns `list[dict]`
- `read_sizes(repo_root, product)` → reads `infra/<product>/sizes.json`, raises `ValueError` if product not found
- `read_flavours(repo_root, product, size)` → reads `infra/<product>/<size>/flavours.json`, raises `ValueError` if not found
- `read_flavour_spec(repo_root, product, size, flavour)` → uses `_load_flavour` from `services/loader.py`, returns clean dict (strips `ChangeState` and content fields)

Error messages follow the pattern in FR-005 and data-model.md.

### mcp_server/server.py

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("infra-sizing")

@mcp.tool()
def list_products() -> str: ...

@mcp.tool()
def list_sizes(product: str) -> str: ...

@mcp.tool()
def list_flavours(product: str, size: str) -> str: ...

@mcp.tool()
def get_flavour_spec(product: str, size: str, flavour: str) -> str: ...
```

All tools return JSON-serialized strings (MCP tool convention). `REPO_ROOT` is read from the environment variable at import time (consistent with existing backend pattern).

### main.py changes

1. Add startup validation in `lifespan`: check `REPO_ROOT/infra/products.json` exists and is non-empty before `state_store.load_state()`.
2. Mount MCP app: `app.mount("/mcp", mcp.sse_app())` after existing router registrations.

### docs/mcp-server/cursor-integration.md

Content:
1. Prerequisites (backend running on port 8000)
2. Project-level config via `.cursor/mcp.json` (recommended, version-controllable)
3. Cursor Settings UI alternative
4. Verification step: ask Cursor "What products are available?"
5. Troubleshooting: server not appearing, connection refused, empty results
