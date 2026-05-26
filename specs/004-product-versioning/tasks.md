# Tasks: Product Version Management

**Input**: Design documents from `specs/004-product-versioning/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/versioning-api.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies within the phase)
- **[Story]**: Maps to user stories US1–US4 from `spec.md`

## Path Conventions

- `src/` — application logic (Python backend + Vue/JS frontend)
- `infra/` — product data (versioning files live here at runtime)
- `docs/` — feature documentation
- Backend root: `src/web-editor/backend/`
- Frontend root: `src/web-editor/frontend/src/`

---

## Phase 1: Foundational (Blocking Prerequisite)

**Purpose**: The shared Pydantic models are the single dependency that all backend endpoints and the extended commit router share. Must be complete before any user story backend work begins.

**⚠️ CRITICAL**: No user story backend work can begin until this phase is complete.

- [ ] T001 Create `src/web-editor/backend/models/versioning.py` with `VersionEntry` (author, date, notes fields), `VersionFile` (version_name, entries fields), and `VersionNoteIn` (product_shortname, author, date, notes fields) Pydantic models; add `field_validator` for `version_name` (`^[A-Za-z0-9._-]+$`) and `author` (per-token regex `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$`, semicolon-split, error lists all invalid tokens per FR-020)

**Checkpoint**: Pydantic models ready — all backend endpoint development and the git.py extension can now proceed.

---

## Phase 2: User Story 1 — View Version History (Priority: P1) 🎯 MVP

**Goal**: Users can open a product's "Versions" tree node and see all available versions in a selector; selecting one shows its entries in a table; WIP is default; released versions are read-only.

**Independent Test**: Open a product that has `infra/<shortname>/versioning/wip.json` with entries; click the "Versions" tree node; confirm the version selector shows "WIP", the entries table renders with author and date columns, and selecting a released version switches to a read-only view. Also verify: a product with no `versioning/` folder shows an empty-state table.

### Backend — User Story 1

- [ ] T002 [P] [US1] Implement `GET /api/products/{shortname}/versioning` in `src/web-editor/backend/routers/versioning.py` — reads `infra/<shortname>/versioning/` directory; returns `{ wip: bool, versions: [str] }` sorted newest-first; returns `{ wip: false, versions: [] }` if directory absent
- [ ] T003 [P] [US1] Implement `GET /api/products/{shortname}/versioning/{version}` in `src/web-editor/backend/routers/versioning.py` — `version` is `"wip"` or a released version_name; returns `VersionFile` JSON plus `readonly` flag; returns 422 with reset hint if `wip.json` is malformed (FR-018)
- [ ] T004 [P] [US1] Implement `POST /api/products/{shortname}/versioning/wip/reset` in `src/web-editor/backend/routers/versioning.py` — writes a fresh `wip.json` with empty version_name and empty entries array; returns the new file content
- [ ] T005 [US1] Register versioning router in `src/web-editor/backend/main.py` with `prefix="/api"` (alongside existing routers)
- [ ] T006 [P] [US1] Write tests for US1 backend in `src/web-editor/backend/tests/test_versioning.py` — list versions (product with WIP+released, product with no versioning dir), get WIP, get released version (readonly=true), get missing version (404), get malformed WIP (422), reset malformed WIP (200)

### Frontend — User Story 1

- [ ] T007 [P] [US1] Create `src/web-editor/frontend/src/stores/versioning.js` — Pinia store with state: `versionList` (from GET list), `selectedVersion` (default `"wip"`), `versionData` (from GET version file); actions: `fetchVersionList(productSn)`, `selectVersion(productSn, version)`, `reset()`
- [ ] T008 [US1] Add "Versions" leaf node (type `'versions'`) inside the per-product `<template v-if="expanded[sn]">` block in `src/web-editor/frontend/src/components/TreePanel.vue` — styled as existing adoc-node; click calls `store.selectNode({ type: 'versions', product: sn })`
- [ ] T009 [US1] Create `src/web-editor/frontend/src/components/edit/VersioningPanel.vue` — mounts with `productSn` prop; on mount calls `versioningStore.fetchVersionList(productSn)` and `selectVersion('wip')`; renders: version selector `<select>` (WIP + released), `version_name` display field (read-only in this story), entries table with columns Author, Date, Notes; shows empty-state when entries is empty; shows error-state with "Reset to empty WIP" button when malformed WIP is detected (calls reset endpoint then refetches)
- [ ] T010 [US1] Add `VersioningPanel` import and `v-else-if="node.type === 'versions'"` branch in `src/web-editor/frontend/src/components/MainPanel.vue` passing `:productSn="node.product"`

**Checkpoint**: User Story 1 is fully functional. Navigate to any product → Versions → see table. Verify against spec acceptance scenarios 1–4 for US1.

---

## Phase 3: User Story 2 — Manage Version Entries (Priority: P1)

**Goal**: Users can create, edit, and delete change entries in the WIP version table; they can update the shared `version_name`; author validation runs inline; released versions remain read-only.

**Independent Test**: With WIP selected, add an entry with valid multi-author string; confirm it appears in the table and `wip.json` is updated. Edit the entry; change author to an invalid format; confirm error message lists the invalid token and entry is not saved. Delete the entry. Edit the `version_name` field; confirm the WIP file reflects the change. Select a released version; confirm all CRUD controls are hidden.

### Backend — User Story 2

- [ ] T011 [P] [US2] Implement `PATCH /api/products/{shortname}/versioning/wip` in `src/web-editor/backend/routers/versioning.py` — accepts `{ version_name: str }`, validates regex, writes updated `wip.json`; returns 422 on invalid format
- [ ] T012 [P] [US2] Implement `POST /api/products/{shortname}/versioning/wip/entries` in `src/web-editor/backend/routers/versioning.py` — appends VersionEntry to `wip.json` entries array; validates author (all tokens); returns 201 with index + entry; returns 422 with per-token error on invalid author (FR-020)
- [ ] T013 [P] [US2] Implement `PUT /api/products/{shortname}/versioning/wip/entries/{index}` in `src/web-editor/backend/routers/versioning.py` — replaces entry at index; same author validation; returns 404 on out-of-range index
- [ ] T014 [P] [US2] Implement `DELETE /api/products/{shortname}/versioning/wip/entries/{index}` in `src/web-editor/backend/routers/versioning.py` — removes entry at index; returns 404 on out-of-range index
- [ ] T015 [P] [US2] Extend `src/web-editor/backend/tests/test_versioning.py` with US2 test cases — create entry (valid single author, valid multi-author, invalid single, mixed valid/invalid), update entry, delete entry, version_name update (valid, invalid chars), CRUD on released version returns 405

### Frontend — User Story 2

- [ ] T016 [US2] Extend `src/web-editor/frontend/src/components/edit/VersioningPanel.vue` with CRUD controls (shown only when WIP selected): "Add Entry" button opens inline entry form (author text input, date picker, notes textarea); each row gains Edit and Delete buttons; edit re-opens form pre-filled; save calls POST or PUT endpoint; delete calls DELETE endpoint; all three refresh `versioningStore.selectVersion` after success
- [ ] T017 [US2] Add reactive author validation to the entry form in `src/web-editor/frontend/src/components/edit/VersioningPanel.vue` — split input on `;\s*`, validate each token against `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$`, show per-token error message listing all invalid tokens; disable save button until valid
- [ ] T018 [US2] Make `version_name` field editable when WIP is selected in `src/web-editor/frontend/src/components/edit/VersioningPanel.vue` — bind to reactive input; validate `^[A-Za-z0-9._-]+$` inline; call `PATCH .../wip` on blur; show validation error without saving when pattern fails

**Checkpoint**: User Story 2 is fully functional. Verify spec acceptance scenarios 1–5 for US2 including multi-author and validation error cases.

---

## Phase 4: User Story 3 — Release a Product Version (Priority: P2)

**Goal**: A user triggers release from the product panel; a popup collects the new WIP version name; the backend validates, writes the named version file, regenerates the .adoc with a version history section, attempts PDF build, creates a git tag, and seeds a new wip.json.

**Independent Test**: With a product that has a populated `wip.json` (version_name = "1.0.0"): click Release, enter "1.1.0" in the popup. Verify: `infra/<sn>/versioning/1.0.0.json` exists, `infra/<sn>/versioning/wip.json` is a fresh file with version_name "1.1.0" and one seeded entry, `output/<sn>.adoc` contains a `== Version History` section, git tag `<sn>-1.0.0` exists. Then: verify Release is blocked with an error when wip.json is empty, and when "1.0.0" is released again.

### Backend pre-requisites — User Story 3

- [ ] T019 [P] [US3] Create `src/versioning.py` with plain Python dataclasses `VersionEntryData(author: str, date: str, notes: str | None)` and `VersionFileData(version_name: str, entries: list[VersionEntryData])` — no Pydantic dependency, shared by the CLI build pipeline and web editor; extend `src/loader.py` `Product` dataclass with `version_file: VersionFileData | None = None`; in `_load_product()` read `infra/<shortname>/versioning/wip.json`, parse JSON dict into `VersionFileData`; on missing file set `None`; on parse error log warning and set `None`; the web editor's Pydantic `VersionFile` in `src/web-editor/backend/models/versioning.py` maps to/from `VersionFileData` at the router boundary — no direct import between `src/loader.py` and the backend models
- [ ] T020 [P] [US3] Extend `src/renderer.py` — add `render_version_table(version_file: VersionFile) -> str` generating a 4-column AsciiDoc table (Version, Date, Author, Notes) from `version_file.entries`; extend `render_product_document()` to append `\n== Version History\n\n{table}` after the global suffix include when `product.version_file is not None`

### Release endpoint — User Story 3

- [ ] T021 [US3] Implement `POST /api/products/{shortname}/release` in `src/web-editor/backend/routers/versioning.py` following the 10-step sequence in `plan.md` Implementation Notes: (1) read+validate wip.json; (2) validate version_name regex; (3) check no duplicate file; (4) validate new_version_name; (5) write `<version>.json`; (6) regenerate .adoc via render_product_document with version_file set to released data; (7) attempt PDF build, log warning on failure; (8) write new wip.json with `version_name = new_version_name` and one seeded entry: author and date from `entries[-1]` of the just-released version (entries are ordered newest-last per data-model.md), notes = "copied from previous version" (FR-010); (9) `git add -A` + commit; (10) create git tag; return `{ version_name, tag, commit_sha, pdf_generated, new_wip_version_name }`
- [ ] T022 [P] [US3] Extend `src/web-editor/backend/tests/test_versioning.py` with release test cases — happy path (file created, tag exists, new wip seeded), empty WIP blocked (FR-017), duplicate version_name blocked (FR-016), invalid version_name rejected (FR-019), invalid new_version_name rejected, malformed wip.json rejected

### Frontend — User Story 3

- [ ] T023 [US3] Add "Release" button and release popup to `src/web-editor/frontend/src/components/edit/ProductEdit.vue` — button visible when product is not ADDED; clicking opens a modal with a `new_version_name` text input (validated `^[A-Za-z0-9._-]+$` inline) and Confirm/Cancel; on Confirm calls `POST /api/products/{shortname}/release`; on success shows `version_name`, `tag`, and `pdf_generated` status; on error surfaces detail message; on close refreshes tree and versioning store

**Checkpoint**: User Story 3 is fully functional. Verify spec acceptance scenarios 1–4 for US3 including the popup, the seeded wip.json, and the git tag.

---

## Phase 5: User Story 4 — Version Note Prompt on Commit (Priority: P3)

**Goal**: When the user commits, the commit panel shows a collapsible per-product section for each changed product, allowing optional version note entry (author, date, notes). Notes are sent with the commit request and appended to the corresponding wip.json files.

**Independent Test**: Make a change to a product. Open CommitPanel. Confirm a collapsible "Add version note" section appears for that product. Fill in a valid author, date, and notes. Click "Commit & Push". Confirm the entry is appended to `infra/<shortname>/versioning/wip.json` in the commit. Confirm skipping the section (leaving it empty) does not block the commit.

### Backend — User Story 4

- [ ] T024 [US4] Extend `CommitBody` in `src/web-editor/backend/routers/git.py` with `version_notes: list[VersionNoteIn] = []`; before `write_all()` loop over notes: validate each (re-raise as 422 listing index + error on failure), read the product's `wip.json`, append new entry, write back; then proceed with existing `write_all()` + commit flow
- [ ] T025 [P] [US4] Extend `src/web-editor/backend/tests/test_versioning.py` with commit+version-note test cases — valid note appended to wip.json, invalid author blocks commit (422), note for product with no pending sizing changes is accepted, empty version_notes list has no effect

### Frontend — User Story 4

- [ ] T026 [US4] Extend `src/web-editor/frontend/src/components/CommitPanel.vue` — after fetching changes, extract unique product shortnames from the `changes` list using this rule: for each entry take the segment before the first ` / ` separator, or the second path segment of `infra/<shortname>/...` strings (e.g. `"acme-crm / small"` → `"acme-crm"`, `"infra/acme-crm/prefix.adoc"` → `"acme-crm"`); deduplicate; for each unique shortname render a collapsible "Version note for <shortname>" section with author text input (inline validation), date input, notes textarea; on commit, collect non-empty sections into `version_notes` array and include in the `POST /api/git/commit` body; empty sections are excluded (commit proceeds as normal)

**Checkpoint**: User Story 4 is fully functional. Verify spec acceptance scenarios 1–4 for US4 including skip, valid note, and invalid author format.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T027 [P] Create `docs/product-versioning/overview.md` — feature description, release workflow diagram (text), and operational notes for adding first version, releasing, and recovering from malformed wip.json
- [ ] T028 [P] Create `docs/product-versioning/file-structure.md` — annotated `versioning/` directory layout, full JSON schemas for wip.json and released version files with field descriptions and validation rules
- [ ] T029 Validate all acceptance scenarios from `specs/004-product-versioning/spec.md` against the running application (US1 ×4, US2 ×5, US3 ×4, US4 ×4) and confirm all edge cases in the Edge Cases section are handled per their specified behaviour

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **User Story 1 (Phase 2)**: Depends on T001 (models) — can begin after Phase 1
- **User Story 2 (Phase 3)**: Depends on Phase 2 complete (CRUD extends the panel from US1)
- **User Story 3 (Phase 4)**: Depends on T001 (models), T005 (router registered) — T019 and T020 can start in parallel with US2
- **User Story 4 (Phase 5)**: Depends on T001 (models) — can begin after Phase 1; independent of US2 and US3
- **Polish (Phase 6)**: Depends on all desired user stories complete

### User Story Dependencies

- **US1 (P1)**: After Phase 1 — no dependency on other stories
- **US2 (P1)**: Builds on US1 frontend panel (extends it with CRUD controls); US1 must be complete first
- **US3 (P2)**: T019, T020 (loader + renderer) independent of US1/US2; T021 (release endpoint) independent of US2; T023 (frontend) depends on US1 (tree node must exist)
- **US4 (P3)**: Fully independent — only depends on T001 (models) and the existing commit flow

### Within Each User Story

- Backend models/validators before router endpoints
- Router registration before frontend integration
- Core endpoint implementation before tests
- Panel base (read-only) before CRUD controls

---

## Parallel Opportunities

### Phase 2 (US1) — can launch these in parallel:
```
T002 GET list endpoint
T003 GET version file endpoint
T004 POST reset endpoint
T006 US1 backend tests
T007 Pinia versioning store
```
Then sequentially: T005 (register router) → T008/T009/T010 (frontend integration)

### Phase 3 (US2) — can launch these in parallel:
```
T011 PATCH version_name endpoint
T012 POST create entry endpoint
T013 PUT update entry endpoint
T014 DELETE entry endpoint
T015 US2 backend tests
```
Then sequentially: T016 → T017 → T018 (frontend in order, same file)

### Phase 4 (US3) — can launch in parallel with Phase 3:
```
T019 loader.py extension
T020 renderer.py extension
T022 US3 backend tests (written after T021)
```
T021 (release endpoint) depends on T019 and T020

### Phase 4 and Phase 5 backend tasks can run in parallel with each other after Phase 1.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001)
2. Complete Phase 2: User Story 1 (T002–T010)
3. **STOP and VALIDATE**: Open the web editor, navigate to a product, click Versions, confirm the table renders
4. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 (US1) → Read-only version history visible in editor (**MVP!**)
3. Phase 3 (US2) → Full CRUD on version entries + version_name editing
4. Phase 4 (US3) → Release flow with PDF, git tag, and seeded WIP
5. Phase 5 (US4) → Commit-time version note prompt
6. Each phase adds value without breaking the previous

### Parallel Team Strategy

After Phase 1 completes:
- Developer A: US1 backend (T002–T006) + US1 frontend (T007–T010)
- Developer B: US3 pre-requisites (T019, T020) — loader + renderer — in parallel
- Once US1 is done: Developer A continues with US2 (T011–T018), Developer B continues with US3 endpoint (T021–T023)
- US4 (T024–T026) can be picked up independently by either developer after Phase 1

---

## Notes

- `[P]` tasks = different files, no dependencies within the same phase — safe to parallelise
- `[Story]` label maps each task to its user story for traceability
- Each user story phase is a complete, independently testable increment
- No new Python or JS dependencies — `requirements.txt` and `package.json` are not modified
- Tests in `test_versioning.py` are additive — append test cases per phase; do not rewrite the file from scratch each time
- Backend validation is authoritative; frontend validation is fast-feedback only and mirrors the backend rules exactly
