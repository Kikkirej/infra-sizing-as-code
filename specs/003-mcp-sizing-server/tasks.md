# Tasks: MCP Sizing Server

**Input**: Design documents from `specs/003-mcp-sizing-server/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/mcp-tools.md ✅, quickstart.md ✅

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3)

## Path Conventions

- **Backend source**: `src/web-editor/backend/`
- **Backend tests**: `src/web-editor/backend/tests/`
- **Documentation**: `docs/`
- **Cursor config example**: `.cursor/mcp.json` at repo root

---

## Phase 1: Setup

**Purpose**: Add new dependency and create the MCP server package skeleton

- [X] T001 Add `mcp>=1.0.0` to `src/web-editor/backend/requirements.txt`
- [X] T002 Create `src/web-editor/backend/mcp_server/__init__.py` (empty)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that all MCP tools depend on. Must be complete before any user story work.

**⚠️ CRITICAL**: No user story tasks can begin until this phase is complete.

- [X] T003 Implement `src/web-editor/backend/mcp_server/reader.py` with four functions: `read_products(repo_root)`, `read_sizes(repo_root, product)`, `read_flavours(repo_root, product, size)`, `read_flavour_spec(repo_root, product, size, flavour)` — reads from disk on every call (no state_store), raises `ValueError` with level-specific messages per FR-005 and data-model.md
- [X] T004 Add `infra/` startup validation to the `lifespan` context manager in `src/web-editor/backend/main.py`: check `REPO_ROOT/infra/products.json` exists and is non-empty before `state_store.load_state()`; raise `RuntimeError` with path in message on failure (FR-010)

**Checkpoint**: `reader.py` functions work in isolation and `main.py` fails fast when `infra/` is missing.

---

## Phase 3: User Story 1 — Query Sizing via AI Assistant (Priority: P1) 🎯 MVP

**Goal**: An AI assistant can retrieve the full hardware specification for any product/size/flavour combination.

**Independent Test**: Invoke `get_flavour_spec("acme-crm", "small", "appserver")` via the MCP server and verify the returned JSON matches `infra/acme-crm/small/appserver/servers.json`. Confirm a not-found error is returned for an invalid flavour name.

- [X] T005 [US1] Create `src/web-editor/backend/mcp_server/server.py`: instantiate `FastMCP("infra-sizing")`, read `REPO_ROOT` from environment, implement `get_flavour_spec(product, size, flavour)` tool using `reader.read_flavour_spec()` — returns JSON string on success, error string on `ValueError`
- [X] T006 [US1] Mount the MCP SSE sub-application in `src/web-editor/backend/main.py`: `app.mount("/mcp", mcp.sse_app())` after existing router registrations; import `mcp` from `mcp_server.server`
- [X] T007 [US1] Add `src/web-editor/backend/tests/test_mcp_tools.py`: test `get_flavour_spec` with valid `acme-crm/small/appserver` (verify CPU, memory, count fields), invalid product (verify error message), invalid size (verify error message), invalid flavour (verify error message)

**Checkpoint**: `get_flavour_spec` is fully functional. Backend starts, MCP endpoint is reachable at `http://localhost:8000/mcp/sse`, and an AI assistant can retrieve flavour hardware specs.

---

## Phase 4: User Story 2 — Discover Available Products and Sizes (Priority: P2)

**Goal**: An AI assistant can discover all available products, the size tiers for each product, and the flavours within a size — without any prior knowledge.

**Independent Test**: Invoke `list_products()` and verify it returns `acme-crm` and `acme-erp`. Invoke `list_sizes("acme-crm")` and verify `small`, `medium`, `large`. Invoke `list_flavours("acme-crm", "small")` and verify `appserver`, `dbserver`.

- [X] T008 [US2] Add `list_products()`, `list_sizes(product)`, and `list_flavours(product, size)` tools to `src/web-editor/backend/mcp_server/server.py` using `reader.read_products()`, `reader.read_sizes()`, `reader.read_flavours()` — return JSON string on success, error string on `ValueError`
- [X] T009 [US2] Extend `src/web-editor/backend/tests/test_mcp_tools.py`: tests for `list_products` (non-empty result, correct shortnames), `list_sizes` with valid product, `list_sizes` with invalid product (error message), `list_flavours` with valid product/size, `list_flavours` with invalid size (error message)

**Checkpoint**: All 4 tools work end-to-end. An AI assistant can navigate the full product → size → flavour → spec hierarchy.

---

## Phase 5: User Story 3 — Connect Cursor to the MCP Server (Priority: P3)

**Goal**: A developer can connect Cursor to the MCP server by following documentation alone, in under 10 minutes.

**Independent Test**: Follow `docs/mcp-server/cursor-integration.md` from start to finish on a clean Cursor installation. Verify the `infra-sizing` server appears in Cursor MCP settings and that asking "What products are available?" returns a correct answer.

- [X] T010 [P] [US3] Create `docs/mcp-server/cursor-integration.md` with: (1) Prerequisites — backend running on port 8000, (2) Project-level config via `.cursor/mcp.json` (recommended), (3) Cursor Settings UI alternative, (4) Verification step — ask "What products are available?", (5) Troubleshooting — server not appearing, connection refused, empty results (per FR-008, FR-009)
- [X] T011 [P] [US3] Create `.cursor/mcp.json` at repository root with the `infra-sizing` server config pointing to `http://localhost:8000/mcp/sse` so team members get instant Cursor integration on clone

**Checkpoint**: A new team member can clone the repo, start the backend, open Cursor, and immediately ask infrastructure sizing questions without any manual configuration.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, clean-up, and ensuring constitution compliance.

- [X] T012 Verify `mcp_server/reader.py` response shapes strip all editor-specific fields (`ChangeState`, `prefix_content`, `suffix_content`, `image_type`, `image_value`) before returning from `read_flavour_spec()` — cross-check against data-model.md FlavourSpec shape
- [X] T013 Run the full test suite from `src/web-editor/backend/`: `pytest tests/` — all tests must pass including existing tests and new MCP tests
- [X] T014 [P] Validate quickstart.md end-to-end: start backend locally, confirm MCP endpoint responds, confirm all 4 tools return expected data for `acme-crm/small/appserver`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002)
- **US1 (Phase 3)**: Depends on Phase 2 completion (T003, T004) — **MVP threshold**
- **US2 (Phase 4)**: Depends on Phase 2 completion; US1 not required but Phase 3 creates `server.py` that Phase 4 extends
- **US3 (Phase 5)**: Can start after Phase 2; fully independent of US1/US2 implementation
- **Polish (Phase 6)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2 foundational work
- **US2 (P2)**: Depends on Phase 2 and the `server.py` file created in US1 (T005)
- **US3 (P3)**: Depends only on Phase 2 (backend must start correctly); no dependency on US1 or US2 tools

### Within Each User Story

- reader.py functions (Phase 2) → tool implementation → mount/wiring → tests
- `server.py` created in T005 (US1), extended in T008 (US2) — sequential, same file

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T010 and T011 can run in parallel (different files, US3 docs + config)
- T013 and T014 can run in parallel (different validation activities)

---

## Parallel Example: US3

```bash
# Both US3 tasks touch different files and can run simultaneously:
Task T010: "Create docs/mcp-server/cursor-integration.md"
Task T011: "Create .cursor/mcp.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: Foundational (T003, T004)
3. Complete Phase 3: US1 (T005, T006, T007)
4. **STOP and VALIDATE**: MCP endpoint live, `get_flavour_spec` works end-to-end
5. Demo: Ask an AI assistant "What are the server specs for ACME CRM small appserver?"

### Incremental Delivery

1. Phases 1+2 → Foundation ready
2. Phase 3 → `get_flavour_spec` live (MVP: AI can answer specific sizing questions)
3. Phase 4 → Discovery tools live (AI can explore available products/sizes)
4. Phase 5 → Cursor docs live (team can self-serve onboarding)
5. Phase 6 → Polish complete, ready to merge

### Single Developer Strategy

Recommended sequence: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014

---

## Notes

- `reader.py` intentionally bypasses `state_store` — this is correct by design (see research.md)
- `mcp.sse_app()` mounts two sub-paths automatically: `/mcp/sse` (SSE stream) and `/mcp/messages` (POST endpoint)
- Cursor connection URL: `http://localhost:8000/mcp/sse`
- All tool return values are strings (JSON-serialized on success, plain error text on failure) — MCP tool convention
- Stop at any checkpoint to validate a user story independently before proceeding
