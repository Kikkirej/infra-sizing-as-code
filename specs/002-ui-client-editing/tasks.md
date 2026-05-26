# Tasks: Infrastructure Sizing Web Editor

**Input**: Design documents from `specs/002-ui-client-editing/`

**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/api.md ✅

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: User story this task belongs to (US1–US7)
- Exact file paths included in every task description

## Path Conventions

- **Backend app**: `src/web-editor/backend/`
- **Frontend app**: `src/web-editor/frontend/`
- **Docker Compose**: `docker-compose.yml` (repo root — justified deviation, see plan.md)
- **Sizing data**: `infra/` (existing layout; editor reads/writes in place)
- **Docs**: `docs/web-editor/`
- **CI/CD**: `.gitlab-ci.yml` + `.github/workflows/` (both required, Constitution IV)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding, Docker wiring, and basic skeleton for both services.

- [X] T001 Create directory tree: `src/web-editor/backend/{models,routers,services}/` and `src/web-editor/frontend/src/{api,stores,components/edit,views}/`
- [X] T002 Write `src/web-editor/backend/requirements.txt` (fastapi, uvicorn, gitpython, python-multipart, pytest, httpx)
- [X] T003 [P] Write `src/web-editor/frontend/package.json` with Vue 3.4, Vite 5, Pinia 2, Asciidoctor.js 3, Axios
- [X] T004 [P] Write `src/web-editor/backend/Dockerfile` (python:3.11-slim, install requirements, expose 8000, CMD uvicorn)
- [X] T005 [P] Write `src/web-editor/frontend/Dockerfile` (node:20-alpine, npm install, expose 5173, CMD vite --host)
- [X] T006 Write `docker-compose.yml` at repo root: backend service (port 8000, SSH_AUTH_SOCK mount, infra/ volume), frontend service (port 5173, depends_on backend)
- [X] T007 [P] Write `src/web-editor/frontend/vite.config.js` (server port 5173, `/api` proxy → `http://backend:8000`, host: true)
- [X] T008 [P] Write `src/web-editor/frontend/index.html` (root div id="app", script type module src/main.js)
- [X] T009 [P] Write `src/web-editor/frontend/src/main.js` (createApp, Pinia install, App.vue mount)
- [ ] T010 Verify `docker compose up -d` builds and starts both containers without errors (manual checkpoint)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, state singleton, loader, and frontend skeleton that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T011 Write Pydantic models in `src/web-editor/backend/models/infra.py`: `TypedValue` (static/dynamic discriminated), `Partition`, `Server`, `FlavourImage`, `Flavour`, `Size`, `Product` — mirror on-disk JSON schema from data-model.md
- [X] T012 [P] Write in-memory state model in `src/web-editor/backend/models/state.py`: `ChangeState` enum (CLEAN/MODIFIED/ADDED/DELETED/ERROR), `TypedValueNode` (+ `invalid: bool`), `PartitionNode`, `ServerNode`, `FlavourNode`, `SizeNode`, `ProductNode` (+ `error` field), `UnitsNode`, `EditorState`
- [X] T013 Write `src/web-editor/backend/services/loader.py`: `load_infra(repo_root) → EditorState` — reads `infra/products.json`, loads each product subtree, handles malformed `servers.json` by setting `ProductNode.change = ERROR` and `ProductNode.error = <message>` (FR-031)
- [X] T014 [P] Write `src/web-editor/backend/services/state_store.py`: module-level `_state: EditorState | None`, `load_state(repo_root)`, `get_state() → EditorState` — called once at FastAPI startup
- [X] T015 [P] Write atomic write utilities in `src/web-editor/backend/services/writer.py`: `atomic_write_json(path, data)` and `atomic_write_text(path, content)` using `tempfile.mkstemp` + `os.replace` (FR-022a)
- [X] T016 Write `src/web-editor/backend/main.py`: FastAPI app factory, `CORSMiddleware` (allow origin `http://localhost:5173`), startup event calls `state_store.load_state(repo_root)`, register router placeholders for tree, products, adoc, files, units, git
- [X] T017 [P] Write `src/web-editor/frontend/src/App.vue`: two-panel layout (left 280px `TreePanel`, right flex `MainPanel`), top nav bar with app title and Commit button stub
- [X] T018 [P] Write `src/web-editor/frontend/src/api/client.js`: Axios instance with `baseURL: '/api'`, JSON content-type default
- [X] T019 [P] Write `src/web-editor/frontend/src/stores/tree.js`: Pinia store — `treeData`, `selectedNode`, `fetchTree()` (GET /api/tree), `selectNode(node)`, `updateNodeChange(path, change)`
- [X] T020 [P] Write `src/web-editor/frontend/src/stores/units.js`: Pinia store — `units: []`, `fetchUnits()` (GET /api/units), `addUnit`, `removeUnit`
- [ ] T021 Verify `docker compose up -d` hits `GET /api/tree` and receives a valid JSON response (manual checkpoint — no UI yet)

---

## Phase 3: User Story 1 — Navigate the Tree and Edit Any Entity (Priority: P1) 🎯 MVP

**Goal**: Operator sees the full hierarchy in a tree, clicks any node to edit its fields in the main panel. Changes are held in memory with visual unsaved indicators.

**Independent Test**: Launch editor → confirm tree populated → click flavour node → server fields appear → edit CPU value → confirm field updates → confirm no disk file changed.

### Implementation for User Story 1

- [X] T022 [P] [US1] Implement `GET /api/tree` in `src/web-editor/backend/routers/tree.py`: serialize `EditorState` to nested tree response with `change` field on each node; include `error` field for ERROR nodes
- [X] T023 [P] [US1] Implement `GET /api/products/{shortname}` in `src/web-editor/backend/routers/products.py`: return full `ProductNode` with all nested data and field values
- [X] T024 [P] [US1] Implement `PUT /api/products/{shortname}` in `src/web-editor/backend/routers/products.py`: update display_name in state_store, mark node MODIFIED
- [X] T025 [P] [US1] Implement `GET` and `PUT` for sizes in `src/web-editor/backend/routers/products.py`: `GET /api/products/{p}/sizes/{s}` returns full SizeNode; `PUT` updates display_name only (prefix/suffix stored as `.adoc` files, edited via T060–T061 adoc router)
- [X] T026 [P] [US1] Implement `GET` and `PUT` for flavours in `src/web-editor/backend/routers/products.py`: `GET /api/products/{p}/sizes/{s}/flavours/{f}`; `PUT` updates display_name and image ref
- [X] T027 [P] [US1] Implement `GET` and `PUT` for servers in `src/web-editor/backend/routers/products.py`: `GET /api/products/{p}/sizes/{s}/flavours/{f}/servers`; `PUT /...servers/{index}` replaces ServerNode, marks MODIFIED
- [X] T028 [US1] Write `src/web-editor/frontend/src/components/TreePanel.vue`: recursive tree rendering (product → size → flavour → server), blue dot indicator for MODIFIED/ADDED nodes, strikethrough + red for DELETED nodes, click handler calls `store.selectNode`
- [X] T029 [P] [US1] Write `src/web-editor/frontend/src/components/edit/ProductEdit.vue`: shortname (readonly), display_name (editable text input); on blur/change call `PUT /api/products/{shortname}` and update store
- [X] T030 [P] [US1] Write `src/web-editor/frontend/src/components/edit/SizeEdit.vue`: shortname (readonly), display_name input; on change call `PUT /api/.../sizes/{shortname}` (prefix/suffix content is editable via AdocEditor when size prefix/suffix nodes are selected in the tree)
- [X] T031 [P] [US1] Write `src/web-editor/frontend/src/components/edit/FlavourEdit.vue`: shortname (readonly), display_name; image ref display (type + value, read-only here — upload handled in US5)
- [X] T032 [P] [US1] Write `src/web-editor/frontend/src/components/edit/TypedValueInput.vue`: toggle static/dynamic mode, value (number) or formula (text) input, unit `<select>` populated from `units` store
- [X] T033 [P] [US1] Write `src/web-editor/frontend/src/components/edit/ServerEdit.vue`: system name, count, cpu (TypedValueInput), cpu_clocking, memory (TypedValueInput), disk partition list (each with TypedValueInput + performance + comment), network[] and software[] as tag-style lists, comment
- [X] T034 [US1] Write `src/web-editor/frontend/src/components/MainPanel.vue`: conditionally renders `ProductEdit`, `SizeEdit`, `FlavourEdit`, or `ServerEdit` based on `selectedNode.type`; falls back to OverviewPanel (stub) when nothing selected
- [X] T035 [US1] Wire tree selection → main panel in `App.vue` and tree store: click node → `fetchDetail(node)` → populate edit component → auto-apply current edits via PUT before switching (FR-011a)

**Checkpoint**: Tree is fully navigable and all entity types are editable. Confirm no disk writes occur. US1 is independently testable.

---

## Phase 4: User Story 2 — Overview Dashboard (Priority: P1)

**Goal**: When no node is selected, the main panel shows a summary of all products with live in-memory counts.

**Independent Test**: Load editor with two products → confirm overview lists both with correct size/flavour/server counts → add a new flavour in memory → confirm count updates in overview.

### Implementation for User Story 2

- [X] T036 [US2] Implement `GET /api/overview` in `src/web-editor/backend/routers/tree.py`: compute per-product counts (sizes, flavours, servers) from in-memory state — include ADDED, exclude DELETED; include `has_error` flag
- [X] T037 [US2] Write `src/web-editor/frontend/src/components/OverviewPanel.vue`: product cards showing display_name, size count, flavour count, server count; red error badge when `has_error`; click product name → selects that product in tree store
- [X] T038 [US2] Wire OverviewPanel into `MainPanel.vue`: render when `selectedNode === null`; refresh on tree store mutations (Pinia watch)

**Checkpoint**: Overview panel shows live counts. Selecting a product from the overview selects it in the tree. US2 independently testable.

---

## Phase 5: User Story 7 — Commit and Reset Changes (Priority: P1)

**Goal**: Operator commits all in-memory changes (writes files, git commit + push) and can reset a product to on-disk state.

**Independent Test**: Edit two products → reset one → confirm its in-memory state reverts while other retains edits → commit second product → confirm file on disk updated → git log shows new commit.

### Implementation for User Story 7

- [X] T039 [US7] Write `src/web-editor/backend/services/git_service.py`: `get_status() → GitStatus` (branch, is_detached, has_remote, remote_name), `commit_and_push(message) → CommitResult` (commit_sha, pushed, push_failed, error), `retry_push() → PushResult` — uses GitPython with inherited SSH_AUTH_SOCK env
- [X] T040 [P] [US7] Implement `GET /api/git/status` in `src/web-editor/backend/routers/git.py`
- [X] T041 [P] [US7] Implement `GET /api/git/changes` in `src/web-editor/backend/routers/git.py`: walk EditorState, collect all nodes with change ≠ CLEAN, return flat list of human-readable names with change type tag
- [X] T042 [US7] Implement write-to-disk logic in `src/web-editor/backend/services/writer.py`: `write_all(state, repo_root)` — write servers.json → meta.json → registry files (products.json, sizes.json, flavours.json) → .adoc files → units.json → delete DELETED dirs (leaf-to-root); all via `atomic_write_json` / `atomic_write_text`
- [X] T043 [US7] Implement `POST /api/git/commit` in `src/web-editor/backend/routers/git.py`: validate commit gates (detached HEAD → 409, invalid TypedValues → 422, empty system/no partitions → 422), call `writer.write_all`, then `git_service.commit_and_push`; on push failure return `push_failed: true` with `commit_sha`
- [X] T044 [US7] Implement `POST /api/git/push` in `src/web-editor/backend/routers/git.py`: call `git_service.retry_push`
- [X] T045 [US7] Implement `POST /api/products/{shortname}/reset` in `src/web-editor/backend/routers/products.py`: call `loader.load_product(repo_root, shortname)` → replace ProductNode in state_store, all other products unaffected
- [X] T046 [US7] Write `src/web-editor/frontend/src/components/CommitPanel.vue`: change list (flat names from GET /api/git/changes), commit message `<textarea>`, "Commit & Push" button and "Commit Only" button (both disabled when no changes or detached HEAD), Retry Push button (shown when last commit response had `push_failed: true`), error/success banners
- [X] T047 [US7] Wire CommitPanel as drawer in `App.vue`: Commit button in top nav opens drawer; on successful commit refresh tree store; detect detached HEAD via GET /api/git/status on open
- [X] T048 [US7] Add Reset Product button to `ProductEdit.vue` header: calls `POST /api/products/{shortname}/reset` → refreshes tree store; button disabled for ADDED products (nothing on disk to reset to)

**Checkpoint**: Full commit cycle works end-to-end. Reset restores one product without affecting others. Push-retry flow works after simulated push failure.

---

## Phase 6: User Story 3 — Add, Copy, and Delete Entries (Priority: P2)

**Goal**: Operator can add new entities at any level, copy/paste flavours, and delete entities with in-memory staging.

**Independent Test**: Copy a flavour → paste under different size → verify duplicate appears with `-copy` suffix → delete a server → verify strikethrough → commit → verify files reflect both operations.

### Implementation for User Story 3

- [X] T049 [P] [US3] Implement `POST /api/products` in `src/web-editor/backend/routers/products.py`: create new ProductNode (ADDED), return 409 on shortname conflict (FR-032)
- [X] T050 [P] [US3] Implement `POST /api/products/{p}/sizes` in `src/web-editor/backend/routers/products.py`: add SizeNode (ADDED), 409 on conflict within product
- [X] T051 [P] [US3] Implement `POST /api/products/{p}/sizes/{s}/flavours` in `src/web-editor/backend/routers/products.py`: add FlavourNode (ADDED, empty servers list), 409 on conflict within size
- [X] T052 [P] [US3] Implement `POST /api/.../servers` in `src/web-editor/backend/routers/products.py`: append ServerNode (ADDED) to flavour's server list
- [X] T053 [P] [US3] Implement `DELETE` for products, sizes, flavours, servers in `src/web-editor/backend/routers/products.py`: mark DELETED; ADDED nodes can be fully removed from state_store instead of marked DELETED (no disk counterpart)
- [X] T054 [US3] Implement `POST /api/products/{p}/sizes/{s}/flavours/{f}/copy` in `src/web-editor/backend/routers/products.py`: deep-copy FlavourNode + all ServerNodes to target size; auto-append `-copy` (then `-copy-2`, etc.) on shortname conflict; mark copy ADDED; return 422 if target size does not exist
- [X] T055 [US3] Add inline shortname conflict feedback: POST endpoints return 409 with `{"detail": "shortname '<x>' already exists"}`, frontend shows inline validation error on shortname field and blocks further input until changed (FR-032)
- [X] T056 [US3] Add "Add" action to `TreePanel.vue` nodes: `+` icon on hover for each node type; clicking adds child entity via POST → selects new node in tree for immediate editing
- [X] T057 [US3] Add "Add first product" empty state to `TreePanel.vue` (shown when `treeData.products` is empty) and welcome message placeholder in `MainPanel.vue` (FR-033)
- [X] T058 [US3] Add "Delete" context action to tree nodes and edit panel headers: confirmation prompt → DELETE call → node stays in tree with strikethrough/red styling (FR-017a)
- [X] T059 [US3] Add "Copy" / "Paste" context actions for flavour nodes in `TreePanel.vue`: copy stores `{product, size, flavour}` path in component state; paste on a size node calls POST `.../copy` with target product+size; paste disabled on non-size targets

**Checkpoint**: Full CRUD cycle at all hierarchy levels works in-memory. Copied flavour appears with `-copy` suffix. DELETED nodes show strikethrough until committed.

---

## Phase 7: User Story 4 — Edit AsciiDoc Files with Integrated Editor (Priority: P2)

**Goal**: Product and flavour prefix/suffix `.adoc` files are editable from the tree with a plain textarea and a live preview toggle.

**Independent Test**: Open product prefix → change a sentence → toggle Preview → verify rendered HTML → commit → verify `.adoc` file on disk updated.

### Implementation for User Story 4

- [X] T060 [P] [US4] Implement `GET /api/adoc/{path:path}` in `src/web-editor/backend/routers/adoc.py`: return adoc content from state_store (empty string + ADDED change if file absent)
- [X] T061 [P] [US4] Implement `PUT /api/adoc/{path:path}` in `src/web-editor/backend/routers/adoc.py`: update adoc content in state_store, mark prefix_change or suffix_change MODIFIED on the parent ProductNode/FlavourNode
- [X] T062 [US4] Add prefix and suffix child nodes to `TreePanel.vue` under each product and each flavour (rendered as leaf nodes with change indicator; shown even when files are absent, ADDED state)
- [X] T063 [US4] Write `src/web-editor/frontend/src/components/edit/AdocEditor.vue`: plain `<textarea>` bound to content fetched via GET /api/adoc/{path}; Edit / Preview toggle button; Preview panel renders content via `asciidoctor.convert(content, {safe: 'safe'})` bound to `v-html` (FR-013a); on textarea change call PUT /api/adoc/{path}
- [X] T064 [US4] Wire AdocEditor into `MainPanel.vue`: render when selected node type is `prefix` or `suffix`

**Checkpoint**: Clicking any prefix/suffix node opens the textarea editor. Preview renders correctly. Change indicator appears on the node after edit.

---

## Phase 8: User Story 5 — Upload Files (Priority: P3)

**Goal**: Operator uploads PNG, SVG, or `.mmd` files to a flavour's directory directly from the flavour edit panel.

**Independent Test**: Open flavour → upload PNG → confirm file appears in flavour directory on host → confirm meta.json image ref updated after commit.

### Implementation for User Story 5

- [X] T065 [US5] Implement `POST /api/files/upload/{product}/{size}/{flavour}` in `src/web-editor/backend/routers/files.py`: validate MIME type (image/png, image/svg+xml) or extension (.mmd); `atomic_write` to flavour dir; update FlavourNode image ref in state_store; return 422 on bad type, 507 on write failure (FR-022a)
- [X] T066 [US5] Add file upload control to `FlavourEdit.vue`: `<input type="file" accept=".png,.svg,.mmd">`; on change POST to upload endpoint; show success (filename) or error banner; update displayed image ref on success; reject unsupported types client-side before upload (FR-022)

**Checkpoint**: File upload writes to disk immediately. Unsupported types are rejected with an error.

---

## Phase 9: User Story 6 — Manage Centrally Defined Units (Priority: P3)

**Goal**: Operator can view, add, and delete units from the central registry; TypedValue fields only offer registry units.

**Independent Test**: Add "PiB" unit → confirm it appears in TypedValueInput unit selector → delete a unit in use → confirm affected TypedValues marked invalid → fix them → commit allowed.

### Implementation for User Story 6

- [X] T067 [P] [US6] Implement `GET /api/units` in `src/web-editor/backend/routers/units.py`
- [X] T068 [P] [US6] Implement `POST /api/units` in `src/web-editor/backend/routers/units.py`: add unit to UnitsNode, mark MODIFIED, 409 on duplicate
- [X] T069 [US6] Implement `DELETE /api/units/{unit}` in `src/web-editor/backend/routers/units.py`: remove unit, walk all TypedValueNodes referencing that unit and set `invalid = true`, return `affected_paths` list (FR-026)
- [X] T070 [US6] Seed `infra/units.json` on startup in `src/web-editor/backend/services/loader.py`: if file absent, create UnitsNode with defaults `["vCPU","GB","GiB","TB","TiB","GHz","MHz"]` and mark ADDED
- [X] T071 [US6] Write `src/web-editor/frontend/src/components/UnitsRegistryPanel.vue`: unit chips list, add-unit text input + Add button (POST /api/units), delete icon per unit (DELETE with warning modal showing `affected_paths` before confirming)
- [X] T072 [US6] Wire `UnitsRegistryPanel` into `App.vue` top nav (Settings → Units link or button opens panel/modal)
- [X] T073 [US6] Update `TypedValueInput.vue` `<select>` to source units from `units` store (already wired in T032); display "⚠ invalid unit" warning on the select when `node.invalid = true`; units store refreshes after any add/delete

**Checkpoint**: Units registry CRUD works. Adding "PiB" makes it available in all TypedValue selectors. Deleting an in-use unit marks TypedValues invalid and blocks commit.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD pipeline wiring, edge-case hardening, and final validation.

- [X] T074 [P] Write `docs/web-editor/overview.md`: feature purpose, architecture (FastAPI + Vue/Vite + Docker), infra/ file structure introduced (units.json), design decisions summary
- [X] T075 [P] Write `docs/web-editor/runbook.md`: launch steps, SSH agent troubleshooting, how to inspect container logs, how to recover from failed push manually
- [X] T076 Add `web-editor` stage to `.gitlab-ci.yml`: backend job (`pytest src/web-editor/backend/`), frontend job (`cd src/web-editor/frontend && npm run test:unit`)
- [X] T077 [P] Add `web-editor` stage to `.github/workflows/` with equivalent backend and frontend jobs (Constitution IV parity with GitLab)
- [X] T078 [P] Wire detached HEAD guard in `CommitPanel.vue`: on panel open call GET /api/git/status; if `is_detached`, disable Commit button and show error banner with `git checkout <branch>` instruction (FR-034)
- [X] T079 [P] Wire ERROR product styling in `TreePanel.vue`: nodes with `change === 'ERROR'` render with red warning icon and tooltip showing `error` message; edit panel shows error state instead of edit form (FR-031)
- [X] T081 [P] Implement Escape key handlers in `CommitPanel.vue` (close drawer), delete-confirmation modal (cancel deletion), and `UnitsRegistryPanel.vue` (close panel) using `@keyup.esc` listeners or a shared focus-trap composable (FR-035)
- [ ] T080 Run quickstart.md validation: follow all steps end-to-end in a clean Docker environment; manually verify SC-001 (launch + first edit ≤ 2 min), SC-002 (tree visible ≤ 3 s), SC-004 (commit ≤ 5 s for ≤ 20 files), SC-005 (reset ≤ 1 s), SC-007 (overview loads ≤ 2 s)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **blocks all user story phases**
- **US1 (Phase 3)**: Depends on Phase 2 — **MVP; must complete before other stories are useful**
- **US2 (Phase 4)**: Depends on Phase 2; can run in parallel with US7 and US3 after US1 backend is up
- **US7 (Phase 5)**: Depends on Phase 2; writer service depends on state model from foundational
- **US3 (Phase 6)**: Depends on US1 (tree must render before add/copy/delete UX makes sense)
- **US4 (Phase 7)**: Depends on Phase 2 (adoc routers independent of US1 tree logic)
- **US5 (Phase 8)**: Depends on US1 (FlavourEdit.vue must exist — US5 adds to it)
- **US6 (Phase 9)**: Depends on Phase 2 (units store wired in T020); TypedValueInput.vue depends on T032 (US1)
- **Polish (Phase 10)**: Depends on all desired user stories complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|-----------|------------------|
| US1 (P1) | Phase 2 | — |
| US2 (P1) | Phase 2 | US7 |
| US7 (P1) | Phase 2 | US2 |
| US3 (P2) | US1 complete | US4 |
| US4 (P2) | Phase 2 | US3 |
| US5 (P3) | US1 (FlavourEdit) | US6 |
| US6 (P3) | Phase 2 + US1 (TypedValueInput) | US5 |

### Within Each User Story

- Backend router tasks marked [P] can run in parallel
- Frontend edit component tasks marked [P] can run in parallel
- Backend must be functional before integration with frontend

---

## Parallel Execution Examples

### Phase 3 — US1

```
Backend endpoints (run together):
  T022 GET /api/tree
  T023 GET /api/products/{shortname}
  T024 PUT /api/products/{shortname}
  T025 GET+PUT sizes
  T026 GET+PUT flavours
  T027 GET+PUT servers

Frontend edit components (run together, after T022 is ready):
  T029 ProductEdit.vue
  T030 SizeEdit.vue
  T031 FlavourEdit.vue
  T032 TypedValueInput.vue
  T033 ServerEdit.vue
```

### Phase 5 — US7

```
Git router stubs (run together):
  T040 GET /api/git/status
  T041 GET /api/git/changes
```

### Phase 6 — US3

```
Add/Delete backend endpoints (run together):
  T049 POST /api/products
  T050 POST .../sizes
  T051 POST .../flavours
  T052 POST .../servers
  T053 DELETE endpoints
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T010)
2. Complete Phase 2: Foundational (T011–T021)
3. Complete Phase 3: US1 (T022–T035)
4. **STOP & VALIDATE**: full tree navigation and field editing works; no disk writes

### Incremental Delivery

1. Phase 1 + 2 → skeleton running in Docker
2. + Phase 3 (US1) → **MVP**: navigable tree with editable fields
3. + Phase 4 (US2) → Overview dashboard
4. + Phase 5 (US7) → Commit/push/reset — editor is now fully usable
5. + Phase 6 (US3) → Add/copy/delete
6. + Phase 7 (US4) → AsciiDoc editor
7. + Phase 8 (US5) → File upload
8. + Phase 9 (US6) → Units registry
9. + Phase 10 → Polish, CI, docs

---

## Summary

| Phase | User Story | Tasks | Priority |
|-------|-----------|-------|----------|
| 1 Setup | — | T001–T010 | — |
| 2 Foundational | — | T011–T021 | — |
| 3 | US1: Tree & Edit | T022–T035 | P1 🎯 MVP |
| 4 | US2: Overview | T036–T038 | P1 |
| 5 | US7: Commit & Reset | T039–T048 | P1 |
| 6 | US3: Add/Copy/Delete | T049–T059 | P2 |
| 7 | US4: AsciiDoc Editor | T060–T064 | P2 |
| 8 | US5: File Upload | T065–T066 | P3 |
| 9 | US6: Units Registry | T067–T073 | P3 |
| 10 Polish | — | T074–T081 | — |
| **Total** | | **81 tasks** | |

---

## Notes

- `[P]` = parallelizable (different files, no inter-task dependencies)
- `[Story]` label maps each task to its user story for traceability
- Commit after each phase checkpoint
- Each phase checkpoint = independently testable increment
- Run quickstart.md end-to-end before marking Phase 10 complete
